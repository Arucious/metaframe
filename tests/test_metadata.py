"""Tests for metadata extraction."""

import pytest
from metaframe.core.metadata import MetadataExtractor, ExtractedMetadata
from metaframe.core.config import MetadataField


class TestExtractedMetadata:
    """Tests for ExtractedMetadata dataclass."""

    def test_get_field(self):
        """Test getting field values."""
        metadata = ExtractedMetadata(
            aperture="f/2.8",
            shutter_speed="1/250s",
            iso="ISO 400",
        )

        assert metadata.get_field(MetadataField.APERTURE) == "f/2.8"
        assert metadata.get_field(MetadataField.SHUTTER_SPEED) == "1/250s"
        assert metadata.get_field(MetadataField.ISO) == "ISO 400"
        assert metadata.get_field(MetadataField.CAMERA_MAKE) is None

    def test_get_display_string(self):
        """Test generating display strings."""
        metadata = ExtractedMetadata(
            aperture="f/2.8",
            shutter_speed="1/250s",
            iso="ISO 400",
            focal_length="50mm",
        )

        fields = [
            MetadataField.FOCAL_LENGTH,
            MetadataField.APERTURE,
            MetadataField.SHUTTER_SPEED,
            MetadataField.ISO,
        ]

        result = metadata.get_display_string(fields, " | ")
        assert result == "50mm | f/2.8 | 1/250s | ISO 400"

    def test_get_display_string_with_missing_fields(self):
        """Test display string with some missing fields."""
        metadata = ExtractedMetadata(
            aperture="f/2.8",
            iso="ISO 400",
        )

        fields = [
            MetadataField.FOCAL_LENGTH,  # Missing
            MetadataField.APERTURE,
            MetadataField.SHUTTER_SPEED,  # Missing
            MetadataField.ISO,
        ]

        result = metadata.get_display_string(fields, " • ")
        assert result == "f/2.8 • ISO 400"

    def test_has_any_data(self):
        """Test checking if metadata has any data."""
        empty = ExtractedMetadata()
        assert not empty.has_any_data()

        with_data = ExtractedMetadata(aperture="f/2.8")
        assert with_data.has_any_data()


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_format_aperture(self):
        """Test aperture formatting."""
        extractor = MetadataExtractor()

        assert extractor._format_aperture(2.8) == "f/2.8"
        assert extractor._format_aperture(4) == "f/4"
        assert extractor._format_aperture(5.6) == "f/5.6"
        assert extractor._format_aperture(None) is None

    def test_format_shutter_speed(self):
        """Test shutter speed formatting."""
        extractor = MetadataExtractor()

        assert extractor._format_shutter_speed(0.004) == "1/250s"
        assert extractor._format_shutter_speed(0.5) == "1/2s"
        assert extractor._format_shutter_speed(1) == "1s"
        assert extractor._format_shutter_speed(2) == "2s"
        assert extractor._format_shutter_speed(None) is None

    def test_format_iso(self):
        """Test ISO formatting."""
        extractor = MetadataExtractor()

        assert extractor._format_iso(100) == "ISO 100"
        assert extractor._format_iso(3200) == "ISO 3200"
        assert extractor._format_iso([400]) == "ISO 400"
        assert extractor._format_iso(None) is None

    def test_format_focal_length(self):
        """Test focal length formatting."""
        extractor = MetadataExtractor()

        assert extractor._format_focal_length(50) == "50mm"
        assert extractor._format_focal_length(24, 36) == "24mm (36mm eq.)"
        assert extractor._format_focal_length(50, 50) == "50mm"
        assert extractor._format_focal_length(None) is None

    def test_clean_string(self):
        """Test string cleaning."""
        extractor = MetadataExtractor()

        assert extractor._clean_string("Canon") == "Canon"
        assert extractor._clean_string("Canon\x00") == "Canon"
        assert extractor._clean_string("  Canon  ") == "Canon"
        assert extractor._clean_string("") is None
        assert extractor._clean_string(None) is None

    def test_format_gps(self):
        """Test GPS coordinate formatting."""
        extractor = MetadataExtractor()

        gps_data = {
            "lat": [37, 47, 15.12],
            "lat_ref": "N",
            "lon": [122, 25, 10.08],
            "lon_ref": "W",
        }

        result = extractor._format_gps(gps_data)
        assert result is not None
        assert "N" in result
        assert "W" in result

    def test_extract_file_not_found(self):
        """Test extracting from non-existent file."""
        extractor = MetadataExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract("/nonexistent/path/image.jpg")
