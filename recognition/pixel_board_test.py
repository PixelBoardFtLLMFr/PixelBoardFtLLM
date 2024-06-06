import serial
import penguin_animation
from PIL import Image

def image_to_serial(image : Image):
    width, height = image.size
    output = ""
    print(width, height)
    for y in range(height):
        for x in range(width):
            output += f"{position_to_index(x, y)},{rgb_to_hex(image.getpixel((x, y)))}\n"
    return output

def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"#{hex(r)[2:]}{hex(g)[2:]}{hex(b)[2:]}"

def position_to_index(x, y):
    board_matrix = [[0, 3, 6],
                    [1, 4, 7],
                    [2, 5, 8]]
    led_matrix = [[15, 10, 5, 0],
                  [16, 11, 6, 1],
                  [17, 12, 7, 2],
                  [18, 13, 8, 3],
                  [19, 14, 9, 4]]
    board_index = board_matrix[y // 5][x // 4]
    led_index = led_matrix[y % 5][x % 4]
    return board_index * 20 + led_index

def send_to_serial(ser, serial_str):
    ser.write(serial_str.encode("ascii"))

ser = serial.Serial("/dev/ttyACM0")
print(ser.name)

angles = [(0, 0, 0, 0, 0)]
penguin_size = 12
penguin_height, penguin_width = penguin_size, penguin_size

penguin_image = Image.new("RGB", (penguin_width, penguin_height), "white")
penguin_image = penguin_animation.draw_penguin_with_arm(penguin_image, angles[0][0], angles[0][1], angles[0][2], angles[0][3], angles[0][4])

send_to_serial(ser, image_to_serial(penguin_image))

# def write_color(index, color):
#     ser.write(f"{index},{color}\n".encode("ascii"))

# write_color(1, "#ff0000")
