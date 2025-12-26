"""Command-line interface for MetaFrame."""

import sys
from pathlib import Path

import click

from metaframe.core.config import (
    PRESET_COLORS,
    FrameSettings,
    MetadataField,
    MetadataPosition,
    RowLayout,
    Separator,
)
from metaframe.core.framer import Framer
from metaframe.core.metadata import MetadataExtractor

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}


def validate_color(ctx, param, value):
    """Validate color input."""
    if value is None:
        return None

    # Check if it's a preset name
    if value.lower() in PRESET_COLORS:
        return PRESET_COLORS[value.lower()]

    # Check if it's a valid hex color
    if value.startswith("#"):
        hex_part = value[1:]
        if len(hex_part) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in hex_part):
            return value

    raise click.BadParameter(
        f"Invalid color '{value}'. Use a preset name ({', '.join(PRESET_COLORS.keys())}) "
        "or a hex color (#RGB or #RRGGBB)."
    )


def validate_fields(ctx, param, value):
    """Validate and parse field names."""
    if value is None:
        return None

    valid_fields = {f.value: f for f in MetadataField}
    fields = []

    for field_name in value.split(","):
        field_name = field_name.strip().lower()
        if field_name not in valid_fields:
            raise click.BadParameter(
                f"Invalid field '{field_name}'. Valid fields: {', '.join(valid_fields.keys())}"
            )
        fields.append(valid_fields[field_name])

    return fields


def get_image_files(paths: tuple[str, ...]) -> list[Path]:
    """Get list of image files from paths (files or directories)."""
    image_files = []

    for path_str in paths:
        path = Path(path_str)

        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                image_files.append(path)
            else:
                click.echo(f"Warning: Skipping unsupported file: {path}", err=True)

        elif path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                image_files.extend(path.glob(f"*{ext}"))
                image_files.extend(path.glob(f"*{ext.upper()}"))

        else:
            click.echo(f"Warning: Path not found: {path}", err=True)

    return sorted(set(image_files))


@click.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    required=True,
    type=click.Path(file_okay=False),
    help="Output directory for framed images.",
)
@click.option(
    "-b", "--background",
    callback=validate_color,
    help=f"Background color. Presets: {', '.join(PRESET_COLORS.keys())}. Or hex: #RRGGBB",
)
@click.option(
    "-p", "--padding",
    type=int,
    help="Padding in pixels between image and frame edge.",
)
@click.option(
    "-t", "--thickness",
    type=int,
    help="Frame thickness in pixels (area for text).",
)
@click.option(
    "-f", "--font",
    help="Font family name or path to font file.",
)
@click.option(
    "--font-size",
    type=int,
    help="Font size in pixels.",
)
@click.option(
    "--no-italic",
    is_flag=True,
    help="Disable italic text.",
)
@click.option(
    "--fields",
    callback=validate_fields,
    help="Comma-separated list of fields to display. "
         f"Available: {', '.join(f.value for f in MetadataField if f != MetadataField.GPS)}",
)
@click.option(
    "--include-gps",
    is_flag=True,
    help="Include GPS coordinates (opt-in for privacy).",
)
@click.option(
    "--position",
    type=click.Choice(["bottom", "top", "left", "right"], case_sensitive=False),
    help="Position of metadata text.",
)
@click.option(
    "--layout",
    type=click.Choice(["single", "two_rows", "multi_row"], case_sensitive=False),
    help="Layout style for metadata.",
)
@click.option(
    "--separator",
    type=click.Choice(["pipe", "bullet", "dash"], case_sensitive=False),
    help="Separator between metadata fields.",
)
@click.option(
    "--suffix",
    default="_framed",
    help="Suffix added to output filenames.",
)
@click.option(
    "--quality",
    type=int,
    default=95,
    help="JPEG quality (1-100).",
)
@click.option(
    "--info",
    is_flag=True,
    help="Show metadata info without creating frames.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed progress.",
)
def cli(
    paths,
    output,
    background,
    padding,
    thickness,
    font,
    font_size,
    no_italic,
    fields,
    include_gps,
    position,
    layout,
    separator,
    suffix,
    quality,
    info,
    verbose,
):
    """
    Add EXIF metadata frames to photographs.

    PATHS can be image files or directories containing images.

    Examples:

        metaframe photo.jpg -o ./output

        metaframe photos/ -o ./framed --background black

        metaframe *.jpg -o ./output --fields aperture,shutter_speed,iso
    """
    # Get list of image files
    image_files = get_image_files(paths)

    if not image_files:
        click.echo("No supported image files found.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(image_files)} image(s)")

    # Info mode: just show metadata
    if info:
        extractor = MetadataExtractor()
        for img_path in image_files:
            click.echo(f"\n{img_path.name}:")
            try:
                metadata = extractor.extract(img_path)
                if metadata.has_any_data():
                    for field in MetadataField:
                        value = metadata.get_field(field)
                        if value:
                            click.echo(f"  {field.value}: {value}")
                else:
                    click.echo("  No EXIF metadata found")
            except Exception as e:
                click.echo(f"  Error: {e}", err=True)
        return

    # Build settings
    settings = FrameSettings()

    if background:
        settings.background_color = background
    if padding is not None:
        settings.padding = padding
    if thickness is not None:
        settings.thickness = thickness
    if font:
        settings.font_family = font
    if font_size is not None:
        settings.font_size = font_size
    if no_italic:
        settings.italic = False
    if fields:
        settings.fields = fields
    if include_gps:
        settings.include_gps = True
    if position:
        settings.position = MetadataPosition(position.lower())
    if layout:
        settings.row_layout = RowLayout(layout.lower())
    if separator:
        settings.separator = Separator(separator.lower())
    if suffix:
        settings.output_suffix = suffix
    if quality:
        settings.jpeg_quality = quality

    # Create output directory
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process images
    framer = Framer(settings)

    def progress_callback(current, total, path):
        if path and verbose:
            click.echo(f"[{current + 1}/{total}] Processing: {path.name}")
        elif current == total:
            click.echo(f"Completed: {total} image(s) processed")

    results = framer.process_batch(image_files, output_dir, progress_callback)

    # Report results
    success_count = sum(1 for _, result in results if isinstance(result, Path))
    error_count = len(results) - success_count

    if error_count > 0:
        click.echo(f"\nErrors ({error_count}):", err=True)
        for input_path, result in results:
            if isinstance(result, Exception):
                click.echo(f"  {input_path.name}: {result}", err=True)

    if success_count > 0:
        click.echo(f"\nOutput saved to: {output_dir}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
