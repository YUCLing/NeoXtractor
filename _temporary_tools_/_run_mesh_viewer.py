import sys
from PySide6 import QtWidgets

import _use_application_modules # pylint: disable=unused-import

from gui.widgets.mesh_viewer.viewer_widget import MeshViewer

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wnd = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout(wnd)

    viewer = MeshViewer()
    viewer.setApi(QtWidgets.QRhiWidget.Api.OpenGL)

    layout.addWidget(viewer)

    wnd.setWindowTitle(f"Mesh Viewer - {viewer.api().name}")
    wnd.resize(800, 600)
    wnd.show()

    print(viewer.api())
    sys.exit(app.exec())
