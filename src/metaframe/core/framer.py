"""Image framing with metadata overlay."""

import platform
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from metaframe.core.config import (
    ASPECT_RATIOS,
    CAMERA_INFO_FIELDS,
    SETTINGS_FIELDS,
    FrameSettings,
    MetadataPosition,
    RowLayout,
    TextAlignment,
    get_font_path,
)
from metaframe.core.metadata import ExtractedMetadata, MetadataExtractor

# RAW file extensions
RAW_EXTENSIONS = {
    ".cr2", ".cr3",  # Canon
    ".nef", ".nrw",  # Nikon
    ".arw", ".srf", ".sr2",  # Sony
    ".orf",  # Olympus
    ".rw2",  # Panasonic
    ".raf",  # Fujifilm
    ".dng",  # Adobe DNG
    ".raw", ".rwl",  # Leica
    ".pef",  # Pentax
    ".3fr",  # Hasselblad
    ".iiq",  # Phase One
}

# HEIF extensions
HEIF_EXTENSIONS = {".heic", ".heif"}


def load_image(image_path: Path) -> Image.Image:
    """Load an image, handling RAW and HEIF formats."""
    suffix = image_path.suffix.lower()

    if suffix in RAW_EXTENSIONS:
        try:
            import rawpy

            with rawpy.imread(str(image_path)) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=False,
                    no_auto_bright=False,
                    output_bps=8,
                )
                return Image.fromarray(rgb)
        except ImportError:
            raise ImportError(
                "rawpy is required for RAW file support. Install with: pip install rawpy"
            )

    if suffix in HEIF_EXTENSIONS:
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            raise ImportError(
                "pillow-heif is required for HEIC/HEIF support. "
                "Install with: pip install pillow-heif"
            )

    return Image.open(image_path)


