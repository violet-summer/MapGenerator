import logging
import random
from typing import List
from vector import Vector
from integrator import FieldIntegrator
from streamlines import StreamlineGenerator, StreamlineParams
from tensor_field import TensorField
from polygon_util import PolygonUtil

class NoiseStreamlineParams:
    """
    噪声流线参数类。
    """
    def __init__(self, noise_enabled: bool, noise_size: float, noise_angle: float):
        self.noise_enabled = noise_enabled  # 是否启用噪声
        self.noise_size = noise_size  # 噪声大小
        self.noise_angle = noise_angle  # 噪声角度

class WaterParams(StreamlineParams):
    """
    水体生成参数类，继承自流线参数类。
    """
    def __init__(self, coast_noise: NoiseStreamlineParams, river_noise: NoiseStreamlineParams, river_bank_size: float, river_size: float, **kwargs):
        super().__init__(**kwargs)
        self.coast_noise = coast_noise  # 海岸线噪声参数
        self.river_noise = river_noise  # 河流噪声参数
        self.river_bank_size = river_bank_size  # 河岸宽度
        self.river_size = river_size  # 河流宽度

class WaterGenerator(StreamlineGenerator):
    """
    水体生成器类，用于生成海岸线和河流的流线，并支持可控的噪声。
    """
    TRIES = 100  # 最大尝试次数

    def __init__(self, integrator: FieldIntegrator, origin: Vector, world_dimensions: Vector, params: WaterParams, tensor_field: TensorField):
        super().__init__(integrator, origin, world_dimensions, params)
        self.tensor_field = tensor_field
        self.coastline_major = True  # 是否为主要海岸线
        self._coastline: List[Vector] = []  # 噪声化的海岸线
        self._sea_polygon: List[Vector] = []  # 海洋多边形
        self._river_polygon: List[Vector] = []  # 河流多边形
        self._river_secondary_road: List[Vector] = []  # 河流次级道路

    @property
    def coastline(self) -> List[Vector]:
        return self._coastline

    @property
    def sea_polygon(self) -> List[Vector]:
        return self._sea_polygon

    @property
    def river_polygon(self) -> List[Vector]:
        return self._river_polygon

    @property
    def river_secondary_road(self) -> List[Vector]:
        return self._river_secondary_road

    def create_coast(self) -> None:
        """
        创建海岸线。
        """
        coast_streamline = []
        seed = None
        major = None

        if self.params.coast_noise.noise_enabled:
            self.tensor_field.enable_global_noise(self.params.coast_noise.noise_angle, self.params.coast_noise.noise_size)

        for _ in range(self.TRIES):
            major = random.random() < 0.5
            seed = self.get_seed(major)
            coast_streamline = self.extend_streamline(self.integrate_streamline(seed, major))

            if self.reaches_edges(coast_streamline):
                break

        self.tensor_field.disable_global_noise()

        self._coastline = coast_streamline
        self.coastline_major = major

        road = self.simplify_streamline(coast_streamline)
        self._sea_polygon = self.get_sea_polygon(road)
        self.all_streamlines_simple.append(road)
        self.tensor_field.sea = self._sea_polygon

        # 创建中间采样点
        complex_streamline = self.complexify_streamline(road)
        self.grid(major).add_polyline(complex_streamline)
        self.streamlines(major).append(complex_streamline)
        self.all_streamlines.append(complex_streamline)

    def create_river(self) -> None:
        """
        创建河流。
        """
        river_streamline = []
        seed = None

        # 忽略海洋以便进行边界检查
        old_sea = self.tensor_field.sea
        self.tensor_field.sea = []

        if self.params.river_noise.noise_enabled:
            self.tensor_field.enable_global_noise(self.params.river_noise.noise_angle, self.params.river_noise.noise_size)

        for i in range(self.TRIES):
            seed = self.get_seed(not self.coastline_major)
            river_streamline = self.extend_streamline(self.integrate_streamline(seed, not self.coastline_major))

            if self.reaches_edges(river_streamline):
                break
            elif i == self.TRIES - 1:
                logging.error("未能找到到达边界的河流")

        self.tensor_field.sea = old_sea
        self.tensor_field.disable_global_noise()

        # 创建河流道路
        expanded_noisy = self.complexify_streamline(PolygonUtil.resize_geometry(river_streamline, self.params.river_size, False))
        self._river_polygon = PolygonUtil.resize_geometry(river_streamline, self.params.river_size - self.params.river_bank_size, False)

        # 创建河流次级道路
        river_split_poly = self.get_sea_polygon(river_streamline)
        road1 = [v for v in expanded_noisy if not PolygonUtil.inside_polygon(v, self._sea_polygon) and not self.vector_off_screen(v) and PolygonUtil.inside_polygon(v, river_split_poly)]
        road1_simple = self.simplify_streamline(road1)
        road2 = [v for v in expanded_noisy if not PolygonUtil.inside_polygon(v, self._sea_polygon) and not self.vector_off_screen(v) and not PolygonUtil.inside_polygon(v, river_split_poly)]
        road2_simple = self.simplify_streamline(road2)

        if not road1 or not road2:
            return

        if road1[0].distance_to_squared(road2[0]) < road1[0].distance_to_squared(road2[-1]):
            road2_simple.reverse()

        self.tensor_field.river = road1_simple + road2_simple

        # 保存次级道路
        self.all_streamlines_simple.append(road1_simple)
        self._river_secondary_road = road2_simple

        self.grid(not self.coastline_major).add_polyline(road1)
        self.grid(not self.coastline_major).add_polyline(road2)
        self.streamlines(not self.coastline_major).append(road1)
        self.streamlines(not self.coastline_major).append(road2)
        self.all_streamlines.append(road1)
        self.all_streamlines.append(road2)

    def get_sea_polygon(self, polyline: List[Vector]) -> List[Vector]:
        """
        获取海洋多边形。
        """
        return PolygonUtil.line_rectangle_polygon_intersection(self.origin, self.world_dimensions, polyline)

    def complexify_streamline(self, s: List[Vector]) -> List[Vector]:
        """
        在流线上插入样本，直到样本间距为 dstep。
        """
        out = []
        for i in range(len(s) - 1):
            out.extend(self.complexify_streamline_recursive(s[i], s[i + 1]))
        return out

    def complexify_streamline_recursive(self, v1: Vector, v2: Vector) -> List[Vector]:
        """
        递归地插入样本点。
        """
        if v1.distance_to_squared(v2) <= self.params_sq["dstep"]:
            return [v1, v2]
        d = v2.clone().sub(v1)
        halfway = v1.clone().add(d.multiply_scalar(0.5))

        complex_part = self.complexify_streamline_recursive(v1, halfway)
        complex_part.extend(self.complexify_streamline_recursive(halfway, v2))
        return complex_part

    def extend_streamline(self, streamline: List[Vector]) -> List[Vector]:
        """
        扩展流线。
        """
        streamline.insert(0, streamline[0].clone().add(streamline[0].clone().sub(streamline[1]).set_length(self.params.dstep * 5)))
        streamline.append(streamline[-1].clone().add(streamline[-1].clone().sub(streamline[-2]).set_length(self.params.dstep * 5)))
        return streamline

    def reaches_edges(self, streamline: List[Vector]) -> bool:
        """
        检查流线是否到达边界。
        """
        return self.vector_off_screen(streamline[0]) and self.vector_off_screen(streamline[-1])

    def vector_off_screen(self, v: Vector) -> bool:
        """
        检查向量是否在屏幕外。
        """
        to_origin = v.clone().sub(self.origin)
        return to_origin.x <= 0 or to_origin.y <= 0 or to_origin.x >= self.world_dimensions.x or to_origin.y >= self.world_dimensions.y
