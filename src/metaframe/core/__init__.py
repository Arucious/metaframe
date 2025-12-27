"""Core modules for metadata extraction and image framing."""

from metaframe.core.config import (
    ASPECT_RATIOS,
    DEFAULT_FIELDS,
    PRESET_COLORS,
    SEPARATORS,
    AspectRatioPreset,
    FrameSettings,
    MetadataField,
    MetadataPosition,
    RowLayout,
    TextAlignment,
)
from metaframe.core.framer import Framer
from metaframe.core.metadata import MetadataExtractor

__all__ = [
    "MetadataExtractor",
    "Framer",
    "FrameSettings",
    "MetadataField",
    "MetadataPosition",
    "RowLayout",
    "TextAlignment",
    "AspectRatioPreset",
    "PRESET_COLORS",
    "SEPARATORS",
    "DEFAULT_FIELDS",
    "ASPECT_RATIOS",
]
