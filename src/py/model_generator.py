import logging
from enum import Enum
from typing import List, Any
from jszip import JSZip  # 假设有一个类似 JSZip 的 Python 库
from three import Vector3, Mesh, Shape, ExtrudeGeometry, ShapeGeometry  # 假设有类似 THREE.js 的 Python 库
from three_csg import CSG  # 假设有类似 three-csg-ts 的 Python 库

# 定义模型生成器的状态枚举
class ModelGeneratorStates(Enum):
    WAITING = 0
    SUBTRACT_OCEAN = 1
    ADD_COASTLINE = 2
    SUBTRACT_RIVER = 3
    ADD_ROADS = 4
    ADD_BLOCKS = 5
    ADD_BUILDINGS = 6
    CREATE_ZIP = 7

class ModelGenerator:
    def __init__(self, ground: List[Vector3], sea: List[Vector3], coastline: List[Vector3], river: List[Vector3],
                 main_roads: List[List[Vector3]], major_roads: List[List[Vector3]], minor_roads: List[List[Vector3]],
                 buildings: List[Any], blocks: List[List[Vector3]]):
        # 地面厚度
        self.ground_level = 20  
        self.export_stl = None  # 假设有类似 threejs-export-stl 的 Python 库
        self.resolve = None
        self.zip = None
        self.state = ModelGeneratorStates.WAITING

        # 初始化几何体和处理队列
        self.ground_mesh = None
        self.ground_bsp = None
        self.polygons_to_process = []
        self.roads_geometry = None
        self.blocks_geometry = None
        self.roads_bsp = None
        self.buildings_geometry = None
        self.buildings_to_process = []

        # 输入数据
        self.ground = ground
        self.sea = sea
        self.coastline = coastline
        self.river = river
        self.main_roads = main_roads
        self.major_roads = major_roads
        self.minor_roads = minor_roads
        self.buildings = buildings
        self.blocks = blocks

    async def get_stl(self) -> Any:
        # 异步生成 STL 文件
        self.zip = JSZip()
        self.zip.file("model/README.txt", "有关如何将这些模型组合成城市的教程，请访问 https://maps.probabletrain.com/#/stl")
        self.ground_mesh = self.polygon_to_mesh(self.ground, self.ground_level)
        self.ground_bsp = CSG.from_mesh(self.ground_mesh)
        self.set_state(ModelGeneratorStates.SUBTRACT_OCEAN)

    def set_state(self, state: ModelGeneratorStates):
        # 设置当前状态
        self.state = state
        logging.info(state.name)

    def update(self) -> bool:
        # 更新状态机，处理模型生成逻辑
        if self.state == ModelGeneratorStates.WAITING:
            return False
        elif self.state == ModelGeneratorStates.SUBTRACT_OCEAN:
            # 处理海洋减去逻辑
            sea_level_mesh = self.polygon_to_mesh(self.ground, 0)
            self.three_to_blender(sea_level_mesh)
            sea_level_stl = self.export_stl.from_mesh(sea_level_mesh)
            self.zip.file("model/domain.stl", sea_level_stl)

            sea_mesh = self.polygon_to_mesh(self.sea, 0)
            self.three_to_blender(sea_mesh)
            sea_mesh_stl = self.export_stl.from_mesh(sea_mesh)
            self.zip.file("model/sea.stl", sea_mesh_stl)
            self.set_state(ModelGeneratorStates.ADD_COASTLINE)
        # ...省略其他状态的处理逻辑...
        elif self.state == ModelGeneratorStates.CREATE_ZIP:
            # 创建 ZIP 文件
            self.zip.generate_async(type="blob").then(lambda blob: self.resolve(blob))
            self.set_state(ModelGeneratorStates.WAITING)
        return True

    def three_to_blender(self, mesh: Mesh):
        # 旋转和缩放网格，使其方向正确
        mesh.scale.multiply_scalar(0.02)
        mesh.update_matrix_world(True)

    def polygon_to_mesh(self, polygon: List[Vector3], height: float) -> Mesh:
        # 将多边形挤出为网格
        if len(polygon) < 3:
            logging.error("尝试将空多边形导出为 OBJ")
            return None
        shape = Shape()
        shape.move_to(polygon[0].x, polygon[0].y)
        for point in polygon[1:]:
            shape.line_to(point.x, point.y)
        shape.line_to(polygon[0].x, polygon[0].y)

        if height == 0:
            return Mesh(ShapeGeometry(shape))

        extrude_settings = {
            "steps": 1,
            "depth": height,
            "bevel_enabled": False,
        }
        geometry = ExtrudeGeometry(shape, extrude_settings)
        mesh = Mesh(geometry)
        mesh.update_matrix_world(True)
        return mesh
