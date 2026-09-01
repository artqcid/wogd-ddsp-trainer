"""MIDI synthesizer wrapper: TorchScript-compatible layer over DDSPModel / PolyDDSPModel.

MidiSynthWrapper wraps a trained DDSPModel (any tier) or PolyDDSPModel so that
inference accepts per-frame MIDI data (note frequency, loudness, optional gate)
instead of audio-derived F0/loudness features. The realtime F0 extractor is
replaced by MIDI-note-to-F0 frame generation at the caller side.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class MidiSynthWrapper(nn.Module):
    """Wraps a trained DDSPModel or PolyDDSPModel for MIDI synthesizer inference.

    Input: per-frame MIDI data (note_hz, loudness_db) and optional latent vector.
    Output: synthesized mono audio waveform.

    Compatible with DDSPModel (single-voice, any engine) and PolyDDSPModel
    (multi-voice). Detects the underlying model type by checking for the
    ``n_voices`` attribute on the wrapped model.

    Example (single-voice DDSPModel)::

        wrapper = MidiSynthWrapper(model)
        audio = wrapper(note_hz, loudness_db)  # (T_audio,)

    Example (PolyDDSPModel, N voices)::

        wrapper = MidiSynthWrapper(poly_model)  # n_voices from the poly model
        audio = wrapper(f0_voices)              # (N, T_frames) -> summed mono

    TorchScript notes
    -----------------
    This module is written to be compatible with ``torch.jit.script`` where
    feasible. Python-only union types (``X | None``) are avoided in favour of
    ``Optional[...]``. ``torch.jit.trace`` is the safer path for models with
    dynamic Python branches; ``torch.jit.script`` may fail on the
    ``hasattr``-based model dispatch inside ``forward``. If scripting is
    required, prefer scripting ``_forward_mono`` / ``_forward_poly``
    individually after binding the correct path at init time.
    """

    def __init__(
        self,
        model: nn.Module,
        frame_size: int = 128,
    ) -> None:
        """Initialise the wrapper.

        Args:
            model: a trained ``DDSPModel`` or ``PolyDDSPModel`` instance.
            frame_size: the frame size (samples per frame) of the wrapped model.
                Stored for documentation/shape validation; does not affect the
                forward pass itself since the model already encodes its hop length.
        """
        super().__init__()
        self.model = model
        self.frame_size = frame_size

        # Derive n_voices from the wrapped model when possible.
        # DDSPModel has n_voices == 1 by default; PolyDDSPModel carries its own.
        self.n_voices: int = getattr(model, "n_voices", 1)

    # ------------------------------------------------------------------
    # Public forward
    # ------------------------------------------------------------------

    def forward(
        self,
        f0: torch.Tensor,  # (T_frames,) or (N, T_frames)
        loudness_db: torch.Tensor,  # (T_frames,)
    ) -> torch.Tensor:
        """Synthesize audio from per-frame MIDI features.

        Args:
            f0: per-frame fundamental frequency in Hz.
                For single-voice (DDSPModel) wrapping this is shape ``(T_frames,)``.
                For polyphonic (PolyDDSPModel) wrapping this is
                ``(N_voices, T_frames)`` — one F0 track per voice.
            loudness_db: per-frame loudness in dB, shape ``(T_frames,)``, shared
                across all voices for polyphonic mode.

        Returns:
            Synthesized mono audio waveform, shape ``(T_audio,)``.
        """
        # Basic shape sanity (kept loose so tracing is not overly constrained).
        if f0.dim() == 1:
            return self._forward_mono(f0, loudness_db)
        if f0.dim() == 2:
            return self._forward_poly(f0, loudness_db)
        raise ValueError(
            f"Expected f0 to be 1-D (T_frames,) or 2-D (N_voices, T_frames), "
            f"got shape {tuple(f0.shape)}"
        )

    # ------------------------------------------------------------------
    # Single-voice path (DDSPModel)
    # ------------------------------------------------------------------

    def _forward_mono(
        self,
        note_hz: torch.Tensor,  # (T_frames,)
        loudness_db: torch.Tensor,  # (T_frames,)
    ) -> torch.Tensor:
        """Single-voice synthesis from one F0 + loudness track.

        Adds the batch dimension expected by ``DDSPModel.forward``, calls the
        model, and removes the batch dimension from the returned audio.
        """
        f0 = note_hz.unsqueeze(0)  # (1, T_frames)
        loudness = loudness_db.unsqueeze(0)  # (1, T_frames)

        out = self.model(f0, loudness)

        audio: torch.Tensor = out["audio"]  # (1, T_audio)
        return audio.squeeze(0)  # (T_audio,)

    # ------------------------------------------------------------------
    # Multi-voice path (PolyDDSPModel)
    # ------------------------------------------------------------------

    def _forward_poly(
        self,
        f0_voices: torch.Tensor,  # (N_voices, T_frames)
        loudness_db: torch.Tensor,  # (T_frames,)
    ) -> torch.Tensor:
        """Multi-voice synthesis from N independent F0 tracks.

        Stacks the per-voice F0 tracks into a single batched tensor and calls
        PolyDDSPModel.forward once. The model handles voice iteration and
        per-voice averaging internally.
        """
        if f0_voices.size(0) == 0:
            raise ValueError("f0_voices must contain at least one voice")

        f0 = f0_voices.unsqueeze(0)  # (1, N, T_frames)
        loudness = loudness_db.unsqueeze(0)  # (1, T_frames)
        out = self.model(f0, loudness)
        return out["audio"].squeeze(0)  # (T_audio,)


__all__ = ["MidiSynthWrapper"]
