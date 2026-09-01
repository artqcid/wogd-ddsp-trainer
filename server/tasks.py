"""
Celery app + async training / synthesis jobs for the wogd-ddsp-trainer M4 backend.

Provides:
- ``celery_app`` (broker ``WOGD_REDIS_URL`` or ``redis://localhost:6379/0``).
- Job helpers: ``runs_dir``, ``run_checkpoint_dir``, ``latest_checkpoint``,
  ``fft_sizes_for_scales``, ``build_training``, ``build_tensors``.
- Celery tasks: ``run_training_job``, ``run_synthesis_job``.
- ``TaskRunner`` protocol + ``CeleryTaskRunner`` + ``get_task_runner()``.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import suppress
from pathlib import Path
from typing import Protocol

import torch
import torchaudio
from celery import Celery
from torch.utils.data import DataLoader

from dataset.cache import FeatureCache
from inference.render import load_model_from_checkpoint, render_to_file
from model import DDSPConfig, DDSPModel, MultiScaleSpectralLoss
from model.ddsp.variant import DDSPVariant
from server.db import (
    connect,
    run_get,
    run_is_stop_requested,
    run_set_error,
    run_set_status,
    synth_get,
    synth_update,
)
from train import Trainer, TrainingConfig

# ---------------------------------------------------------------------------
# Celery app
# ---------------------------------------------------------------------------

celery_app = Celery(
    "wogd_ddsp",
    broker_url=os.environ.get("WOGD_REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.environ.get("WOGD_REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True

# ---------------------------------------------------------------------------
# Job helpers
# ---------------------------------------------------------------------------


def runs_dir() -> Path:
    """Return the runs output folder under the effective data root."""
    from server.paths import runs_dir as _paths_runs_dir

    return _paths_runs_dir()


def run_checkpoint_dir(run_id: str) -> Path:
    return runs_dir() / run_id / "checkpoints"


def latest_checkpoint(run_id: str) -> Path | None:
    ckpt_dir = run_checkpoint_dir(run_id)
    step_numbers: list[int] = []
    for p in ckpt_dir.iterdir():
        if p.is_file() and p.suffix == ".pt" and p.stem.startswith("step-"):
            try:
                step_numbers.append(int(p.stem.split("-", 1)[1]))
            except ValueError:
                continue
    if not step_numbers:
        return None
    return ckpt_dir / f"step-{max(step_numbers)}.pt"


def fft_sizes_for_scales(n: int) -> list[int]:
    """Deterministic, log-spaced FFT sizes for :data:`n` stft scales."""
    if n == 3:
        return [512, 1024, 2048]
    if n == 5:
        return [256, 512, 1024, 2048, 4096]
    if n == 8:
        return [128, 256, 512, 1024, 2048, 4096, 8192, 16384]
    return [512, 1024, 2048]


def build_training(
    model_config: dict, checkpoint_dir: Path
) -> tuple[TrainingConfig, DDSPConfig, MultiScaleSpectralLoss | None]:
    hidden_size = model_config["hidden_size"]
    stft_scales = model_config["stft_scales"]
    mixed_precision = model_config["mixed_precision"]
    gradient_checkpointing = model_config["gradient_checkpointing"]
    learning_rate = float(model_config["learning_rate"])
    max_steps = int(model_config.get("max_steps", 1000))
    device = model_config.get("device", "auto")

    variant_dict = model_config.get("variant", {}) or {}
    variant = DDSPVariant.from_dict(variant_dict)
    use_latent = model_config.get("use_latent", False)
    latent_dim = int(model_config.get("latent_dim", 32))
    kl_beta = float(model_config.get("kl_beta", 0.0001))
    kl_warmup = int(model_config.get("kl_warmup_steps", 2000))
    dcfg = DDSPConfig(
        hidden_size=hidden_size,
        stft_scales=fft_sizes_for_scales(stft_scales),
        variant=variant,
        use_latent=use_latent,
        latent_dim=latent_dim,
    )

    band_mask = None
    if variant.loss_band_mask:
        band_mask = [tuple(pair) for pair in variant.loss_band_mask]
    loss_fn = MultiScaleSpectralLoss(
        fft_sizes=fft_sizes_for_scales(stft_scales),
        band_mask=band_mask,
        sample_rate=16000,
    ) if band_mask else None

    use_mixed_precision = mixed_precision in {"required", "recommended"}
    use_gradient_checkpointing = gradient_checkpointing == "enabled"

    tcfg = TrainingConfig(
        device=device,
        learning_rate=learning_rate,
        max_steps=max_steps,
        use_mixed_precision=use_mixed_precision,
        use_gradient_checkpointing=use_gradient_checkpointing,
        log_dir=str(checkpoint_dir.parent / "tb"),
        log_interval=10,
        checkpoint_interval=500,
        gradient_accumulation_steps=1,
        kl_beta=kl_beta if use_latent else 0.0,
        kl_warmup_steps=kl_warmup,
    )
    return tcfg, dcfg, loss_fn


def build_tensors(
    model: DDSPModel, dataset_id: str | None
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if dataset_id is not None:
        from server.paths import datasets_dir

        cache = FeatureCache(datasets_dir() / dataset_id)
        if cache.exists("train"):
            arrays = cache.load("train")  # dict-like
            f0 = arrays.get("f0_hz") or arrays.get("f0")
            loudness = arrays.get("loudness_db") or arrays.get("loudness")
            audio = arrays.get("audio") or arrays.get("waveform")
            if f0 is not None and loudness is not None:
                f0_t = torch.as_tensor(f0, dtype=torch.float32)
                loudness_t = torch.as_tensor(loudness, dtype=torch.float32)
                if audio is not None:
                    target_t = torch.as_tensor(audio, dtype=torch.float32)
                else:
                    with torch.no_grad():
                        target_t = model(f0_t, loudness_t)["audio"]
                if f0_t.dim() == 1:
                    f0_t = f0_t.unsqueeze(0)
                if loudness_t.dim() == 1:
                    loudness_t = loudness_t.unsqueeze(0)
                return f0_t, loudness_t, target_t

    if dataset_id is None:
        logging.warning("no dataset_id provided, using synthetic data")
    else:
        has_f0 = f0 is not None if "f0" in locals() else False
        has_loudness = loudness is not None if "loudness" in locals() else False
        has_audio = audio is not None if "audio" in locals() else False
        if "cache" in locals() and not cache.exists("train"):
            logging.warning(
                "cache not found for dataset_id=%s, using synthetic data",
                dataset_id,
            )
        else:
            logging.warning(
                "missing expected keys in cache for dataset_id=%s "
                "(missing f0=%s, loudness=%s, audio=%s), using synthetic data",
                dataset_id,
                has_f0,
                has_loudness,
                has_audio,
            )

    torch.manual_seed(0)
    f0 = torch.full((1, 16), 220.0, dtype=torch.float32)
    loudness = torch.rand(1, 16, dtype=torch.float32).log()
    with torch.no_grad():
        target = model(f0, loudness)["audio"]
    return f0, loudness, target


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------


@celery_app.task(name="server.tasks.run_training_job")
def run_training_job(run_id: str) -> dict:
    conn = connect()
    run = run_get(conn, run_id)
    if run is None:
        conn.close()
        return {"ok": False, "error": "run not found"}

    run_set_status(conn, run_id, "running")
    conn.commit()

    checkpoint_dir = run_checkpoint_dir(run_id)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    try:
        tcfg, dcfg, loss_fn = build_training(run["config"], checkpoint_dir)
        model = DDSPModel(dcfg)

        latest = latest_checkpoint(run_id)
        if latest is not None:
            trainer_loader = Trainer(model, tcfg, loss_fn=None)  # temporary for load_checkpoint
            trainer_loader.load_checkpoint(str(latest))
            model.eval()

        dataset_id = run.get("dataset_id")

        # Data loading branch: real DataLoader when a valid dataset_id is
        # provided and the cache on disk exists; otherwise fall back to a
        # single-batch synthetic tensor via build_tensors() (which also owns
        # the M4.7.1 warning logging).
        data_loader: DataLoader | None = None
        f0: torch.Tensor | None = None
        loudness: torch.Tensor | None = None
        target: torch.Tensor | None = None

        if dataset_id is not None:
            from server.paths import datasets_dir

            cache_path = datasets_dir() / dataset_id
            if cache_path.exists():
                from dataset.loader import DDSPDataset

                ds = DDSPDataset(str(cache_path), key="train", seq_len=64000)
                data_loader = DataLoader(ds, batch_size=1, shuffle=True)
            else:
                f0, loudness, target = build_tensors(model, dataset_id)
        else:
            f0, loudness, target = build_tensors(model, None)

        trainer = Trainer(model, tcfg, loss_fn=loss_fn)
        trainer._checkpoint_dir = str(checkpoint_dir)

        stop_event = threading.Event()

        def _watch_stop_request() -> None:
            while not stop_event.is_set():
                try:
                    my_conn = connect()
                    stop = run_is_stop_requested(my_conn, run_id)
                    my_conn.close()
                except Exception:
                    stop = False
                if stop:
                    stop_event.set()
                    break
                stop_event.wait(timeout=0.5)

        watcher = threading.Thread(target=_watch_stop_request, daemon=True)
        watcher.start()

        stop_requested = False
        try:
            if data_loader is not None:
                summary = trainer.run(data_loader=data_loader, stop_event=stop_event)
            else:
                summary = trainer.run(f0, loudness, target, stop_event=stop_event)
            stop_requested = stop_event.is_set()
            status = "stopped" if stop_requested else "completed"
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            err_msg = str(exc)
            summary = {"error": err_msg}
            run_set_error(conn, run_id, err_msg)
        finally:
            run_set_status(conn, run_id, status)
            conn.commit()
            with suppress(Exception):
                trainer.close()
        return {"ok": True, "run_id": run_id, "status": status, "summary": summary}
    finally:
        conn.close()


@celery_app.task(name="server.tasks.run_synthesis_job")
def run_synthesis_job(job_id: str) -> dict:
    conn = connect()
    job = synth_get(conn, job_id)
    if job is None:
        conn.close()
        return {"ok": False, "error": "job not found"}

    params = job["params"]
    run_id = params["run_id"]
    ckpt = latest_checkpoint(run_id)
    if ckpt is None:
        synth_update(conn, job_id, status="failed", error="no checkpoint")
        conn.commit()
        conn.close()
        return {"ok": False, "error": "no checkpoint"}

    synth_update(conn, job_id, status="running")
    conn.commit()

    try:
        model = load_model_from_checkpoint(str(ckpt))

        seed = int(params.get("seed", 0))
        torch.manual_seed(seed)
        base_f0 = float(params.get("base_f0", 220.0)) + float(params.get("pitch_shift", 0.0))
        f0 = torch.full((1, 32), base_f0, dtype=torch.float32)
        loudness = torch.rand(1, 32, dtype=torch.float32).log()

        out_path = runs_dir() / run_id / "synthesis" / f"{job_id}.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        enhance = bool(params.get("enhance", False))
        render_to_file(model, f0, loudness, str(out_path), enhance=enhance)

        synth_update(conn, job_id, status="completed", artifact_path=str(out_path))
        conn.commit()
        conn.close()
        return {"ok": True, "job_id": job_id, "status": "completed", "artifact_path": str(out_path)}
    except Exception as exc:
        err_msg = str(exc)
        synth_update(conn, job_id, status="failed", error=err_msg)
        conn.commit()
        conn.close()
        return {"ok": False, "error": err_msg}


@celery_app.task(name="server.tasks.run_morph_job")
def run_morph_job(job_id: str) -> dict:
    conn = connect()
    job = synth_get(conn, job_id)
    if job is None:
        conn.close()
        return {"ok": False, "error": "job not found"}

    params = job["params"]
    run_id_a = params["run_id_a"]
    run_id_b = params["run_id_b"]
    alpha = float(params.get("alpha", 0.5))

    ckpt_a = latest_checkpoint(run_id_a)
    ckpt_b = latest_checkpoint(run_id_b)
    if ckpt_a is None or ckpt_b is None:
        synth_update(conn, job_id, status="failed", error="missing checkpoint")
        conn.commit()
        conn.close()
        return {"ok": False, "error": "missing checkpoint"}

    synth_update(conn, job_id, status="running")
    conn.commit()

    try:
        model_a = load_model_from_checkpoint(str(ckpt_a))
        model_b = load_model_from_checkpoint(str(ckpt_b))

        seed = int(params.get("seed", 0))
        torch.manual_seed(seed)
        base_f0 = float(params.get("base_f0", 220.0)) + float(params.get("pitch_shift", 0.0))
        f0 = torch.full((1, 32), base_f0, dtype=torch.float32)
        loudness = torch.rand(1, 32, dtype=torch.float32).log()

        if model_a.config.use_latent and model_b.config.use_latent:
            model_a.eval()
            model_b.eval()
            with torch.no_grad():
                mu_a, _ = model_a.encoder(f0, loudness)
                mu_b, _ = model_b.encoder(f0, loudness)
                z = alpha * mu_a + (1 - alpha) * mu_b
        else:
            z = None

        if z is not None:
            features = torch.cat([torch.stack([f0, loudness], dim=-1), z], dim=-1)
            gru_out, _ = model_a.gru(features)
            hidden = torch.relu(model_a.feature_proj(gru_out))
            n_samples = (f0.shape[1] - 1) * model_a.config.frame_size + 1
            audio = model_a.ddsp_core(
                amplitudes=torch.sigmoid(model_a.amplitude_out(hidden)),
                harmonic_distribution=torch.softmax(model_a.distribution_out(hidden), dim=-1),
                f0=f0,
                noise_magnitudes=torch.sigmoid(model_a.noise_magnitudes_out(hidden)),
                n_samples=n_samples,
            )
        else:
            audio = model_a(f0, loudness)["audio"]

        out_path = runs_dir() / run_id_a / "synthesis" / f"{job_id}.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(out_path), audio.cpu().unsqueeze(0), 16000)

        synth_update(conn, job_id, status="completed", artifact_path=str(out_path))
        conn.commit()
        conn.close()
        return {"ok": True, "job_id": job_id, "status": "completed", "artifact_path": str(out_path)}
    except Exception as exc:
        err_msg = str(exc)
        synth_update(conn, job_id, status="failed", error=err_msg)
        conn.commit()
        conn.close()
        return {"ok": False, "error": err_msg}


# ---------------------------------------------------------------------------
# Task runner abstraction
# ---------------------------------------------------------------------------


class TaskRunner(Protocol):
    """Protocol for task runners wired into the REST layer."""

    def submit_training(self, run_id: str) -> str:
        """Submit a training job; return the Celery task id (str)."""

    def submit_synthesis(self, job_id: str) -> str:
        """Submit a synthesis job; return the Celery task id (str)."""


class CeleryTaskRunner:
    """Default :class:`TaskRunner` that delegates to Celery tasks."""

    def submit_training(self, run_id: str) -> str:
        result = run_training_job.apply_async(args=[run_id])
        return result.id  # type: ignore[no-any-return]

    def submit_synthesis(self, job_id: str) -> str:
        result = run_synthesis_job.apply_async(args=[job_id])
        return result.id  # type: ignore[no-any-return]


_runner: TaskRunner | None = None


def get_task_runner() -> TaskRunner:
    """Lazily construct and return the module-global ``TaskRunner``."""
    global _runner
    if _runner is None:
        _runner = CeleryTaskRunner()
    return _runner
