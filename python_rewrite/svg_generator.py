# svg_generator.py
class SVGGenerator:
    def __init__(self, model):
        self.model = model

    def save(self, filename):
        svg = self.to_svg()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg)

    def to_svg(self):
        # 这里只输出道路为例，可扩展地块、建筑等
        svg_lines = ['<svg xmlns="http://www.w3.org/2000/svg" version="1.1">']
        for line in self.model.result.get('roads', []):
            path = 'M ' + ' L '.join(f'{x},{y}' for x, y in line)
            svg_lines.append(f'<path d="{path}" stroke="black" fill="none" stroke-width="2"/>')
        svg_lines.append('</svg>')
        return '\n'.join(svg_lines)
