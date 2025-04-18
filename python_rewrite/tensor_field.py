import math
import random
from typing import Tuple

from basis_field import Grid, Radial
from polygon_util import PolygonUtil
from tensor import Tensor
from vector import Vector


class NoiseParams:
    def __init__(self, global_noise=False, noise_size_park=0, noise_angle_park=0, noise_size_global=0, noise_angle_global=0):
        self.global_noise = global_noise
        self.noise_size_park = noise_size_park
        self.noise_angle_park = noise_angle_park
        self.noise_size_global = noise_size_global
        self.noise_angle_global = noise_angle_global

class TensorField:
    """
    张量场实现，用于生成道路网络的基础。
    """

    def __init__(self, noise_params: NoiseParams):
        """
        初始化张量场

        Args:
            noise_params: 噪声参数
        """
        self.basis_fields = []
        self.noise_params = noise_params
        self.parks = []
        self.sea = []
        self.river = []
        self.ignore_river = False
        self.smooth = False

    def enable_global_noise(self, angle, size):
        self.noise_params.global_noise = True
        self.noise_params.noise_angle_global = angle
        self.noise_params.noise_size_global = size

    def disable_global_noise(self):
        self.noise_params.global_noise = False

    def add_grid(self, centre, size, decay, theta):
        grid = Grid(centre, size, decay, theta)
        self.add_field(grid)

    def add_radial(self, centre, size, decay):
        radial = Radial(centre, size, decay)
        self.add_field(radial)

    def add_field(self, field):
        self.basis_fields.append(field)

    def remove_field(self, field):
        if field in self.basis_fields:
            self.basis_fields.remove(field)

    def reset(self):
        self.basis_fields = []
        self.parks = []
        self.sea = []
        self.river = []

    def get_centre_points(self):
        return [field.centre for field in self.basis_fields]

    def get_basis_fields(self):
        return self.basis_fields

    def sample_point(self, point: Vector):
        if not self.on_land(point):
            return Tensor.zero()
        if len(self.basis_fields) == 0:
            return Tensor(1, [0, 0])
        tensor_acc = Tensor.zero()
        for field in self.basis_fields:
            tensor_acc.add(field.get_weighted_tensor(point, self.smooth), self.smooth)
        if any(PolygonUtil.inside_polygon(point, p) for p in self.parks):
            tensor_acc.rotate(self.get_rotational_noise(point, self.noise_params.noise_size_park, self.noise_params.noise_angle_park))
        if self.noise_params.global_noise:
            tensor_acc.rotate(self.get_rotational_noise(point, self.noise_params.noise_size_global, self.noise_params.noise_angle_global))
        return tensor_acc

    def get_rotational_noise(self, point, noise_size, noise_angle):
        # 使用python随机噪声模拟，实际可用更优噪声库
        return (random.uniform(-1, 1)) * noise_angle * math.pi / 180

    def on_land(self, point):
        in_sea = PolygonUtil.inside_polygon(point, self.sea)
        if self.ignore_river:
            return not in_sea
        return not in_sea and not PolygonUtil.inside_polygon(point, self.river)

    def in_parks(self, point):
        return any(PolygonUtil.inside_polygon(point, p) for p in self.parks)

    def sample_at(self, x: float, y: float) -> Tuple[float, float, float, float]:
        """
        在指定位置对张量场进行采样

        Args:
            x: x坐标
            y: y坐标

        Returns:
            (a, b, c, d) 张量矩阵的四个分量
        """
        # 实现张量场采样算法
        # 结合所有基础场的影响
        # 添加噪声（如果启用）
        # 返回最终的张量值
        pass

    def get_major_direction(self, x: float, y: float) -> Tuple[float, float]:
        """
        获取指定位置的主方向向量

        Args:
            x: x坐标
            y: y坐标

        Returns:
            (dx, dy) 主方向单位向量
        """
        a, b, c, d = self.sample_at(x, y)
        # 计算特征向量以获取主方向
        # 返回归一化后的主方向向量
        pass

    def get_minor_direction(self, x: float, y: float) -> Tuple[float, float]:
        """
        获取指定位置的次方向向量（与主方向垂直）

        Args:
            x: x坐标
            y: y坐标

        Returns:
            (dx, dy) 次方向单位向量
        """
        # 获取主方向并旋转90度
        dx, dy = self.get_major_direction(x, y)
        return -dy, dx  # 垂直向量
