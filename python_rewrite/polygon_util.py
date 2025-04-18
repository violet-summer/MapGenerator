# polygon_util.py
from vector import Vector
import math

class PolygonUtil:
    @staticmethod
    def calc_polygon_area(polygon):
        total = 0
        n = len(polygon)
        for i in range(n):
            addX = polygon[i].x
            addY = polygon[(i + 1) % n].y
            subX = polygon[(i + 1) % n].x
            subY = polygon[i].y
            total += (addX * addY * 0.5)
            total -= (subX * subY * 0.5)
        return abs(total)

    @staticmethod
    def average_point(polygon):
        if not polygon:
            return Vector.zero()
        sum_v = Vector.zero()
        for v in polygon:
            sum_v.add(v)
        return sum_v.divide_scalar(len(polygon))

    @staticmethod
    def inside_polygon(point, polygon):
        if not polygon:
            return False
        inside = False
        n = len(polygon)
        for i in range(n):
            j = (i - 1) % n
            xi, yi = polygon[i].x, polygon[i].y
            xj, yj = polygon[j].x, polygon[j].y
            intersect = ((yi > point.y) != (yj > point.y)) and \
                        (point.x < (xj - xi) * (point.y - yi) / (yj - yi + 1e-12) + xi)
            if intersect:
                inside = not inside
        return inside

    @staticmethod
    def point_in_rectangle(point, origin, dimensions):
        return (origin.x <= point.x <= origin.x + dimensions.x and
                origin.y <= point.y <= origin.y + dimensions.y)
