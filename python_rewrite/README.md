# MapGenerator Python 重写

这个目录包含了 MapGenerator 的 Python 实现版本。此版本完全基于原始 TypeScript 代码的算法实现，但不包含任何可视化交互组件。

## 功能

- 通过参数化输入生成地图
- 输出 SVG 图像和 JSON 数据
- 保持与原始 TypeScript 算法完全一致的行为

## 使用方法

```python
from map_generator import MapGenerator

# 从 JSON 文件加载参数
generator = MapGenerator.from_json_file("map_params.json")

# 或直接设置参数
generator = MapGenerator(
    zoom=1.4,
    world_dimensions={"x": 2000, "y": 1000},
    # 其他参数...
)

# 生成地图
generator.generate()

# 导出结果
generator.export_svg("output_map.svg")
generator.export_json("output_data.json")
```
