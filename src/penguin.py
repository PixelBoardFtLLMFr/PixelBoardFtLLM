import PIL.Image, PIL.ImageDraw
import numpy as np
import utils

black  = (0,   0,   0)
white  = (10, 10, 10)
orange = (255, 125, 0)
green  = (0, 255, 130)
yellow = (255, 222, 40)
blue   = (50, 50, 255)

def _rotate_point(x, y, cx, cy, angle):
    """
    Rotate point (X, Y) by ANGLE from (CX, CY).
    GPT-generated function.
    """
    radians = np.radians(angle)
    cos_angle = np.cos(radians)
    sin_angle = np.sin(radians)

    tx = x - cx
    ty = y - cy

    rx = tx * cos_angle - ty * sin_angle
    ry = tx * sin_angle + ty * cos_angle

    return rx + cx, ry + cy

def _draw_rotated_rectangle(draw, x1, y1, x2, y2, cx, cy, angle, fill):
    """
    GPT-generated function.
    """
    corners = [
        (x1, y1),
        (x1, y2),
        (x2, y2),
        (x2, y1),
    ]
    rotated_corners = [_rotate_point(x, y, cx, cy, angle) for x, y in corners]
    draw.polygon(rotated_corners, fill=fill)

def _draw_rotated_circle(draw, x1, y1, r, cx, cy, angle, fill, outline = None):
    x2, y2 = _rotate_point(x1 + r, y1 + r, cx, cy, angle)
    draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=fill, outline=outline)

def _draw_true_rotated_ellipse(image, x1, y1, x2, y2, cx, cy, angle, fill):
    ellipse = PIL.Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(ellipse)
    box = (x1, y1, x2, y2)
    draw.ellipse(box, fill)
    ellipse = ellipse.rotate(angle, expand=False, center=(cx, cy))
    image.paste(ellipse, (0, 0), ellipse)

