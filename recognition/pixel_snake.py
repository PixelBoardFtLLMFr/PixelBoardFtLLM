from time import sleep
from pixel_board_test import send_to_serial, clear_serial, position_to_index, rgb_to_hex, ser
import keyboard
from collections import deque
from random import randint
direction = (0, 0)
stop = False

# g = 75
# d = 77
# h = 72
# b = 80
# esc = 1

class Direction:
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP = (0, -1)
    DOWN = (0, 1)

def is_inside(position, size):
    return not (position[0] < 0 or position[0] >= size[0] or position[1] < 0 or position[1] >= size[1])

def is_opposite(old_dir, new_dir):
    return tuple(a + b for a, b in zip(old_dir, new_dir)) == (0,0)


def gen_apple(snake, size):
    apple = snake[0]
    while apple in snake:
        apple = (randint(0, size[0] - 1), randint(0, size[1] - 1))
    return apple


def snake_loop(ser, size):
    keyboard.on_press(change_direction)
    global direction, stop
    position = (size[0]//2, size[1]//2)
    snake = deque()
    snake.append(position)
    apple = gen_apple(snake, size)
    send_to_serial(ser, f"{position_to_index(position)},{rgb_to_hex((255,255,255))}\n")
    send_to_serial(ser, f"{position_to_index(apple)},{rgb_to_hex((0,255,0))}\n")
    growing = False
    while not stop:
        old_pos = snake[0]
        output = f"{position_to_index(old_pos)},{rgb_to_hex((0,0,0))}\n"
        position = tuple(a + b for a, b in zip(position, direction))

        if not is_inside(position, size) or (position in snake and direction != (0,0)):
            print("LOOSER")
            return

        snake.append(position)
        output += f"{position_to_index(position)},{rgb_to_hex((255,255,255))}\n"

        if position == apple:
            apple = gen_apple(snake, size)
            send_to_serial(ser, f"{position_to_index(apple)},{rgb_to_hex((0,255,0))}\n")
            growing = True

        if not growing:
            snake.popleft()
        else:
            growing = False

        if old_pos != position:
            send_to_serial(ser, output)
        sleep(0.2)
        

        

def change_direction(event : keyboard.KeyboardEvent):
    global direction, stop
    if event.scan_code == 1:
        stop = True
    direction_dict = {75: Direction.LEFT, 77: Direction.RIGHT, 72: Direction.UP, 80: Direction.DOWN}
    if event.scan_code in direction_dict and not is_opposite(direction, direction_dict[event.scan_code]):
        direction = direction_dict[event.scan_code]


if __name__ == "__main__":
    send_to_serial(ser, clear_serial())
    snake_loop(ser, (4, 5))
    send_to_serial(ser, clear_serial())
