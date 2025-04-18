# model_generator.py
from streamlines import StreamlineGenerator
from tensor_field import TensorField


class ModelGenerator:
    def __init__(self, tensor_field: TensorField, streamlines: StreamlineGenerator, config: dict):
        self.tensor_field = tensor_field
        self.streamlines = streamlines
        self.config = config
        self.result = {}

    def generate(self):
        # 这里只做主流程示例，细节可根据ts逻辑补充
        # 1. 生成道路流线
        self.streamlines.create_all_streamlines()
        # 2. 生成地块、建筑等（可扩展）
        self.result['roads'] = [[(v.x, v.y) for v in line] for line in self.streamlines.allStreamlines]
        # 3. 生成海岸、河流等（可扩展）
        # ...

    def to_json(self):
        return self.result
