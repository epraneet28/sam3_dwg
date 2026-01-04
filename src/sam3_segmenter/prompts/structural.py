"""Prompt configurations for structural/construction drawings."""

from typing import Any

# Comprehensive prompts for structural/construction drawing zones
STRUCTURAL_ZONE_PROMPTS: dict[str, dict[str, Any]] = {
    # Title block and metadata
    "title_block": {
        "primary_prompt": "title block with project name drawing number and engineer stamp",
        "alternate_prompts": [
            "drawing title block",
            "project information block",
            "engineer stamp and project details",
            "drawing information box",
        ],
        "typical_location": "bottom_right",
        "typical_size_ratio": (0.15, 0.20),
        "expected_per_page": 1,
        "priority": 1,
    },
    "revision_block": {
        "primary_prompt": "revision history block with dates and change descriptions",
        "alternate_prompts": [
            "revision table",
            "drawing revisions",
            "revision history",
            "change log block",
        ],
        "typical_location": "top_right",
        "typical_size_ratio": (0.15, 0.10),
        "expected_per_page": 1,
        "priority": 2,
    },
    # Drawing types
    "plan_view": {
        "primary_prompt": "floor plan or framing plan view from above showing structural layout",
        "alternate_prompts": [
            "roof framing plan",
            "foundation plan",
            "floor framing plan",
            "structural plan view",
            "floor plan layout",
            "building plan from above",
        ],
        "typical_location": "center",
        "typical_size_ratio": (0.5, 0.5),
        "expected_per_page": 1,
        "priority": 3,
    },
    "elevation_view": {
        "primary_prompt": "building elevation view showing side or front of structure",
        "alternate_prompts": [
            "structural elevation",
            "building section elevation",
            "exterior elevation",
            "side view of building",
            "front elevation",
        ],
        "typical_location": "center",
        "typical_size_ratio": (0.4, 0.35),
        "expected_per_page": "variable",
        "priority": 3,
    },
    "section_view": {
        "primary_prompt": "section cut view showing internal structural components",
        "alternate_prompts": [
            "building section",
            "wall section",
            "structural section cut",
            "cross section view",
            "sectional drawing",
        ],
        "typical_location": "center",
        "typical_size_ratio": (0.35, 0.40),
        "expected_per_page": "variable",
        "priority": 3,
    },
    "detail_view": {
        "primary_prompt": "construction detail drawing showing specific connection or component",
        "alternate_prompts": [
            "structural detail",
            "connection detail",
            "typical detail",
            "detail callout",
            "enlarged detail",
            "component detail",
        ],
        "typical_location": "any",
        "typical_size_ratio": (0.2, 0.25),
        "expected_per_page": "variable",
        "priority": 4,
    },
    # Supporting elements
    "schedule_table": {
        "primary_prompt": "schedule or table with structural specifications",
        "alternate_prompts": [
            "beam schedule",
            "column schedule",
            "footing schedule",
            "material schedule",
            "door schedule",
            "window schedule",
            "rebar schedule",
            "structural schedule table",
        ],
        "typical_location": "right_side",
        "typical_size_ratio": (0.25, 0.30),
        "expected_per_page": "variable",
        "priority": 5,
    },
    "notes_area": {
        "primary_prompt": "general notes text area with specifications and requirements",
        "alternate_prompts": [
            "structural notes",
            "general notes",
            "specifications text",
            "design notes",
            "construction notes",
        ],
        "typical_location": "left_side",
        "typical_size_ratio": (0.20, 0.40),
        "expected_per_page": 1,
        "priority": 5,
    },
    "legend": {
        "primary_prompt": "legend or key explaining drawing symbols and abbreviations",
        "alternate_prompts": [
            "symbol legend",
            "abbreviations list",
            "drawing key",
            "notation legend",
        ],
        "typical_location": "corner",
        "typical_size_ratio": (0.12, 0.15),
        "expected_per_page": 1,
        "priority": 6,
    },
    "grid_system": {
        "primary_prompt": "column grid lines with bubble markers",
        "alternate_prompts": [
            "grid bubbles",
            "column line markers",
            "structural grid",
            "grid line system",
        ],
        "typical_location": "edges",
        "typical_size_ratio": (0.05, 0.05),
        "expected_per_page": 1,
        "priority": 7,
    },
    # Additional structural elements
    "dimension_string": {
        "primary_prompt": "dimension lines and measurements",
        "alternate_prompts": [
            "dimensions",
            "measurement annotations",
            "dimension strings",
        ],
        "typical_location": "any",
        "expected_per_page": "variable",
        "priority": 8,
    },
    "north_arrow": {
        "primary_prompt": "north arrow or orientation indicator",
        "alternate_prompts": [
            "compass indicator",
            "direction arrow",
            "orientation symbol",
        ],
        "typical_location": "corner",
        "typical_size_ratio": (0.05, 0.05),
        "expected_per_page": 1,
        "priority": 9,
    },
    "scale_bar": {
        "primary_prompt": "graphic scale bar",
        "alternate_prompts": [
            "scale indicator",
            "measurement scale",
        ],
        "typical_location": "bottom",
        "typical_size_ratio": (0.10, 0.03),
        "expected_per_page": 1,
        "priority": 9,
    },
}


