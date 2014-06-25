from svg.path import parse_path, Path, Line, QuadraticBezier
import xml.etree.ElementTree as ET
import sys

preamble = "G21 G90 G94 G92 X0 Y0 Z0"
epilogue = "G0 Z0 M30"
def min_max_points(points):
    min_point = max_point = points[0]
    for point in points[1:]:
        min_point = min(min_point.real, point.real) + min(min_point.imag, point.imag) * 1j
        max_point = max(max_point.real, point.real) + max(max_point.imag, point.imag) * 1j
    return min_point, max_point

def segments(n, path):
    return [path.point(float(t) / n) for t in range(0, n)]

def path_bounds(path):
    steps = 100
    return min_max_points(segments(steps, path))

def bounding_box(paths):
    return min_max_points([point for path in paths for point in path_bounds(path)])

def gcode_move_to(x, y):
    return "G1 X{} Y{}".format(round(x, 5), round(y, 5))

def gcode_pen_up():
    return "G1 Z{}".format(0)

def gcode_pen_down():
    return "G1 Z{}".format(15)

def gcode_move_to_point(point, scale=1+1j, offset=0):
    return gcode_move_to((point.real + offset.real) * scale.real,
                         (point.imag + offset.imag) * scale.imag)
path_count = 0
current_path_num = 0
def gcodify_path(path, scale=1+1j, offset=0):
    global path_count, current_path_num
    current_path_num += 1
    sys.stderr.write("{}/{}\n".format(current_path_num, path_count))
    steps = max(int(round(path.length() * 10 * min(scale.imag, scale.real))), 5)
    points = segments(steps, path)
    return [
        gcode_pen_up(),
        gcode_move_to_point(points[0], scale, offset),
        gcode_pen_down(),
    ] + [gcode_move_to_point(point, scale, offset) for point in points]

def gcodify(paths, scale=1+1j, offset=0):
    global path_count
    path_count = len(paths)
    return (command for path in paths for command in gcodify_path(path, scale, offset))

def build_gcode(filename, desired_size):
    svg = ET.parse(filename)
    svg_tag = svg.getroot()
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    svg_paths = list(parse_path(path.attrib['d']) for path in paths)

    desired_size = desired_size
    try:
        size = float(svg_tag.attrib['width']) + float(svg_tag.attrib['height']) * 1j
    except Exception:
        zx, zy, x, y = svg_tag.attrib['viewBox'].split()
        size = float(x) + float(y) * 1j

    max_dimension = max(size.real, size.imag)
    scale = desired_size / max_dimension
    gcode = [preamble] + list(gcodify(svg_paths, scale + scale * 1j, -0.5 * size)) + [epilogue]
    return gcode

if __name__ == '__main__':
    print "\n".join(build_gcode(sys.argv[1], 100))
