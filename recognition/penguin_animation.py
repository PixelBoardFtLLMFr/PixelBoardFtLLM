import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import math
import gpt_api
import ast

def rotate_point(x, y, cx, cy, angle):
    radians = math.radians(angle)
    cos_angle = math.cos(radians)
    sin_angle = math.sin(radians)

    tx = x - cx
    ty = y - cy

    rx = tx * cos_angle - ty * sin_angle
    ry = tx * sin_angle + ty * cos_angle

    return rx + cx, ry + cy

def draw_rotated_rectangle(draw, x1, y1, x2, y2, cx, cy, angle, fill):
    corners = [
        (x1, y1),
        (x1, y2),
        (x2, y2),
        (x2, y1),
    ]
    rotated_corners = [rotate_point(x, y, cx, cy, angle) for x, y in corners]
    draw.polygon(rotated_corners, fill=fill)

def draw_rotated_ellipse(draw, x1, y1, r, cx, cy, angle, fill, outline=None):
    x2, y2 = rotate_point(x1 + r, y1 + r, cx, cy, angle)
    draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=fill, outline=outline)


def draw_penguin_with_arm(image, angle_left_arm, angle_right_arm, angle_left_foot, angle_right_foot, angle_head):
    draw = ImageDraw.Draw(image)

    black = (0, 0, 0)
    white = (255, 255, 255)
    orange = (255, 165, 0)

    body_width, body_height = 60, 100
    body_x, body_y = (width - body_width) // 2, (height - body_height) // 2

    head_size = 40
    head_x, head_y = body_x + (body_width - head_size) // 2, body_y - head_size

    eye_size = 5
    eye_y_offset = 10
    eye_x_offset = 10

    foot_width, foot_height = 20, 10
    foot_y = body_y + body_height

    arm_width, arm_height = 10, 40
    arm_y = body_y + 20

    draw.rectangle([body_x, body_y, body_x + body_width, body_y + body_height], fill=white, outline=black)

    head_cx = head_x + head_size // 2
    head_cy = head_y + head_size
    draw_rotated_ellipse(draw, head_x, head_y, head_size//2, head_cx, head_cy, angle_head, fill=white, outline=black)

    eye_left_x = head_cx - eye_x_offset
    eye_left_y = head_cy - 3*eye_y_offset
    eye_right_x = head_cx + eye_x_offset
    eye_right_y = eye_left_y
    draw_rotated_ellipse(draw, eye_left_x, eye_left_y, eye_size//2, head_cx, head_cy, angle_head, fill=black)
    draw_rotated_ellipse(draw, eye_right_x, eye_right_y, eye_size//2, head_cx, head_cy, angle_head, fill=black)

    beak_width, beak_height = 10, 8
    beak_x, beak_y = head_x + (head_size - beak_width) // 2, head_y + head_size // 2
    # Rotation
    beak_x0, beak_y0 = rotate_point(beak_x, beak_y, head_cx, head_cy, angle_head)
    beak_x1, beak_y1 = rotate_point(beak_x + beak_width, beak_y, head_cx, head_cy, angle_head)
    beak_x2, beak_y2 = rotate_point(beak_x + beak_width // 2, beak_y + beak_height, head_cx, head_cy, angle_head)
    draw.polygon([(beak_x0, beak_y0), (beak_x1, beak_y1), (beak_x2, beak_y2)], fill=orange)

    foot_left_x = body_x
    foot_right_x = body_x + body_width - foot_width
    draw_rotated_rectangle(draw, foot_left_x, foot_y, foot_left_x + foot_width, foot_y + foot_height, foot_left_x, foot_y, angle_left_foot, fill=orange)
    draw_rotated_rectangle(draw, foot_right_x, foot_y, foot_right_x + foot_width, foot_y + foot_height, foot_right_x + foot_width, foot_y, angle_right_foot, fill=orange)

    arm_left_x1 = body_x - arm_width
    arm_left_y1 = arm_y
    arm_left_x2 = arm_left_x1 + arm_width
    arm_left_y2 = arm_y + arm_height
    arm_center_left_x, arm_center_left_y = (arm_left_x1 + arm_left_x2) / 2, arm_left_y1

    draw_rotated_rectangle(draw, arm_left_x1, arm_left_y1, arm_left_x2, arm_left_y2, arm_center_left_x, arm_center_left_y, angle_left_arm, fill=black)

    arm_right_x1 = body_x + body_width
    arm_right_y1 = arm_y
    arm_right_x2 = arm_right_x1 + arm_width
    arm_right_y2 = arm_y + arm_height
    arm_center_right_x, arm_center_right_y = (arm_right_x1 + arm_right_x2) / 2, arm_right_y1

    draw_rotated_rectangle(draw, arm_right_x1, arm_right_y1, arm_right_x2, arm_right_y2, arm_center_right_x, arm_center_right_y, angle_right_arm, fill=black)

    return image

def update_image():
    global frame_index, angles, root
    frame_index += 1

    if frame_index >= len(angles):
        prompt = input("What should I do next ? ")
        if prompt == "quit":
            root.quit()
            return
        response = gpt_api.get_angle_from_prompt(prompt)
        try:
            angles = ast.literal_eval(response)
        except SyntaxError:
            print(f"GPT returned an invalid synthax : {response}")
        frame_index = 0


    angle_left_arm, angle_right_arm, angle_left_foot, angle_right_foot, angle_head = angles[frame_index]

    image = Image.new("RGB", (width, height), "white")
    image = draw_penguin_with_arm(image, angle_left_arm, angle_right_arm, angle_left_foot, angle_right_foot, angle_head)

    tk_image = ImageTk.PhotoImage(image)
    canvas.itemconfig(image_on_canvas, image=tk_image)
    canvas.image = tk_image

    root.after(50, update_image)

width, height = 200, 300

angles = [
    (0, 0, 0, 0, 0),
    (10, -10, 5, -5, 5),
    (20, -20, 10, -5, 10),
    (30, -30, 15, 0, 15),
    (40, -40, 10, 0, 20),
    (50, -50, 5, 0, 25),
    (60, -60, 0, 0, 30),
    (50, -50, 0, 0, 25),
    (40, -40, 0, 0, 20),
    (30, -30, 0, 0, 15),
    (20, -20, 0, 0, 10),
    (10, -10, 0, 0, 5),
    (0, 0, 0, 0, 0),
]

# angles = [
#     (0, 0, 0, 0, 0),
#     (10, -10, 0, 0, 0),
#     (20, -20, 0, 0, 0),
#     (30, -30, 0, 0, 0),
#     (20, -20, 0, 0, 0),
#     (10, -10, 0, 0, 0),
#     (0, 0, 0, 0, 0),
#     (-10, 10, 0, 0, 0),
#     (-20, 20, 0, 0, 0),
#     (-30, 30, 0, 0, 0),
#     (-20, 20, 0, 0, 0),
#     (-10, 10, 0, 0, 0),
#     (0, 0, 0, 0, 0),
# ]

# angles = [
#     (0, 0),
#     (5, -5),
#     (10, -10),
#     (15, -15),
#     (20, -20),
#     (25, -25),
#     (30, -30),
#     (35, -35),
#     (40, -40),
#     (35, -35),
#     (30, -30),
#     (25, -25),
#     (20, -20),
#     (15, -15),
#     (10, -10),
#     (5, -5),
#     (0, 0),
#     (-5, 5),
#     (-10, 10),
#     (-15, 15),
#     (-20, 20),
#     (-25, 25),
#     (-30, 30),
#     (-35, 35),
#     (-40, 40),
#     (-35, 35),
#     (-30, 30),
#     (-25, 25),
#     (-20, 20),
#     (-15, 15),
#     (-10, 10),
#     (-5, 5),
#     (0, 0),
# ]

# rx, ry = rotate_point(20, 10, 10, 10, -90)
# print("rotate_point(20, 10, 10, 10, 90) =", rx, ",", ry)
# exit(0)



frame_index = 0

# Créer la fenêtre tkinter
root = tk.Tk()
canvas = tk.Canvas(root, width=width, height=height)
canvas.pack()

# Initialiser l'image
image = Image.new("RGB", (width, height), "white")
image = draw_penguin_with_arm(image, angles[0][0], angles[0][1], angles[0][2], angles[0][3], angles[0][4])

tk_image = ImageTk.PhotoImage(image)
image_on_canvas = canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
canvas.image = tk_image

# Démarrer l'animation
root.after(50, update_image)

# Lancer la boucle principale de tkinter
root.mainloop()
