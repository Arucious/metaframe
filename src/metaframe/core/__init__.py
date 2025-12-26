"""Core modules for metadata extraction and image framing."""

from metaframe.core.config import (
    DEFAULT_FIELDS,
    PRESET_COLORS,
    SEPARATORS,
    FrameSettings,
    MetadataField,
    MetadataPosition,
    RowLayout,
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
    "PRESET_COLORS",
    "SEPARATORS",
    "DEFAULT_FIELDS",
]
