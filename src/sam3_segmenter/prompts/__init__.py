"""Prompt configurations for drawing segmentation."""

from .base import BasePromptConfig
from .structural import STRUCTURAL_ZONE_PROMPTS, PAGE_TYPE_RULES

__all__ = [
    "BasePromptConfig",
    "STRUCTURAL_ZONE_PROMPTS",
    "PAGE_TYPE_RULES",
]
