"""EXIF metadata extraction from images."""

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import exifread
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from metaframe.core.config import MetadataField


@dataclass
class ExtractedMetadata:
    """Container for extracted metadata values."""

    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    focal_length: str | None = None
    aperture: str | None = None
    shutter_speed: str | None = None
    iso: str | None = None
    date_time: str | None = None
    gps: str | None = None

    # Raw values for potential future use
    _raw: dict = None

    def __post_init__(self):
        if self._raw is None:
            self._raw = {}

    def get_field(self, field: MetadataField) -> str | None:
        """Get a formatted field value by MetadataField enum."""
        field_map = {
            MetadataField.CAMERA_MAKE: self.camera_make,
            MetadataField.CAMERA_MODEL: self.camera_model,
            MetadataField.LENS: self.lens,
            MetadataField.FOCAL_LENGTH: self.focal_length,
            MetadataField.APERTURE: self.aperture,
            MetadataField.SHUTTER_SPEED: self.shutter_speed,
            MetadataField.ISO: self.iso,
            MetadataField.DATE_TIME: self.date_time,
            MetadataField.GPS: self.gps,
        }
        return field_map.get(field)

    def get_display_string(
        self, fields: list[MetadataField], separator: str = " | "
    ) -> str:
        """Get a formatted display string for the given fields."""
        values = []
        for field in fields:
            value = self.get_field(field)
            if value:
                values.append(value)
        return separator.join(values)

    def has_any_data(self) -> bool:
        """Check if any metadata was extracted."""
        return any(
            [
                self.camera_make,
                self.camera_model,
                self.lens,
                self.focal_length,
                self.aperture,
                self.shutter_speed,
                self.iso,
                self.date_time,
                self.gps,
            ]
        )


