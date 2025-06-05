"""Code for viewer tab window customization."""

from typing import cast, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from core.mesh_converter import FORMATS, convert_mesh
from gui.widgets.managed_rhi_widget import ManagedRhiWidget
if TYPE_CHECKING:
    from gui.widgets.mesh_viewer.viewer_widget import MeshViewer
    from gui.windows.viewer_tab_window import ViewerTabWindow

def _save_as_format(window: 'ViewerTabWindow', target_format):
    """
    Save the current mesh in the specified format.
    
    Parameters:
    - target_format: The format to save the mesh as.
    """
    viewer = cast('MeshViewer', window.tab_widget.currentWidget())
    if viewer is None:
        QtWidgets.QMessageBox.warning(
            window,
            "No File Opened",
            "Please open a mesh file before saving."
        )
        return
    mesh = viewer.render_widget.mesh_data
    if mesh is None:
        QtWidgets.QMessageBox.warning(
            window,
            "No Mesh Loaded",
            "Please load a mesh file before saving."
        )
        return
    file_dialog = QtWidgets.QFileDialog()
    file_path, _ = file_dialog.getSaveFileName(
        None,
        f"Save Mesh as {target_format.NAME}",
        "",
        f"{target_format.NAME} Files (*{target_format.EXTENSION})"
    )
    if file_path:
        with open(file_path, "wb") as f:
            f.write(convert_mesh(mesh.raw_data, target_format))

class _EventFilter(QtCore.QObject):
    """Event filter for the mesh viewer tab window. Removes the surface type setter after shown."""

    def __init__(self, tab_window: 'ViewerTabWindow', setter: ManagedRhiWidget):
        super().__init__(tab_window)
        self._tab_window = tab_window
        self._setter = setter

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.Show:
            self._tab_window.central_layout.removeWidget(self._setter)
            return True
        return False

def setup_mesh_viewer_tab_window(tab_window: 'ViewerTabWindow'):
    """Setup the mesh viewer tab window."""

    # Forces the tab window to use current graphics backend.
    surface_type_setter = ManagedRhiWidget()
    tab_window.central_layout.addWidget(surface_type_setter)

    event_filter = _EventFilter(tab_window, surface_type_setter)
    tab_window.installEventFilter(event_filter)

    save_as_menu = tab_window.menuBar().addMenu("Save As")

    for fmt in FORMATS:
        action = save_as_menu.addAction(fmt.NAME)
        action.triggered.connect(lambda _, fmt=fmt: _save_as_format(tab_window, fmt))
