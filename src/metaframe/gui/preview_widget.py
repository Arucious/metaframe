"""Image preview widget for MetaFrame GUI."""

from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QImage, QMouseEvent, QPixmap, QWheelEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class PreviewWidget(QWidget):
    """Widget for displaying image preview with zoom controls."""

    def __init__(self):
        super().__init__()

        self._current_image: Image.Image | None = None
        self._current_path: Path | None = None
        self._zoom_level = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0

        # Panning state
        self._is_panning = False
        self._pan_start_pos: QPoint | None = None
        self._scroll_start_h = 0
        self._scroll_start_v = 0

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area for the image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)  # Allow image to be larger than viewport
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.scroll_area, 1)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        self.image_label.setCursor(Qt.CursorShape.OpenHandCursor)
        self.scroll_area.setWidget(self.image_label)

        # Placeholder text
        self.image_label.setText("Drop an image here\nor use File → Open")
        self.image_label.setStyleSheet(
            "background-color: #f0f0f0; color: #888; font-size: 16px;"
        )

        # Zoom controls
        zoom_layout = QHBoxLayout()
        layout.addLayout(zoom_layout)

        # Fit button
        fit_btn = QPushButton("Fit")
        fit_btn.setMaximumWidth(50)
        fit_btn.clicked.connect(self._fit_to_view)
        zoom_layout.addWidget(fit_btn)

        # Zoom out button
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)  # 10%
        self.zoom_slider.setMaximum(500)  # 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._on_slider_changed)
        zoom_layout.addWidget(self.zoom_slider, 1)

        # Zoom in button
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        # Zoom percentage label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_layout.addWidget(self.zoom_label)

        # 100% button
        actual_btn = QPushButton("100%")
        actual_btn.setMaximumWidth(50)
        actual_btn.clicked.connect(self._zoom_actual)
        zoom_layout.addWidget(actual_btn)

    def set_image(self, image: Image.Image, path: Path | None = None):
        """
        Set the image to display.

        Args:
            image: PIL Image to display.
            path: Optional path for display purposes.
        """
        self._current_image = image
        self._current_path = path

        # Convert PIL image to QPixmap
        self._pixmap = self._pil_to_pixmap(image)

        # Fit to view on first load
        self._fit_to_view()

    def _pil_to_pixmap(self, image: Image.Image) -> QPixmap:
        """Convert a PIL Image to QPixmap."""
        # Convert to RGB if necessary
        if image.mode == "RGBA":
            # Keep alpha
            data = image.tobytes("raw", "RGBA")
            qimage = QImage(
                data, image.width, image.height, QImage.Format.Format_RGBA8888
            )
        else:
            # Convert to RGB
            if image.mode != "RGB":
                image = image.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(
                data, image.width, image.height, QImage.Format.Format_RGB888
            )

        return QPixmap.fromImage(qimage)

    def _update_display(self):
        """Update the displayed image with current zoom level."""
        if self._current_image is None:
            return

        # Calculate scaled size
        original_size = self._pixmap.size()
        scaled_size = QSize(
            int(original_size.width() * self._zoom_level),
            int(original_size.height() * self._zoom_level),
        )

        # Scale pixmap
        scaled_pixmap = self._pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.adjustSize()

        # Update zoom label
        self.zoom_label.setText(f"{int(self._zoom_level * 100)}%")

        # Update slider without triggering signal
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(self._zoom_level * 100))
        self.zoom_slider.blockSignals(False)

    def _fit_to_view(self):
        """Fit image to the scroll area size."""
        if self._current_image is None:
            return

        # Get available size
        available = self.scroll_area.viewport().size()
        image_size = self._pixmap.size()

        # Calculate zoom to fit
        width_ratio = available.width() / image_size.width()
        height_ratio = available.height() / image_size.height()

        # Use smaller ratio to ensure full image fits, with some padding
        self._zoom_level = min(width_ratio, height_ratio) * 0.95

        # Clamp to valid range
        self._zoom_level = max(self._min_zoom, min(self._max_zoom, self._zoom_level))

        self._update_display()

    def _zoom_actual(self):
        """Set zoom to 100%."""
        self._zoom_level = 1.0
        self._update_display()

    def _zoom_in(self):
        """Zoom in by 10%."""
        self._zoom_level = min(self._max_zoom, self._zoom_level * 1.1)
        self._update_display()

    def _zoom_out(self):
        """Zoom out by 10%."""
        self._zoom_level = max(self._min_zoom, self._zoom_level / 1.1)
        self._update_display()

    def _on_slider_changed(self, value: int):
        """Handle zoom slider changes."""
        self._zoom_level = value / 100.0
        self._update_display()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if self._current_image is None:
            return

        # Zoom with Ctrl+wheel
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        """Handle resize to maintain fit if needed."""
        super().resizeEvent(event)
        # Could auto-fit here if desired

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.LeftButton and self._current_image is not None:
            self._is_panning = True
            self._pan_start_pos = event.globalPosition().toPoint()
            self._scroll_start_h = self.scroll_area.horizontalScrollBar().value()
            self._scroll_start_v = self.scroll_area.verticalScrollBar().value()
            self.image_label.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning."""
        if self._is_panning and self._pan_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._pan_start_pos
            self.scroll_area.horizontalScrollBar().setValue(
                self._scroll_start_h - delta.x()
            )
            self.scroll_area.verticalScrollBar().setValue(
                self._scroll_start_v - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to end panning."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_panning:
            self._is_panning = False
            self._pan_start_pos = None
            self.image_label.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
