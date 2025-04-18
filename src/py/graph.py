import logging
from typing import List, Set, Tuple
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree
from vector import Vector
from isect import bush

class Node:
    def __init__(self, value: Vector):
        self.value = value
        self.segments: Set[Tuple[Vector, Vector]] = set()
        self.neighbors: Set['Node'] = set()
        self.adj: List['Node'] = []

    def add_segment(self, segment: Tuple[Vector, Vector]) -> None:
        self.segments.add(segment)

    def add_neighbor(self, node: 'Node') -> None:
        if node != self:
            self.neighbors.add(node)
            node.neighbors.add(self)

class Graph:
    def __init__(self, streamlines: List[List[Vector]], dstep: float, delete_dangling: bool = False):
        intersections = bush(self.streamlines_to_segment(streamlines)).run()
        nodes = []
        node_add_radius = 0.001

        for streamline in streamlines:
            for i, point in enumerate(streamline):
                node = Node(point)
                if i > 0:
                    node.add_segment(self.vectors_to_segment(streamline[i - 1], point))
                if i < len(streamline) - 1:
                    node.add_segment(self.vectors_to_segment(point, streamline[i + 1]))
                self.fuzzy_add_to_tree(nodes, node, node_add_radius)

        for intersection in intersections:
            node = Node(Vector(intersection.point.x, intersection.point.y))
            for s in intersection.segments:
                node.add_segment(s)
            self.fuzzy_add_to_tree(nodes, node, node_add_radius)

        spatial_index = STRtree([Point(n.value.x, n.value.y) for n in nodes])

        for streamline in streamlines:
            for i in range(len(streamline) - 1):
                nodes_along_segment = self.get_nodes_along_segment(
                    self.vectors_to_segment(streamline[i], streamline[i + 1]),
                    spatial_index, node_add_radius, dstep
                )
                if len(nodes_along_segment) > 1:
                    for j in range(len(nodes_along_segment) - 1):
                        nodes_along_segment[j].add_neighbor(nodes_along_segment[j + 1])
                else:
                    logging.error("Error Graph.py: segment with less than 2 nodes")

        for n in nodes:
            if delete_dangling:
                self.delete_dangling_nodes(n, nodes)
            n.adj = list(n.neighbors)

        self.nodes = nodes
        self.intersections = [Vector(i.point.x, i.point.y) for i in intersections]

    def delete_dangling_nodes(self, n: Node, nodes: List[Node]) -> None:
        if len(n.neighbors) == 1:
            nodes.remove(n)
            for neighbor in n.neighbors:
                neighbor.neighbors.discard(n)
                self.delete_dangling_nodes(neighbor, nodes)

    def get_nodes_along_segment(self, segment: Tuple[Vector, Vector], spatial_index: STRtree, radius: float, step: float) -> List[Node]:
        found_nodes = []
        nodes_along_segment = []

        start = Vector(segment[0].x, segment[0].y)
        end = Vector(segment[1].x, segment[1].y)

        difference_vector = end.clone().sub(start)
        step = min(step, difference_vector.length() / 2)
        steps = int(difference_vector.length() / step)

        for i in range(steps + 1):
            current_point = start.clone().add(difference_vector.clone().multiply_scalar(i / steps))
            nodes_to_add = []
            point = Point(current_point.x, current_point.y)
            nearby_nodes = spatial_index.query(point.buffer(radius + step / 2))

            for nearby_point in nearby_nodes:
                node = next((n for n in self.nodes if n.value.x == nearby_point.x and n.value.y == nearby_point.y), None)
                if node and any(self.fuzzy_segments_equal(s, segment) for s in node.segments):
                    nodes_to_add.append(node)

            nodes_to_add.sort(key=lambda n: self.dot_product_to_segment(n, start, difference_vector))
            nodes_along_segment.extend(nodes_to_add)

        return nodes_along_segment

    def fuzzy_segments_equal(self, s1: Tuple[Vector, Vector], s2: Tuple[Vector, Vector], tolerance: float = 0.0001) -> bool:
        return (
            abs(s1[0].x - s2[0].x) <= tolerance and
            abs(s1[0].y - s2[0].y) <= tolerance and
            abs(s1[1].x - s2[1].x) <= tolerance and
            abs(s1[1].y - s2[1].y) <= tolerance
        )

    def dot_product_to_segment(self, node: Node, start: Vector, difference_vector: Vector) -> float:
        dot_vector = node.value.clone().sub(start)
        return difference_vector.dot(dot_vector)

    def fuzzy_add_to_tree(self, nodes: List[Node], node: Node, radius: float) -> None:
        for existing_node in nodes:
            if existing_node.value.distance(node.value) <= radius:
                existing_node.neighbors.update(node.neighbors)
                existing_node.segments.update(node.segments)
                return
        nodes.append(node)

    def streamlines_to_segment(self, streamlines: List[List[Vector]]) -> List[Tuple[Vector, Vector]]:
        return [
            self.vectors_to_segment(s[i], s[i + 1])
            for s in streamlines for i in range(len(s) - 1)
        ]

    def vectors_to_segment(self, v1: Vector, v2: Vector) -> Tuple[Vector, Vector]:
        return (v1, v2)
