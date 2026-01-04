"""Base prompt configuration classes."""

from dataclasses import dataclass, field
from typing import Literal, Optional, Union


@dataclass
class BasePromptConfig:
    """Base configuration for a zone detection prompt."""

    primary_prompt: str
    alternate_prompts: list[str] = field(default_factory=list)
    typical_location: Optional[
        Literal[
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
            "center",
            "left_side",
            "right_side",
            "top",
            "bottom",
            "edges",
            "corner",
            "any",
        ]
    ] = None
    typical_size_ratio: Optional[tuple[float, float]] = None  # (width_ratio, height_ratio)
    expected_per_page: Union[int, Literal["variable"]] = 1
    priority: int = 5

    def get_all_prompts(self) -> list[str]:
        """Get primary and all alternate prompts."""
        return [self.primary_prompt] + self.alternate_prompts


@dataclass
class ZonePromptSet:
    """Collection of prompts for a specific drawing type."""

    name: str
    description: str
    prompts: dict[str, BasePromptConfig] = field(default_factory=dict)

    def get_primary_prompts(self) -> list[str]:
        """Get all primary prompts."""
        return [config.primary_prompt for config in self.prompts.values()]

    def get_zone_types(self) -> list[str]:
        """Get all zone type names."""
        return list(self.prompts.keys())
