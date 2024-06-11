from random import randint

def dirs_opposite(old_dir, new_dir):
    return old_dir[0] == -new_dir[0] and old_dir[1] == -new_dir[1]

class Direction:
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP = (0, -1)
    DOWN = (0, 1)

class PixelSnake:
    _direction_dict = {
        75: Direction.LEFT,
        77: Direction.RIGHT,
        72: Direction.UP,
        80: Direction.DOWN
    }

    def __init__(self, board_size):
        self.board_size = board_size

        self.direction = (1, 0)
        self.body = [(self.board_size//2, self.board_size//2)]
        self.stop = False
        self._gen_apple()

    def handle_key(self, key):
        if key == "z":
            self._change_dir(Direction.UP)
        elif key == "q":
            self._change_dir(Direction.LEFT)
        elif key == "s":
            self._change_dir(Direction.DOWN)
        elif key == "d":
            self._change_dir(Direction.RIGHT)
        elif key == "q":
            self._stop()

    def _stop(self):
        self.stop = True

    def _change_dir(self, new_dir):
        if not dirs_opposite(self.direction, new_dir):
            self.direction = new_dir

    def _destroy(self):
        keyboard.unhook_all()

    def _is_inside(self):
        pos = self.body[-1]
        return not (pos[0] < 0
                    or pos[0] >= size[0]
                    or pos[1] < 0
                    or pos[1] >= size[1])

    def _gen_apple(self):
        self.apple = self.body[-1]
        while self.apple in self.body:
            self.apple = (randint(0, self.board_size - 1),
                          randint(0, self.board_size - 1))

    def gen_pixels(self):
        pixels = [[(0, 0, 0)
                   for j in range(self.board_size)]
                  for i in range(self.board_size)]

        pixels[self.apple[1]][self.apple[0]] = (255, 0, 0)

        for pos in self.body:
            pixels[pos[1]][pos[0]] = (0, 255, 0)

        return pixels

    def loop(self):
        """
        Main loop for the snake game. Game runs while this loop function
        returns the pixel matrix and ends when this function returns None.
        """
        new_pos = self.body[-1]
        new_pos[0] += self.direction[0]
        new_pos[1] += self.direction[1]
        self.body.append(new_pos)

        if self.stop or not self._is_inside() or self.body[-1] in self.body[:-1]:
            # End
            return None

        if new_pos == self.apple:
            self._gen_apple()
        else:
            self.body.pop(0)

        return self.gen_pixels()
