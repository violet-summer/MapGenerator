import logging
from typing import List, Dict, Optional
from simplify import simplify
from vector import Vector
from grid_storage import GridStorage
from integrator import FieldIntegrator

class StreamlineParams:
    """
    流线参数类，用于定义流线生成的各种参数。
    """
    def __init__(self, **kwargs):
        self.dsep: float = kwargs.get("dsep", 1.0)  # 流线种子分隔距离
        self.dtest: float = kwargs.get("dtest", 1.0)  # 流线积分分隔距离
        self.dstep: float = kwargs.get("dstep", 1.0)  # 步长
        self.dcirclejoin: float = kwargs.get("dcirclejoin", 1.0)  # 圆形连接的查找距离
        self.dlookahead: float = kwargs.get("dlookahead", 1.0)  # 向前查找的距离
        self.joinangle: float = kwargs.get("joinangle", 1.0)  # 连接道路的角度（弧度）
        self.pathIterations: int = kwargs.get("pathIterations", 100)  # 路径积分迭代限制
        self.seedTries: int = kwargs.get("seedTries", 10)  # 最大种子尝试次数
        self.simplifyTolerance: float = kwargs.get("simplifyTolerance", 0.1)  # 简化容差
        self.collideEarly: float = kwargs.get("collideEarly", 0.5)  # 提前碰撞的概率（0-1）

class StreamlineGenerator:
    """
    流线生成器类，用于通过积分张量场生成多段折线。
    """
    SEED_AT_ENDPOINTS = False  # 是否在端点处生成种子
    NEAR_EDGE = 3  # 靠近边缘的采样距离

    def __init__(self, integrator: FieldIntegrator, origin: Vector, world_dimensions: Vector, params: StreamlineParams):
        self.integrator = integrator
        self.origin = origin
        self.world_dimensions = world_dimensions
        self.params = params

        if params.dstep > params.dsep:
            logging.error("流线采样距离大于分隔距离 (dstep > dsep)")

        # 确保测试距离小于分隔距离
        params.dtest = min(params.dtest, params.dsep)

        # 设置自碰撞检测的距离平方
        self.dcollideself_sq = (params.dcirclejoin / 2) ** 2
        self.n_streamline_step = int(params.dcirclejoin / params.dstep)
        self.n_streamline_look_back = 2 * self.n_streamline_step

        # 初始化主网格和次网格
        self.major_grid = GridStorage(world_dimensions, origin, params.dsep)
        self.minor_grid = GridStorage(world_dimensions, origin, params.dsep)

        # 候选种子
        self.candidate_seeds_major: List[Vector] = []
        self.candidate_seeds_minor: List[Vector] = []

        # 流线状态
        self.streamlines_done = True
        self.resolve = None
        self.last_streamline_major = True

        # 存储流线
        self.all_streamlines: List[List[Vector]] = []
        self.streamlines_major: List[List[Vector]] = []
        self.streamlines_minor: List[List[Vector]] = []
        self.all_streamlines_simple: List[List[Vector]] = []

        self.set_params_sq()

    def clear_streamlines(self) -> None:
        """
        清空所有流线数据。
        """
        self.all_streamlines_simple = []
        self.streamlines_major = []
        self.streamlines_minor = []
        self.all_streamlines = []

    def join_dangling_streamlines(self) -> None:
        """
        连接悬挂的流线。
        """
        for major in [True, False]:
            for streamline in self.streamlines(major):
                # 忽略闭合的流线
                if streamline[0] == streamline[-1]:
                    continue

                # 连接起点
                new_start = self.get_best_next_point(streamline[0], streamline[4], streamline)
                if new_start is not None:
                    for p in self.points_between(streamline[0], new_start, self.params.dstep):
                        streamline.insert(0, p)
                        self.grid(major).add_sample(p)

                # 连接终点
                new_end = self.get_best_next_point(streamline[-1], streamline[-4], streamline)
                if new_end is not None:
                    for p in self.points_between(streamline[-1], new_end, self.params.dstep):
                        streamline.append(p)
                        self.grid(major).add_sample(p)

        # 简化流线
        self.all_streamlines_simple = [self.simplify_streamline(s) for s in self.all_streamlines]

    def points_between(self, v1: Vector, v2: Vector, dstep: float) -> List[Vector]:
        """
        返回从 v1 到 v2 的点数组，点之间的间隔不超过 dstep。
        """
        d = v1.distance_to(v2)
        n_points = int(d / dstep)
        if n_points == 0:
            return []

        step_vector = v2.clone().sub(v1)
        out = []
        for i in range(1, n_points + 1):
            next_point = v1.clone().add(step_vector.clone().multiply_scalar(i / n_points))
            if self.integrator.integrate(next_point, True).length_sq() > 0.001:
                out.append(next_point)
            else:
                return out
        return out

    def get_best_next_point(self, point: Vector, previous_point: Vector, streamline: List[Vector]) -> Optional[Vector]:
        """
        获取连接流线的最佳下一个点。
        """
        nearby_points = self.major_grid.get_nearby_points(point, self.params.dlookahead)
        nearby_points.extend(self.minor_grid.get_nearby_points(point, self.params.dlookahead))
        direction = point.clone().sub(previous_point)

        closest_sample = None
        closest_distance = float("inf")

        for sample in nearby_points:
            if sample != point and sample != previous_point:
                difference_vector = sample.clone().sub(point)
                if difference_vector.dot(direction) < 0:
                    continue

                distance_to_sample = point.distance_to_squared(sample)
                if distance_to_sample < 2 * self.params_sq["dstep"]:
                    closest_sample = sample
                    break

                angle_between = abs(Vector.angle_between(direction, difference_vector))
                if angle_between < self.params.joinangle and distance_to_sample < closest_distance:
                    closest_distance = distance_to_sample
                    closest_sample = sample

        if closest_sample is not None:
            closest_sample = closest_sample.clone().add(direction.set_length(self.params.simplifyTolerance * 4))

        return closest_sample

    def simplify_streamline(self, streamline: List[Vector]) -> List[Vector]:
        """
        简化流线以减少顶点数量。
        """
        return [Vector(p.x, p.y) for p in simplify(streamline, self.params.simplifyTolerance)]

    def set_params_sq(self) -> None:
        """
        设置平方参数，用于距离平方计算。
        """
        self.params_sq = {k: v ** 2 if isinstance(v, (int, float)) else v for k, v in vars(self.params).items()}

    def grid(self, major: bool) -> GridStorage:
        """
        返回主网格或次网格。
        """
        return self.major_grid if major else self.minor_grid

    def streamlines(self, major: bool) -> List[List[Vector]]:
        """
        返回主流线或次流线。
        """
        return self.streamlines_major if major else self.streamlines_minor
