import sys
from PySide6 import QtWidgets

import _use_application_modules # pylint: disable=unused-import

from gui.widgets.mesh_viewer.viewer_widget import MeshViewer

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wnd = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout(wnd)

    open_button = QtWidgets.QPushButton("Open Mesh File")
    layout.addWidget(open_button)

    def open_mesh_file():
        file_dialog = QtWidgets.QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            wnd, 
            "Open Mesh File", 
            "", 
            "Mesh Files (*.mesh)"
        )
        if file_path:
            with open(file_path, "rb") as f:
                viewer.load_mesh(f.read())

    open_button.clicked.connect(open_mesh_file)

    viewer = MeshViewer()
    viewer.setApi(QtWidgets.QRhiWidget.Api.Vulkan)
    viewer.draw_normals = True

    layout.addWidget(viewer)

    wnd.setWindowTitle(f"Mesh Viewer - {viewer.api().name}")
    wnd.resize(800, 600)
    wnd.show()

    print(viewer.api())
    sys.exit(app.exec())
