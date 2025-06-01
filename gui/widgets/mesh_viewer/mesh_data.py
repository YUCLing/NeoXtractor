"""Provides mesh data class for Mesh Viewer."""

from dataclasses import dataclass

import numpy as np

from core.mesh_loader.parsers import MeshData

@dataclass
class ProcessedMeshData:
    """
    Data structure to hold processed mesh data.
    """
    raw_data: MeshData
    position: np.ndarray
    normal: np.ndarray

    vertices: np.ndarray  # Combined position and normals
    indices: np.ndarray

    def __init__(self, raw_data: MeshData):
        self.raw_data = raw_data

        # Process mesh data
        pos = np.array(raw_data.position)
        pos[:, 0] = -pos[:, 0]  # Flip X-axis
        norm = np.array(raw_data.normal)
        norm[:, 0] = -norm[:, 0]  # Flip X-axis for normals as well

        # Combine position and normals into a single array
        self.vertices = np.hstack((pos, norm))

        # Reorder indices
        self.indices = np.array(raw_data.face)[:, [1, 0, 2]]

        # Calculate normal lines
        normal_line_vertices = np.empty((pos.shape[0] * 2, 3), dtype='f4')
        normal_line_vertices[0::2] = pos
        normal_line_vertices[1::2] = pos + norm * 0.008

        self.normal_lines = normal_line_vertices

        # Calculate each bone's position and connections
        bone_positions = []
        bone_lines = []

        for i, parent in enumerate(raw_data.bone_parent):
            # Apply the flip to the bone's matrix
            matrix = raw_data.bone_matrix[i]
            pos = np.asarray(matrix.T)[:3, 3].copy()
            pos[0] = -pos[0]  # Flip X-axis for bone positions
            bone_positions.append(pos)

            # Only create a line if the bone has a parent
            if parent != -1:
                parent_matrix = raw_data.bone_matrix[parent]
                parent_pos = np.asarray(parent_matrix.T)[:3, 3].copy()
                parent_pos[0] = -parent_pos[0]
                bone_lines.extend([pos, parent_pos])

        self.bone_positions = bone_positions
        self.bone_lines = bone_lines