class Framer:
    """Creates framed images with metadata overlays."""

    def __init__(self, settings: FrameSettings | None = None):
        """
        Initialize the framer with settings.

        Args:
            settings: Frame settings. Uses defaults if not provided.
        """
        self.settings = settings or FrameSettings()
        self._font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}

    def _get_font(
        self, size: int | None = None, italic: bool | None = None
    ) -> ImageFont.FreeTypeFont:
        """Get or create a font with the specified settings."""
        size = size or self.settings.font_size
        italic = italic if italic is not None else self.settings.italic

        cache_key = (self.settings.font_family, size, italic)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font = self._load_font(self.settings.font_family, size, italic)
        self._font_cache[cache_key] = font
        return font

    def _load_font(self, font_name: str, size: int, italic: bool) -> ImageFont.FreeTypeFont:
        """Load a font, falling back to system defaults if needed."""
        # Try to find the font file
        font_path = get_font_path(font_name)

        if font_path:
            try:
                return ImageFont.truetype(str(font_path), size)
            except OSError:
                pass

        # Try common system font locations
        system_fonts = self._get_system_font_paths(font_name, italic)

        for path in system_fonts:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue

        # Fall back to default font
        try:
            # Try to load a basic system font
            if platform.system() == "Darwin":
                return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
            elif platform.system() == "Windows":
                return ImageFont.truetype("arial.ttf", size)
            else:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except OSError:
            # Ultimate fallback
            return ImageFont.load_default()

    def _get_system_font_paths(self, font_name: str, italic: bool) -> list[str]:
        """Get potential system font paths for a font name."""
        paths = []
        system = platform.system()

        # Normalize font name
        italic_suffix_short = "i" if italic else ""

        if system == "Darwin":
            font_dirs = [
                "/System/Library/Fonts",
                "/Library/Fonts",
                Path.home() / "Library/Fonts",
            ]
            extensions = [".ttf", ".ttc", ".otf"]

            for font_dir in font_dirs:
                for ext in extensions:
                    # Try various naming conventions
                    paths.extend([
                        f"{font_dir}/{font_name}{ext}",
                        f"{font_dir}/{font_name}-{'Italic' if italic else 'Regular'}{ext}",
                        f"{font_dir}/{font_name} {'Italic' if italic else 'Regular'}{ext}",
                    ])

        elif system == "Windows":
            font_dir = "C:/Windows/Fonts"
            paths.extend([
                f"{font_dir}/{font_name.lower()}{italic_suffix_short}.ttf",
                f"{font_dir}/{font_name.lower()}.ttf",
                f"{font_dir}/arial{italic_suffix_short}.ttf",
            ])

        else:  # Linux
            font_dirs = [
                "/usr/share/fonts/truetype",
                "/usr/share/fonts/opentype",
                "/usr/local/share/fonts",
                Path.home() / ".fonts",
                Path.home() / ".local/share/fonts",
            ]

            for font_dir in font_dirs:
                name_l = font_name.lower()
                style = "italic" if italic else "regular"
                paths.extend([
                    f"{font_dir}/{name_l}/{name_l}-{style}.ttf",
                    f"{font_dir}/dejavu/DejaVuSans{'-Oblique' if italic else ''}.ttf",
                ])

        return [str(p) for p in paths]

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        """Parse a color string to RGB tuple."""
        color = color.strip()

        # Handle hex colors
        if color.startswith("#"):
            color = color[1:]
            if len(color) == 3:
                color = "".join(c * 2 for c in color)
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

        # Handle named colors
        named_colors = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "grey": (128, 128, 128),
            "gray": (128, 128, 128),
            "cream": (245, 245, 220),
        }

        return named_colors.get(color.lower(), (255, 255, 255))

    def create_frame(
        self,
        image_path: str | Path,
        metadata: ExtractedMetadata | None = None,
    ) -> Image.Image:
        """
        Create a framed version of the image with metadata.

        Args:
            image_path: Path to the source image.
            metadata: Pre-extracted metadata. If None, will extract from image.

        Returns:
            PIL Image with frame and metadata applied.
        """
        image_path = Path(image_path)

        # Load original image (supports RAW and HEIF formats)
        img = load_image(image_path)
        try:
            # Handle EXIF orientation
            img = self._apply_exif_orientation(img)

            # Convert to RGB if necessary (for consistent processing)
            if img.mode in ("RGBA", "P"):
                # Preserve alpha if present
                if img.mode == "P":
                    img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Extract metadata if not provided
            if metadata is None:
                extractor = MetadataExtractor()
                metadata = extractor.extract(image_path)

            # Get text lines to render
            text_lines = self._get_text_lines(metadata)

            # Create framed image
            framed = self._create_framed_image(img, text_lines)

            return framed
        finally:
            img.close()

    def _apply_exif_orientation(self, img: Image.Image) -> Image.Image:
        """Apply EXIF orientation to the image."""
        try:
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)  # Orientation tag
                if orientation:
                    rotations = {
                        3: 180,
                        6: 270,
                        8: 90,
                    }
                    if orientation in rotations:
                        img = img.rotate(rotations[orientation], expand=True)
                    elif orientation in (2, 4, 5, 7):
                        # Handle mirrored orientations
                        img = img.transpose(Image.FLIP_LEFT_RIGHT)
                        if orientation in (5, 7):
                            img = img.rotate(270 if orientation == 5 else 90, expand=True)
        except (AttributeError, KeyError, TypeError):
            pass
        return img

    def _get_text_lines(self, metadata: ExtractedMetadata) -> list[str]:
        """Get formatted text lines based on settings."""
        separator = self.settings.get_separator_string()
        active_fields = self.settings.get_active_fields()

        if self.settings.row_layout == RowLayout.SINGLE:
            # All fields on one line
            text = metadata.get_display_string(active_fields, separator)
            return [text] if text else []

        elif self.settings.row_layout == RowLayout.TWO_ROWS:
            # Camera/lens info on row 1, settings on row 2
            row1_fields = [f for f in active_fields if f in CAMERA_INFO_FIELDS]
            row2_fields = [f for f in active_fields if f in SETTINGS_FIELDS]

            lines = []
            row1 = metadata.get_display_string(row1_fields, separator)
            row2 = metadata.get_display_string(row2_fields, separator)

            if row1:
                lines.append(row1)
            if row2:
                lines.append(row2)

            return lines

        else:  # MULTI_ROW
            # Each field on its own line
            lines = []
            for field in active_fields:
                value = metadata.get_field(field)
                if value:
                    lines.append(value)
            return lines

    def _apply_aspect_ratio(self, img: Image.Image) -> Image.Image:
        """Apply aspect ratio preset by cropping to target ratio."""
        aspect_preset = self.settings.aspect_ratio
        target_ratio = ASPECT_RATIOS.get(aspect_preset)

        if target_ratio is None:
            # Original aspect ratio, no change
            return img

        target_w, target_h = target_ratio
        target_aspect = target_w / target_h
        current_aspect = img.width / img.height

        if abs(current_aspect - target_aspect) < 0.01:
            # Already close enough to target
            return img

        # Crop to target aspect ratio (center crop)
        if current_aspect > target_aspect:
            # Image is wider than target, crop width
            new_width = int(img.height * target_aspect)
            left = (img.width - new_width) // 2
            return img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller than target, crop height
            new_height = int(img.width / target_aspect)
            top = (img.height - new_height) // 2
            return img.crop((0, top, img.width, top + new_height))

    def _create_framed_image(
        self, img: Image.Image, text_lines: list[str]
    ) -> Image.Image:
        """Create the framed image with text overlay."""
        # Apply aspect ratio crop first
        img = self._apply_aspect_ratio(img)

        bg_color = self._parse_color(self.settings.background_color)
        text_color = self._parse_color(self.settings.text_color)

        # Calculate auto font size based on image dimensions
        font_size = self.settings.get_auto_font_size(img.width, img.height)
        font = self._get_font(size=font_size)

        position = self.settings.position
        padding = self.settings.padding
        thickness = self.settings.thickness

        # Calculate text dimensions
        temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        line_heights = []
        line_widths = []

        for line in text_lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        line_spacing = 10
        total_text_height = sum(line_heights) + line_spacing * max(0, len(text_lines) - 1)
        max_text_width = max(line_widths) if line_widths else 0

        # Calculate new image dimensions based on position
        orig_width, orig_height = img.size

        if position in (MetadataPosition.TOP, MetadataPosition.BOTTOM):
            # Frame on top or bottom
            frame_height = thickness + padding + total_text_height + padding
            new_width = orig_width + padding * 2
            new_height = orig_height + frame_height + padding

            # Create new image
            framed = Image.new("RGB", (new_width, new_height), bg_color)

            # Paste original image
            if position == MetadataPosition.BOTTOM:
                img_x = padding
                img_y = padding
                text_y_start = orig_height + padding + thickness
            else:  # TOP
                img_x = padding
                img_y = frame_height
                text_y_start = padding + (thickness - total_text_height) // 2

            framed.paste(img, (img_x, img_y))

            # Draw text
            draw = ImageDraw.Draw(framed)
            current_y = text_y_start

            for i, line in enumerate(text_lines):
                text_width = line_widths[i]
                # Calculate text_x based on alignment
                if self.settings.text_alignment == TextAlignment.LEFT:
                    text_x = padding
                elif self.settings.text_alignment == TextAlignment.RIGHT:
                    text_x = new_width - padding - text_width
                else:  # CENTER
                    text_x = (new_width - text_width) // 2
                draw.text((text_x, current_y), line, font=font, fill=text_color)
                current_y += line_heights[i] + line_spacing

        else:  # LEFT or RIGHT
            # Frame on left or right (rotated text)
            frame_width = thickness + padding + total_text_height + padding
            new_width = orig_width + frame_width + padding
            new_height = orig_height + padding * 2

            # Create new image
            framed = Image.new("RGB", (new_width, new_height), bg_color)

            # Paste original image
            if position == MetadataPosition.RIGHT:
                img_x = padding
                img_y = padding
                text_x_start = orig_width + padding + thickness
            else:  # LEFT
                img_x = frame_width
                img_y = padding
                text_x_start = padding + (thickness - total_text_height) // 2

            framed.paste(img, (img_x, img_y))

            # Draw rotated text
            # Create a temporary image for the text, then rotate it
            text_img_height = max(max_text_width + padding * 2, orig_height)
            text_img_width = total_text_height + padding * 2
            text_img = Image.new("RGB", (text_img_height, text_img_width), bg_color)
            text_draw = ImageDraw.Draw(text_img)

            current_y = padding
            for i, line in enumerate(text_lines):
                text_width = line_widths[i]
                text_x = (text_img_height - text_width) // 2
                text_draw.text((text_x, current_y), line, font=font, fill=text_color)
                current_y += line_heights[i] + line_spacing

            # Rotate the text image
            if position == MetadataPosition.RIGHT:
                text_img = text_img.rotate(270, expand=True)
            else:  # LEFT
                text_img = text_img.rotate(90, expand=True)

            # Paste the rotated text
            text_paste_y = (new_height - text_img.height) // 2
            if position == MetadataPosition.RIGHT:
                framed.paste(text_img, (text_x_start, text_paste_y))
            else:
                framed.paste(text_img, (text_x_start, text_paste_y))

        return framed

    def save_framed_image(
        self,
        framed_image: Image.Image,
        output_path: str | Path,
        original_format: str | None = None,
    ) -> Path:
        """
        Save the framed image to disk.

        Args:
            framed_image: The framed PIL Image.
            output_path: Path to save the image.
            original_format: Original image format to preserve. If None, infers from output_path.

        Returns:
            Path to the saved image.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine format
        suffix = output_path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            framed_image = framed_image.convert("RGB")
            framed_image.save(
                output_path,
                "JPEG",
                quality=self.settings.jpeg_quality,
                optimize=True,
            )
        elif suffix == ".png":
            framed_image.save(output_path, "PNG", optimize=True)
        else:
            # Default to JPEG
            output_path = output_path.with_suffix(".jpg")
            framed_image = framed_image.convert("RGB")
            framed_image.save(
                output_path,
                "JPEG",
                quality=self.settings.jpeg_quality,
                optimize=True,
            )

        return output_path

    def process_image(
        self,
        input_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> Path:
        """
        Process a single image: extract metadata, create frame, and save.

        Args:
            input_path: Path to the input image.
            output_dir: Directory to save the output. If None, saves alongside original.

        Returns:
            Path to the saved framed image.
        """
        input_path = Path(input_path)

        # Determine output path
        if output_dir:
            output_dir = Path(output_dir)
            output_name = f"{input_path.stem}{self.settings.output_suffix}{input_path.suffix}"
            output_path = output_dir / output_name
        else:
            suffix = self.settings.output_suffix
            output_path = input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"

        # Extract metadata
        extractor = MetadataExtractor()
        metadata = extractor.extract(input_path)

        # Create framed image
        framed = self.create_frame(input_path, metadata)

        # Save
        return self.save_framed_image(framed, output_path)

    def process_batch(
        self,
        input_paths: list[str | Path],
        output_dir: str | Path,
        progress_callback: Callable | None = None,
    ) -> list[tuple[Path, Path | Exception]]:
        """
        Process multiple images.

        Args:
            input_paths: List of input image paths.
            output_dir: Directory to save outputs.
            progress_callback: Optional callback(current, total, path) for progress updates.

        Returns:
            List of tuples (input_path, output_path or exception).
        """
        results = []
        total = len(input_paths)

        for i, input_path in enumerate(input_paths):
            input_path = Path(input_path)

            if progress_callback:
                progress_callback(i, total, input_path)

            try:
                output_path = self.process_image(input_path, output_dir)
                results.append((input_path, output_path))
            except Exception as e:
                results.append((input_path, e))

        if progress_callback:
            progress_callback(total, total, None)

        return results
