import serial
import utils

# Pixels on a single tile
TILE_WIDTH = 4
TILE_HEIGHT = 5

def tuple_to_hex(pixel):
    """
    Convert pixel to (R, G, B) format to '#RRGGBB' format.
    """
    res = "#"

    for i in range(3):
        suffix = hex(pixel[i])[2:]

        if len(suffix) == 1:
            res += "0" + suffix
        else:
            res += suffix

    return res

def array_diff(arr1, arr2):
    """
    Return a list of coordinates (i, j) where ARR1 and ARR2 differ.
    """
    assert len(arr1) == len(arr2)
    assert len(arr1[0]) == len(arr2[0])

    res = []
    for y in range(len(arr1)):
        for x in range(len(arr1[0])):
            if arr1[y][x] != arr2[y][x]:
                res.append((x, y))

    return res

class PixelBoard:
    def __init__(self, port, tile_matrix, pixel_matrix):
        self.port = port
        self.tile_matrix = tile_matrix
        self.pixel_matrix = pixel_matrix

        self.height = len(self.tile_matrix)*TILE_HEIGHT
        self.width = len(self.tile_matrix[0])*TILE_WIDTH
        self.pixels = [[(0, 0, 0)
                        for i in range(self.width)]
                       for j in range(self.height)]
        try:
            self.serial = serial.Serial(port=self.port, baudrate= 9600, writeTimeout=0)
            self._clear_serial()
            utils.debug("Connected to pixel board")
        except Exception as e:
            self.serial = None
            utils.debug(e)
            utils.debug("Not connected to pixel board")

    def _coords_to_idx(self, x, y):
        tile_index = self.tile_matrix[y//TILE_HEIGHT][x//TILE_WIDTH]
        pixel_index = self.pixel_matrix[y%TILE_HEIGHT][x%TILE_WIDTH]
        return tile_index*TILE_HEIGHT*TILE_WIDTH + pixel_index

    def _send_to_serial(self, serial_str):
        if self.serial:
            serial_str += "499,#000000\n"
            self.serial.write(serial_str.encode("ascii"))

    def _write_pixels(self, coords):
        output = ""
        for (x, y) in coords:
            output += f"{self._coords_to_idx(x, y)},{tuple_to_hex(self.pixels[y][x])}\n"

        self._send_to_serial(output)

    def _clear_serial(self):
        new_pixels = [(x, y) for x in range(self.width) for y in range(self.height)]

        self._write_pixels(new_pixels)

    def draw_pixels(self, pixels):
        assert len(pixels) == self.height
        assert len(pixels[0]) == self.width

        diff_coords = array_diff(pixels, self.pixels)
        self.pixels = pixels
        self._write_pixels(diff_coords)