class MetadataExtractor:
    """Extract and format EXIF metadata from images."""

    def __init__(self):
        pass

    def extract(self, image_path: str | Path) -> ExtractedMetadata:
        """
        Extract metadata from an image file.

        Uses both Pillow and exifread for maximum compatibility.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Try Pillow first (handles most common cases)
        pillow_data = self._extract_pillow(image_path)

        # Use exifread as fallback/supplement for edge cases
        exifread_data = self._extract_exifread(image_path)

        # Merge data, preferring Pillow but filling gaps with exifread
        return self._merge_metadata(pillow_data, exifread_data)

    def _extract_pillow(self, image_path: Path) -> dict[str, Any]:
        """Extract metadata using Pillow."""
        data = {}

        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if not exif:
                    return data

                # Decode EXIF tags
                decoded = {}
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    decoded[tag] = value

                # Extract specific fields
                data["make"] = decoded.get("Make")
                data["model"] = decoded.get("Model")
                data["lens"] = decoded.get("LensModel") or decoded.get("LensInfo")
                data["focal_length"] = decoded.get("FocalLength")
                data["focal_length_35mm"] = decoded.get("FocalLengthIn35mmFilm")
                data["aperture"] = decoded.get("FNumber")
                data["exposure_time"] = decoded.get("ExposureTime")
                data["iso"] = decoded.get("ISOSpeedRatings")
                data["date_time"] = decoded.get("DateTimeOriginal") or decoded.get(
                    "DateTime"
                )

                # GPS data
                gps_info = decoded.get("GPSInfo")
                if gps_info:
                    data["gps"] = self._parse_gps_pillow(gps_info)

        except Exception:
            pass

        return data

    def _extract_exifread(self, image_path: Path) -> dict[str, Any]:
        """Extract metadata using exifread (handles more edge cases)."""
        data = {}

        try:
            with open(image_path, "rb") as f:
                tags = exifread.process_file(f, details=False)

            data["make"] = self._get_exifread_value(tags, "Image Make")
            data["model"] = self._get_exifread_value(tags, "Image Model")
            data["lens"] = self._get_exifread_value(
                tags, "EXIF LensModel"
            ) or self._get_exifread_value(tags, "EXIF LensInfo")
            data["focal_length"] = self._get_exifread_value(tags, "EXIF FocalLength")
            data["focal_length_35mm"] = self._get_exifread_value(
                tags, "EXIF FocalLengthIn35mmFilm"
            )
            data["aperture"] = self._get_exifread_value(tags, "EXIF FNumber")
            data["exposure_time"] = self._get_exifread_value(tags, "EXIF ExposureTime")
            data["iso"] = self._get_exifread_value(tags, "EXIF ISOSpeedRatings")
            data["date_time"] = self._get_exifread_value(
                tags, "EXIF DateTimeOriginal"
            ) or self._get_exifread_value(tags, "Image DateTime")

            # GPS data
            gps_lat = self._get_exifread_value(tags, "GPS GPSLatitude")
            gps_lat_ref = self._get_exifread_value(tags, "GPS GPSLatitudeRef")
            gps_lon = self._get_exifread_value(tags, "GPS GPSLongitude")
            gps_lon_ref = self._get_exifread_value(tags, "GPS GPSLongitudeRef")

            if gps_lat and gps_lon:
                data["gps"] = {
                    "lat": gps_lat,
                    "lat_ref": gps_lat_ref,
                    "lon": gps_lon,
                    "lon_ref": gps_lon_ref,
                }

        except Exception:
            pass

        return data

    def _get_exifread_value(self, tags: dict, key: str) -> Any:
        """Safely get a value from exifread tags."""
        if key in tags:
            value = tags[key]
            # exifread returns IfdTag objects, get the actual value
            if hasattr(value, "values"):
                values = value.values
                if len(values) == 1:
                    return values[0]
                return values
            return str(value)
        return None

    def _parse_gps_pillow(self, gps_info: dict) -> dict | None:
        """Parse GPS info from Pillow's GPSInfo dict."""
        try:
            # Decode GPS tags
            gps_decoded = {}
            for tag_id, value in gps_info.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                gps_decoded[tag] = value

            lat = gps_decoded.get("GPSLatitude")
            lat_ref = gps_decoded.get("GPSLatitudeRef")
            lon = gps_decoded.get("GPSLongitude")
            lon_ref = gps_decoded.get("GPSLongitudeRef")

            if lat and lon:
                return {
                    "lat": lat,
                    "lat_ref": lat_ref,
                    "lon": lon,
                    "lon_ref": lon_ref,
                }
        except Exception:
            pass
        return None

    def _merge_metadata(
        self, pillow_data: dict, exifread_data: dict
    ) -> ExtractedMetadata:
        """Merge metadata from both sources and format values."""

        def get_value(key: str) -> Any:
            """Get value preferring Pillow, falling back to exifread."""
            return pillow_data.get(key) or exifread_data.get(key)

        # Format camera make/model
        camera_make = self._clean_string(get_value("make"))
        camera_model = self._clean_string(get_value("model"))

        # Format lens
        lens = self._format_lens(get_value("lens"))

        # Format focal length
        focal_length = self._format_focal_length(
            get_value("focal_length"), get_value("focal_length_35mm")
        )

        # Format aperture
        aperture = self._format_aperture(get_value("aperture"))

        # Format shutter speed
        shutter_speed = self._format_shutter_speed(get_value("exposure_time"))

        # Format ISO
        iso = self._format_iso(get_value("iso"))

        # Format date/time
        date_time = self._format_datetime(get_value("date_time"))

        # Format GPS
        gps = self._format_gps(get_value("gps"))

        return ExtractedMetadata(
            camera_make=camera_make,
            camera_model=camera_model,
            lens=lens,
            focal_length=focal_length,
            aperture=aperture,
            shutter_speed=shutter_speed,
            iso=iso,
            date_time=date_time,
            gps=gps,
            _raw={"pillow": pillow_data, "exifread": exifread_data},
        )

    def _clean_string(self, value: Any) -> str | None:
        """Clean and return a string value."""
        if value is None:
            return None
        s = str(value).strip()
        # Remove null bytes and extra whitespace
        s = s.replace("\x00", "").strip()
        return s if s else None

    def _format_lens(self, value: Any) -> str | None:
        """Format lens information."""
        if value is None:
            return None

        if isinstance(value, str):
            return self._clean_string(value)

        # Handle tuple/list (LensInfo format: min_focal, max_focal, min_f, max_f)
        if isinstance(value, (tuple, list)) and len(value) >= 2:
            try:
                min_focal = float(value[0])
                max_focal = float(value[1])
                if min_focal == max_focal:
                    return f"{int(min_focal)}mm"
                return f"{int(min_focal)}-{int(max_focal)}mm"
            except (ValueError, TypeError):
                pass

        return self._clean_string(str(value))

    def _format_focal_length(
        self, focal_length: Any, focal_length_35mm: Any = None
    ) -> str | None:
        """Format focal length value."""
        if focal_length is None:
            return None

        try:
            # Handle Fraction or IFDRational
            if hasattr(focal_length, "numerator"):
                fl = float(focal_length.numerator) / float(focal_length.denominator)
            elif isinstance(focal_length, (int, float)):
                fl = float(focal_length)
            else:
                fl = float(focal_length)

            result = f"{int(fl)}mm"

            # Add 35mm equivalent if different and available
            if focal_length_35mm:
                try:
                    fl_35 = int(focal_length_35mm)
                    if fl_35 != int(fl):
                        result = f"{int(fl)}mm ({fl_35}mm eq.)"
                except (ValueError, TypeError):
                    pass

            return result

        except (ValueError, TypeError, ZeroDivisionError):
            return None

    def _format_aperture(self, value: Any) -> str | None:
        """Format aperture (f-number) value."""
        if value is None:
            return None

        try:
            # Handle Fraction or IFDRational
            if hasattr(value, "numerator"):
                f_number = float(value.numerator) / float(value.denominator)
            elif isinstance(value, (int, float)):
                f_number = float(value)
            else:
                f_number = float(value)

            # Format nicely: f/2.8, f/4, f/5.6, etc.
            if f_number == int(f_number):
                return f"f/{int(f_number)}"
            return f"f/{f_number:.1f}"

        except (ValueError, TypeError, ZeroDivisionError):
            return None

    def _format_shutter_speed(self, value: Any) -> str | None:
        """Format shutter speed (exposure time) value."""
        if value is None:
            return None

        try:
            # Handle Fraction or IFDRational
            if hasattr(value, "numerator"):
                num = value.numerator
                denom = value.denominator
            elif isinstance(value, Fraction):
                num = value.numerator
                denom = value.denominator
            elif isinstance(value, (int, float)):
                # Convert decimal to fraction for display
                if value >= 1:
                    return f"{int(value)}s"
                frac = Fraction(value).limit_denominator(8000)
                num = frac.numerator
                denom = frac.denominator
            else:
                # Try to parse string like "1/250"
                s = str(value)
                if "/" in s:
                    parts = s.split("/")
                    num = int(parts[0])
                    denom = int(parts[1])
                else:
                    return f"{float(s):.1f}s"

            # Format as fraction or seconds
            if num == 0:
                return None

            exposure = num / denom

            if exposure >= 1:
                if exposure == int(exposure):
                    return f"{int(exposure)}s"
                return f"{exposure:.1f}s"
            else:
                # Show as fraction: 1/250s
                if num == 1:
                    return f"1/{denom}s"
                # Simplify to 1/x format
                equivalent_denom = int(denom / num)
                return f"1/{equivalent_denom}s"

        except (ValueError, TypeError, ZeroDivisionError):
            return None

    def _format_iso(self, value: Any) -> str | None:
        """Format ISO value."""
        if value is None:
            return None

        try:
            # Handle list/tuple (some cameras store as array)
            if isinstance(value, (list, tuple)):
                value = value[0]

            iso = int(value)
            return f"ISO {iso}"

        except (ValueError, TypeError, IndexError):
            return None

    def _format_datetime(self, value: Any) -> str | None:
        """Format date/time value."""
        if value is None:
            return None

        try:
            s = str(value)
            # EXIF format: "2024:01:15 14:30:00"
            dt = datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
            # Return in a nicer format
            return dt.strftime("%b %d, %Y %H:%M")

        except (ValueError, TypeError):
            # Return as-is if parsing fails
            return self._clean_string(value)

    def _format_gps(self, gps_data: dict | None) -> str | None:
        """Format GPS coordinates."""
        if gps_data is None:
            return None

        try:
            lat = self._dms_to_decimal(gps_data["lat"], gps_data.get("lat_ref", "N"))
            lon = self._dms_to_decimal(gps_data["lon"], gps_data.get("lon_ref", "E"))

            if lat is not None and lon is not None:
                lat_dir = "N" if lat >= 0 else "S"
                lon_dir = "E" if lon >= 0 else "W"
                return f"{abs(lat):.4f}\u00b0{lat_dir}, {abs(lon):.4f}\u00b0{lon_dir}"

        except (KeyError, TypeError):
            pass

        return None

    def _dms_to_decimal(self, dms: Any, ref: str) -> float | None:
        """Convert degrees/minutes/seconds to decimal degrees."""
        try:
            if isinstance(dms, (list, tuple)) and len(dms) >= 3:
                # Handle various formats
                def to_float(v):
                    if hasattr(v, "numerator"):
                        return float(v.numerator) / float(v.denominator)
                    return float(v)

                d = to_float(dms[0])
                m = to_float(dms[1])
                s = to_float(dms[2])

                decimal = d + m / 60 + s / 3600

                if ref in ("S", "W"):
                    decimal = -decimal

                return decimal

        except (ValueError, TypeError, ZeroDivisionError):
            pass

        return None
