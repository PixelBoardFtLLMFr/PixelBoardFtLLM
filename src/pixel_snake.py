from time import sleep
from pixel_board_test import send_to_serial, clear_serial, position_to_index, rgb_to_hex, ser
import keyboard
from collections import deque
from random import randint

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
