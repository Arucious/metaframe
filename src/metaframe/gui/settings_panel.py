"""Settings panel widget for MetaFrame GUI."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from metaframe.core.config import (
    PRESET_COLORS,
    AspectRatioPreset,
    FrameSettings,
    MetadataField,
    MetadataPosition,
    RowLayout,
    Separator,
    TextAlignment,
)
from metaframe.core.metadata import ExtractedMetadata


class ColorButton(QPushButton):
    """Button that displays and allows selection of a color."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#FFFFFF"):
        super().__init__()
        self._color = color
        self.setMinimumWidth(60)
        self.setMaximumWidth(60)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        """Update button style to show current color."""
        # Calculate contrasting text color
        r, g, b = self._hex_to_rgb(self._color)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        text_color = "#000000" if luminance > 0.5 else "#FFFFFF"

        self.setStyleSheet(
            f"background-color: {self._color}; color: {text_color}; "
            f"border: 1px solid #999; padding: 4px;"
        )
        self.setText(self._color)

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        """Get the current color."""
        return self._color

    def set_color(self, color: str):
        """Set the current color."""
        self._color = color
        self._update_style()


class SettingsPanel(QWidget):
    """Panel for customizing frame settings."""

    settings_changed = pyqtSignal(FrameSettings)

    def __init__(self, settings: FrameSettings):
        super().__init__()

        self._settings = settings
        self._updating = False  # Prevent recursive updates
        self._metadata_availability: dict[MetadataField, bool] = {}

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll)

        # Content widget
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        # Frame Settings Group
        frame_group = QGroupBox("Frame")
        frame_layout = QFormLayout(frame_group)
        layout.addWidget(frame_group)

        # Padding
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(10, 200)
        self.padding_spin.setSuffix(" px")
        self.padding_spin.valueChanged.connect(self._emit_changes)
        frame_layout.addRow("Padding:", self.padding_spin)

        # Thickness
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(20, 300)
        self.thickness_spin.setSuffix(" px")
        self.thickness_spin.valueChanged.connect(self._emit_changes)
        frame_layout.addRow("Thickness:", self.thickness_spin)

        # Background color
        bg_layout = QHBoxLayout()
        self.bg_color_btn = ColorButton()
        self.bg_color_btn.color_changed.connect(self._emit_changes)
        bg_layout.addWidget(self.bg_color_btn)

        # Preset buttons
        for name, hex_color in PRESET_COLORS.items():
            btn = QPushButton(name.title())
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, c=hex_color: self._set_bg_color(c))
            bg_layout.addWidget(btn)

        bg_layout.addStretch()
        frame_layout.addRow("Background:", bg_layout)

        # Text color
        text_layout = QHBoxLayout()
        self.text_color_btn = ColorButton("#000000")
        self.text_color_btn.color_changed.connect(self._emit_changes)
        text_layout.addWidget(self.text_color_btn)

        # Quick toggle
        black_btn = QPushButton("Black")
        black_btn.setMaximumWidth(60)
        black_btn.clicked.connect(lambda: self._set_text_color("#000000"))
        text_layout.addWidget(black_btn)

        white_btn = QPushButton("White")
        white_btn.setMaximumWidth(60)
        white_btn.clicked.connect(lambda: self._set_text_color("#FFFFFF"))
        text_layout.addWidget(white_btn)

        text_layout.addStretch()
        frame_layout.addRow("Text Color:", text_layout)

        # Font Settings Group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        layout.addWidget(font_group)

        # Font family
        self.font_combo = QComboBox()
        self.font_combo.setEditable(True)
        # Populate with system fonts (static method in PyQt6)
        families = QFontDatabase.families()
        self.font_combo.addItems(sorted(families))
        self.font_combo.currentTextChanged.connect(self._emit_changes)
        font_layout.addRow("Font:", self.font_combo)

        # Font size (0 = auto)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(0, 72)
        self.font_size_spin.setSpecialValueText("Auto")
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.valueChanged.connect(self._emit_changes)
        font_layout.addRow("Size:", self.font_size_spin)

        # Italic
        self.italic_check = QCheckBox("Italic")
        self.italic_check.stateChanged.connect(self._emit_changes)
        font_layout.addRow("", self.italic_check)

        # Layout Settings Group
        layout_group = QGroupBox("Layout")
        layout_form = QFormLayout(layout_group)
        layout.addWidget(layout_group)

        # Position
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Bottom", "Top", "Left", "Right"])
        self.position_combo.currentIndexChanged.connect(self._emit_changes)
        layout_form.addRow("Position:", self.position_combo)

        # Row layout
        self.row_layout_combo = QComboBox()
        self.row_layout_combo.addItems(["Single Row", "Two Rows", "Multi-Row"])
        self.row_layout_combo.currentIndexChanged.connect(self._emit_changes)
        layout_form.addRow("Rows:", self.row_layout_combo)

        # Separator
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["Pipe ( | )", "Bullet ( \u2022 )", "Dash ( \u2014 )"])
        self.separator_combo.currentIndexChanged.connect(self._emit_changes)
        layout_form.addRow("Separator:", self.separator_combo)

        # Text alignment
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItems(["Left", "Center", "Right"])
        self.alignment_combo.currentIndexChanged.connect(self._emit_changes)
        layout_form.addRow("Alignment:", self.alignment_combo)

        # Aspect ratio presets
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems([
            "Original",
            "1:1 (Square)",
            "4:5 (Instagram)",
            "16:9 (Widescreen)",
            "3:2 (Classic)",
            "9:16 (Stories)",
        ])
        self.aspect_combo.currentIndexChanged.connect(self._emit_changes)
        layout_form.addRow("Aspect Ratio:", self.aspect_combo)

        # Metadata Fields Group
        fields_group = QGroupBox("Metadata Fields")
        fields_layout = QVBoxLayout(fields_group)
        layout.addWidget(fields_group)

        # Field checkboxes
        self.field_checks: dict[MetadataField, QCheckBox] = {}

        field_labels = {
            MetadataField.CAMERA_MAKE: "Camera Make",
            MetadataField.CAMERA_MODEL: "Camera Model",
            MetadataField.LENS: "Lens",
            MetadataField.FOCAL_LENGTH: "Focal Length",
            MetadataField.APERTURE: "Aperture",
            MetadataField.SHUTTER_SPEED: "Shutter Speed",
            MetadataField.ISO: "ISO",
            MetadataField.DATE_TIME: "Date/Time",
            MetadataField.GPS: "GPS Location \u26a0\ufe0f",
        }

        for field, label in field_labels.items():
            check = QCheckBox(label)
            check.stateChanged.connect(self._emit_changes)
            fields_layout.addWidget(check)
            self.field_checks[field] = check

        # GPS warning
        self.gps_warning = QLabel(
            "\u26a0\ufe0f GPS data may reveal your location"
        )
        self.gps_warning.setStyleSheet("color: #cc7700; font-size: 11px;")
        self.gps_warning.setVisible(False)
        fields_layout.addWidget(self.gps_warning)

        # Connect GPS checkbox to show/hide warning
        self.field_checks[MetadataField.GPS].stateChanged.connect(
            lambda state: self.gps_warning.setVisible(state == Qt.CheckState.Checked.value)
        )

        # Stretch at bottom
        layout.addStretch()

    def _load_settings(self):
        """Load settings into the UI."""
        self._updating = True

        self.padding_spin.setValue(self._settings.padding)
        self.thickness_spin.setValue(self._settings.thickness)
        self.bg_color_btn.set_color(self._settings.background_color)
        self.text_color_btn.set_color(self._settings.text_color)

        # Set font
        index = self.font_combo.findText(self._settings.font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        else:
            self.font_combo.setEditText(self._settings.font_family)

        self.font_size_spin.setValue(self._settings.font_size)
        self.italic_check.setChecked(self._settings.italic)

        # Position
        position_map = {
            MetadataPosition.BOTTOM: 0,
            MetadataPosition.TOP: 1,
            MetadataPosition.LEFT: 2,
            MetadataPosition.RIGHT: 3,
        }
        self.position_combo.setCurrentIndex(position_map.get(self._settings.position, 0))

        # Row layout
        layout_map = {
            RowLayout.SINGLE: 0,
            RowLayout.TWO_ROWS: 1,
            RowLayout.MULTI_ROW: 2,
        }
        self.row_layout_combo.setCurrentIndex(layout_map.get(self._settings.row_layout, 0))

        # Separator
        separator_map = {
            Separator.PIPE: 0,
            Separator.BULLET: 1,
            Separator.DASH: 2,
        }
        self.separator_combo.setCurrentIndex(separator_map.get(self._settings.separator, 0))

        # Text alignment
        alignment_map = {
            TextAlignment.LEFT: 0,
            TextAlignment.CENTER: 1,
            TextAlignment.RIGHT: 2,
        }
        self.alignment_combo.setCurrentIndex(alignment_map.get(self._settings.text_alignment, 1))

        # Aspect ratio
        aspect_map = {
            AspectRatioPreset.ORIGINAL: 0,
            AspectRatioPreset.SQUARE_1_1: 1,
            AspectRatioPreset.PORTRAIT_4_5: 2,
            AspectRatioPreset.LANDSCAPE_16_9: 3,
            AspectRatioPreset.LANDSCAPE_3_2: 4,
            AspectRatioPreset.PORTRAIT_9_16: 5,
        }
        self.aspect_combo.setCurrentIndex(aspect_map.get(self._settings.aspect_ratio, 0))

        # Field checkboxes
        for field, check in self.field_checks.items():
            if field == MetadataField.GPS:
                check.setChecked(self._settings.include_gps)
            else:
                check.setChecked(field in self._settings.fields)

        self._updating = False

    def _set_bg_color(self, color: str):
        """Set background color from preset."""
        self.bg_color_btn.set_color(color)
        self._emit_changes()

    def _set_text_color(self, color: str):
        """Set text color."""
        self.text_color_btn.set_color(color)
        self._emit_changes()

    def _emit_changes(self):
        """Emit settings changed signal."""
        if self._updating:
            return

        # Build new settings
        settings = FrameSettings(
            padding=self.padding_spin.value(),
            thickness=self.thickness_spin.value(),
            background_color=self.bg_color_btn.get_color(),
            text_color=self.text_color_btn.get_color(),
            font_family=self.font_combo.currentText(),
            font_size=self.font_size_spin.value(),
            italic=self.italic_check.isChecked(),
            position=self._get_position(),
            row_layout=self._get_row_layout(),
            separator=self._get_separator(),
            text_alignment=self._get_text_alignment(),
            aspect_ratio=self._get_aspect_ratio(),
            fields=self._get_selected_fields(),
            include_gps=self.field_checks[MetadataField.GPS].isChecked(),
        )

        self._settings = settings
        self.settings_changed.emit(settings)

    def _get_position(self) -> MetadataPosition:
        """Get selected position."""
        index = self.position_combo.currentIndex()
        positions = [
            MetadataPosition.BOTTOM,
            MetadataPosition.TOP,
            MetadataPosition.LEFT,
            MetadataPosition.RIGHT,
        ]
        return positions[index]

    def _get_row_layout(self) -> RowLayout:
        """Get selected row layout."""
        index = self.row_layout_combo.currentIndex()
        layouts = [RowLayout.SINGLE, RowLayout.TWO_ROWS, RowLayout.MULTI_ROW]
        return layouts[index]

    def _get_separator(self) -> Separator:
        """Get selected separator."""
        index = self.separator_combo.currentIndex()
        separators = [Separator.PIPE, Separator.BULLET, Separator.DASH]
        return separators[index]

    def _get_text_alignment(self) -> TextAlignment:
        """Get selected text alignment."""
        index = self.alignment_combo.currentIndex()
        alignments = [TextAlignment.LEFT, TextAlignment.CENTER, TextAlignment.RIGHT]
        return alignments[index]

    def _get_aspect_ratio(self) -> AspectRatioPreset:
        """Get selected aspect ratio preset."""
        index = self.aspect_combo.currentIndex()
        presets = [
            AspectRatioPreset.ORIGINAL,
            AspectRatioPreset.SQUARE_1_1,
            AspectRatioPreset.PORTRAIT_4_5,
            AspectRatioPreset.LANDSCAPE_16_9,
            AspectRatioPreset.LANDSCAPE_3_2,
            AspectRatioPreset.PORTRAIT_9_16,
        ]
        return presets[index]

    def _get_selected_fields(self) -> list[MetadataField]:
        """Get list of selected metadata fields."""
        fields = []
        for field, check in self.field_checks.items():
            if field != MetadataField.GPS and check.isChecked():
                fields.append(field)
        return fields

    def update_metadata_availability(self, metadata: ExtractedMetadata):
        """
        Update field checkboxes based on available metadata.

        Disables checkboxes for fields not present in the image.
        """
        for field, check in self.field_checks.items():
            value = metadata.get_field(field)
            available = value is not None

            self._metadata_availability[field] = available

            # Update checkbox tooltip to show value or "not available"
            if available:
                check.setToolTip(f"Value: {value}")
                check.setEnabled(True)
            else:
                check.setToolTip("Not available in this image")
                # Don't disable, just show as unavailable
                # User might still want to keep it selected for batch processing
