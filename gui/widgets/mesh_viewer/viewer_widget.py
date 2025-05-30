"""Mesh Viewer Widget"""

import ctypes
import os
from typing import cast, overload

from PySide6 import QtCore, QtGui, QtWidgets

from core.mesh_loader.loader import MeshLoader
from core.mesh_loader.parsers import MeshData
from core.utils import get_application_path
from gui.renderers.text_renderer import TextRenderer
from gui.utils.rendering import grid
from gui.widgets.mesh_viewer.mesh_data import ProcessedMeshData

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

MESH_COLOR = [0.8, 0.8, 0.8]

class MeshViewer(QtWidgets.QRhiWidget, CameraController):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self._rhi: QtGui.QRhi | None = None

        self._colored_vertices_shaders: tuple[QtGui.QShader, QtGui.QShader] | None = None
        self._mesh_shaders: tuple[QtGui.QShader, QtGui.QShader] | None = None

        self._colored_line_vertices_pipeline: QtGui.QRhiGraphicsPipeline | None = None
        self._mesh_pipeline: QtGui.QRhiGraphicsPipeline | None = None

        self._grid_vbuf: QtGui.QRhiBuffer | None = None
        self._grid_ubuf: QtGui.QRhiBuffer | None = None
        self._grid_srb: QtGui.QRhiShaderResourceBindings | None = None

        self._mesh_data: ProcessedMeshData | None = None
        self._mesh_vbuf: QtGui.QRhiBuffer | None = None
        self._mesh_ibuf: QtGui.QRhiBuffer | None = None
        self._mesh_vert_ubuf: QtGui.QRhiBuffer | None = None
        self._mesh_frag_ubuf: QtGui.QRhiBuffer | None = None
        self._mesh_srb: QtGui.QRhiShaderResourceBindings | None = None

        self._text_renderer = TextRenderer(self, 14)

        self._alternative_actions = False

    def initialize(self, cb: QtGui.QRhiCommandBuffer):
        if self._rhi != self.rhi() or self._rhi is None: # type hint
            self._colored_line_vertices_pipeline = None
            self._mesh_pipeline = None
            self._text_renderer.releaseResources()
            self._rhi = self.rhi()

        app_path = get_application_path()
        if self._colored_vertices_shaders is None:
            with open(os.path.join(app_path, "data", "shaders", "colored_vertices.vert.qsb"), "rb") as f:
                vsrc = f.read()
                vsrc = QtGui.QShader.fromSerialized(vsrc)
                with open(os.path.join(app_path, "data", "shaders", "colored_vertices.frag.qsb"), "rb") as f:
                    fsrc = f.read()
                    fsrc = QtGui.QShader.fromSerialized(fsrc)

                    self._colored_vertices_shaders = (vsrc, fsrc)

        if self._mesh_shaders is None:
            with open(os.path.join(app_path, "data", "shaders", "mesh.vert.qsb"), "rb") as f:
                vsrc = f.read()
                vsrc = QtGui.QShader.fromSerialized(vsrc)
                with open(os.path.join(app_path, "data", "shaders", "mesh.frag.qsb"), "rb") as f:
                    fsrc = f.read()
                    fsrc = QtGui.QShader.fromSerialized(fsrc)

                    self._mesh_shaders = (vsrc, fsrc)

        if self._colored_line_vertices_pipeline is None:
            self._grid_vbuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Immutable,
                                             QtGui.QRhiBuffer.UsageFlag.VertexBuffer,
                                             ctypes.sizeof(ctypes.c_float) * len(GRID_VERTEX_DATA)
                                             )
            self._grid_vbuf.create()

            self._grid_ubuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Dynamic,
                                            QtGui.QRhiBuffer.UsageFlag.UniformBuffer,
                                            16 * ctypes.sizeof(ctypes.c_float)
                                            )
            self._grid_ubuf.create()

            self._grid_srb = self._rhi.newShaderResourceBindings()
            self._grid_srb.setBindings([
                QtGui.QRhiShaderResourceBinding.uniformBuffer(0,
                                                            QtGui.QRhiShaderResourceBinding.StageFlag.VertexStage,
                                                            self._grid_ubuf),
            ])
            self._grid_srb.create()

            self._colored_line_vertices_pipeline = self._rhi.newGraphicsPipeline()
            self._colored_line_vertices_pipeline.setShaderStages([
                QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Vertex, self._colored_vertices_shaders[0]),
                QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Fragment, self._colored_vertices_shaders[1])
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
            self._colored_line_vertices_pipeline.setShaderResourceBindings(self._grid_srb)
            self._colored_line_vertices_pipeline.setTopology(QtGui.QRhiGraphicsPipeline.Topology.Lines)
            self._colored_line_vertices_pipeline.setRenderPassDescriptor(self.renderTarget().renderPassDescriptor())
            self._colored_line_vertices_pipeline.create()

            resource_updates = self._rhi.nextResourceUpdateBatch()
            arr = (ctypes.c_float * len(GRID_VERTEX_DATA))(*GRID_VERTEX_DATA)
            resource_updates.uploadStaticBuffer(self._grid_vbuf, cast(int, arr))
            cb.resourceUpdate(resource_updates)

        if self._mesh_pipeline is None:
            self._mesh_vert_ubuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Dynamic,
                                            QtGui.QRhiBuffer.UsageFlag.UniformBuffer,
                                            2 * 16 * ctypes.sizeof(ctypes.c_float)
                                            )
            self._mesh_vert_ubuf.create()

            self._mesh_frag_ubuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Immutable,
                                            QtGui.QRhiBuffer.UsageFlag.UniformBuffer,
                                            3 * ctypes.sizeof(ctypes.c_float)
                                            )
            self._mesh_frag_ubuf.create()

            self._mesh_srb = self._rhi.newShaderResourceBindings()
            self._mesh_srb.setBindings([
                QtGui.QRhiShaderResourceBinding.uniformBuffer(0,
                                                            QtGui.QRhiShaderResourceBinding.StageFlag.VertexStage,
                                                            self._mesh_vert_ubuf),
                QtGui.QRhiShaderResourceBinding.uniformBuffer(1,
                                                            QtGui.QRhiShaderResourceBinding.StageFlag.FragmentStage,
                                                            self._mesh_frag_ubuf),
            ])
            self._mesh_srb.create()

            self._mesh_pipeline = self._rhi.newGraphicsPipeline()
            self._mesh_pipeline.setShaderStages([
                QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Vertex, self._mesh_shaders[0]),
                QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Fragment, self._mesh_shaders[1])
            ])
            input_layout = QtGui.QRhiVertexInputLayout()
            input_layout.setBindings([
                QtGui.QRhiVertexInputBinding(6 * ctypes.sizeof(ctypes.c_float)),
            ])
            input_layout.setAttributes([
                QtGui.QRhiVertexInputAttribute(0, 0, QtGui.QRhiVertexInputAttribute.Format.Float3, 0),
                QtGui.QRhiVertexInputAttribute(0, 1, QtGui.QRhiVertexInputAttribute.Format.Float3,
                                               3 * ctypes.sizeof(ctypes.c_float)
                                               )
            ])
            self._mesh_pipeline.setDepthTest(True)
            self._mesh_pipeline.setDepthWrite(True)
            self._mesh_pipeline.setVertexInputLayout(input_layout)
            self._mesh_pipeline.setShaderResourceBindings(self._mesh_srb)
            self._mesh_pipeline.setRenderPassDescriptor(self.renderTarget().renderPassDescriptor())
            self._mesh_pipeline.create()

            resource_updates = self._rhi.nextResourceUpdateBatch()
            arr = (ctypes.c_float * len(MESH_COLOR))(*MESH_COLOR)
            resource_updates.uploadStaticBuffer(self._mesh_frag_ubuf, cast(int, arr))
            cb.resourceUpdate(resource_updates)

        self._text_renderer.initialize(cb)

        output_size = self.renderTarget().pixelSize()
        self.camera.set_aspect_ratio(output_size.width(), output_size.height())

    def render(self, cb: QtGui.QRhiCommandBuffer):
        self._camera_update()

        if self._rhi is None or \
            self._grid_ubuf is None or \
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
        view_proj = self._rhi.clipSpaceCorrMatrix()
        view_proj = view_proj * self.camera.view_proj()

        vp_data = view_proj.data()
        ubuf_data = list(vp_data) # MVP data
        arr = (ctypes.c_float * len(ubuf_data))(*ubuf_data)
        resource_updates.updateDynamicBuffer(self._grid_ubuf, 0, ctypes.sizeof(arr), cast(int, arr))

        if self._mesh_data is not None and self._mesh_vert_ubuf is not None:
            mv = self.camera.view() * QtGui.QMatrix4x4()
            mvp = self._rhi.clipSpaceCorrMatrix() * self.camera.proj() * mv

            ubuf_data = mv.data() + mvp.data()
            ubuf_arr = (ctypes.c_float * len(ubuf_data))(*ubuf_data)
            resource_updates.updateDynamicBuffer(self._mesh_vert_ubuf, 0, 2 * 16 * ctypes.sizeof(ctypes.c_float),
                                                 cast(int, ubuf_arr))

            if self._mesh_vbuf is None or self._mesh_ibuf is None:
                vbuf_data = self._mesh_data.vertices.flatten().astype("f4").tolist()
                ibuf_data = self._mesh_data.indices.flatten().astype("uint32").tolist()

                # Create vertex and index buffers for the mesh
                self._mesh_vbuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Immutable,
                                                    QtGui.QRhiBuffer.UsageFlag.VertexBuffer,
                                                    ctypes.sizeof(ctypes.c_float) * len(vbuf_data)
                                                    )
                self._mesh_vbuf.create()

                self._mesh_ibuf = self._rhi.newBuffer(QtGui.QRhiBuffer.Type.Immutable,
                                                    QtGui.QRhiBuffer.UsageFlag.IndexBuffer,
                                                    ctypes.sizeof(ctypes.c_uint) * len(ibuf_data)
                                                    )
                self._mesh_ibuf.create()

                vbuf_arr = (ctypes.c_float * len(vbuf_data))(*vbuf_data)
                ibuf_arr = (ctypes.c_uint * len(ibuf_data))(*ibuf_data)
                resource_updates.uploadStaticBuffer(self._mesh_vbuf, cast(int, vbuf_arr))
                resource_updates.uploadStaticBuffer(self._mesh_ibuf, cast(int, ibuf_arr))

        clr = QtGui.QColor.fromRgbF(0.23, 0.23, 0.23)
        cb.beginPass(self.renderTarget(), clr, QtGui.QRhiDepthStencilClearValue(0.999, 0), resource_updates)

        cb.setGraphicsPipeline(self._colored_line_vertices_pipeline)
        cb.setViewport(QtGui.QRhiViewport(0, 0, self.renderTarget().pixelSize().width(),
                                          self.renderTarget().pixelSize().height()))
        cb.setShaderResources()
        cb.setVertexInput(0, [(self._grid_vbuf, 0)])
        cb.draw(len(GRID_VERTEX_DATA) // 6)  # 6 floats per vertex (3 for position, 3 for color)

        if self._mesh_data is not None and self._mesh_pipeline is not None:
            cb.setGraphicsPipeline(self._mesh_pipeline)
            cb.setViewport(QtGui.QRhiViewport(0, 0, self.renderTarget().pixelSize().width(),
                                              self.renderTarget().pixelSize().height()))
            cb.setShaderResources()
            cb.setVertexInput(0, [(self._mesh_vbuf, 0)], self._mesh_ibuf, 0,
                              QtGui.QRhiCommandBuffer.IndexFormat.IndexUInt32)
            cb.drawIndexed(self._mesh_data.indices.size)

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

    def unload_mesh(self):
        """
        Unloads the currently loaded mesh by destroying GPU buffers and clearing mesh data.
        This method safely cleans up mesh resources by:
        - Destroying the index buffer if it exists
        - Destroying the vertex buffer if it exists  
        - Clearing the mesh data reference
        If no mesh is currently loaded, this method returns early without performing any operations.
        """

        if not self._mesh_data:
            return

        if self._mesh_ibuf:
            self._mesh_ibuf.destroy()
            self._mesh_ibuf = None
        if self._mesh_vbuf:
            self._mesh_vbuf.destroy()
            self._mesh_vbuf = None
        self._mesh_data = None

    @overload
    def load_mesh(self, data: MeshData) -> None:
        ...

    @overload
    def load_mesh(self, data: bytes) -> None:
        ...

    def load_mesh(self, data: MeshData | bytes) -> None:
        """Load mesh data into the viewer widget.
        Args:
            data: Either a MeshData object or raw bytes containing mesh data.
                  If bytes are provided, they will be loaded using MeshLoader.
        Raises:
            ValueError: If the provided bytes cannot be loaded as valid mesh data.
        Note:
            The loaded mesh data is stored internally as ProcessedMeshData for
            rendering purposes.
        """

        self.unload_mesh()

        if isinstance(data, MeshData):
            self._mesh_data = ProcessedMeshData(data)
        else:
            loader = MeshLoader()
            dat = loader.load_from_bytes(data)
            if dat is None:
                raise ValueError("Failed to load mesh data from bytes")
            self._mesh_data = ProcessedMeshData(dat)
