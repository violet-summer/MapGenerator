from vector import Vector
import math

class Tensor:
    """
    张量类，用于表示和操作张量。
    """

    def __init__(self, r: float, matrix: list):
        """
        初始化张量。
        :param r: 张量的模长
        :param matrix: 张量的矩阵表示，包含两个元素 [cos(2θ), sin(2θ)]
        """
        self.r = r
        self.matrix = matrix
        self.old_theta = False  # 标记是否需要重新计算角度
        self._theta = self.calculate_theta()  # 初始化角度

    @staticmethod
    def from_angle(angle: float) -> 'Tensor':
        """
        根据角度创建张量。
        :param angle: 角度（弧度制）
        :return: 张量对象
        """
        return Tensor(1, [math.cos(angle * 4), math.sin(angle * 4)])

    @staticmethod
    def from_vector(vector: Vector) -> 'Tensor':
        """
        根据向量创建张量。
        :param vector: 向量对象
        :return: 张量对象
        """
        t1 = vector.x ** 2 - vector.y ** 2
        t2 = 2 * vector.x * vector.y
        t3 = t1 ** 2 - t2 ** 2
        t4 = 2 * t1 * t2
        return Tensor(1, [t3, t4])

    @staticmethod
    def zero() -> 'Tensor':
        """
        返回零张量。
        :return: 零张量对象
        """
        return Tensor(0, [0, 0])

    @property
    def theta(self) -> float:
        """
        获取张量的角度（弧度制）。
        :return: 张量的角度
        """
        if self.old_theta:
            self._theta = self.calculate_theta()
            self.old_theta = False
        return self._theta

    def add(self, tensor: 'Tensor', smooth: bool) -> 'Tensor':
        """
        将另一个张量加到当前张量上。
        :param tensor: 另一个张量
        :param smooth: 是否平滑处理
        :return: 当前张量对象
        """
        self.matrix = [v * self.r + tensor.matrix[i] * tensor.r for i, v in enumerate(self.matrix)]

        if smooth:
            self.r = math.hypot(*self.matrix)
            self.matrix = [v / self.r for v in self.matrix]
        else:
            self.r = 2

        self.old_theta = True
        return self

    def scale(self, s: float) -> 'Tensor':
        """
        缩放张量的模长。
        :param s: 缩放因子
        :return: 当前张量对象
        """
        self.r *= s
        self.old_theta = True
        return self

    def rotate(self, theta: float) -> 'Tensor':
        """
        旋转张量。
        :param theta: 旋转角度（弧度制）
        :return: 当前张量对象
        """
        if theta == 0:
            return self

        new_theta = self.theta + theta
        if new_theta < math.pi:
            new_theta += math.pi
        if new_theta >= math.pi:
            new_theta -= math.pi

        self.matrix[0] = math.cos(2 * new_theta) * self.r
        self.matrix[1] = math.sin(2 * new_theta) * self.r
        self._theta = new_theta
        return self

    def get_major(self) -> Vector:
        """
        获取张量的主方向向量。
        :return: 主方向向量
        """
        if self.r == 0:  # 退化情况
            return Vector.zero_vector()
        return Vector(math.cos(self.theta), math.sin(self.theta))

    def get_minor(self) -> Vector:
        """
        获取张量的次方向向量。
        :return: 次方向向量
        """
        if self.r == 0:  # 退化情况
            return Vector.zero_vector()
        angle = self.theta + math.pi / 2
        return Vector(math.cos(angle), math.sin(angle))

    def calculate_theta(self) -> float:
        """
        计算张量的角度。
        :return: 张量的角度（弧度制）
        """
        if self.r == 0:
            return 0
        return math.atan2(self.matrix[1] / self.r, self.matrix[0] / self.r) / 2
