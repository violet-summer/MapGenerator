from tensor_field import TensorField
from vector import Vector
from streamlines import StreamlineParams

class FieldIntegrator:
    """
    抽象类：场积分器，用于在张量场中进行积分。
    """
    def __init__(self, field: TensorField):
        self.field = field

    def integrate(self, point: Vector, major: bool) -> Vector:
        """
        抽象方法：在给定点上进行积分。
        :param point: 当前点
        :param major: 是否为主方向
        :return: 积分后的向量
        """
        raise NotImplementedError("子类必须实现 integrate 方法")

    def sample_field_vector(self, point: Vector, major: bool) -> Vector:
        """
        采样张量场中的向量。
        :param point: 当前点
        :param major: 是否为主方向
        :return: 采样的向量
        """
        tensor = self.field.sample_point(point)
        return tensor.get_major() if major else tensor.get_minor()

    def on_land(self, point: Vector) -> bool:
        """
        检查点是否在陆地上。
        :param point: 当前点
        :return: 是否在陆地上
        """
        return self.field.on_land(point)

class EulerIntegrator(FieldIntegrator):
    """
    欧拉积分器，使用欧拉方法进行积分。
    """
    def __init__(self, field: TensorField, params: StreamlineParams):
        super().__init__(field)
        self.params = params

    def integrate(self, point: Vector, major: bool) -> Vector:
        """
        使用欧拉方法进行积分。
        :param point: 当前点
        :param major: 是否为主方向
        :return: 积分后的向量
        """
        return self.sample_field_vector(point, major).multiply_scalar(self.params.dstep)

class RK4Integrator(FieldIntegrator):
    """
    四阶龙格-库塔积分器，使用 RK4 方法进行积分。
    """
    def __init__(self, field: TensorField, params: StreamlineParams):
        super().__init__(field)
        self.params = params

    def integrate(self, point: Vector, major: bool) -> Vector:
        """
        使用四阶龙格-库塔方法进行积分。
        :param point: 当前点
        :param major: 是否为主方向
        :return: 积分后的向量
        """
        k1 = self.sample_field_vector(point, major)
        k23 = self.sample_field_vector(point.clone().add(Vector.from_scalar(self.params.dstep / 2)), major)
        k4 = self.sample_field_vector(point.clone().add(Vector.from_scalar(self.params.dstep)), major)

        return k1.add(k23.multiply_scalar(4)).add(k4).multiply_scalar(self.params.dstep / 6)
