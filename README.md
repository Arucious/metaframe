# MetaFrame

Add EXIF metadata frames to your photographs. Create beautiful framed images with camera settings displayed.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

## Features

- **Extract EXIF metadata** from photos (camera, lens, aperture, shutter speed, ISO, focal length, GPS)
- **Customizable frames** with adjustable padding, thickness, and colors
- **Flexible layouts** - position metadata on any side (top, bottom, left, right)
- **Multiple row layouts** - single line, two rows, or multi-row
- **Font customization** - choose any system font, adjust size, enable/disable italic
- **Separator options** - pipe (`|`), bullet (`•`), or dash (`—`)
- **Batch processing** - process entire folders of images
- **Cross-platform** - works on Windows, macOS, and Linux
- **Completely offline** - no internet connection required

## Installation

### From Releases (Recommended)

Download the latest release for your platform from the [Releases](https://github.com/yourusername/metaframe/releases) page:

- **Windows**: `metaframe-windows-amd64.exe`
- **macOS**: `metaframe-macos-arm64` or `MetaFrame-macos.app.zip`
- **Linux**: `metaframe-linux-amd64`

### From Source

Requires Python 3.11+

```bash
# Clone the repository
git clone https://github.com/yourusername/metaframe.git
cd metaframe

# Install in development mode
pip install -e ".[dev]"
```

## Usage

### GUI Application

Simply run the executable or launch from source:

```bash
# From source
python -m metaframe
```

- **Open an image**: File → Open or drag and drop
- **Adjust settings** in the right panel
- **Save**: File → Save Framed Image
- **Batch process**: File → Batch Process

### Command Line

```bash
# Single image
metaframe photo.jpg -o ./output

# Multiple images
metaframe photo1.jpg photo2.jpg -o ./output

# Entire folder
metaframe ./photos/ -o ./framed

# With options
metaframe photo.jpg -o ./output \
  --background black \
  --padding 80 \
  --font "Helvetica" \
  --fields aperture,shutter_speed,iso,focal_length \
  --separator bullet
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory (required) |
| `-b, --background` | Background color (white, black, grey, cream, or #RRGGBB) |
| `-p, --padding` | Padding in pixels |
| `-t, --thickness` | Frame thickness in pixels |
| `-f, --font` | Font family name |
| `--font-size` | Font size in pixels |
| `--no-italic` | Disable italic text |
| `--fields` | Comma-separated fields to display |
| `--include-gps` | Include GPS coordinates (opt-in) |
| `--position` | Metadata position (bottom, top, left, right) |
| `--layout` | Row layout (single, two_rows, multi_row) |
| `--separator` | Field separator (pipe, bullet, dash) |
| `--suffix` | Output filename suffix (default: _framed) |
| `--quality` | JPEG quality 1-100 (default: 95) |
| `--info` | Show metadata without creating frames |
| `-v, --verbose` | Show detailed progress |

### Available Metadata Fields

| Field | Example |
|-------|---------|
| `camera_make` | Canon |
| `camera_model` | EOS R5 |
| `lens` | RF 50mm f/1.2L |
| `focal_length` | 50mm |
| `aperture` | f/1.2 |
| `shutter_speed` | 1/250s |
| `iso` | ISO 100 |
| `date_time` | Jan 15, 2024 14:30 |
| `gps` | 37.7749°N, 122.4194°W |

## Examples

### Basic framed photo

```bash
metaframe photo.jpg -o ./output
```

Creates a white-framed photo with default metadata (focal length, aperture, shutter speed, ISO) at the bottom.

### Dark frame with custom fields

```bash
metaframe photo.jpg -o ./output \
  --background black \
  --fields camera_model,lens,focal_length,aperture,shutter_speed,iso
```

### Minimal side layout

```bash
metaframe photo.jpg -o ./output \
  --position right \
  --layout multi_row \
  --fields aperture,shutter_speed,iso
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Building Executables

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Build with PyInstaller
pyinstaller metaframe.spec
```

### Code Style

```bash
# Check with ruff
ruff check src/

# Format
ruff format src/
```

## Privacy Note

GPS location data is opt-in and requires explicit `--include-gps` flag in CLI or checkbox in GUI. Be mindful when sharing photos with location data.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
