import json
from typing import Dict

from basis_field import Grid
from svg_generator import SVGGenerator
from tensor_field import TensorField, NoiseParams
from vector import Vector


class MapGenerator:
    """
    城市地图生成器的Python实现。
    基于原始TypeScript代码，但只通过参数化输入，生成SVG和JSON输出。
    """

    def __init__(self, 
                 zoom: float = 0.3,
                 world_dimensions: Dict[str, int] = None,
                 origin: Dict[str, int] = None,
                 tensor_field_params: Dict = None,
                 water_params: Dict = None,
                 streamlines_params: Dict = None,
                 parks_params: Dict = None,
                 buildings_params: Dict = None,
                 options_params: Dict = None):
        """
        初始化地图生成器

        Args:
            zoom: 缩放级别
            world_dimensions: 世界尺寸，包含 x 和 y 属性
            origin: 原点坐标
            tensor_field_params: 张量场参数
            water_params: 水体参数
            streamlines_params: 流线参数
            parks_params: 公园参数
            buildings_params: 建筑参数
            options_params: 选项参数，包括drawCentre等
        """
        self.zoom = zoom
        self.world_dimensions = world_dimensions or {"x": 2000, "y": 1000}
        self.origin = origin or {"x": 0, "y": 0}
        self.tensor_field_params = tensor_field_params or {}
        self.water_params = water_params or {}
        self.streamlines_params = streamlines_params or {}
        self.parks_params = parks_params or {}
        self.buildings_params = buildings_params or {}
        self.options_params = options_params or {"drawCentre": True}

        # 将在生成过程中使用的数据结构
        self.tensor_field = None
        self.water_features = None
        self.streamlines = None
        self.parks = None
        self.buildings = None
        self.result = {}

    @classmethod
    def from_json_file(cls, json_path: str) -> 'MapGenerator':
        """
        从JSON文件加载参数并创建地图生成器实例

        Args:
            json_path: JSON参数文件的路径

        Returns:
            初始化的MapGenerator实例
        """
        with open(json_path, 'r') as f:
            params = json.load(f)

        return cls(
            zoom=params.get('zoom', 0.3),
            world_dimensions=params.get('worldDimensions'),
            origin=params.get('origin'),
            tensor_field_params=params.get('tensorField'),
            water_params=params.get('water'),
            streamlines_params=params.get('streamlines'),
            parks_params=params.get('parks'),
            buildings_params=params.get('buildings'),
            options_params=params.get('options')
        )

    def generate(self):
        """
        生成整个地图，包括张量场、水体、道路、公园和建筑
        """
        self._generate_tensor_field()
        self._generate_water_features()
        self._generate_streamlines()
        self._generate_parks()
        self._generate_buildings()

        # 将生成的数据添加到result中，供SVGGenerator使用
        if hasattr(self, 'streamlines') and self.streamlines is not None:
            self.result['roads'] = [[(v.x, v.y) for v in line] for line in self.streamlines.allStreamlines]

    def _generate_tensor_field(self):
        """
        生成张量场，这是生成地图的基础
        """
        # 创建噪声参数
        noise_params = NoiseParams(
            global_noise=self.water_params.get('coastParams', {}).get('noiseEnabled', False),
            noise_size_park=self.tensor_field_params.get('noiseParams', {}).get('noiseSizePark', 100),
            noise_angle_park=self.tensor_field_params.get('noiseParams', {}).get('noiseAnglePark', 30),
            noise_size_global=self.tensor_field_params.get('noiseParams', {}).get('noiseSizeGlobal', 100),
            noise_angle_global=self.tensor_field_params.get('noiseParams', {}).get('noiseAngleGlobal', 30)
        )

        # 创建张量场
        self.tensor_field = TensorField(noise_params)

        # 添加基础场
        for field in self.tensor_field_params.get('basisFields', []):
            if field.get('type') == 'grid':
                self.tensor_field.add_grid(
                    Vector(field.get('x', 0), field.get('y', 0)),
                    field.get('size', 1000),
                    field.get('decay', 30),
                    field.get('theta', 0)
                )
            elif field.get('type') == 'radial':
                self.tensor_field.add_radial(
                    Vector(field.get('x', 0), field.get('y', 0)),
                    field.get('size', 200),
                    field.get('decay', 5)
                )

        # 设置是否绘制中心点
        self.draw_centre = self.options_params.get('drawCentre', True)

    def _generate_water_features(self):
        """
        生成水体特征，包括海岸和河流
        """
        # 在这里实现从 TypeScript 转换的水体生成算法
        pass

    def _generate_streamlines(self):
        """
        基于张量场生成道路网络
        """
        # 在这里实现从 TypeScript 转换的流线算法
        # 为了解决当前错误，我们先创建一个空的streamlines对象，包含allStreamlines属性
        class DummyStreamlines:
            def __init__(self):
                self.allStreamlines = []

        self.streamlines = DummyStreamlines()

    def _generate_parks(self):
        """
        生成公园
        """
        # 在这里实现从 TypeScript 转换的公园生成算法
        pass

    def _generate_buildings(self):
        """
        在城市区块中生成建筑物
        """
        # 在这里实现从 TypeScript 转换的建筑生成算法
        pass

    def export_svg(self, output_path: str):
        """
        将生成的地图导出为SVG文件

        Args:
            output_path: 输出文件路径
        """
        # 创建SVG生成器
        if hasattr(self, 'tensor_field') and hasattr(self, 'streamlines'):
            svg_gen = SVGGenerator(self)
            svg_gen.save(output_path)
        else:
            print("Error: Cannot export SVG before generating the map")

    def to_json(self):
        """
        将地图数据转换为JSON格式

        Returns:
            包含地图数据的字典
        """
        return {
            "zoom": self.zoom,
            "worldDimensions": self.world_dimensions,
            "origin": self.origin,
            "tensorField": {
                "basisFields": [
                    {
                        "type": "grid" if isinstance(field, Grid) else "radial",
                        "x": field.centre.x,
                        "y": field.centre.y,
                        "size": field._size,
                        "decay": field._decay,
                        "theta": getattr(field, '_theta', 0) if hasattr(field, '_theta') else 0
                    } for field in self.tensor_field.get_basis_fields()
                ] if hasattr(self, 'tensor_field') else []
            },
            "options": self.options_params
        }

    def export_json(self, output_path: str):
        """
        将生成的地图数据导出为JSON文件

        Args:
            output_path: 输出文件路径
        """
        # 导出JSON数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=2)

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # 使用新的参数文件格式
    generator = MapGenerator.from_json_file('new_map_params.json')
    generator.generate()
    generator.export_svg('map.svg')
    generator.export_json('map.json')

    # 以下是旧的实现方式，保留作为参考
    """
    config = load_config('config.json')
    # 构建张量场
    coast = config['Water']['CoastParams']
    river = config['Water']['RiverParams']
    noise_params = NoiseParams(
        global_noise=coast['noiseEnabled'],
        noise_size_park=coast['noiseSize'],
        noise_angle_park=coast['noiseAngle'],
        noise_size_global=river['noiseSize'],
        noise_angle_global=river['noiseAngle']
    )
    tensor_field = TensorField(noise_params)
    for grid in config['Tensor Field'].get('Grids', []):
        tensor_field.add_grid(Vector(grid['x'], grid['y']), grid['_size'], grid['_decay'], grid['theta'])
    for radial in config['Tensor Field'].get('Radials', []):
        tensor_field.add_radial(Vector(radial['x'], radial['y']), radial['_size'], radial['_decay'])
    # 生成流线
    main_params = config['Main']['Params']
    streamline_params = StreamlineParams(**main_params)
    streamlines = StreamlineGenerator(
        integrator=None,  # 需根据张量场选择积分器
        origin=Vector(0, 0),
        world_dimensions=Vector(config['Options']['_size'], config['Options']['_size']),
        params=streamline_params
    )
    # 生成地图主结构
    model = ModelGenerator(tensor_field, streamlines, config)
    model.generate()
    # 输出SVG和JSON
    svg_gen = SVGGenerator(model)
    svg_gen.save('map.svg')
    with open('map.json', 'w', encoding='utf-8') as f:
        json.dump(model.to_json(), f, ensure_ascii=False, indent=2)
    """

if __name__ == '__main__':
    main()
