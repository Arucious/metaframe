"""Configuration and settings for MetaFrame."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MetadataField(Enum):
    """Available metadata fields to display."""

    CAMERA_MAKE = "camera_make"
    CAMERA_MODEL = "camera_model"
    LENS = "lens"
    FOCAL_LENGTH = "focal_length"
    APERTURE = "aperture"
    SHUTTER_SPEED = "shutter_speed"
    ISO = "iso"
    DATE_TIME = "date_time"
    GPS = "gps"


class MetadataPosition(Enum):
    """Position of metadata text on the frame."""

    BOTTOM = "bottom"
    TOP = "top"
    LEFT = "left"
    RIGHT = "right"


class TextAlignment(Enum):
    """Text alignment within the frame."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class AspectRatioPreset(Enum):
    """Preset aspect ratios for output."""

    ORIGINAL = "original"  # Keep original aspect ratio
    SQUARE_1_1 = "1:1"  # Instagram square
    PORTRAIT_4_5 = "4:5"  # Instagram portrait
    LANDSCAPE_16_9 = "16:9"  # Widescreen
    LANDSCAPE_3_2 = "3:2"  # Classic 35mm
    PORTRAIT_9_16 = "9:16"  # Stories/Reels


ASPECT_RATIOS = {
    AspectRatioPreset.ORIGINAL: None,
    AspectRatioPreset.SQUARE_1_1: (1, 1),
    AspectRatioPreset.PORTRAIT_4_5: (4, 5),
    AspectRatioPreset.LANDSCAPE_16_9: (16, 9),
    AspectRatioPreset.LANDSCAPE_3_2: (3, 2),
    AspectRatioPreset.PORTRAIT_9_16: (9, 16),
}


class RowLayout(Enum):
    """Layout style for metadata rows."""

    SINGLE = "single"  # All fields on one line
    TWO_ROWS = "two_rows"  # Camera/lens on row 1, settings on row 2
    MULTI_ROW = "multi_row"  # Each field group on its own line


class Separator(Enum):
    """Separator styles for metadata fields."""

    PIPE = "pipe"
    BULLET = "bullet"
    DASH = "dash"


# Separator characters
SEPARATORS = {
    Separator.PIPE: " | ",
    Separator.BULLET: " \u2022 ",
    Separator.DASH: " \u2014 ",
}

# Preset background colors
PRESET_COLORS = {
    "white": "#FFFFFF",
    "black": "#000000",
    "grey": "#808080",
    "cream": "#F5F5DC",
}

# Default fields to display
DEFAULT_FIELDS = [
    MetadataField.FOCAL_LENGTH,
    MetadataField.APERTURE,
    MetadataField.SHUTTER_SPEED,
    MetadataField.ISO,
]

# Fields that go on the first row in TWO_ROWS layout
CAMERA_INFO_FIELDS = [
    MetadataField.CAMERA_MAKE,
    MetadataField.CAMERA_MODEL,
    MetadataField.LENS,
    MetadataField.DATE_TIME,
]

# Fields that go on the second row in TWO_ROWS layout
SETTINGS_FIELDS = [
    MetadataField.FOCAL_LENGTH,
    MetadataField.APERTURE,
    MetadataField.SHUTTER_SPEED,
    MetadataField.ISO,
    MetadataField.GPS,
]


@dataclass
class FrameSettings:
    """Settings for frame generation."""

    # Frame dimensions
    padding: int = 60  # Space between image and text
    thickness: int = 80  # Total frame thickness (includes padding for text)

    # Colors
    background_color: str = "#FFFFFF"  # Frame background
    text_color: str = "#000000"  # Metadata text color

    # Font settings
    font_family: str = "Arial"  # Font name or path
    font_size: int = 0  # 0 = auto-calculate based on image size
    italic: bool = True

    # Layout
    position: MetadataPosition = MetadataPosition.BOTTOM
    row_layout: RowLayout = RowLayout.SINGLE
    separator: Separator = Separator.PIPE
    text_alignment: TextAlignment = TextAlignment.CENTER

    # Aspect ratio
    aspect_ratio: AspectRatioPreset = AspectRatioPreset.ORIGINAL

    # Metadata fields to include
    fields: list[MetadataField] = field(default_factory=lambda: DEFAULT_FIELDS.copy())
    include_gps: bool = False  # Explicit opt-in for GPS

    # Output
    output_suffix: str = "_framed"
    jpeg_quality: int = 95

    def get_auto_font_size(self, image_width: int, image_height: int) -> int:
        """Calculate appropriate font size based on image dimensions."""
        if self.font_size > 0:
            return self.font_size
        # Base font size on the smaller dimension, roughly 2% of it
        base_size = min(image_width, image_height)
        calculated = max(16, int(base_size * 0.025))
        return min(calculated, 72)  # Cap at 72pt

    def get_separator_string(self) -> str:
        """Get the separator string for the current separator style."""
        return SEPARATORS[self.separator]

    def get_active_fields(self) -> list[MetadataField]:
        """Get list of active fields including GPS if enabled."""
        fields = self.fields.copy()
        if self.include_gps and MetadataField.GPS not in fields:
            fields.append(MetadataField.GPS)
        return fields

    @classmethod
    def from_dict(cls, data: dict) -> "FrameSettings":
        """Create settings from a dictionary."""
        # Convert string enums back to enum types
        if "position" in data and isinstance(data["position"], str):
            data["position"] = MetadataPosition(data["position"])
        if "row_layout" in data and isinstance(data["row_layout"], str):
            data["row_layout"] = RowLayout(data["row_layout"])
        if "separator" in data and isinstance(data["separator"], str):
            data["separator"] = Separator(data["separator"])
        if "fields" in data and data["fields"]:
            data["fields"] = [
                MetadataField(f) if isinstance(f, str) else f for f in data["fields"]
            ]
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert settings to a dictionary."""
        return {
            "padding": self.padding,
            "thickness": self.thickness,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "italic": self.italic,
            "position": self.position.value,
            "row_layout": self.row_layout.value,
            "separator": self.separator.value,
            "fields": [f.value for f in self.fields],
            "include_gps": self.include_gps,
            "output_suffix": self.output_suffix,
            "jpeg_quality": self.jpeg_quality,
        }


def get_font_path(font_name: str) -> Path | None:
    """
    Try to find a font file path for the given font name.
    Returns None if using system font.
    """
    # Check if it's already a path
    path = Path(font_name)
    if path.exists() and path.suffix.lower() in (".ttf", ".otf"):
        return path

    # Check bundled fonts directory
    bundled_fonts = Path(__file__).parent.parent / "gui" / "resources" / "fonts"
    if bundled_fonts.exists():
        for ext in (".ttf", ".otf"):
            font_file = bundled_fonts / f"{font_name}{ext}"
            if font_file.exists():
                return font_file

    # Return None to use system font
    return None
