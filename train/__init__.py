"""Train package — GPU detection + VRAM-based parameter proposal.

:noindex:
"""

from train.gpu import (
    ParameterBounds,
    detect_gpus,
    propose_parameters,
    propose_presets,
    suggest_for_host,
    vram_tier,
)
from train.trainer import (
    Trainer,
    TrainingConfig,
)

__all__ = [
    "detect_gpus",
    "vram_tier",
    "ParameterBounds",
    "propose_parameters",
    "propose_presets",
    "suggest_for_host",
    "Trainer",
    "TrainingConfig",
]
