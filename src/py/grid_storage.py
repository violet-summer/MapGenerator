import logging
from typing import List
from vector import Vector

class GridStorage:
    def __init__(self, world_dimensions: Vector, origin: Vector, dsep: float):
        """
        world_dimensions assumes origin of 0,0
        :param dsep: Separation distance between samples
        """
        self.world_dimensions = world_dimensions
        self.origin = origin
        self.dsep = dsep
        self.dsep_sq = self.dsep * self.dsep
        self.grid_dimensions = world_dimensions.clone().divide_scalar(self.dsep)
        self.grid = [
            [[] for _ in range(int(self.grid_dimensions.y))]
            for _ in range(int(self.grid_dimensions.x))
        ]

    def add_all(self, grid_storage: 'GridStorage') -> None:
        """
        Add all samples from another grid to this one
        """
        for row in grid_storage.grid:
            for cell in row:
                for sample in cell:
                    self.add_sample(sample)

    def add_polyline(self, line: List[Vector]) -> None:
        for v in line:
            self.add_sample(v)

    def add_sample(self, v: Vector, coords: Vector = None) -> None:
        """
        Does not enforce separation
        Does not clone
        """
        if coords is None:
            coords = self.get_sample_coords(v)
        self.grid[int(coords.x)][int(coords.y)].append(v)

    def is_valid_sample(self, v: Vector, d_sq: float = None) -> bool:
        """
        Tests whether v is at least d away from samples
        Performance very important - this is called at every integration step
        :param d_sq: squared test distance (default is self.dsep_sq)
        """
        if d_sq is None:
            d_sq = self.dsep_sq

        coords = self.get_sample_coords(v)

        # Check samples in 9 cells in 3x3 grid
        for x in range(-1, 2):
            for y in range(-1, 2):
                cell = coords.clone().add(Vector(x, y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    if not self.vector_far_from_vectors(v, self.grid[int(cell.x)][int(cell.y)], d_sq):
                        return False

        return True

    def vector_far_from_vectors(self, v: Vector, vectors: List[Vector], d_sq: float) -> bool:
        """
        Test whether v is at least d away from vectors
        Performance very important - this is called at every integration step
        :param d_sq: squared test distance
        """
        for sample in vectors:
            if sample != v:
                distance_sq = sample.distance_to_squared(v)
                if distance_sq < d_sq:
                    return False

        return True

    def get_nearby_points(self, v: Vector, distance: float) -> List[Vector]:
        """
        Returns points in cells surrounding v
        Results include v, if it exists in the grid
        :param distance: returns samples (kind of) closer than distance - returns all samples in
                         cells so approximation (square to approximate circle)
        """
        radius = int((distance / self.dsep) - 0.5)
        coords = self.get_sample_coords(v)
        out = []
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                cell = coords.clone().add(Vector(x, y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    out.extend(self.grid[int(cell.x)][int(cell.y)])

        return out

    def world_to_grid(self, v: Vector) -> Vector:
        return v.clone().sub(self.origin)

    def grid_to_world(self, v: Vector) -> Vector:
        return v.clone().add(self.origin)

    def vector_out_of_bounds(self, grid_v: Vector, bounds: Vector) -> bool:
        return (
            grid_v.x < 0 or grid_v.y < 0 or
            grid_v.x >= bounds.x or grid_v.y >= bounds.y
        )

    def get_sample_coords(self, world_v: Vector) -> Vector:
        """
        :return: Cell coords corresponding to vector
        Performance important - called at every integration step
        """
        v = self.world_to_grid(world_v)
        if self.vector_out_of_bounds(v, self.world_dimensions):
            # logging.error("Tried to access out-of-bounds sample in grid")
            return Vector.zero_vector()

        return Vector(
            int(v.x // self.dsep),
            int(v.y // self.dsep)
        )
