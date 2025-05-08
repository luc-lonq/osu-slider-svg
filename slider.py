import svgwrite
import numpy as np
import math

class SliderPoint:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.anchor = False


class Slider:

    def __init__(self, slider_code):
        self.slider_points = []
        self.slider_type = None
        parts = slider_code.split(',')
        x0 = int(parts[0])
        y0 = int(parts[1])
        data = parts[5]
        points = data.split('|')
        self.slider_type = points.pop(0)
        prev_x, prev_y = None, None
        self.slider_points.append(SliderPoint(0, 0))
        for point in points:
            x, y = point.split(':')
            if prev_x == x and prev_y == y:
                self.slider_points[-1].anchor = True
            else:
                prev_x = x
                prev_y = y
                x = int(x)
                y = int(y)
                self.slider_points.append(SliderPoint(x - x0, y - y0))

        self.ajust_points_coordinates()
        print(f"Slider Type: {self.slider_type}")
        self.print_points()
        self.svg()

    # Adjusts the coordinates of the points to ensure all points are positive
    def ajust_points_coordinates(self):
        min_x = min(p.x for p in self.slider_points)
        min_y = min(p.y for p in self.slider_points)
        if min_x < 0:
            for point in self.slider_points:
                point.x -= min_x
        if min_y < 0:
            for point in self.slider_points:
                point.y -= min_y


    def print_points(self):
        for point in self.slider_points:
            print(f"Point: ({point.x}, {point.y}), Anchor: {point.anchor}")


    def svg(self, filename="slider_path.svg", show_path=False):

        def draw_bezier_curve(dwg, control_points, translate_fn, radius=32, color="white", show_path=False):
            if len(control_points) < 2:
                return
            curve_pts = bezier_curve(control_points, num_points=50)
            translated = [translate_fn(x, y) for x, y in curve_pts]
            if show_path:
                path = dwg.path(d=f"M {translated[0][0]},{translated[0][1]}", stroke="blue", fill="none", stroke_width=2)
            for x, y in translated[1:]:
                if show_path:
                    path.push(f"L {x},{y}")
                dwg.add(dwg.circle(center=(x, y), r=radius, fill=color, fill_opacity=1, stroke="none"))
            if show_path:
                dwg.add(path)

        
        def draw_segment(dwg, p1, p2, translate_fn, radius=32, steps=50, color="white", show_path=False):
            for i in range(steps + 1):
                t = i / steps
                x = p1.x * (1 - t) + p2.x * t
                y = p1.y * (1 - t) + p2.y * t
                cx, cy = translate_fn(x, y)
                dwg.add(dwg.circle(center=(cx, cy), r=radius, fill=color, fill_opacity=1, stroke="none"))

            if show_path:
                x1, y1 = translate_fn(p1.x, p1.y)
                x2, y2 = translate_fn(p2.x, p2.y)
                dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="green", stroke_width=2))


        def draw_point(dwg, point, index, translate_fn):
            x, y = translate_fn(point.x, point.y)
            color = "red" if point.anchor else "white"
            dwg.add(dwg.circle(center=(x, y), r=3, fill=color))
            dwg.add(dwg.text(str(index), insert=(x + 5, y - 5), font_size="10px", fill="gray"))


        # Calculates the Bernstein polynomial for Bezier curves
        def bernstein(i, n, t):
            return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))


        # Generates the Bezier curve points based on slider points
        def bezier_curve(slider_points, num_points=100):
            n = len(slider_points) - 1
            t_values = np.linspace(0, 1, num_points)
            curve = np.zeros((num_points, 2))
            for i, p in enumerate(slider_points):
                b = bernstein(i, n, t_values)
                curve[:, 0] += b * p.x
                curve[:, 1] += b * p.y
            return curve


        all_points = self.slider_points
        bezier_seqs = self.get_bezier_sequences()
        line_segs = self.get_segments()

        all_x = [p.x for p in all_points]
        all_y = [p.y for p in all_points]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        padding = 50
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        dwg = svgwrite.Drawing(filename, size=(width, height))

        def translate(x, y):
            return (x - min_x + padding, y - min_y + padding)

        for seq in bezier_seqs:
            draw_bezier_curve(dwg, seq, translate)

        for p1, p2 in line_segs:
            draw_segment(dwg, p1, p2, translate)

        for seq in bezier_seqs:
            draw_bezier_curve(dwg, seq, translate, radius=30, color="black")

        for p1, p2 in line_segs:
            draw_segment(dwg, p1, p2, translate, radius=30, color="black")

        if show_path:
            for i, point in enumerate(self.slider_points):
                draw_point(dwg, point, i, translate)

        dwg.save()
        print(f"SVG saved as {filename}")
    

    # Gets all the Bezier sequences in the slider
    def get_bezier_sequences(self):
        sequences = []
        current_sequence = []
        for point in self.slider_points:
            if point.anchor and current_sequence and current_sequence[-1].anchor:
                if current_sequence and len(current_sequence) > 2:
                    sequences.append(current_sequence)
                current_sequence = [point]
            else:
                current_sequence.append(point)
        if current_sequence:
            sequences.append(current_sequence)
        return sequences


    # Gets all the linear segments in the slider
    def get_segments(self):
        segments = []
        prev_point = None
        for point in self.slider_points:
            if point.anchor and prev_point and prev_point.anchor:
                segments.append([prev_point, point])
            prev_point = point
        return segments
