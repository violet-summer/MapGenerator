# util.py
import random
import re

class Util:
    @staticmethod
    def random_range(max_val, min_val=0):
        return random.uniform(min_val, max_val)

    @staticmethod
    def clamp_css_byte(i):
        i = round(i)
        return max(0, min(255, i))

    @staticmethod
    def clamp_css_float(f):
        return max(0.0, min(1.0, f))

    @staticmethod
    def parse_css_int(s):
        if s.endswith('%'):
            return Util.clamp_css_byte(float(s[:-1]) / 100 * 255)
        return Util.clamp_css_byte(int(s))

    @staticmethod
    def parse_css_float(s):
        if s.endswith('%'):
            return Util.clamp_css_float(float(s[:-1]) / 100)
        return Util.clamp_css_float(float(s))

    @staticmethod
    def css_hue_to_rgb(m1, m2, h):
        if h < 0: h += 1
        elif h > 1: h -= 1
        if h * 6 < 1: return m1 + (m2 - m1) * h * 6
        if h * 2 < 1: return m2
        if h * 3 < 2: return m1 + (m2 - m1) * (2/3 - h) * 6
        return m1

    @staticmethod
    def parse_css_color(css_str):
        str_ = css_str.replace(' ', '').lower()
        css_color_table = {
            'black': [0,0,0,1], 'white': [255,255,255,1], 'red': [255,0,0,1], 'green': [0,128,0,1], 'blue': [0,0,255,1],
            'transparent': [0,0,0,0]
        }
        if str_ in css_color_table:
            return css_color_table[str_][:]
        if str_.startswith('#'):
            if len(str_) == 4:
                iv = int(str_[1:], 16)
                return [((iv & 0xf00) >> 4) | ((iv & 0xf00) >> 8), (iv & 0xf0) | ((iv & 0xf0) >> 4), (iv & 0xf) | ((iv & 0xf) << 4), 1]
            elif len(str_) == 7:
                iv = int(str_[1:], 16)
                return [(iv & 0xff0000) >> 16, (iv & 0xff00) >> 8, iv & 0xff, 1]
            return None
        m = re.match(r'(rgba?|hsla?)\(([^)]+)\)', str_)
        if m:
            fname, params = m.group(1), m.group(2).split(',')
            alpha = 1
            if fname in ('rgba', 'rgb'):
                if len(params) not in (3,4): return None
                if fname == 'rgba':
                    alpha = Util.parse_css_float(params.pop())
                return [Util.parse_css_int(params[0]), Util.parse_css_int(params[1]), Util.parse_css_int(params[2]), alpha]
        return None