from tensor_field import TensorField
from vector import Vector
from streamlines import StreamlineParams

class FieldIntegrator:
    def __init__(self, field: TensorField):
        self.field = field

    def integrate(self, point: Vector, major: bool):
        raise NotImplementedError()

    def sample_field_vector(self, point: Vector, major: bool):
        tensor = self.field.sample_point(point)
        if major:
            return tensor.get_major()
        return tensor.get_minor()

    def on_land(self, point: Vector):
        return self.field.on_land(point)

class EulerIntegrator(FieldIntegrator):
    def __init__(self, field: TensorField, params: StreamlineParams):
        super().__init__(field)
        self.params = params

    def integrate(self, point: Vector, major: bool):
        return self.sample_field_vector(point, major).multiply_scalar(self.params.dstep)

class RK4Integrator(FieldIntegrator):
    def __init__(self, field: TensorField, params: StreamlineParams):
        super().__init__(field)
        self.params = params

    def integrate(self, point: Vector, major: bool):
        k1 = self.sample_field_vector(point, major)
        k23 = self.sample_field_vector(point.clone().add(Vector.from_scalar(self.params.dstep / 2)), major)
        k4 = self.sample_field_vector(point.clone().add(Vector.from_scalar(self.params.dstep)), major)
        return k1.add(k23.multiply_scalar(4)).add(k4).multiply_scalar(self.params.dstep / 6)
