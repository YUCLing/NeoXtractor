import sys
from PySide6 import QtWidgets

import _use_application_modules # pylint: disable=unused-import

from gui.widgets.mesh_viewer import MeshViewer

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

    msaa_combobox = QtWidgets.QComboBox()
    layout.addWidget(msaa_combobox)

    viewer = MeshViewer()
    viewer.render_widget.setApi(QtWidgets.QRhiWidget.Api.OpenGL)

    layout.addWidget(viewer)

    wnd.setWindowTitle(f"Mesh Viewer - {viewer.render_widget.api().name}")
    wnd.resize(800, 600)
    wnd.show()

    for sample_count in viewer.render_widget.rhi().supportedSampleCounts():
        if sample_count == 1:
            msaa_combobox.addItem("No MSAA", 1)
        else:
            msaa_combobox.addItem(f"{sample_count}x MSAA", sample_count)
    msaa_combobox.setCurrentIndex(0)
    def set_msaa(value):
        viewer.render_widget.setSampleCount(value)
    msaa_combobox.currentIndexChanged.connect(lambda idx: set_msaa(msaa_combobox.itemData(idx)))

    print(viewer.render_widget.api())
    sys.exit(app.exec())