# Page type classification rules based on detected zones
PAGE_TYPE_RULES: dict[str, dict[str, Any]] = {
    "spec_sheet": {
        "required_zones": ["notes_area"],
        "optional_zones": ["schedule_table", "legend"],
        "excluded_zones": ["plan_view", "elevation_view", "section_view"],
        "min_text_ratio": 0.4,
        "description": "Specification sheet with primarily text content",
    },
    "plan": {
        "required_zones": ["plan_view"],
        "optional_zones": ["schedule_table", "notes_area", "legend", "grid_system"],
        "excluded_zones": [],
        "dominant_zone": "plan_view",
        "description": "Floor plan, framing plan, or foundation plan",
    },
    "elevation": {
        "required_zones": ["elevation_view"],
        "optional_zones": ["section_view", "notes_area", "detail_view"],
        "excluded_zones": [],
        "dominant_zone": "elevation_view",
        "description": "Building elevation views",
    },
    "section": {
        "required_zones": ["section_view"],
        "optional_zones": ["detail_view", "notes_area", "elevation_view"],
        "excluded_zones": [],
        "dominant_zone": "section_view",
        "description": "Building section cuts",
    },
    "details": {
        "required_zones": [],
        "optional_zones": ["notes_area", "legend"],
        "excluded_zones": [],
        "condition": "detail_view_count >= 3",
        "dominant_zone": "detail_view",
        "description": "Detail sheet with multiple construction details",
    },
    "schedule": {
        "required_zones": ["schedule_table"],
        "optional_zones": ["notes_area", "legend"],
        "excluded_zones": ["plan_view", "elevation_view", "section_view"],
        "dominant_zone": "schedule_table",
        "min_schedule_count": 2,
        "description": "Schedule sheet with multiple tables",
    },
}


def get_all_primary_prompts() -> list[str]:
    """Get all primary prompts from structural zone configurations."""
    return [config["primary_prompt"] for config in STRUCTURAL_ZONE_PROMPTS.values()]


def get_zone_type_from_prompt(prompt: str) -> str:
    """Map a prompt back to its zone type."""
    for zone_type, config in STRUCTURAL_ZONE_PROMPTS.items():
        if prompt == config["primary_prompt"]:
            return zone_type
        if prompt in config.get("alternate_prompts", []):
            return zone_type
    return "unknown"


def get_prompts_for_zone_type(zone_type: str) -> list[str]:
    """Get all prompts (primary and alternates) for a zone type."""
    if zone_type not in STRUCTURAL_ZONE_PROMPTS:
        return []
    config = STRUCTURAL_ZONE_PROMPTS[zone_type]
    return [config["primary_prompt"]] + config.get("alternate_prompts", [])
