"""Polyphonic DDSP model: N shared/independent DDSP voices summed to mono audio."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from model.ddsp_model import DDSPConfig, DDSPModel

if TYPE_CHECKING:
    from torch import Tensor


class PolyDDSPModel(nn.Module):
    """N-voice polyphonic DDSP model.

    Shared decoder weights across all voices by default. Each voice receives
    its own f0 track; loudness is shared.
    """

    def __init__(self, config: DDSPConfig, n_voices: int = 2, independent: bool = False) -> None:
        super().__init__()
        self.config = config
        self.n_voices = n_voices
        if independent:
            self.voices = nn.ModuleList([DDSPModel(config) for _ in range(n_voices)])
        else:
            self.shared_voice = DDSPModel(config)
            self.voices = None

    def forward(self, f0_voices: Tensor, loudness: Tensor) -> dict[str, Tensor]:
        """Run the polyphonic model.

        Args:
            f0_voices: per-voice per-frame fundamental frequency in Hz,
                shape (B, N, T_frames).
            loudness: per-frame log energy, shape (B, T_frames);
                shared across all voices.

        Returns:
            Dict with summed and normalised audio under the ''audio'' key.
        """
        audio_sum = None
        for i in range(self.n_voices):
            model = self.voices[i] if self.voices else self.shared_voice
            f0_i = f0_voices[:, i, :]
            out_i = model(f0_i, loudness)
            audio_sum = out_i["audio"] if audio_sum is None else audio_sum + out_i["audio"]
        return {"audio": audio_sum / self.n_voices}

    def save_checkpoint(self, path: str) -> None:
        state = {
            "model_state_dict": self.state_dict(),
            "config": self.config,
            "n_voices": self.n_voices,
        }
        torch.save(state, path)

    @classmethod
    def load_checkpoint(
        cls, path: str, n_voices: int = 2, independent: bool = False
    ) -> PolyDDSPModel:
        import torch.serialization as _ts

        with _ts.safe_globals([DDSPConfig]):
            state = torch.load(path, map_location="cpu", weights_only=True)

        saved_n_voices = state.get("n_voices", 2)
        if saved_n_voices != n_voices:
            raise ValueError(
                f"Checkpoint n_voices '{saved_n_voices}' does not match "
                f"requested n_voices '{n_voices}'"
            )

        config = state["config"]
        if not isinstance(config, DDSPConfig):
            config = DDSPConfig(**config)
        config.n_voices = saved_n_voices

        model = cls(config=config, n_voices=n_voices, independent=independent)
        model.load_state_dict(state["model_state_dict"])
        return model
