import math
import logging

class Vector:
    """
    A class representing a 2D vector with basic operations.
    """

    def __init__(self, x: float, y: float):
        """
        Initialize a vector with x and y components.
        :param x: X component of the vector.
        :param y: Y component of the vector.
        """
        self.x = x
        self.y = y

    @staticmethod
    def zero_vector() -> 'Vector':
        return Vector(0, 0)

    @staticmethod
    def from_scalar(s: float) -> 'Vector':
        return Vector(s, s)

    @staticmethod
    def angle_between(v1: 'Vector', v2: 'Vector') -> float:
        """
        -pi to pi
        """
        angle_between = v1.angle() - v2.angle()
        if angle_between > math.pi:
            angle_between -= 2 * math.pi
        elif angle_between <= -math.pi:
            angle_between += 2 * math.pi
        return angle_between

    @staticmethod
    def is_left(line_point: 'Vector', line_direction: 'Vector', point: 'Vector') -> bool:
        """
        Tests whether a point lies to the left of a line
        """
        perpendicular_vector = Vector(line_direction.y, -line_direction.x)
        return point.clone().sub(line_point).dot(perpendicular_vector) < 0

    def add(self, v: 'Vector') -> 'Vector':
        self.x += v.x
        self.y += v.y
        return self

    def sub(self, v: 'Vector') -> 'Vector':
        self.x -= v.x
        self.y -= v.y
        return self

    def multiply_scalar(self, scalar: float) -> 'Vector':
        self.x *= scalar
        self.y *= scalar
        return self

    def length(self) -> float:
        return math.sqrt(self.length_sq())

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalize(self) -> 'Vector':
        l = self.length()
        if l == 0:
            logging.warning("Zero Vector")
            return self
        return self.divide_scalar(l)

    def clone(self) -> 'Vector':
        return Vector(self.x, self.y)

    def copy(self, v: 'Vector') -> 'Vector':
        self.x = v.x
        self.y = v.y
        return self

    def cross(self, v: 'Vector') -> float:
        return self.x * v.y - self.y * v.x

    def distance_to(self, v: 'Vector') -> float:
        return math.sqrt(self.distance_to_squared(v))

    def distance_to_squared(self, v: 'Vector') -> float:
        dx = self.x - v.x
        dy = self.y - v.y
        return dx * dx + dy * dy

    def divide(self, v: 'Vector') -> 'Vector':
        if v.x == 0 or v.y == 0:
            logging.warning("Division by zero")
            return self
        self.x /= v.x
        self.y /= v.y
        return self

    def divide_scalar(self, s: float) -> 'Vector':
        if s == 0:
            logging.warning("Division by zero")
            return self
        return self.multiply_scalar(1 / s)

    def dot(self, v: 'Vector') -> float:
        return self.x * v.x + self.y * v.y

    def equals(self, v: 'Vector') -> bool:
        return self.x == v.x and self.y == v.y

    def multiply(self, v: 'Vector') -> 'Vector':
        self.x *= v.x
        self.y *= v.y
        return self

    def negate(self) -> 'Vector':
        return self.multiply_scalar(-1)

    def rotate_around(self, center: 'Vector', angle: float) -> 'Vector':
        """
        Rotate around a center by a given angle in radians
        """
        cos = math.cos(angle)
        sin = math.sin(angle)

        x = self.x - center.x
        y = self.y - center.y

        self.x = x * cos - y * sin + center.x
        self.y = x * sin + y * cos + center.y
        return self

    def set(self, v: 'Vector') -> 'Vector':
        self.x = v.x
        self.y = v.y
        return self

    def set_x(self, x: float) -> 'Vector':
        self.x = x
        return self

    def set_y(self, y: float) -> 'Vector':
        self.y = y
        return self

    def set_length(self, length: float) -> 'Vector':
        return self.normalize().multiply_scalar(length)

    def angle(self) -> float:
        """
        Angle in radians to positive x-axis between -pi and pi
        """
        return math.atan2(self.y, self.x)

    def __repr__(self) -> str:
        """
        String representation of the vector.
        :return: A string in the format "Vector(x, y)".
        """
        return f"Vector({self.x}, {self.y})"
