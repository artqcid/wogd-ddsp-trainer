"""Optional output enhancer for DDSP-synthesized audio.

Uses a pre-trained vocoder (Vocos primary, BigVGAN fallback) to improve
perceived audio quality. Falls back to identity (passthrough) when no
vocoder is available.
"""

from __future__ import annotations

import logging

import torch

logger = logging.getLogger(__name__)


class OutputEnhancer:
    """Post-processing enhancer for DDSP audio output.

    Supports three backends in priority order:
    1. Vocos (best — lightweight, MIT, HF from_pretrained)
    2. BigVGAN (fallback — MIT, HF, slightly heavier)
    3. Identity (passthrough — always works)
    """

    def __init__(self, device: str | torch.device = "cpu") -> None:
        self.device = torch.device(device)
        self._model = None
        self._sample_rate: int = 16000
        self._vocoder_sr: int = 24000  # Vocos default
        self._backend: str = "identity"
        self._init_vocos()

    def _init_vocos(self) -> None:
        """Try to load Vocos; fall back to BigVGAN, then identity."""
        if self._try_vocos():
            return
        if self._try_bigvgan():
            return
        logger.warning("No vocoder available; enhancer operates as passthrough (identity).")

    def _try_vocos(self) -> bool:
        try:
            import vocos
        except ImportError:
            return False
        try:
            model = vocos.Vocos.from_pretrained("charactr/vocos-mel-24khz")
            model = model.to(self.device)
            model.eval()
            self._model = model
            self._backend = "vocos"
            self._vocoder_sr = 24000
            logger.info("OutputEnhancer using Vocos (charactr/vocos-mel-24khz)")
            return True
        except Exception as e:
            logger.warning("Vocos load failed: %s", e)
            return False

    def _try_bigvgan(self) -> bool:
        try:
            from transformers import AutoModel

            model = AutoModel.from_pretrained("nvidia/bigvgan_base_22khz_80band")
            model = model.to(self.device)
            model.eval()
            self._model = model
            self._backend = "bigvgan"
            self._vocoder_sr = 22000
            logger.info("OutputEnhancer using BigVGAN (nvidia/bigvgan_base_22khz_80band)")
            return True
        except Exception as e:
            logger.warning("BigVGAN load failed: %s", e)
            return False

    @property
    def is_active(self) -> bool:
        """True when a real vocoder backend is loaded (not identity)."""
        return self._backend != "identity"

    @property
    def backend_name(self) -> str:
        return self._backend

    @torch.no_grad()
    def enhance(
        self,
        audio: torch.Tensor,
        sample_rate: int = 16000,
    ) -> torch.Tensor:
        """Enhance audio through the loaded vocoder.

        Args:
            audio: Audio tensor, shape (T,) or (1, T) or (B, T), float32 in [-1, 1].
            sample_rate: Sample rate of input audio.

        Returns:
            Enhanced audio, same shape and sample rate as input.
        """
        if not self.is_active:
            return audio

        # Ensure 3D (B, 1, T) for resampling
        input_was_1d = False
        if audio.dim() == 1:
            audio = audio.unsqueeze(0).unsqueeze(0)
            input_was_1d = True
        elif audio.dim() == 2:
            audio = audio.unsqueeze(1)

        B, C, T = audio.shape

        if sample_rate != self._vocoder_sr:
            new_t = int(T * self._vocoder_sr / sample_rate)
            audio = torch.nn.functional.interpolate(
                audio, size=new_t, mode="linear", align_corners=False
            )

        if self._backend == "vocos":
            enhanced = self._enhance_vocos(audio)
        elif self._backend == "bigvgan":
            enhanced = self._enhance_bigvgan(audio)
        else:
            enhanced = audio

        # Resample back to original sample rate if needed
        if sample_rate != self._vocoder_sr:
            enhanced = torch.nn.functional.interpolate(
                enhanced, size=T, mode="linear", align_corners=False
            )

        if input_was_1d:
            enhanced = enhanced.squeeze(0).squeeze(0)
        elif C == 1 and enhanced.size(1) == 1:
            enhanced = enhanced.squeeze(1)

        return enhanced

    def _enhance_vocos(self, audio: torch.Tensor) -> torch.Tensor:
        """Vocos: expects (B, 1, T) float32 at 24kHz, returns (B, 1, T) float32."""
        audio_24k = audio
        model = self._model
        # Vocos.from_pretrained expects mel input or raw audio for copy-synthesis
        # Use model forward for copy-synthesis
        enhanced = model(audio_24k)
        if isinstance(enhanced, tuple):
            enhanced = enhanced[0]
        return enhanced

    def _enhance_bigvgan(self, audio: torch.Tensor) -> torch.Tensor:
        """BigVGAN: compute mel from audio, then vocode."""
        model = self._model
        # BigVGAN uses its own mel transform
        mel = model.mel_spectrogram(audio.squeeze(1))
        enhanced = model(mel)
        return enhanced.unsqueeze(1)

    def to(self, device: str | torch.device) -> OutputEnhancer:
        if self._model is not None:
            self._model = self._model.to(device)
        self.device = torch.device(device)
        return self
