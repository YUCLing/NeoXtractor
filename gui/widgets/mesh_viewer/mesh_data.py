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
