import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python_rewrite.map_generator import MapGenerator

def main():
    """
    测试地图生成器
    """
    print("Testing MapGenerator with new_map_params.json...")

    # 从JSON文件加载参数
    generator = MapGenerator.from_json_file("new_map_params.json")

    # 生成地图
    print("Generating map...")
    generator.generate()

    # 导出结果
    print("Exporting SVG...")
    generator.export_svg("test_output.svg")

    print("Exporting JSON...")
    generator.export_json("test_output.json")

    print("Done!")

if __name__ == "__main__":
    main()
