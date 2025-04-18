from enum import Enum
from typing import Dict
from tensor import Tensor
from vector import Vector

class FIELD_TYPE(Enum):
    Radial = 0
    Grid = 1

class BasisField:
    folder_name_index = 0

    def __init__(self, centre: Vector, size: float, decay: float):
        self._centre = centre.clone()
        self._size = size
        self._decay = decay
        self.params: Dict[str, float] = {
            "x": self._centre.x,
            "y": self._centre.y,
            "size": self._size,
            "decay": self._decay
        }

    @property
    def centre(self) -> Vector:
        return self._centre.clone()

    @centre.setter
    def centre(self, centre: Vector) -> None:
        self._centre.copy(centre)
        self.params["x"] = self._centre.x
        self.params["y"] = self._centre.y

    @property
    def decay(self) -> float:
        return self._decay

    @decay.setter
    def decay(self, decay: float) -> None:
        self._decay = decay
        self.params["decay"] = decay

    @property
    def size(self) -> float:
        return self._size

    @size.setter
    def size(self, size: float) -> None:
        self._size = size
        self.params["size"] = size

    def drag_start_listener(self) -> None:
        self.set_folder()

    def drag_move_listener(self, delta: Vector) -> None:
        # Delta assumed to be in world space (only relevant when zoomed)
        self._centre.add(delta)
        self.params["x"] = self._centre.x
        self.params["y"] = self._centre.y

    def get_weighted_tensor(self, point: Vector, smooth: bool) -> Tensor:
        return self.get_tensor(point).scale(self.get_tensor_weight(point, smooth))

    def set_folder(self) -> None:
        # Placeholder for GUI folder logic
        pass

    def remove_folder_from_parent(self) -> None:
        # Placeholder for GUI folder removal logic
        pass

    def set_gui(self, params: Dict[str, float]) -> None:
        """
        Sets the parameters for the field.
        """
        self.params.update(params)

    def get_tensor_weight(self, point: Vector, smooth: bool) -> float:
        norm_distance_to_centre = point.clone().sub(self._centre).length() / self._size
        if smooth:
            return norm_distance_to_centre ** -self._decay
        if self._decay == 0 and norm_distance_to_centre >= 1:
            return 0
        return max(0, (1 - norm_distance_to_centre)) ** self._decay

    def get_tensor(self, point: Vector) -> Tensor:
        raise NotImplementedError("Subclasses must implement get_tensor.")

class Grid(BasisField):
    def __init__(self, centre: Vector, size: float, decay: float, theta: float):
        super().__init__(centre, size, decay)
        self._theta = theta
        self.params["theta"] = self._theta

    @property
    def theta(self) -> float:
        return self._theta

    @theta.setter
    def theta(self, theta: float) -> None:
        self._theta = theta
        self.params["theta"] = theta

    def set_gui(self, params: Dict[str, float]) -> None:
        super().set_gui(params)
        if "theta" in params:
            self._theta = params["theta"]

    def get_tensor(self, point: Vector) -> Tensor:
        cos = math.cos(2 * self._theta)
        sin = math.sin(2 * self._theta)
        return Tensor(1, [cos, sin])

class Radial(BasisField):
    def __init__(self, centre: Vector, size: float, decay: float):
        super().__init__(centre, size, decay)

    def get_tensor(self, point: Vector) -> Tensor:
        t = point.clone().sub(self._centre)
        t1 = t.y**2 - t.x**2
        t2 = -2 * t.x * t.y
        return Tensor(1, [t1, t2])
