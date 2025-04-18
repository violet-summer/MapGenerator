import math
import random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import polygonize
from vector import Vector

class PolygonUtil:
    """多边形处理工具类"""
    
    @staticmethod
    def slice_rectangle(origin, world_dimensions, p1, p2):
        """通过线切割矩形，返回最小多边形"""
        rectangle = [
            [origin.x, origin.y],
            [origin.x + world_dimensions.x, origin.y],
            [origin.x + world_dimensions.x, origin.y + world_dimensions.y],
            [origin.x, origin.y + world_dimensions.y]
        ]
        
        rect_poly = Polygon(rectangle)
        line = LineString([(p1.x, p1.y), (p2.x, p2.y)])
        
        # 使用切割线切开矩形
        split_polys = []
        
        # 使用shapely的polygonize函数
        sliced_polys = list(polygonize(rect_poly.boundary.union(line)))
        
        if len(sliced_polys) < 2:
            # 如果切割失败，返回原始矩形
            return [Vector(x, y) for x, y in rectangle]
            
        # 找到面积最小的多边形
        min_area = float('inf')
        min_poly = None
        
        for poly in sliced_polys:
            area = poly.area
            if area < min_area:
                min_area = area
                min_poly = poly
                
        return [Vector(x, y) for x, y in list(min_poly.exterior.coords)[:-1]]
    
    @staticmethod
    def line_rectangle_polygon_intersection(origin, world_dimensions, line):
        """创建海域多边形"""
        if len(line) < 2:
            return []
            
        bounds = [
            (origin.x, origin.y),
            (origin.x + world_dimensions.x, origin.y),
            (origin.x + world_dimensions.x, origin.y + world_dimensions.y),
            (origin.x, origin.y + world_dimensions.y)
        ]
        
        bounding_poly = Polygon(bounds)
        line_shape = LineString([(p.x, p.y) for p in line])
        
        # 联合边界和线
        union = bounding_poly.exterior.union(line_shape)
        
        # 多边形化
        polygons = list(polygonize(union))
        
        if not polygons:
            return []
            
        # 找到最小面积的多边形
        smallest_poly = min(polygons, key=lambda p: p.area)
        
        return [Vector(x, y) for x, y in list(smallest_poly.exterior.coords)[:-1]]
    
    @staticmethod
    def calc_polygon_area(polygon):
        """计算多边形面积"""
        if len(polygon) < 3:
            return 0
            
        total = 0
        
        for i in range(len(polygon)):
            add_x = polygon[i].x
            add_y = polygon[(i + 1) % len(polygon)].y
            sub_x = polygon[(i + 1) % len(polygon)].x
            sub_y = polygon[i].y
            
            total += (add_x * add_y * 0.5)
            total -= (sub_x * sub_y * 0.5)
            
        return abs(total)
    
    @staticmethod
    def subdivide_polygon(p, min_area):
        """递归地沿着最长边分割多边形，直到满足最小面积停止条件"""
        area = PolygonUtil.calc_polygon_area(p)
        
        if area < 0.5 * min_area:
            return []
            
        divided = []
        
        # 找最长边
        longest_side_length = 0
        longest_side = [p[0], p[1]]
        
        perimeter = 0
        
        for i in range(len(p)):
            side_length = p[i].clone().sub(p[(i+1) % len(p)]).length()
            perimeter += side_length
            
            if side_length > longest_side_length:
                longest_side_length = side_length
                longest_side = [p[i], p[(i+1) % len(p)]]
        
        # 形状指数，使用1:4矩形比例作为限制
        if area / (perimeter * perimeter) < 0.04:
            return []
            
        if area < 2 * min_area:
            return [p]
            
        # 介于0.4和0.6之间
        deviation = (random.random() * 0.2) + 0.4
        
        average_point = longest_side[0].clone().add(longest_side[1]).multiply_scalar(deviation)
        difference_vector = longest_side[0].clone().sub(longest_side[1])
        perp_vector = Vector(difference_vector.y, -1 * difference_vector.x)
        perp_vector.normalize().multiply_scalar(100)
        
        bisect = [average_point.clone().add(perp_vector), average_point.clone().sub(perp_vector)]
        
        # 使用Shapely执行分割
        try:
            poly = Polygon([(v.x, v.y) for v in p])
            cut_line = LineString([(bisect[0].x, bisect[0].y), (bisect[1].x, bisect[1].y)])
            
            # 将多边形分割成两部分
            sliced = []
            for geom in PolygonUtil._split(poly, cut_line):
                if isinstance(geom, Polygon):
                    sliced.append([Vector(x, y) for x, y in list(geom.exterior.coords)[:-1]])
            
            # 递归调用
            for s in sliced:
                divided.extend(PolygonUtil.subdivide_polygon(s, min_area))
                
            return divided
        except Exception as e:
            print(f"多边形分割错误: {e}")
            return []
    
    @staticmethod
    def _split(polygon, line):
        """辅助函数，用于分割多边形"""
        merged = polygon.boundary.union(line)
        borders = polygonize(merged)
        return list(borders)
    
    @staticmethod
    def resize_geometry(geometry, spacing, is_polygon=True):
        """收缩或扩展多边形"""
        try:
            if is_polygon:
                if len(geometry) < 3:
                    return []
                geom = Polygon([(v.x, v.y) for v in geometry])
            else:
                if len(geometry) < 2:
                    return []
                geom = LineString([(v.x, v.y) for v in geometry])
                
            # 使用buffer进行扩展或收缩
            resized = geom.buffer(spacing, cap_style=1)
            
            if not resized.is_simple:
                return []
                
            if is_polygon:
                return [Vector(x, y) for x, y in list(resized.exterior.coords)[:-1]]
            else:
                return [Vector(x, y) for x, y in list(resized.coords)]
        except Exception as e:
            print(f"几何调整错误: {e}")
            return []
    
    @staticmethod
    def average_point(polygon):
        """计算多边形的平均点"""
        if not polygon:
            return Vector.zero_vector()
            
        sum_point = Vector.zero_vector()
        for v in polygon:
            sum_point.add(v)
            
        return sum_point.divide_scalar(len(polygon))
    
    @staticmethod
    def inside_polygon(point, polygon):
        """判断点是否在多边形内部"""
        if not polygon:
            return False
        
        # 射线投射算法
        inside = False
        for i in range(len(polygon)):
            j = (i - 1) % len(polygon)
            
            xi, yi = polygon[i].x, polygon[i].y
            xj, yj = polygon[j].x, polygon[j].y
            
            intersect = ((yi > point.y) != (yj > point.y)) and \
                       (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi)
                       
            if intersect:
                inside = not inside
                
        return inside
    
    @staticmethod
    def point_in_rectangle(point, origin, dimensions):
        """判断点是否在矩形内部"""
        return (point.x >= origin.x and point.y >= origin.y and 
                point.x <= dimensions.x and point.y <= dimensions.y)