"""Post-processing and zone/page classification logic."""

import logging
from collections import Counter
from typing import Optional

from .models import ZoneResult, PageType
from .prompts.structural import PAGE_TYPE_RULES, STRUCTURAL_ZONE_PROMPTS

logger = logging.getLogger(__name__)


def classify_page_type(zones: list[ZoneResult]) -> tuple[str, float]:
    """
    Classify the page type based on detected zones.

    Args:
        zones: List of detected zones

    Returns:
        Tuple of (page_type, confidence)
    """
    if not zones:
        return PageType.UNKNOWN.value, 0.0

    # Count zone types
    zone_types = [z.zone_type for z in zones]
    zone_counts = Counter(zone_types)

    # Calculate total confidence
    avg_confidence = sum(z.confidence for z in zones) / len(zones) if zones else 0.0

    # Apply classification rules in order of specificity
    scores = {}

    for page_type, rules in PAGE_TYPE_RULES.items():
        score = 0.0
        matched_required = 0
        total_required = len(rules.get("required_zones", []))

        # Check required zones
        for required_zone in rules.get("required_zones", []):
            if required_zone in zone_types:
                matched_required += 1
                score += 1.0

        # If not all required zones present, skip this page type
        if total_required > 0 and matched_required < total_required:
            continue

        # Check excluded zones
        excluded = False
        for excluded_zone in rules.get("excluded_zones", []):
            if excluded_zone in zone_types:
                excluded = True
                break

        if excluded:
            continue

        # Check special conditions
        condition = rules.get("condition")
        if condition:
            if "detail_view_count >= 3" in condition:
                if zone_counts.get("detail_view", 0) < 3:
                    continue

        # Check minimum schedule count
        min_schedule = rules.get("min_schedule_count", 0)
        if min_schedule > 0:
            if zone_counts.get("schedule_table", 0) < min_schedule:
                continue

        # Bonus for dominant zone
        dominant = rules.get("dominant_zone")
        if dominant and dominant in zone_types:
            # Calculate area coverage of dominant zone
            dominant_zones = [z for z in zones if z.zone_type == dominant]
            total_area = sum(z.area_ratio or 0 for z in dominant_zones)
            score += total_area * 2  # Weight by area coverage

        # Bonus for optional zones
        for optional_zone in rules.get("optional_zones", []):
            if optional_zone in zone_types:
                score += 0.25

        scores[page_type] = score

    if not scores:
        return PageType.UNKNOWN.value, 0.0

    # Select highest scoring page type
    best_type = max(scores.keys(), key=lambda k: scores[k])
    best_score = scores[best_type]

    # Normalize confidence (simple heuristic)
    # Higher score and higher avg detection confidence = higher page confidence
    confidence = min(1.0, (best_score / 3.0) * avg_confidence)

    return best_type, confidence


def filter_overlapping_zones(
    zones: list[ZoneResult],
    iou_threshold: float = 0.7,
) -> list[ZoneResult]:
    """
    Filter out overlapping zones, keeping the highest confidence one.

    Args:
        zones: List of zones to filter
        iou_threshold: IoU threshold for considering zones as overlapping

    Returns:
        Filtered list of zones
    """
    from .utils.geometry import calculate_iou

    if not zones:
        return []

    # Sort by confidence (highest first)
    sorted_zones = sorted(zones, key=lambda z: z.confidence, reverse=True)
    kept_zones = []

    for zone in sorted_zones:
        # Check if this zone overlaps with any kept zone
        overlaps = False
        for kept in kept_zones:
            iou = calculate_iou(zone.bbox, kept.bbox)
            if iou > iou_threshold:
                overlaps = True
                break

        if not overlaps:
            kept_zones.append(zone)

    return kept_zones


