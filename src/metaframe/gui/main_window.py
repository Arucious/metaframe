"""Main window for MetaFrame GUI."""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QWidget,
)

from metaframe.core.config import FrameSettings
from metaframe.core.framer import HEIF_EXTENSIONS, RAW_EXTENSIONS, Framer
from metaframe.core.metadata import ExtractedMetadata, MetadataExtractor
from metaframe.gui.preview_widget import PreviewWidget
from metaframe.gui.settings_panel import SettingsPanel

# All supported image extensions
STANDARD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}
SUPPORTED_EXTENSIONS = STANDARD_EXTENSIONS | RAW_EXTENSIONS | HEIF_EXTENSIONS


class BatchProcessWorker(QThread):
    """Worker thread for batch processing images."""

    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(list)  # results
    error = pyqtSignal(str)

    def __init__(self, framer: Framer, input_paths: list[Path], output_dir: Path):
        super().__init__()
        self.framer = framer
        self.input_paths = input_paths
        self.output_dir = output_dir
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        results = []
        total = len(self.input_paths)

        for i, input_path in enumerate(self.input_paths):
            if self._cancelled:
                break

            self.progress.emit(i, total, input_path.name)

            try:
                output_path = self.framer.process_image(input_path, self.output_dir)
                results.append((input_path, output_path))
            except Exception as e:
                results.append((input_path, e))

        self.finished.emit(results)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.current_image_path: Path | None = None
        self.current_metadata: ExtractedMetadata | None = None
        self.settings = FrameSettings()
        self.extractor = MetadataExtractor()

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("MetaFrame")
        self.setMinimumSize(1000, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout with splitter
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Preview widget (left side)
        self.preview = PreviewWidget()
        splitter.addWidget(self.preview)

        # Settings panel (right side)
        self.settings_panel = SettingsPanel(self.settings)
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        splitter.addWidget(self.settings_panel)

        # Set splitter proportions (70% preview, 30% settings)
        splitter.setSizes([700, 300])

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save Framed Image...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_image)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        batch_action = QAction("&Batch Process...", self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self._batch_process)
        file_menu.addAction(batch_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready - Open an image or drag and drop")

    def _open_file(self):
        """Open an image file."""
        # Build filter string with all supported extensions
        all_ext = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        raw_filter = "RAW Images (*.cr2 *.cr3 *.nef *.arw *.dng *.raf *.orf *.rw2)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            f"Images ({all_ext});;{raw_filter};;All Files (*)",
        )

        if file_path:
            self._load_image(Path(file_path))

    def _load_image(self, path: Path):
        """Load an image and extract metadata."""
        try:
            # Extract metadata
            self.current_metadata = self.extractor.extract(path)
            self.current_image_path = path

            # Update settings panel with available metadata
            self.settings_panel.update_metadata_availability(self.current_metadata)

            # Update preview
            self._update_preview()

            # Update status bar
            self.statusbar.showMessage(f"Loaded: {path.name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def _update_preview(self):
        """Update the preview with current settings."""
        if self.current_image_path is None:
            return

        try:
            framer = Framer(self.settings)
            framed_image = framer.create_frame(
                self.current_image_path, self.current_metadata
            )
            self.preview.set_image(framed_image, self.current_image_path)

        except Exception as e:
            self.statusbar.showMessage(f"Preview error: {e}")

    def _on_settings_changed(self, new_settings: FrameSettings):
        """Handle settings changes from the panel."""
        self.settings = new_settings
        self._update_preview()

    def _save_image(self):
        """Save the framed image."""
        if self.current_image_path is None:
            QMessageBox.warning(self, "No Image", "Please open an image first.")
            return

        # Suggest filename
        stem = self.current_image_path.stem
        suffix = self.settings.output_suffix
        ext = self.current_image_path.suffix
        suggested_name = f"{stem}{suffix}{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Framed Image",
            suggested_name,
            "JPEG (*.jpg *.jpeg);;PNG (*.png);;All Files (*)",
        )

        if file_path:
            try:
                framer = Framer(self.settings)
                framed_image = framer.create_frame(
                    self.current_image_path, self.current_metadata
                )
                output_path = framer.save_framed_image(framed_image, file_path)
                self.statusbar.showMessage(f"Saved: {output_path}")
                QMessageBox.information(
                    self, "Saved", f"Image saved to:\n{output_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image: {e}")

    def _batch_process(self):
        """Batch process multiple images."""
        # Select input files/folder
        all_ext = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        raw_filter = "RAW Images (*.cr2 *.cr3 *.nef *.arw *.dng *.raf *.orf *.rw2)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            f"Images ({all_ext});;{raw_filter};;All Files (*)",
        )

        if not file_paths:
            return

        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
        )

        if not output_dir:
            return

        # Filter to supported files
        input_paths = [
            Path(p) for p in file_paths
            if Path(p).suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not input_paths:
            QMessageBox.warning(self, "No Images", "No supported image files selected.")
            return

        # Create progress dialog
        progress = QProgressDialog(
            "Processing images...",
            "Cancel",
            0,
            len(input_paths),
            self,
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        # Create worker thread
        framer = Framer(self.settings)
        worker = BatchProcessWorker(framer, input_paths, Path(output_dir))

        def on_progress(current, total, filename):
            progress.setValue(current)
            progress.setLabelText(f"Processing: {filename}")

        def on_finished(results):
            progress.close()

            success_count = sum(1 for _, r in results if isinstance(r, Path))
            error_count = len(results) - success_count

            message = f"Processed {success_count} of {len(results)} images."
            if error_count > 0:
                message += f"\n\n{error_count} errors occurred."

            QMessageBox.information(self, "Batch Complete", message)
            self.statusbar.showMessage(
                f"Batch complete: {success_count} images saved to {output_dir}"
            )

        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        progress.canceled.connect(worker.cancel)

        worker.start()

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MetaFrame",
            "MetaFrame v0.1.0\n\n"
            "Add EXIF metadata frames to your photographs.\n\n"
            "Create beautiful framed images with camera settings displayed.",
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(
                Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTENSIONS
                for url in urls
            ):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        for url in urls:
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                self._load_image(path)
                break  # Load first valid image


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("MetaFrame")
    app.setOrganizationName("MetaFrame")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
