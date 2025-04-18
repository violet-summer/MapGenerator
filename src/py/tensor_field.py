import math
from typing import List, Dict
from simplex_noise import SimplexNoise
from tensor import Tensor
from vector import Vector
from basis_field import Grid, Radial, BasisField
from polygon_util import PolygonUtil

class TensorField:
    def __init__(self, noise_params: Dict[str, float]):
        self.basis_fields: List[BasisField] = []
        self.noise = SimplexNoise()

        self.parks: List[List[Vector]] = []
        self.sea: List[Vector] = []
        self.river: List[Vector] = []
        self.ignore_river = False

        self.smooth = False
        self.noise_params = noise_params

    def enable_global_noise(self, angle: float, size: float) -> None:
        self.noise_params["globalNoise"] = True
        self.noise_params["noiseAngleGlobal"] = angle
        self.noise_params["noiseSizeGlobal"] = size

    def disable_global_noise(self) -> None:
        self.noise_params["globalNoise"] = False

    def add_grid(self, centre: Vector, size: float, decay: float, theta: float) -> None:
        grid = Grid(centre, size, decay, theta)
        self.add_field(grid)

    def add_radial(self, centre: Vector, size: float, decay: float) -> None:
        radial = Radial(centre, size, decay)
        self.add_field(radial)

    def add_field(self, field: BasisField) -> None:
        self.basis_fields.append(field)

    def remove_field(self, field: BasisField) -> None:
        if field in self.basis_fields:
            self.basis_fields.remove(field)

    def reset(self) -> None:
        self.basis_fields = []
        self.parks = []
        self.sea = []
        self.river = []

    def get_centre_points(self) -> List[Vector]:
        return [field.centre for field in self.basis_fields]

    def get_basis_fields(self) -> List[BasisField]:
        return self.basis_fields

    def sample_point(self, point: Vector) -> Tensor:
        if not self.on_land(point):
            # Degenerate point
            return Tensor.zero()

        # Default field is a grid
        if not self.basis_fields:
            return Tensor(1, [0, 0])

        tensor_acc = Tensor.zero()
        for field in self.basis_fields:
            tensor_acc.add(field.get_weighted_tensor(point, self.smooth), self.smooth)

        # Add rotational noise for parks - range -pi/2 to pi/2
        if any(PolygonUtil.inside_polygon(point, p) for p in self.parks):
            tensor_acc.rotate(self.get_rotational_noise(point, self.noise_params["noiseSizePark"], self.noise_params["noiseAnglePark"]))

        if self.noise_params.get("globalNoise", False):
            tensor_acc.rotate(self.get_rotational_noise(point, self.noise_params["noiseSizeGlobal"], self.noise_params["noiseAngleGlobal"]))

        return tensor_acc

    def get_rotational_noise(self, point: Vector, noise_size: float, noise_angle: float) -> float:
        return self.noise.noise2d(point.x / noise_size, point.y / noise_size) * noise_angle * math.pi / 180

    def on_land(self, point: Vector) -> bool:
        in_sea = PolygonUtil.inside_polygon(point, self.sea)
        if self.ignore_river:
            return not in_sea

        return not in_sea and not PolygonUtil.inside_polygon(point, self.river)

    def in_parks(self, point: Vector) -> bool:
        return any(PolygonUtil.inside_polygon(point, p) for p in self.parks)
