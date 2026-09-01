"""Load precomputed .npy features written by dataset.features.save_features."""

from __future__ import annotations

import os

import numpy as np
import torch
from torch.utils.data import Dataset

from dataset.cache import FeatureCache

# feature temporal resolution: 1 feature frame per 160 audio samples (10 ms at 16 kHz)
AUDIO_SAMPLES_PER_FRAME = 160


def load_features(
    out_dir: str,
    base_name: str,
) -> dict[str, np.ndarray]:
    """Read the three .npy feature files back into a dict (float32).

    Keys: "f0_hz", "f0_confidence", "loudness_db".
    """
    keys = ("f0_hz", "f0_confidence", "loudness_db")
    result: dict[str, np.ndarray] = {}
    for key in keys:
        path = os.path.join(out_dir, f"{base_name}.{key}.npy")
        result[key] = np.load(path).astype(np.float32)
    # Optional multi-voice f0
    voices_path = os.path.join(out_dir, f"{base_name}.f0_hz_voices.npy")
    if os.path.exists(voices_path):
        result["f0_hz_voices"] = np.load(voices_path).astype(np.float32)
    # Optional content embedding
    ce_path = os.path.join(out_dir, f"{base_name}.content_embedding.npy")
    if os.path.exists(ce_path):
        result["content_embedding"] = np.load(ce_path).astype(np.float32)
    return result


class DDSPDataset(Dataset):
    """PyTorch Dataset wrapping a merged FeatureCache, yielding chunked training samples.

    The cache stores a single merged array per key (audio + features concatenated from
    all source files). Audio is 16 kHz; features are at 10 ms resolution (hop = 160
    samples). Chunks are ``seq_len`` audio samples; corresponding feature frames are
    computed from sample indices.
    """

    def __init__(
        self,
        cache_dir: str | os.PathLike,
        key: str = "train",
        seq_len: int = 64000,
        seed: int = 42,
        n_voices: int = 1,
    ) -> None:
        self.seq_len = seq_len
        self.n_voices = n_voices
        self._rng = np.random.default_rng(seed)

        cache = FeatureCache(cache_dir)
        features, meta = cache.load(key)
        if features is None:
            raise FileNotFoundError(f"No cached features for key={key!r} in {cache_dir!r}")

        self.audio = features["audio"].astype(np.float32)
        self.f0_hz = features["f0_hz"].astype(np.float32)
        self.loudness_db = features["loudness_db"].astype(np.float32)

        # Content embedding
        self.content_embedding: np.ndarray | None = None
        if "content_embedding" in features:
            self.content_embedding = features["content_embedding"].astype(np.float32)

        total_audio = self.audio.shape[0]
        self.n_chunks = total_audio // seq_len
        self._frames_per_chunk = seq_len // AUDIO_SAMPLES_PER_FRAME

        if n_voices > 1:
            total_frames = self.f0_hz.shape[0]
            if "f0_hz_voices" in features:
                self.f0_voices = features["f0_hz_voices"].astype(np.float32)
            else:
                self.f0_voices = np.zeros((n_voices, total_frames), dtype=np.float32)
                self.f0_voices[0, :] = self.f0_hz
        else:
            self.f0_voices = None

    def __len__(self) -> int:
        return self.n_chunks

    def __getitem__(
        self, index: int
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor | None]:
        """Return (f0_chunk, loudness_chunk, audio_chunk, content_embedding) as tensors.

        Shapes: (1, n_frames_features) for f0/loudness, (1, seq_len) for audio.
        content_embedding is (T_frames, D) float32 or None if not cached.
        """
        if not 0 <= index < self.n_chunks:
            raise IndexError(f"index {index} out of range [0, {self.n_chunks})")

        start_sample = index * self.seq_len
        end_sample = start_sample + self.seq_len

        audio_chunk = self.audio[start_sample:end_sample]
        start_frame = index * self._frames_per_chunk
        end_frame = start_frame + self._frames_per_chunk

        loudness_chunk = self.loudness_db[start_frame:end_frame]

        # Content embedding (optional)
        content_t: torch.Tensor | None = None
        if self.content_embedding is not None:
            content_chunk = self.content_embedding[start_frame:end_frame]
            content_t = torch.from_numpy(content_chunk).float()

        if self.n_voices > 1:
            f0_voices_chunk = self.f0_voices[:, start_frame:end_frame]
            return (
                torch.from_numpy(f0_voices_chunk).float(),
                torch.from_numpy(loudness_chunk).float().unsqueeze(0),
                torch.from_numpy(audio_chunk).float().unsqueeze(0),
                content_t,
            )

        f0_chunk = self.f0_hz[start_frame:end_frame]

        # (1, T) tensors for model input
        audio_t = torch.from_numpy(audio_chunk).float().unsqueeze(0)
        f0_t = torch.from_numpy(f0_chunk).float().unsqueeze(0)
        loudness_t = torch.from_numpy(loudness_chunk).float().unsqueeze(0)

        return f0_t, loudness_t, audio_t, content_t
