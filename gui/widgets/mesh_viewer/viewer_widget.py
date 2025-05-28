"""Mesh Viewer Widget"""

import ctypes
import os
from typing import cast

from PySide6 import QtCore, QtGui, QtWidgets

from core.utils import get_application_path
from gui.renderers.text_renderer import TextRenderer
from gui.utils.rendering import grid

from .camera_controller import CameraController

INSTRUCTIONS = [
    ("Key F", "Focus Object"),
    ("M-Right", "Orbit"),
    ("M-Left", "Pan"),
    ("M-Middle", "Dolly"),
    ("W, A, S, D", "Move Camera"),
    ("Shift", "Sprint"),
    ("Key 1", ("Front View", "Back View")),
    ("Key 3", ("Right View", "Left View")),
    ("Key 7", ("Top View", "Bottom View")),
    ("Ctrl", "Alternative Actions")
]

GRID_COLOR = [0.3, 0.3, 0.3]
GRID_VERTEX_DATA = [
    float(coord)
    for grid_line in grid(5, 10)
    for grid_vertex in grid_line
    for coord in [*grid_vertex, *GRID_COLOR]
]

class MeshViewer(QtWidgets.QRhiWidget, CameraController):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self._rhi: QtGui.QRhi | None = None
        self._colored_line_vertices_pipeline: QtGui.QRhiGraphicsPipeline | None = None

        self._grid_vbuf: QtGui.QRhiBuffer | None = None
        self._ubuf: QtGui.QRhiBuffer | None = None
        self._srb: QtGui.QRhiShaderResourceBindings | None = None
        self._view_proj: QtGui.QMatrix4x4 | None = None

        self._text_renderer = TextRenderer(self, 14)

        self._alternative_actions = False

    def initialize(self, cb: QtGui.QRhiCommandBuffer):
        if self._rhi != self.rhi() or self._rhi is None: # type hint
            self._colored_line_vertices_pipeline = None
            self._text_renderer.releaseResources()
            self._rhi = self.rhi()

        if self._colored_line_vertices_pipeline is None:
            self._grid_vbuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Immutable,
                                             QtGui.QRhiBuffer.UsageFlag.VertexBuffer,
                                             ctypes.sizeof(ctypes.c_float) * len(GRID_VERTEX_DATA)
                                             )
            self._grid_vbuf.create()

            self._ubuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Dynamic,
                                             QtGui.QRhiBuffer.UsageFlag.UniformBuffer,
                                             64
                                             )
            self._ubuf.create()

            self._srb = self._rhi.newShaderResourceBindings()
            self._srb.setBindings([
                QtGui.QRhiShaderResourceBinding.uniformBuffer(0,
                                                              QtGui.QRhiShaderResourceBinding.StageFlag.VertexStage,
                                                              self._ubuf),
            ])
            self._srb.create()

            self._colored_line_vertices_pipeline = self._rhi.newGraphicsPipeline()
            app_path = get_application_path()
            with open(os.path.join(app_path, "data", "shaders", "colored_vertices.vert.qsb"), "rb") as f:
                vsrc = f.read()
                vsrc = QtGui.QShader.fromSerialized(vsrc)
                with open(os.path.join(app_path, "data", "shaders", "colored_vertices.frag.qsb"), "rb") as f:
                    fsrc = f.read()
                    fsrc = QtGui.QShader.fromSerialized(fsrc)

                    self._colored_line_vertices_pipeline.setShaderStages([
                        QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Vertex, vsrc),
                        QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Fragment, fsrc)
                    ])
            input_layout = QtGui.QRhiVertexInputLayout()
            input_layout.setBindings([
                QtGui.QRhiVertexInputBinding(6 * ctypes.sizeof(ctypes.c_float)),
            ])
            input_layout.setAttributes([
                QtGui.QRhiVertexInputAttribute(0, 0, QtGui.QRhiVertexInputAttribute.Format.Float3, 0),
                QtGui.QRhiVertexInputAttribute(0, 1, QtGui.QRhiVertexInputAttribute.Format.Float3,
                                               3 * ctypes.sizeof(ctypes.c_float)
                                               ),
            ])
            self._colored_line_vertices_pipeline.setDepthTest(True)
            self._colored_line_vertices_pipeline.setDepthWrite(True)
            self._colored_line_vertices_pipeline.setVertexInputLayout(input_layout)
            self._colored_line_vertices_pipeline.setShaderResourceBindings(self._srb)
            self._colored_line_vertices_pipeline.setTopology(QtGui.QRhiGraphicsPipeline.Topology.Lines)
            self._colored_line_vertices_pipeline.setRenderPassDescriptor(self.renderTarget().renderPassDescriptor())
            self._colored_line_vertices_pipeline.create()

            resource_updates = self._rhi.nextResourceUpdateBatch()
            arr = (ctypes.c_float * len(GRID_VERTEX_DATA))(*GRID_VERTEX_DATA)
            resource_updates.uploadStaticBuffer(self._grid_vbuf, cast(int, arr))
            cb.resourceUpdate(resource_updates)

        self._text_renderer.initialize(cb)

        output_size = self.renderTarget().pixelSize()
        self.camera.set_aspect_ratio(output_size.width(), output_size.height())
        self._view_proj = self._rhi.clipSpaceCorrMatrix()
        self._view_proj = self._view_proj * self.camera.view_proj()

    def render(self, cb: QtGui.QRhiCommandBuffer):
        self._camera_update()

        if self._rhi is None or \
            self._view_proj is None or \
            self._ubuf is None or \
            self._colored_line_vertices_pipeline is None:
            return

        viewport_height = self.renderTarget().pixelSize().height()

        # Calculate starting Y position from bottom
        start_y = viewport_height - (len(INSTRUCTIONS) * self._text_renderer.font_height) - 20

        for i, (key, action) in enumerate(INSTRUCTIONS):
            if isinstance(action, tuple):
                if self._alternative_actions:
                    action = action[1]
                else:
                    action = action[0]
            y_pos = start_y + i * self._text_renderer.font_height
            self._text_renderer.render_text(f"{key}:", (20, y_pos), (0.5, 1.0, 1.0, 1.0))
            self._text_renderer.render_text(action, (90, y_pos), (1.0, 1.0, 1.0, 1.0))

        self._text_renderer.update_resources(cb)

        resource_updates = self._rhi.nextResourceUpdateBatch()

        # Update view-projection matrix from camera
        output_size = self.renderTarget().pixelSize()
        self.camera.set_aspect_ratio(output_size.width(), output_size.height())
        view_proj = self._rhi.clipSpaceCorrMatrix()
        view_proj = view_proj * self.camera.view_proj()

        vp_data = view_proj.data()
        ubuf_data = list(vp_data) # MVP data
        arr = (ctypes.c_float * len(ubuf_data))(*ubuf_data)
        resource_updates.updateDynamicBuffer(self._ubuf, 0, ctypes.sizeof(arr), cast(int, arr))

        clr = QtGui.QColor.fromRgbF(0.23, 0.23, 0.23)
        cb.beginPass(self.renderTarget(), clr, QtGui.QRhiDepthStencilClearValue(0.999, 0), resource_updates)

        cb.setGraphicsPipeline(self._colored_line_vertices_pipeline)
        cb.setViewport(QtGui.QRhiViewport(0, 0, self.renderTarget().pixelSize().width(),
                                          self.renderTarget().pixelSize().height()))
        cb.setShaderResources()
        cb.setVertexInput(0, [(self._grid_vbuf, 0)])
        cb.draw(len(GRID_VERTEX_DATA) // 6)  # 6 floats per vertex (3 for position, 3 for color)

        self._text_renderer.render(cb)

        cb.endPass()

        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super()._camera_mouse_pressed_event(event)
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super()._camera_mouse_released_event(event)
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super()._camera_mouse_moved_event(event)
    def wheelEvent(self, event: QtGui.QWheelEvent):
        super()._camera_wheel_event(event)
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Control:
            self._alternative_actions = True
        super()._camera_key_pressed_event(event)
    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Control:
            self._alternative_actions = False
        super()._camera_key_released_event(event)
