from time import sleep
import serial
import penguin_animation
from PIL import Image
import gpt_api

def image_to_serial(image : Image):
    width, height = image.size
    output = ""
    for y in range(height):
        for x in range(width):
            output += f"{position_to_index(x, y)},{rgb_to_hex(image.getpixel((x, y-1)))}\n"
    return output

def rgb_to_hex(rgb):
    r, g, b = rgb
    # Vérifie si les valeurs sont dans la plage correcte
    if (0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255):
        return f'#{r:02x}{g:02x}{b:02x}'
    else:
        print(r, g, b)
        raise ValueError("Les valeurs RGB doivent être comprises entre 0 et 255")

def position_to_index(x, y = None):
    if y == None:
        x, y = x
    board_matrix = [[0, 9, 10, 15, 20],
                    [1, 8, 11, 16, 21],
                    [2, 7, 12, 17, 22],
                    [3, 6, 13, 18, 23],
                    [4, 5, 14, 19, 24]]
    led_matrix = [[15, 10, 5, 0],
                  [16, 11, 6, 1],
                  [17, 12, 7, 2],
                  [18, 13, 8, 3],
                  [19, 14, 9, 4]]
    board_index = board_matrix[y // 5][x // 4]
    led_index = led_matrix[y % 5][x % 4]
    return board_index * 20 + led_index

def gradiant_serial():
    output = ""
    for y in range(15):
        for x in range(12):
            color = int(((y * 12 + x) / (15 * 12)) * 255)
            output += f"{y*12 + x},{rgb_to_hex(((color),)*3)}\n"
    return output

def clear_serial():
    output = ""
    for i in range(20):
        output += f"{i},#000000\n"
    return output

def send_to_serial(ser, serial_str):
    ser.write(serial_str.encode("ascii"))

def all_colours(ser):
    index = 0
    rate = 16
    for r in range(256 // rate):
        for g in range(256 // rate):
            for b in range(256 // rate):
                send_to_serial(ser, f"{position_to_index(index % 12, index // 12)},{rgb_to_hex((r * rate,g * rate,b * rate))}\n")
                index = (index+1) % (12 * 15)
                print(r, g, b)
                sleep(0.02)

def get_changed_pixel(old : Image, new : Image):
    old_data, new_data = list(old.getdata()), list(new.getdata())
    assert len(old_data) == len(new_data), "Invalid diff"
    width, _ = old.size
    res = []
    for i in range(len(old_data)):
        if old_data[i] != new_data[i]:
            res += [{"pos": (i % width, i // width), "color": new_data[i]}]
    return res

def pixels_to_serial(pixels):
    output = ""
    for p in pixels:
        output += f"{position_to_index(p['pos'])},{rgb_to_hex(p['color'])}\n"
    return output

def penguin_loop(ser, width, height):
    angles = [(0, 0, 0, 0, 0)]
    penguin_size = height
    penguin_image = Image.new("RGB", (width, height), "black")
    penguin_image = penguin_animation.draw_penguin_with_arm(penguin_image, angles[0], penguin_size)
    send_to_serial(ser, image_to_serial(penguin_image))
    frame = 0
    particle = "None"
    while True:
        if frame >= len(angles):
            prompt = input("What should I do next ? ")
            if prompt == "quit":
                return
            angles = gpt_api.get_angle_from_prompt(prompt, True)
            print(angles)
            print(particle)
            frame = 0
        tmp = penguin_image.copy()
        penguin_image = Image.new("RGB", (width, height), "black")
        penguin_image = penguin_animation.draw_penguin_with_arm(penguin_image, angles[frame], penguin_size)
        penguin_image = penguin_animation.add_particle(penguin_image, particle, (0,0))
        diff = get_changed_pixel(tmp, penguin_image)
        output = pixels_to_serial(diff)
        send_to_serial(ser, output)
        sleep(0.2)
        frame += 1



ser = serial.Serial("COM3")

if __name__ == "__main__":
    send_to_serial(ser, clear_serial())
    #penguin_loop(ser, 20, 25)
    #send_to_serial(ser, clear_serial())


# def write_color(index, color):
#     ser.write(f"{index},{color}\n".encode("ascii"))

# write_color(1, "#ff0000")
