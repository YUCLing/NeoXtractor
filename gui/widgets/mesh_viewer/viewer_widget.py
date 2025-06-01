from PySide6 import QtWidgets, QtCore

from gui.widgets.mesh_viewer.render_widget import MeshRenderWidget

class MeshViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)

        control_layout = QtWidgets.QHBoxLayout()

        self.wireframe_checkbox = QtWidgets.QCheckBox("Wireframe Mode", self)
        def toggle_wireframe(state):
            self.render_widget.wireframe_mode = state == QtCore.Qt.CheckState.Checked
        self.wireframe_checkbox.checkStateChanged.connect(toggle_wireframe)
        control_layout.addWidget(self.wireframe_checkbox)

        self.bone_checkbox = QtWidgets.QCheckBox("Show Bones", self)
        self.bone_checkbox.setChecked(True)
        def toggle_bones(state):
            self.render_widget.draw_bones = state == QtCore.Qt.CheckState.Checked
        self.bone_checkbox.checkStateChanged.connect(toggle_bones)
        control_layout.addWidget(self.bone_checkbox)

        self.normal_checkbox = QtWidgets.QCheckBox("Show Normals", self)
        def toggle_normals(state):
            self.render_widget.draw_normals = state == QtCore.Qt.CheckState.Checked
        self.normal_checkbox.checkStateChanged.connect(toggle_normals)
        control_layout.addWidget(self.normal_checkbox)

        layout.addLayout(control_layout)

        self.render_widget = MeshRenderWidget(self)
        layout.addWidget(self.render_widget)

        self.load_mesh = self.render_widget.load_mesh
        self.unload_mesh = self.render_widget.unload_mesh
