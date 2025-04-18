# MapGenerator Python 重写

这个目录包含了 MapGenerator 的 Python 实现版本。此版本完全基于原始 TypeScript 代码的算法实现，但不包含任何可视化交互组件。

## 新增功能

- 支持 `drawCentre` 参数，用于控制是否绘制基础场的中心点
- 支持从 JSON 文件加载参数并生成地图
- 输出 SVG 图像和 JSON 数据

## 参数格式

参数可以通过 JSON 文件提供，格式如下：

```json
{
  "zoom": 1.4,
  "worldDimensions": {"x": 2000, "y": 1000},
  "origin": {"x": 0, "y": 0},
  "tensorField": {
    "noiseParams": {
      "globalNoise": false,
      "noiseSizePark": 100,
      "noiseAnglePark": 30,
      "noiseSizeGlobal": 100,
      "noiseAngleGlobal": 30
    },
    "basisFields": [
      {
        "type": "grid",
        "x": 520,
        "y": 258,
        "size": 1124,
        "decay": 31,
        "theta": 61
      }
    ]
  },
  "water": {
    "coastParams": {
      "noiseEnabled": true,
      "noiseSize": 30,
      "noiseAngle": 20
    },
    "riverParams": {
      "noiseEnabled": true,
      "noiseSize": 30,
      "noiseAngle": 20
    }
  },
  "streamlines": {
    "main": {
      "dsep": 400,
      "dtest": 200,
      "pathIterations": 3072,
      "seedTries": 300,
      "dstep": 1,
      "dlookahead": 500,
      "dcirclejoin": 5,
      "joinangle": 0.1,
      "simplifyTolerance": 0.5,
      "collideEarly": 0
    }
  },
  "parks": {
    "numBigParks": 2,
    "numSmallParks": 0
  },
  "buildings": {
    "minArea": 50,
    "shrinkSpacing": 4,
    "chanceNoDivide": 0.05
  },
  "options": {
    "drawCentre": true,
    "animationSpeed": 30,
    "orthographic": false,
    "cameraX": 0,
    "cameraY": 0,
    "showFrame": false,
    "zoomBuildings": false,
    "buildingModels": false
  }
}
```

## 使用方法

```python
# 假设你在python_rewrite目录下
from python_rewrite.map_generator import MapGenerator

# 从 JSON 文件加载参数
generator = MapGenerator.from_json_file("new_map_params.json")

# 生成地图
generator.generate()

# 导出结果
generator.export_svg("output_map.svg")
generator.export_json("output_data.json")
```

## 测试

可以使用提供的测试脚本来验证实现：

```bash
python test_map_generator.py
```

这将使用 `new_map_params.json` 中的参数生成地图，并将结果导出为 `test_output.svg` 和 `test_output.json`。