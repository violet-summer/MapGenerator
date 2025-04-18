# basis_field.py
from tensor import Tensor
from vector import Vector
import math

class BasisField:
    def __init__(self, centre: Vector, size: float, decay: float):
        self._centre = centre.clone()
        self._size = size
        self._decay = decay

    @property
    def centre(self):
        return self._centre.clone()

    @centre.setter
    def centre(self, value):
        self._centre = value.clone()

    @property
    def decay(self):
        return self._decay

    @decay.setter
    def decay(self, value):
        self._decay = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def get_weighted_tensor(self, point: Vector, smooth: bool):
        return self.get_tensor(point).scale(self.get_tensor_weight(point, smooth))

    def get_tensor_weight(self, point: Vector, smooth: bool):
        norm_distance = point.clone().sub(self._centre).length() / self._size
        if smooth:
            return norm_distance ** -self._decay
        if self._decay == 0 and norm_distance >= 1:
            return 0
        return max(0, (1 - norm_distance)) ** self._decay

    def get_tensor(self, point: Vector):
        raise NotImplementedError()

class Grid(BasisField):
    def __init__(self, centre: Vector, size: float, decay: float, theta: float):
        super().__init__(centre, size, decay)
        self._theta = theta

    @property
    def theta(self):
        return self._theta

    @theta.setter
    def theta(self, value):
        self._theta = value

    def get_tensor(self, point: Vector):
        cos = math.cos(2 * self._theta)
        sin = math.sin(2 * self._theta)
        return Tensor(1, [cos, sin])

class Radial(BasisField):
    def __init__(self, centre: Vector, size: float, decay: float):
        super().__init__(centre, size, decay)

    def get_tensor(self, point: Vector):
        t = point.clone().sub(self._centre)
        t1 = t.y ** 2 - t.x ** 2
        t2 = -2 * t.x * t.y
        return Tensor(1, [t1, t2])
