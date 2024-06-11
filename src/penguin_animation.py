import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import math
import gpt_api
import os

particles = None

def load_particles(particles_folder_path):
    image_dict = {}
    for filename in os.listdir(particles_folder_path):
        if filename.endswith('.png'):
            file_path = os.path.join(particles_folder_path, filename)
            image_name = os.path.splitext(filename)[0]
            image = Image.open(file_path)
            image_dict[image_name] = image
    return image_dict

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



def draw_rotated_ellipse(draw, x1, y1, r, cx, cy, angle, fill, outline = None):
    x2, y2 = rotate_point(x1 + r, y1 + r, cx, cy, angle)
    draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=fill, outline=outline)

def draw_true_rotated_ellipse(image : Image, x1, y1, x2, y2, cx, cy, angle, fill):
    ellipse = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ellipse)
    box = (x1, y1, x2, y2)
    draw.ellipse(box, fill)
    ellipse = ellipse.rotate(angle, expand=False, center=(cx, cy))
    image.paste(ellipse, (0, 0), ellipse)

def draw_penguin_with_arm(image, angles, size):
    draw = ImageDraw.Draw(image)

    angle_left_arm, angle_right_arm, angle_left_foot, angle_right_foot, angle_head = angles

    penguin_height, penguin_width = size, size

    black = (0, 0, 0)
    white = (200, 200, 200)
    orange = (255, 165, 0)
    blue = (0,0,255)

    #Oscar colors
    green = (169-100,218,195-100)
    yellow = (250,222,12)

    body_width, body_height = penguin_width * 0.4, penguin_height * 0.6
    head_size = body_height * 0.4

    body_x, body_y = (penguin_width - body_width) // 2, (penguin_height - body_height) // 2 + head_size // 2
    head_x, head_y = body_x + (body_width - head_size) // 2, body_y - head_size

    eye_size = body_height * 0.05
    eye_y_offset = body_height * 0.1
    eye_x_offset = body_height * 0.1

    foot_width, foot_height = body_height * 0.2, body_height * 0.1
    foot_y = body_y + body_height

    arm_width, arm_height = body_height * 0.1, body_height * 0.6
    arm_y = body_y + body_height * 0.2
    arm_inside_width, arm_inside_height = arm_width * 0.6, arm_height * 0.6

    draw.rectangle([body_x, body_y, body_x + body_width, body_y + body_height], fill=green)
    draw.rectangle([body_x + 0.1*body_width, body_y+0.1*body_height, body_x + body_width*0.9, body_y + body_height*0.9], fill=white)


    head_cx = head_x + head_size // 2
    head_cy = head_y + head_size
    draw_rotated_ellipse(draw, head_x, head_y, head_size//2, head_cx, head_cy, angle_head, fill=white, outline= green)

    eye_left_x = round(head_cx - eye_x_offset)
    eye_left_y = head_cy - 3 * eye_y_offset
    eye_right_x = round(head_cx + eye_x_offset)
    eye_right_y = eye_left_y
    draw.line([rotate_point(eye_left_x, eye_left_y, head_cx, head_cy, angle_head),
               rotate_point(eye_left_x, eye_left_y + eye_size, head_cx, head_cy, angle_head)], fill=blue)
    draw.line([rotate_point(eye_right_x, eye_right_y, head_cx, head_cy, angle_head),
               rotate_point(eye_right_x, eye_right_y + eye_size, head_cx, head_cy, angle_head)], fill=blue)

    beak_width, beak_height = body_height * 0.1, body_height * 0.08
    beak_x, beak_y = round(head_x + (head_size - beak_width) / 2), head_y + head_size // 2

    # Rotation
    beak_x0, beak_y0 = rotate_point(beak_x, beak_y, head_cx, head_cy, angle_head)
    beak_x1, beak_y1 = rotate_point(beak_x + beak_width, beak_y, head_cx, head_cy, angle_head)
    beak_x2, beak_y2 = rotate_point(beak_x + beak_width // 2, beak_y + beak_height, head_cx, head_cy, angle_head)
    draw.polygon([(beak_x0, beak_y0), (beak_x1, beak_y1), (beak_x2, beak_y2)], fill=yellow)

    foot_left_x = body_x
    foot_right_x = body_x + body_width - foot_width
    draw_rotated_rectangle(draw, foot_left_x, foot_y, foot_left_x + foot_width, foot_y + foot_height, foot_left_x, foot_y, angle_left_foot, fill=yellow)
    draw_rotated_rectangle(draw, foot_right_x, foot_y, foot_right_x + foot_width, foot_y + foot_height, foot_right_x + foot_width, foot_y, angle_right_foot, fill=yellow)

    # Left arm
    arm_left_x1 = body_x - arm_width
    arm_left_y1 = arm_y
    arm_left_x2 = arm_left_x1 + arm_width
    arm_left_y2 = arm_y + arm_height
    arm_center_left_x, arm_center_left_y = (arm_left_x1 + arm_left_x2)/2 , arm_left_y1

    arm_inside_left_x1, arm_inside_left_x2 = arm_center_left_x - round(arm_inside_width / 2), arm_center_left_x + round(arm_inside_width / 2)

    draw_true_rotated_ellipse(image, arm_left_x1, arm_left_y1, arm_left_x2, arm_left_y2, arm_center_left_x, arm_center_left_y, -angle_left_arm, fill=green)
    #draw_true_rotated_ellipse(image, arm_inside_left_x1, arm_left_y1, arm_inside_left_x2, arm_left_y1 + arm_inside_height, arm_center_left_x, arm_center_left_y, angle_left_arm, white)

    # Right arm
    arm_right_x1 = body_x + body_width
    arm_right_y1 = arm_y
    arm_right_x2 = arm_right_x1 + arm_width
    arm_right_y2 = arm_y + arm_height
    arm_center_right_x, arm_center_right_y = (arm_right_x1 + arm_right_x2) / 2, arm_right_y1

    draw_true_rotated_ellipse(image, arm_right_x1, arm_right_y1, arm_right_x2, arm_right_y2, arm_center_right_x, arm_center_right_y, angle_right_arm, fill=green)

    return image

def add_particle(image : Image, particle, position):
    scale = 1
    global particles
    if particles == None:
        particles = load_particles("particles")
    if particle not in particles:
        return image
    particle_im = particles[particle].copy()
    image.paste(particle_im, position, particle_im)
    return image

def update_image():
    global frame_index, angles, root
    frame_index += 1

    if frame_index >= len(angles):
        prompt = input("What should I do next ? ")
        if prompt == "quit":
            root.quit()
            return
        angles = gpt_api.get_angle_from_prompt(prompt)
        #particle = gpt_api.get_particle_from_prompt(prompt)
        frame_index = 0


    penguin_image = Image.new("RGB", (penguin_width, penguin_height), "white")
    penguin_image = draw_penguin_with_arm(penguin_image, angles[frame_index], penguin_size)

    tk_penguin_image = ImageTk.PhotoImage(penguin_image)
    penguin_canvas.itemconfig(penguin_image_on_canvas, image=tk_penguin_image)
    penguin_canvas.image = tk_penguin_image

    update_pixel_board_canvas(penguin_image)

    root.after(50, update_image)


def update_pixel_board_canvas(penguin_image):
    pixel_board_image = Image.new("RGB", (pixel_board_size, pixel_board_size), "white")
    pixel_board_draw = ImageDraw.Draw(pixel_board_image)

    for i in range(penguin_height):
        for j in range(penguin_width):
            pixel = penguin_image.getpixel((i, j))
            pixel_board_draw.rectangle([(pixel_board_scale*i, pixel_board_scale*j),
                                        (pixel_board_scale*(i+1/2), pixel_board_scale*(j+1/2))], fill=pixel)

    tk_pixel_board_image = ImageTk.PhotoImage(pixel_board_image)
    pixel_board_canvas.itemconfig(pixel_board_image_on_canvas, image=tk_pixel_board_image)
    pixel_board_canvas.image = tk_pixel_board_image

if __name__ == "__main__":
    penguin_size = 25
    penguin_height, penguin_width = penguin_size, penguin_size
    pixel_board_scale = 8
    pixel_board_size = pixel_board_scale * penguin_size

    angles = [
        (0, 0, 0, 0, 0)
    ]

    frame_index = 0

    # Create the tkinter window
    root = tk.Tk()
    penguin_canvas = tk.Canvas(root, width=penguin_width, height=penguin_height)
    penguin_canvas.pack(side='left')

    pixel_board_canvas = tk.Canvas(root, width=pixel_board_size, height=pixel_board_size)
    pixel_board_canvas.pack(side='right')

    # Initialize the images
    penguin_image = Image.new("RGB", (penguin_width, penguin_height), "white")
    penguin_image = draw_penguin_with_arm(penguin_image, angles[0], penguin_size)

    tk_penguin_image = ImageTk.PhotoImage(penguin_image)
    penguin_image_on_canvas = penguin_canvas.create_image(0, 0, anchor=tk.NW, image=tk_penguin_image)
    penguin_canvas.image = tk_penguin_image

    pixel_board_image = Image.new("RGB", (pixel_board_size, pixel_board_size), "white")
    tk_pixel_board_image = ImageTk.PhotoImage(pixel_board_image)
    pixel_board_image_on_canvas = pixel_board_canvas.create_image(0, 0, anchor=tk.NW, image=tk_pixel_board_image)
    pixel_board_canvas.image = tk_pixel_board_image
    update_pixel_board_canvas(penguin_image)

    # Start the animation
    root.after(50, update_image)

    # Launch the main tkinter loop
    root.mainloop()
