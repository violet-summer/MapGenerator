import logging
from typing import List
from vector import Vector
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import split

class PolygonUtil:
    """
    多边形工具类，提供多边形相关的操作方法。
    """

    @staticmethod
    def slice_rectangle(origin: Vector, world_dimensions: Vector, p1: Vector, p2: Vector) -> List[Vector]:
        """
        切割矩形，返回最小的多边形。
        :param origin: 矩形的起点
        :param world_dimensions: 矩形的宽高
        :param p1: 切割线的起点
        :param p2: 切割线的终点
        :return: 切割后的最小多边形顶点数组
        """
        rectangle = Polygon([
            (origin.x, origin.y),
            (origin.x + world_dimensions.x, origin.y),
            (origin.x + world_dimensions.x, origin.y + world_dimensions.y),
            (origin.x, origin.y + world_dimensions.y)
        ])
        line = LineString([(p1.x, p1.y), (p2.x, p2.y)])
        sliced = split(rectangle, line)

        if len(sliced) > 1:
            areas = [poly.area for poly in sliced]
            smallest_poly = sliced[areas.index(min(areas))]
            return [Vector(coord[0], coord[1]) for coord in smallest_poly.exterior.coords[:-1]]
        return [Vector(coord[0], coord[1]) for coord in sliced[0].exterior.coords[:-1]]

    @staticmethod
    def calc_polygon_area(polygon: List[Vector]) -> float:
        """
        计算多边形的面积。
        :param polygon: 多边形顶点数组
        :return: 多边形的面积
        """
        shapely_polygon = Polygon([(v.x, v.y) for v in polygon])
        return abs(shapely_polygon.area)

    @staticmethod
    def subdivide_polygon(polygon: List[Vector], min_area: float) -> List[List[Vector]]:
        """
        递归地将多边形按最长边分割，直到满足最小面积条件。
        :param polygon: 多边形顶点数组
        :param min_area: 最小面积
        :return: 分割后的多边形数组
        """
        area = PolygonUtil.calc_polygon_area(polygon)
        if area < 0.5 * min_area:
            return []

        shapely_polygon = Polygon([(v.x, v.y) for v in polygon])
        perimeter = shapely_polygon.length

        # 形状指数
        if area / (perimeter * perimeter) < 0.04:
            return []

        if area < 2 * min_area:
            return [polygon]

        # 偏移量在 0.4 到 0.6 之间
        deviation = (random.random() * 0.2) + 0.4
        longest_side = max(shapely_polygon.exterior.coords[:-1], key=lambda p: Point(p).distance(Point(polygon[0].x, polygon[0].y)))
        midpoint = Vector((longest_side[0] + longest_side[1]) * deviation, (longest_side[2] + longest_side[3]) * deviation)

        # 构造分割线
        line = LineString([(midpoint.x, midpoint.y), (midpoint.x + 100, midpoint.y + 100)])

        try:
            sliced = split(shapely_polygon, line)
            divided = []
            for part in sliced:
                divided.append(PolygonUtil.subdivide_polygon([Vector(coord[0], coord[1]) for coord in part.exterior.coords[:-1]], min_area))
            return divided
        except Exception as e:
            logging.error(f"分割多边形时出错: {e}")
            return []

    @staticmethod
    def resize_geometry(geometry: List[Vector], spacing: float, is_polygon: bool = True) -> List[Vector]:
        """
        缩放多边形或线段。
        :param geometry: 多边形或线段顶点数组
        :param spacing: 缩放距离
        :param is_polygon: 是否为多边形
        :return: 缩放后的顶点数组
        """
        try:
            shapely_geometry = Polygon([(v.x, v.y) for v in geometry]) if is_polygon else LineString([(v.x, v.y) for v in geometry])
            resized = shapely_geometry.buffer(spacing)
            if not resized.is_valid:
                return []
            return [Vector(coord[0], coord[1]) for coord in resized.exterior.coords[:-1]]
        except Exception as e:
            logging.error(f"缩放几何体时出错: {e}")
            return []

    @staticmethod
    def average_point(polygon: List[Vector]) -> Vector:
        """
        计算多边形的平均点。
        :param polygon: 多边形顶点数组
        :return: 平均点
        """
        if not polygon:
            return Vector(0, 0)
        sum_x = sum(v.x for v in polygon)
        sum_y = sum(v.y for v in polygon)
        return Vector(sum_x / len(polygon), sum_y / len(polygon))

    @staticmethod
    def inside_polygon(point: Vector, polygon: List[Vector]) -> bool:
        """
        判断点是否在多边形内。
        :param point: 点
        :param polygon: 多边形顶点数组
        :return: 是否在多边形内
        """
        shapely_polygon = Polygon([(v.x, v.y) for v in polygon])
        return shapely_polygon.contains(Point(point.x, point.y))

    @staticmethod
    def point_in_rectangle(point: Vector, origin: Vector, dimensions: Vector) -> bool:
        """
        判断点是否在矩形内。
        :param point: 点
        :param origin: 矩形的起点
        :param dimensions: 矩形的宽高
        :return: 是否在矩形内
        """
        return origin.x <= point.x <= origin.x + dimensions.x and origin.y <= point.y <= origin.y + dimensions.y
