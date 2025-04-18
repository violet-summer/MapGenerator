# grid_storage.py
from vector import Vector

class GridStorage:
    def __init__(self, world_dimensions: Vector, origin: Vector, dsep: float):
        self.world_dimensions = world_dimensions
        self.origin = origin
        self.dsep = dsep
        self.dsep_sq = dsep * dsep
        self.grid_dimensions = world_dimensions.clone().divide_scalar(dsep)
        self.grid = []
        for x in range(int(self.grid_dimensions.x)):
            row = []
            for y in range(int(self.grid_dimensions.y)):
                row.append([])
            self.grid.append(row)

    def add_all(self, grid_storage):
        for x, row in enumerate(grid_storage.grid):
            for y, cell in enumerate(row):
                for sample in cell:
                    self.add_sample(sample)

    def add_polyline(self, line):
        for v in line:
            self.add_sample(v)

    def add_sample(self, v, coords=None):
        if coords is None:
            coords = self.get_sample_coords(v)
        self.grid[int(coords.x)][int(coords.y)].append(v)

    def is_valid_sample(self, v, d_sq=None):
        if d_sq is None:
            d_sq = self.dsep_sq
        coords = self.get_sample_coords(v)
        for x in range(-1, 2):
            for y in range(-1, 2):
                cell = coords.clone().add(Vector(x, y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    if not self.vector_far_from_vectors(v, self.grid[int(cell.x)][int(cell.y)], d_sq):
                        return False
        return True

    def vector_far_from_vectors(self, v, vectors, d_sq):
        for sample in vectors:
            if sample is not v:
                distance_sq = sample.distance_to_squared(v)
                if distance_sq < d_sq:
                    return False
        return True

    def get_nearby_points(self, v, distance):
        radius = int((distance / self.dsep) - 0.5) + 1
        coords = self.get_sample_coords(v)
        out = []
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                cell = coords.clone().add(Vector(x, y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    out.extend(self.grid[int(cell.x)][int(cell.y)])
        return out

    def world_to_grid(self, v):
        return v.clone().sub(self.origin)

    def grid_to_world(self, v):
        return v.clone().add(self.origin)

    def vector_out_of_bounds(self, grid_v, bounds):
        return (grid_v.x < 0 or grid_v.y < 0 or grid_v.x >= bounds.x or grid_v.y >= bounds.y)

    def get_sample_coords(self, world_v):
        v = self.world_to_grid(world_v)
        if self.vector_out_of_bounds(v, self.world_dimensions):
            return Vector.zero()
        return Vector(int(v.x // self.dsep), int(v.y // self.dsep))
