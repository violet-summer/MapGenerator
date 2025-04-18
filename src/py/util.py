import random
import re
from typing import Dict, List, Optional, Union

class Util:
    """
    Utility class providing helper functions for random number generation and other utilities.
    """
    # Must match style.css and index.html
    CANVAS_ID = 'map-canvas'  # 主画布的 HTML 元素 ID
    IMG_CANVAS_ID = 'img-canvas'  # 用于导出图像的隐藏画布 ID
    SVG_ID = 'map-svg'  # 用于导出 SVG 的 HTML 元素 ID

    # How far to integrate streamlines beyond screen - for making buildings reach the edge
    DRAW_INFLATE_AMOUNT = 1.2  # 用于扩展流线超出屏幕范围的比例

    @staticmethod
    def random_range(max_value: float, min_value: float = 0) -> float:
        """
        生成指定范围内的随机数
        """
        return random.uniform(min_value, max_value)

    # CSS colour parser
    # (c) Dean McNamee <dean@gmail.com>, 2012.
    # License: MIT

    kCSSColorTable: Dict[str, List[Union[int, float]]] = {
        "transparent": [0, 0, 0, 0], "aliceblue": [240, 248, 255, 1],
        "antiquewhite": [250, 235, 215, 1], "aqua": [0, 255, 255, 1],
        "aquamarine": [127, 255, 212, 1], "azure": [240, 255, 255, 1],
        "beige": [245, 245, 220, 1], "bisque": [255, 228, 196, 1],
        "black": [0, 0, 0, 1], "blanchedalmond": [255, 235, 205, 1],
        "blue": [0, 0, 255, 1], "blueviolet": [138, 43, 226, 1],
        # ...existing color definitions...
        "yellow": [255, 255, 0, 1], "yellowgreen": [154, 205, 50, 1]
    }

    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Clamp a value to ensure it lies within a specified range.
        :param value: The value to clamp.
        :param min_value: The minimum allowed value.
        :param max_value: The maximum allowed value.
        :return: The clamped value.
        """
        return max(min_value, min(value, max_value))

    @staticmethod
    def clamp_css_byte(i: float) -> int:
        """
        Clamp to integer 0 .. 255.
        """
        i = round(i)
        return max(0, min(255, i))

    @staticmethod
    def clamp_css_float(f: float) -> float:
        """
        Clamp to float 0.0 .. 1.0.
        """
        return max(0.0, min(1.0, f))

    @staticmethod
    def parse_css_int(value: str) -> int:
        """
        Parse int or percentage.
        """
        if value.endswith('%'):
            return Util.clamp_css_byte(float(value.strip('%')) / 100 * 255)
        return Util.clamp_css_byte(int(value))

    @staticmethod
    def parse_css_float(value: str) -> float:
        """
        Parse float or percentage.
        """
        if value.endswith('%'):
            return Util.clamp_css_float(float(value.strip('%')) / 100)
        return Util.clamp_css_float(float(value))

    @staticmethod
    def css_hue_to_rgb(m1: float, m2: float, h: float) -> float:
        """
        Convert hue to RGB.
        """
        if h < 0:
            h += 1
        elif h > 1:
            h -= 1

        if h * 6 < 1:
            return m1 + (m2 - m1) * h * 6
        if h * 2 < 1:
            return m2
        if h * 3 < 2:
            return m1 + (m2 - m1) * (2 / 3 - h) * 6
        return m1

    @staticmethod
    def parse_css_color(css_str: str) -> Optional[List[Union[int, float]]]:
        """
        Parse a CSS color string into RGBA components.
        """
        css_str = css_str.replace(" ", "").lower()

        # Color keywords (and transparent) lookup.
        if css_str in Util.kCSSColorTable:
            return Util.kCSSColorTable[css_str][:]

        # #abc and #abc123 syntax.
        if css_str.startswith('#'):
            if len(css_str) == 4:
                iv = int(css_str[1:], 16)
                return [
                    ((iv & 0xF00) >> 4) | ((iv & 0xF00) >> 8),
                    (iv & 0xF0) | ((iv & 0xF0) >> 4),
                    (iv & 0xF) | ((iv & 0xF) << 4),
                    1
                ]
            elif len(css_str) == 7:
                iv = int(css_str[1:], 16)
                return [
                    (iv & 0xFF0000) >> 16,
                    (iv & 0xFF00) >> 8,
                    iv & 0xFF,
                    1
                ]
            return None

        # Functional syntax (e.g., rgb(), rgba(), hsl(), hsla()).
        match = re.match(r'(rgba?|hsla?)\(([^)]+)\)', css_str)
        if match:
            fname, params = match.groups()
            params = params.split(',')
            alpha = 1.0
            if fname in ('rgba', 'hsla') and len(params) == 4:
                alpha = Util.parse_css_float(params.pop())
            if fname in ('rgb', 'rgba') and len(params) == 3:
                return [
                    Util.parse_css_int(params[0]),
                    Util.parse_css_int(params[1]),
                    Util.parse_css_int(params[2]),
                    alpha
                ]
            if fname in ('hsl', 'hsla') and len(params) == 3:
                h = (((float(params[0]) % 360) + 360) % 360) / 360
                s = Util.parse_css_float(params[1])
                l = Util.parse_css_float(params[2])
                m2 = l * (s + 1) if l <= 0.5 else l + s - l * s
                m1 = l * 2 - m2
                return [
                    Util.clamp_css_byte(Util.css_hue_to_rgb(m1, m2, h + 1 / 3) * 255),
                    Util.clamp_css_byte(Util.css_hue_to_rgb(m1, m2, h) * 255),
                    Util.clamp_css_byte(Util.css_hue_to_rgb(m1, m2, h - 1 / 3) * 255),
                    alpha
                ]
        return None