class Penguin:
    facial_expressions = [
        "neutral",
        "happy",
        "sad"
    ]

    def __init__(self, size):
        self.set_size(size)
        self.image = PIL.Image.new("RGB", (self.size, self.size), "black")
        self.draw = PIL.ImageDraw.Draw(self.image)

        self.angle_right_arm  = None
        self.angle_left_arm   = None
        self.angle_right_foot = None
        self.angle_left_foot  = None
        self.angle_head       = None
        self.fe = "neutral"

    def set_size(self, new_size):
        self.size = new_size
        
        self.body_width   = int(self.size * 0.4)
        self.body_height  = int(self.size * 0.4)
        self.head_size    = int(self.size * 0.5)
        self.eye_size     = int(self.size * 0.1)
        self.eye_x_offset = int(self.head_size * 0.3)
        self.eye_y_offset = int(self.head_size * 0.7)
        self.beak_size    = int(self.size * 0.15)
        self.foot_width   = int(self.size * 0.15)
        self.foot_height  = int(self.size * 0.1)
        self.arm_width    = int(self.size * 0.1)
        self.arm_height   = int(self.size * 0.4)

        self.body_x = (self.size - self.body_width)  // 2
        self.body_y = self.size // 2
        self.head_x = self.body_x + (self.body_width - self.head_size) // 2
        self.head_y = self.body_y - self.head_size
        self.foot_y = self.body_y + self.body_height
        self.arm_y  = self.body_y

        self.head_cx = self.head_x + self.head_size // 2
        self.head_cy = self.head_y + self.head_size

        self.eye_left_x = round(self.head_cx - self.eye_x_offset)
        self.eye_y = self.head_cy - self.eye_y_offset
        self.eye_right_x = round(self.head_cx + self.eye_x_offset)
        self.eye_points = [(self.eye_left_x, self.eye_y),
                           (self.eye_right_x, self.eye_y)]

        self.beak_x1 = self.head_cx - 3*self.beak_size // 4
        self.beak_x2 = self.head_cx + 3*self.beak_size // 4
        self.beak_x3 = self.head_cx
        self.beak_y1 = self.head_cy - self.head_size // 3
        self.beak_y2 = self.beak_y1
        self.beak_y3 = self.beak_y1 + self.beak_size

        self.dx = min(1, self.body_width * 0.1)
        self.dy = min(1, self.body_width * 0.1)

    def set_fe(self, new_fe):
        if new_fe in self.facial_expressions:
            self.fe = new_fe
        else:
            utils.debug("warning: attempted to give penguin illegal "
                        + "facial expression:",
                        new_fe)
        
    def _reset_image(self):
        self.draw.rectangle([0, 0, self.size - 1, self.size - 1], fill=black)

    def _draw_body(self):
        self.draw.rectangle([self.body_x,
                             self.body_y,
                             self.body_x + self.body_width,
                             self.body_y + self.body_height],
                            fill=green)

        self.draw.rectangle([self.body_x + self.dx,
                             self.body_y + self.dy,
                             self.body_x + self.body_width  - self.dx,
                             self.body_y + self.body_height - self.dy],
                            fill=white)
        

    def _rotate_head_point(self, x, y):
        return _rotate_point(x, y, self.head_cx, self.head_cy, self.head_angle)

    def _draw_head(self, angle):
        self.head_angle = angle
        _draw_rotated_circle(self.draw,
                             self.head_x, self.head_y,
                             self.head_size // 2,
                             self.head_cx, self.head_cy,
                             self.head_angle,
                             fill=white,
                             outline=green)

        if self.fe == "neutral":
            # Vertical Eyes (| _ |)
            for point in self.eye_points:
                x1, y1 = self._rotate_head_point(point[0], point[1])
                x2, y2 = self._rotate_head_point(point[0], point[1] + self.eye_size)

                self.draw.line([x1, y1, x2, y2], fill=yellow)
        elif self.fe == "sad":
            # Horizontal Eyes (- _ -)
            for point in self.eye_points:
                # Tear
                x1, y1 = self._rotate_head_point(point[0], point[1] + 1)
                x2, y2 = self._rotate_head_point(point[0] + self.eye_size//2, point[1] + 1)

                self.draw.line([x1, y1, x1, y2], fill=blue)
                # Eye
                x1, y1 = self._rotate_head_point(point[0] - self.eye_size//2, point[1])
                x2, y2 = self._rotate_head_point(point[0] + self.eye_size//2, point[1])

                self.draw.line([x1, y1, x2, y2], fill=yellow)
        elif self.fe == "happy":
            # Half-circle Eyes (^ _ ^)
            #         (x0, y0)
            #        /        \
            # (x1, y1)       (x2, y2)
            for point in self.eye_points:
                x0, y0 = self._rotate_head_point(point[0], point[1])
                x1, y1 = self._rotate_head_point(point[0] - self.eye_size//2, point[1] + self.eye_size//2)
                x2, y2 = self._rotate_head_point(point[0] + self.eye_size//2, point[1] + self.eye_size//2)

                self.draw.line([x1, y1, x0, y0], fill=yellow)
                self.draw.line([x0, y0, x2, y2], fill=yellow)

        beak_x1, beak_y1 = self._rotate_head_point(self.beak_x1, self.beak_y1)
        beak_x2, beak_y2 = self._rotate_head_point(self.beak_x2, self.beak_y2)
        beak_x3, beak_y3 = self._rotate_head_point(self.beak_x3, self.beak_y3)

        self.draw.polygon([(beak_x1, beak_y1),
                           (beak_x2, beak_y2),
                           (beak_x3, beak_y3)],
                          fill=orange)
        
        self.draw.rectangle([self.body_x + 2*self.dx + 1,
                             self.body_y - self.dy,
                             self.body_x + self.body_width - 2*self.dx - 1,
                             self.body_y],
                             fill = black)

    def _draw_arms(self, angle_right, angle_left):
        self.angle_left_arm = angle_left

        arm_left_x1 = self.body_x - self.arm_width
        arm_left_y1 = self.arm_y
        arm_left_x2 = arm_left_x1 + self.arm_width
        arm_left_y2 = arm_left_y1 + self.arm_height

        arm_center_left_x = (arm_left_x1 + arm_left_x2) // 2
        arm_center_left_y = arm_left_y1

        _draw_true_rotated_ellipse(self.image,
                                   arm_left_x1, arm_left_y1,
                                   arm_left_x2, arm_left_y2,
                                   arm_center_left_x, arm_center_left_y,
                                   self.angle_left_arm,
                                   fill=green)

        self.angle_right_arm = angle_right

        arm_right_x1 = self.body_x + self.body_width
        arm_right_y1 = self.arm_y
        arm_right_x2 = arm_right_x1 + self.arm_width
        arm_right_y2 = arm_right_y1 + self.arm_height

        arm_center_right_x = (arm_right_x1 + arm_right_x2) // 2
        arm_center_right_y = arm_right_y1

        _draw_true_rotated_ellipse(self.image,
                                   arm_right_x1, arm_right_y1,
                                   arm_right_x2, arm_right_y2,
                                   arm_center_right_x, arm_center_right_y,
                                   self.angle_right_arm,
                                   fill=green)

    def _draw_feet(self, angle_right, angle_left):
        self.angle_left_foot = angle_left

        foot_left_x1 = self.body_x
        foot_left_y1 = self.foot_y
        foot_left_x2 = foot_left_x1 + self.foot_width
        foot_left_y2 = foot_left_y1 + self.foot_height

        _draw_rotated_rectangle(self.draw,
                                foot_left_x1, foot_left_y1,
                                foot_left_x2, foot_left_y2,
                                foot_left_x1, foot_left_y1,
                                self.angle_left_foot,
                                fill=orange)

        self.angle_right_foot = angle_right

        foot_right_x1 = self.body_x + self.body_width - self.foot_width
        foot_right_y1 = self.foot_y
        foot_right_x2 = foot_right_x1 + self.foot_width
        foot_right_y2 = foot_right_y1 + self.foot_height

        _draw_rotated_rectangle(self.draw,
                                foot_right_x1, foot_right_y1,
                                foot_right_x2, foot_right_y2,
                                foot_right_x1 + self.foot_width, foot_right_y1,
                                self.angle_right_foot,
                                fill=orange)

    def get_pixels(self):
        """
        Return the pixel matrix of the drawn penguin as an array of arrays. Each
        pixel is a tuple of integers (R, G, B).
        """
        # return self.image.getdata()
        return [[self.image.getpixel((j, i))
                 for j in range(self.size)]
                for i in range(self.size)]

    def do_draw(self,
                angle_right_arm, angle_left_arm,
                angle_right_foot, angle_left_foot,
                angle_head):
        """
        Draw the penguin with the given angles. Sadly, calling this method
        'draw' causes an error. Return the computed matrix of pixels.
        """
        self._reset_image()
        self._draw_body()
        self._draw_head(angle_head)
        self._draw_arms(angle_right_arm, angle_left_arm)
        self._draw_feet(angle_right_foot, angle_left_foot)
        return self.get_pixels()