def validate_zone_locations(
    zones: list[ZoneResult],
    image_width: int,
    image_height: int,
) -> list[ZoneResult]:
    """
    Validate zones against their expected locations and adjust confidence.

    Args:
        zones: List of detected zones
        image_width: Image width
        image_height: Image height

    Returns:
        Zones with adjusted confidence based on location validation
    """
    from .utils.geometry import is_bbox_in_region

    validated_zones = []

    for zone in zones:
        config = STRUCTURAL_ZONE_PROMPTS.get(zone.zone_type)
        if not config:
            validated_zones.append(zone)
            continue

        typical_location = config.get("typical_location")
        if typical_location and typical_location not in ("any", "edges", "corner"):
            # Check if zone is in expected location
            in_expected_location = is_bbox_in_region(
                zone.bbox,
                image_width,
                image_height,
                typical_location,
            )

            if in_expected_location:
                # Boost confidence slightly for zones in expected locations
                zone.confidence = min(1.0, zone.confidence * 1.1)
            else:
                # Reduce confidence for zones in unexpected locations
                zone.confidence = zone.confidence * 0.9

        validated_zones.append(zone)

    return validated_zones


def merge_adjacent_zones(
    zones: list[ZoneResult],
    zone_type: str,
    gap_threshold: float = 20.0,
) -> list[ZoneResult]:
    """
    Merge adjacent zones of the same type that are close together.

    Args:
        zones: List of all zones
        zone_type: Type of zone to merge
        gap_threshold: Maximum gap (in pixels) to consider zones as adjacent

    Returns:
        List with merged zones
    """
    target_zones = [z for z in zones if z.zone_type == zone_type]
    other_zones = [z for z in zones if z.zone_type != zone_type]

    if len(target_zones) <= 1:
        return zones

    # Sort by y position, then x
    target_zones.sort(key=lambda z: (z.bbox[1], z.bbox[0]))

    merged = []
    current = target_zones[0]

    for next_zone in target_zones[1:]:
        # Check if zones are adjacent (horizontally or vertically)
        x1, y1, x2, y2 = current.bbox
        nx1, ny1, nx2, ny2 = next_zone.bbox

        # Check horizontal adjacency
        h_gap = max(0, nx1 - x2)
        v_overlap = min(y2, ny2) - max(y1, ny1)

        # Check vertical adjacency
        v_gap = max(0, ny1 - y2)
        h_overlap = min(x2, nx2) - max(x1, nx1)

        should_merge = False
        if h_gap <= gap_threshold and v_overlap > 0:
            should_merge = True
        elif v_gap <= gap_threshold and h_overlap > 0:
            should_merge = True

        if should_merge:
            # Merge bounding boxes
            merged_bbox = [
                min(x1, nx1),
                min(y1, ny1),
                max(x2, nx2),
                max(y2, ny2),
            ]
            current = ZoneResult(
                zone_id=current.zone_id,
                zone_type=current.zone_type,
                prompt_matched=current.prompt_matched,
                confidence=max(current.confidence, next_zone.confidence),
                bbox=merged_bbox,
                bbox_normalized=current.bbox_normalized,  # Will need recalculation
                area_ratio=current.area_ratio,  # Will need recalculation
            )
        else:
            merged.append(current)
            current = next_zone

    merged.append(current)

    return other_zones + merged


def post_process_zones(
    zones: list[ZoneResult],
    image_width: int,
    image_height: int,
    filter_overlapping: bool = True,
    validate_locations: bool = True,
) -> list[ZoneResult]:
    """
    Apply all post-processing steps to detected zones.

    Args:
        zones: Raw detected zones
        image_width: Image width
        image_height: Image height
        filter_overlapping: Whether to filter overlapping zones
        validate_locations: Whether to validate zone locations

    Returns:
        Post-processed zones
    """
    if not zones:
        return []

    processed = zones

    # Filter overlapping zones
    if filter_overlapping:
        processed = filter_overlapping_zones(processed)

    # Validate locations and adjust confidence
    if validate_locations:
        processed = validate_zone_locations(processed, image_width, image_height)

    # Sort by priority (using zone type priority from config)
    def get_priority(zone: ZoneResult) -> int:
        config = STRUCTURAL_ZONE_PROMPTS.get(zone.zone_type, {})
        return config.get("priority", 99)

    processed.sort(key=get_priority)

    return processed
