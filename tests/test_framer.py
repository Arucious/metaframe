"""Tests for image framing."""

import pytest
from PIL import Image
from pathlib import Path
import tempfile

from metaframe.core.framer import Framer
from metaframe.core.config import (
    FrameSettings,
    MetadataField,
    MetadataPosition,
    RowLayout,
    Separator,
)
from metaframe.core.metadata import ExtractedMetadata


class TestFramer:
    """Tests for the Framer class."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        return img

    @pytest.fixture
    def sample_image_file(self, sample_image):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            sample_image.save(f.name, "JPEG")
            yield Path(f.name)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata."""
        return ExtractedMetadata(
            camera_make="Canon",
            camera_model="EOS R5",
            lens="RF 50mm f/1.2L",
            focal_length="50mm",
            aperture="f/1.2",
            shutter_speed="1/250s",
            iso="ISO 100",
        )

    def test_create_frame_default_settings(self, sample_image_file, sample_metadata):
        """Test creating a frame with default settings."""
        framer = Framer()
        result = framer.create_frame(sample_image_file, sample_metadata)

        assert isinstance(result, Image.Image)
        # Frame should be larger than original (800x600)
        assert result.width >= 800
        assert result.height >= 600

    def test_create_frame_bottom_position(self, sample_image_file, sample_metadata):
        """Test frame with bottom metadata position."""
        settings = FrameSettings(position=MetadataPosition.BOTTOM)
        framer = Framer(settings)
        result = framer.create_frame(sample_image_file, sample_metadata)

        # Height should increase more than width
        assert result.height > 600 + settings.padding * 2

    def test_create_frame_right_position(self, sample_image_file, sample_metadata):
        """Test frame with right-side metadata position."""
        settings = FrameSettings(position=MetadataPosition.RIGHT)
        framer = Framer(settings)
        result = framer.create_frame(sample_image_file, sample_metadata)

        # Width should increase more for side positioning
        assert result.width > 800 + settings.padding

    def test_color_parsing(self):
        """Test color parsing."""
        framer = Framer()

        # Hex colors
        assert framer._parse_color("#FFFFFF") == (255, 255, 255)
        assert framer._parse_color("#000000") == (0, 0, 0)
        assert framer._parse_color("#FF0000") == (255, 0, 0)
        assert framer._parse_color("#fff") == (255, 255, 255)

        # Named colors
        assert framer._parse_color("white") == (255, 255, 255)
        assert framer._parse_color("black") == (0, 0, 0)
        assert framer._parse_color("grey") == (128, 128, 128)

    def test_get_text_lines_single_row(self, sample_metadata):
        """Test text line generation for single row layout."""
        settings = FrameSettings(
            row_layout=RowLayout.SINGLE,
            fields=[MetadataField.APERTURE, MetadataField.ISO],
            separator=Separator.PIPE,
        )
        framer = Framer(settings)
        lines = framer._get_text_lines(sample_metadata)

        assert len(lines) == 1
        assert "f/1.2" in lines[0]
        assert "ISO 100" in lines[0]
        assert "|" in lines[0]

    def test_get_text_lines_multi_row(self, sample_metadata):
        """Test text line generation for multi-row layout."""
        settings = FrameSettings(
            row_layout=RowLayout.MULTI_ROW,
            fields=[
                MetadataField.FOCAL_LENGTH,
                MetadataField.APERTURE,
                MetadataField.ISO,
            ],
        )
        framer = Framer(settings)
        lines = framer._get_text_lines(sample_metadata)

        assert len(lines) == 3
        assert "50mm" in lines[0]
        assert "f/1.2" in lines[1]
        assert "ISO 100" in lines[2]

    def test_save_framed_image_jpeg(self, sample_image_file, sample_metadata):
        """Test saving framed image as JPEG."""
        framer = Framer()
        framed = framer.create_frame(sample_image_file, sample_metadata)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            output_path = Path(f.name)

        result_path = framer.save_framed_image(framed, output_path)

        assert result_path.exists()
        assert result_path.suffix.lower() == ".jpg"

        # Verify it's a valid image
        with Image.open(result_path) as img:
            assert img.format == "JPEG"

        # Cleanup
        result_path.unlink()

    def test_save_framed_image_png(self, sample_image_file, sample_metadata):
        """Test saving framed image as PNG."""
        framer = Framer()
        framed = framer.create_frame(sample_image_file, sample_metadata)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)

        result_path = framer.save_framed_image(framed, output_path)

        assert result_path.exists()
        assert result_path.suffix.lower() == ".png"

        # Verify it's a valid image
        with Image.open(result_path) as img:
            assert img.format == "PNG"

        # Cleanup
        result_path.unlink()

    def test_process_image(self, sample_image_file):
        """Test processing a single image."""
        settings = FrameSettings(output_suffix="_test")
        framer = Framer(settings)

        with tempfile.TemporaryDirectory() as output_dir:
            result_path = framer.process_image(sample_image_file, output_dir)

            assert result_path.exists()
            assert "_test" in result_path.stem

    def test_process_batch(self, sample_image):
        """Test batch processing multiple images."""
        # Create multiple test images
        with tempfile.TemporaryDirectory() as input_dir:
            input_paths = []
            for i in range(3):
                path = Path(input_dir) / f"test_{i}.jpg"
                sample_image.save(path, "JPEG")
                input_paths.append(path)

            with tempfile.TemporaryDirectory() as output_dir:
                framer = Framer()
                results = framer.process_batch(input_paths, output_dir)

                assert len(results) == 3
                for input_path, result in results:
                    assert isinstance(result, Path)
                    assert result.exists()


class TestFrameSettings:
    """Tests for FrameSettings."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = FrameSettings()

        assert settings.padding == 60
        assert settings.thickness == 80
        assert settings.background_color == "#FFFFFF"
        assert settings.italic is True
        assert settings.position == MetadataPosition.BOTTOM

    def test_get_separator_string(self):
        """Test getting separator string."""
        settings = FrameSettings(separator=Separator.PIPE)
        assert settings.get_separator_string() == " | "

        settings = FrameSettings(separator=Separator.BULLET)
        assert settings.get_separator_string() == " \u2022 "

        settings = FrameSettings(separator=Separator.DASH)
        assert settings.get_separator_string() == " \u2014 "

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = FrameSettings(
            padding=100,
            thickness=50,
            background_color="#000000",
            position=MetadataPosition.TOP,
            separator=Separator.BULLET,
        )

        data = original.to_dict()
        restored = FrameSettings.from_dict(data)

        assert restored.padding == original.padding
        assert restored.thickness == original.thickness
        assert restored.background_color == original.background_color
        assert restored.position == original.position
        assert restored.separator == original.separator
