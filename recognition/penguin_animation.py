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

def draw_penguin_with_arm(image, angle_left_arm, angle_right_arm):
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

    beak_width, beak_height = 10, 8
    beak_x, beak_y = head_x + (head_size - beak_width) // 2, head_y + head_size // 2

    foot_width, foot_height = 20, 10
    foot_y = body_y + body_height

    arm_width, arm_height = 10, 40
    arm_y = body_y + 20

    draw.rectangle([body_x, body_y, body_x + body_width, body_y + body_height], fill=white, outline=black)
    draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], fill=white, outline=black)

    eye_left_x = head_x + eye_x_offset
    eye_right_x = head_x + head_size - eye_x_offset - eye_size
    eye_y = head_y + eye_y_offset
    draw.ellipse([eye_left_x, eye_y, eye_left_x + eye_size, eye_y + eye_size], fill=black)
    draw.ellipse([eye_right_x, eye_y, eye_right_x + eye_size, eye_y + eye_size], fill=black)

    draw.polygon([(beak_x, beak_y), (beak_x + beak_width, beak_y), (beak_x + beak_width // 2, beak_y + beak_height)], fill=orange)

    foot_left_x = body_x
    foot_right_x = body_x + body_width - foot_width
    draw.rectangle([foot_left_x, foot_y, foot_left_x + foot_width, foot_y + foot_height], fill=orange, outline=black)
    draw.rectangle([foot_right_x, foot_y, foot_right_x + foot_width, foot_y + foot_height], fill=orange, outline=black)

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


    angle_left_arm, angle_right_arm = angles[frame_index]

    image = Image.new("RGB", (width, height), "white")
    image = draw_penguin_with_arm(image, angle_left_arm, angle_right_arm)

    tk_image = ImageTk.PhotoImage(image)
    canvas.itemconfig(image_on_canvas, image=tk_image)
    canvas.image = tk_image

    root.after(50, update_image)

width, height = 200, 300

angles = [
    (0, 0),
]




frame_index = 0

# Créer la fenêtre tkinter
root = tk.Tk()
canvas = tk.Canvas(root, width=width, height=height)
canvas.pack()

# Initialiser l'image
image = Image.new("RGB", (width, height), "white")
image = draw_penguin_with_arm(image, angles[0][0], angles[0][1])

tk_image = ImageTk.PhotoImage(image)
image_on_canvas = canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
canvas.image = tk_image

# Démarrer l'animation
root.after(50, update_image)

# Lancer la boucle principale de tkinter
root.mainloop()
