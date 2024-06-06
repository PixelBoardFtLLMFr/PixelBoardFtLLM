from time import sleep
import serial
import penguin_animation
from PIL import Image

def image_to_serial(image : Image):
    width, height = image.size
    output = ""
    for y in range(height):
        for x in range(width):
            output += f"{position_to_index(x, y)},{rgb_to_hex(image.getpixel((x, y)))}\n"
    return output

def rgb_to_hex(rgb):
    r, g, b = rgb
    # Vérifie si les valeurs sont dans la plage correcte
    if (0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255):
        return f'#{r:02x}{g:02x}{b:02x}'
    else:
        print(r, g, b)
        raise ValueError("Les valeurs RGB doivent être comprises entre 0 et 255")

def position_to_index(x, y):
    board_matrix = [[0, 5, 6],
                    [1, 4, 7],
                    [2, 3, 8]]
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
    for i in range(20 * 9):
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



ser = serial.Serial("COM3")
print(ser.name)

angles = [(0, 0, 0, 0, 0)]
penguin_size = 12
penguin_height, penguin_width = penguin_size, penguin_size

penguin_image = Image.new("RGB", (12, 15), "white")
penguin_image = penguin_animation.draw_penguin_with_arm(penguin_image, angles[0][0], angles[0][1], angles[0][2], angles[0][3], angles[0][4])

send_to_serial(ser, clear_serial())
# send_to_serial(ser, gradiant_serial())
all_colours(ser)
#send_to_serial(ser, image_to_serial(penguin_image))
#print(clear_serial())
#send_to_serial(ser, f"{position_to_index(8,10)},#ffffff\n")

# def write_color(index, color):
#     ser.write(f"{index},{color}\n".encode("ascii"))

# write_color(1, "#ff0000")
