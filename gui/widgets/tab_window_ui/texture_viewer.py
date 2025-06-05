"""Code for viewer tab window customization."""

from typing import cast, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from gui.widgets.texture_viewer import TextureViewer
    from gui.windows.viewer_tab_window import ViewerTabWindow

SAVE_AS_FORMATS = {
    "PNG": "PNG Files (*.png)",
    "JPG": "JPEG Files (*.jpg *.jpeg)",
    "BMP": "BMP Files (*.bmp)"
}

def _save_as_format(window: 'ViewerTabWindow', target_format: str):
    """
    Save the current image in the specified format.
    
    Parameters:
    - target_format: The format to save the image as.
    """
    viewer = cast('TextureViewer', window.tab_widget.currentWidget())
    if viewer is None:
        QtWidgets.QMessageBox.warning(
            window,
            "No File Opened",
            "Please open an image file before saving."
        )
        return
    image = viewer.processed_texture if viewer.processed_texture else viewer.texture
    if image is None:
        QtWidgets.QMessageBox.warning(
            window,
            "No Image Loaded",
            "Please load an image file before saving."
        )
        return
    file_dialog = QtWidgets.QFileDialog()
    file_path, _ = file_dialog.getSaveFileName(
        None,
        f"Save Image as {target_format}",
        "",
        SAVE_AS_FORMATS[target_format]
    )
    if file_path:
        byte_array = QtCore.QByteArray()
        buffer = QtCore.QBuffer(byte_array)
        buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, cast(bytes, target_format))
        with open(file_path, "wb") as f:
            f.write(byte_array.data())



def setup_texture_viewer_tab_window(tab_window: 'ViewerTabWindow'):
    """Setup the texture viewer tab window."""

    save_as_menu = tab_window.menuBar().addMenu("Save As")

    for name in SAVE_AS_FORMATS:
        action = save_as_menu.addAction(name)
        action.triggered.connect(lambda _, fmt=name: _save_as_format(tab_window, fmt))
