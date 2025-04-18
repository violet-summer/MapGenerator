# vector.py
import math

class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @staticmethod
    def zero():
        return Vector(0, 0)

    @staticmethod
    def from_scalar(s: float):
        return Vector(s, s)

    def clone(self):
        return Vector(self.x, self.y)

    def add(self, v):
        self.x += v.x
        self.y += v.y
        return self

    def sub(self, v):
        self.x -= v.x
        self.y -= v.y
        return self

    def multiply(self, v):
        self.x *= v.x
        self.y *= v.y
        return self

    def multiply_scalar(self, s: float):
        self.x *= s
        self.y *= s
        return self

    def divide(self, v):
        if v.x == 0 or v.y == 0:
            raise ZeroDivisionError('Division by zero in Vector.divide')
        self.x /= v.x
        self.y /= v.y
        return self

    def divide_scalar(self, s: float):
        if s == 0:
            raise ZeroDivisionError('Division by zero in Vector.divide_scalar')
        return self.multiply_scalar(1 / s)

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def cross(self, v):
        return self.x * v.y - self.y * v.x

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_sq(self):
        return self.x * self.x + self.y * self.y

    def normalize(self):
        l = self.length()
        if l == 0:
            return self
        return self.divide_scalar(l)

    def negate(self):
        return self.multiply_scalar(-1)

    def set_length(self, length: float):
        return self.normalize().multiply_scalar(length)

    def angle(self):
        return math.atan2(self.y, self.x)

    def rotate_around(self, center, angle):
        cos = math.cos(angle)
        sin = math.sin(angle)
        x = self.x - center.x
        y = self.y - center.y
        self.x = x * cos - y * sin + center.x
        self.y = x * sin + y * cos + center.y
        return self

    def equals(self, v):
        return self.x == v.x and self.y == v.y

    def distance_to(self, v):
        return math.sqrt(self.distance_to_squared(v))

    def distance_to_squared(self, v):
        dx = self.x - v.x
        dy = self.y - v.y
        return dx * dx + dy * dy

    def copy(self, v):
        self.x = v.x
        self.y = v.y
        return self

    def set(self, v):
        self.x = v.x
        self.y = v.y
        return self

    def set_x(self, x):
        self.x = x
        return self

    def set_y(self, y):
        self.y = y
        return self