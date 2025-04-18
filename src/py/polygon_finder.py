import logging
from typing import List, Optional
from vector import Vector
from graph import Node
from polygon_util import PolygonUtil
from tensor_field import TensorField

class PolygonParams:
    """
    多边形参数类，用于定义多边形生成的各种参数。
    """
    def __init__(self, max_length: int, min_area: float, shrink_spacing: float, chance_no_divide: float):
        self.max_length = max_length  # 多边形的最大边数
        self.min_area = min_area  # 多边形的最小面积
        self.shrink_spacing = shrink_spacing  # 收缩间距
        self.chance_no_divide = chance_no_divide  # 不分割的概率

class PolygonFinder:
    """
    多边形查找器类，用于在图中查找多边形，主要用于生成地块和公园。
    """
    def __init__(self, nodes: List[Node], params: PolygonParams, tensor_field: TensorField):
        self.nodes = nodes
        self.params = params
        self.tensor_field = tensor_field

        self._polygons: List[List[Vector]] = []
        self._shrunk_polygons: List[List[Vector]] = []
        self._divided_polygons: List[List[Vector]] = []
        self.to_shrink: List[List[Vector]] = []
        self.to_divide: List[List[Vector]] = []
        self.resolve_shrink = None
        self.resolve_divide = None

    @property
    def polygons(self) -> List[List[Vector]]:
        """
        获取当前的多边形列表。
        """
        if self._divided_polygons:
            return self._divided_polygons
        if self._shrunk_polygons:
            return self._shrunk_polygons
        return self._polygons

    def reset(self) -> None:
        """
        重置多边形查找器的状态。
        """
        self.to_shrink = []
        self.to_divide = []
        self._polygons = []
        self._shrunk_polygons = []
        self._divided_polygons = []

    def update(self) -> bool:
        """
        更新多边形的收缩和分割状态。
        """
        change = False
        if self.to_shrink:
            resolve = len(self.to_shrink) == 1
            if self.step_shrink(self.to_shrink.pop()):
                change = True
            if resolve:
                self.resolve_shrink()

        if self.to_divide:
            resolve = len(self.to_divide) == 1
            if self.step_divide(self.to_divide.pop()):
                change = True
            if resolve:
                self.resolve_divide()

        return change

    async def shrink(self, animate: bool = False) -> None:
        """
        收缩多边形，使其边距与道路保持一致。
        """
        if not self._polygons:
            self.find_polygons()

        if animate:
            if not self._polygons:
                return
            self.to_shrink = self._polygons[:]
        else:
            self._shrunk_polygons = []
            for polygon in self._polygons:
                self.step_shrink(polygon)

    def step_shrink(self, polygon: List[Vector]) -> bool:
        """
        收缩单个多边形。
        """
        shrunk = PolygonUtil.resize_geometry(polygon, -self.params.shrink_spacing)
        if shrunk:
            self._shrunk_polygons.append(shrunk)
            return True
        return False

    async def divide(self, animate: bool = False) -> None:
        """
        分割多边形。
        """
        if not self._polygons:
            self.find_polygons()

        polygons = self._shrunk_polygons if self._shrunk_polygons else self._polygons

        if animate:
            if not polygons:
                return
            self.to_divide = polygons[:]
        else:
            self._divided_polygons = []
            for polygon in polygons:
                self.step_divide(polygon)

    def step_divide(self, polygon: List[Vector]) -> bool:
        """
        分割单个多边形。
        """
        if self.params.chance_no_divide > 0 and random.random() < self.params.chance_no_divide:
            self._divided_polygons.append(polygon)
            return True

        divided = PolygonUtil.subdivide_polygon(polygon, self.params.min_area)
        if divided:
            self._divided_polygons.extend(divided)
            return True
        return False

    def find_polygons(self) -> None:
        """
        在图中查找多边形。
        """
        self._shrunk_polygons = []
        self._divided_polygons = []
        polygons = []

        for node in self.nodes:
            if len(node.adj) < 2:
                continue
            for next_node in node.adj:
                polygon = self.recursive_walk([node, next_node])
                if polygon and len(polygon) < self.params.max_length:
                    self.remove_polygon_adjacencies(polygon)
                    polygons.append([n.value.clone() for n in polygon])

        self._polygons = self.filter_polygons_by_water(polygons)

    def filter_polygons_by_water(self, polygons: List[List[Vector]]) -> List[List[Vector]]:
        """
        过滤掉位于水域上的多边形。
        """
        out = []
        for polygon in polygons:
            average_point = PolygonUtil.average_point(polygon)
            if self.tensor_field.on_land(average_point) and not self.tensor_field.in_parks(average_point):
                out.append(polygon)
        return out

    def remove_polygon_adjacencies(self, polygon: List[Node]) -> None:
        """
        移除多边形的邻接关系。
        """
        for i in range(len(polygon)):
            current = polygon[i]
            next_node = polygon[(i + 1) % len(polygon)]

            if next_node in current.adj:
                current.adj.remove(next_node)
            else:
                logging.error("PolygonFinder - 节点不在邻接列表中")

    def recursive_walk(self, visited: List[Node], count: int = 0) -> Optional[List[Node]]:
        """
        递归遍历图以查找多边形。
        """
        if count >= self.params.max_length:
            return None

        next_node = self.get_rightmost_node(visited[-2], visited[-1])
        if not next_node:
            return None

        if next_node in visited:
            return visited[visited.index(next_node):]
        else:
            visited.append(next_node)
            return self.recursive_walk(visited, count + 1)

    def get_rightmost_node(self, node_from: Node, node_to: Node) -> Optional[Node]:
        """
        获取右转方向的下一个节点。
        """
        if not node_to.adj:
            return None

        backwards_difference_vector = node_from.value.clone().sub(node_to.value)
        transform_angle = math.atan2(backwards_difference_vector.y, backwards_difference_vector.x)

        rightmost_node = None
        smallest_theta = math.pi * 2

        for next_node in node_to.adj:
            if next_node != node_from:
                next_vector = next_node.value.clone().sub(node_to.value)
                next_angle = math.atan2(next_vector.y, next_vector.x) - transform_angle
                if next_angle < 0:
                    next_angle += math.pi * 2

                if next_angle < smallest_theta:
                    smallest_theta = next_angle
                    rightmost_node = next_node

        return rightmost_node
