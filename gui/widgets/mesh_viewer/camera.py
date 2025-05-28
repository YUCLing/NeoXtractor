from enum import IntEnum
import math
from PySide6.QtGui import QVector3D, QVector4D, QMatrix4x4

class OrthogonalDirection(IntEnum):
    FRONT = 1
    RIGHT = 3
    TOP = 7

class Camera:
    def __init__(self):
        self._pos = QVector4D(0, 1, 4, 1)
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        self.dist = 5
        self.fov_y = 45
        self.aspect_ratio = 1
        self.perspective = True
        self.min_dist = 5
        self.max_dist = 1500

    def move(self, velocity: QVector4D):
        """Update camera position based on velocity."""
        vec = self.rot().inverted()[0].map(velocity)
        self._pos += vec

    def pos(self):
        """Return camera position."""
        return self._pos

    def euler(self):
        """Return euler angles in radians as QVector3D"""
        roll = math.radians(self.roll)
        pitch = math.radians(self.pitch)
        yaw = math.radians(self.yaw)
        return QVector3D(pitch, yaw, roll)

    def rot(self):
        """Return rotation matrix"""
        matrix = QMatrix4x4()
        euler = self.euler()
        matrix.rotate(math.degrees(euler.x()), QVector3D(1, 0, 0))  # pitch
        matrix.rotate(math.degrees(euler.y()), QVector3D(0, 1, 0))  # yaw
        matrix.rotate(math.degrees(euler.z()), QVector3D(0, 0, 1))  # roll
        return matrix

    def view(self):
        """Return view matrix"""
        view = QMatrix4x4()
        view.translate(-self._pos.toVector3D())
        view = self.rot() * view

        # Apply distance translation by multiplying from the left
        dist_matrix = QMatrix4x4()
        dist_matrix.translate(QVector3D(0.0, 0.0, -self.dist))
        view = dist_matrix * view

        return view

    def proj(self):
        """Return projection matrix"""
        proj = QMatrix4x4()
        if self.perspective:
            proj.perspective(self.fov_y, self.aspect_ratio, 0.1, 1000.0)
        else:
            length = math.tan(math.radians(self.fov_y / 2)) * abs(self.dist)
            if self.aspect_ratio >= 1:
                proj.ortho(-length * self.aspect_ratio, length * self.aspect_ratio,
                          -length, length, 0.1, 1000.0)
            else:
                proj.ortho(-length, length,
                          -length / self.aspect_ratio, length / self.aspect_ratio,
                          0.1, 1000.0)
        return proj

    def view_proj(self):
        """Return combined view-projection matrix"""
        return self.proj() * self.view()

    def dolly(self, amount):
        """Zoom in/out by adjusting distance"""
        self.dist += amount
        self.dist = max(self.min_dist, min(self.dist, self.max_dist))

    def orbit(self, dx, dy):
        """Orbit camera around target"""
        self.perspective = True
        self.yaw -= dx * 0.5
        self.pitch = max(-89.0, min(89.0, self.pitch - dy * 0.5))

    def pan(self, dx, dy):
        """Pan camera in screen space"""
        pan_speed = 0.01 * self.dist  # Scale pan speed by distance
        dv = QVector4D(dx * -pan_speed, dy * pan_speed, 0.0, 0.0)

        # Transform by inverse rotation
        rot_inv = self.rot().inverted()[0]
        transformed = rot_inv.map(dv)

        self._pos = QVector4D(
            self._pos.x() + transformed.x(),
            self._pos.y() + transformed.y(),
            self._pos.z() + transformed.z(),
            1.0
        )

    def orthogonal(self, direct: OrthogonalDirection, opposite = False):
        """Set camera to orthogonal view"""
        self.perspective = False
        self.yaw, self.pitch, self.roll = 0.0, 0.0, 0.0
        if direct == OrthogonalDirection.FRONT:
            self.yaw = 0.0 if not opposite else 180.0
        elif direct == OrthogonalDirection.RIGHT:
            self.yaw = 90.0 if not opposite else -90.0
        elif direct == OrthogonalDirection.TOP:
            self.pitch = -90.0 if not opposite else 90.0

    def focus(self, point):
        """Focus camera on a specific point"""
        if isinstance(point, (list, tuple)) and len(point) >= 3:
            focus_point = QVector4D(point[0], point[1], point[2], 1.0)
        else:
            # TODO: Confirm this behavior
            focus_point = QVector4D(0.0, 0.0, 0.0, 1.0)

        self._pos = focus_point
        self.dist = math.sqrt((self._pos.x() - focus_point.x())**2 +
                            (self._pos.y() - focus_point.y())**2 +
                            (self._pos.z() - focus_point.z())**2)

    def set_aspect_ratio(self, width, height):
        """Set camera aspect ratio"""
        self.aspect_ratio = width / height if height != 0 else 1.0
