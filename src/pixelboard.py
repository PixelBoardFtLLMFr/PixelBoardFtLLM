import serial

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
    for i in range(len(arr1)):
        for j in range(len(arr1[0])):
            if arr1[i][j] != arr2[i][j]:
                res.append((i, j))

    return res

class PixelBoard:
    def __init__(self, port, tile_matrix, pixel_matrix):
        self.port = port
        self.tile_matrix = tile_matrix
        self.pixel_matrix = pixel_matrix

        try:
            self.serial = serial.Serial(port=self.port, baudrate=9600)
        except:
            self.serial = None

        self.height = len(self.tile_matrix)*TILE_HEIGHT
        self.width = len(self.tile_matrix[0])*TILE_WIDTH
        self.pixels = [[(0, 0, 0)
                        for i in range(self.width)]
                       for j in range(self.height)]

    def _coords_to_idx(self, i, j):
        tile_index = self.tile_matrix[i//TILE_HEIGHT][j//TILE_WIDTH]
        pixel_index = self.pixel_matrix[i%TILE_HEIGHT][j%TILE_WIDTH]
        return tile_index*TILE_HEIGHT*TILE_WIDTH + pixel_index

    def _send_to_serial(self, serial_str):
        if self.serial:
            self.serial.write(serial_str.encode("ascii"))

    def _write_pixels(self, coords):
        output = ""
        for (i, j) in coords:
            output += f"{self._coords_to_idx(i, j)},{tuple_to_hex(self.pixels[i][j])}\n"

        self._send_to_serial(output)

    def _clear_serial(self):
        new_pixels = [[(0, 0, 0)
                       for i in range(self.width)]
                      for j in range(self.height)]

        diff_coords = array_diff(self.pixels, new_pixels)
        self.pixels = new_pixels

        self.write_pixels(diff_coords)

    def draw_pixels(self, pixels):
        assert len(pixels) == self.height
        assert len(pixels[0]) == self.width

        diff_coords = array_diff(pixels, self.pixels)
        self.pixels = pixels
        self._write_pixels(diff_coords)
