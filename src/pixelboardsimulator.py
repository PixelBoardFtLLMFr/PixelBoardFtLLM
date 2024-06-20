import PIL.Image, PIL.ImageDraw

class PixelBoardSimulator:
    def __init__(self, scale):
        self.gap = 5
        self.image = None
        self.draw  = None
        self.scale = None
        self.drawing_size = None
        self.set_scale(scale)

    def set_scale(self, new_scale):
        if new_scale != self.scale:
            self.scale = new_scale
            self.pixel_size = self.scale // (self.gap + 1)

    def get_image(self):
        return self.image

    def _reset_image(self):
        self.draw.rectangle([0,
                             0,
                             self.drawing_size*self.scale - 1,
                             self.drawing_size*self.scale - 1],
                            fill=(0, 0, 0))

    def do_draw(self, pixels):
        drawing_size = len(pixels)

        if self.image == None or drawing_size != self.drawing_size:
            self.drawing_size = drawing_size
            self.image = PIL.Image.new("RGB",
                                       (self.scale*self.drawing_size,
                                        self.scale*self.drawing_size),
                                       "black")
            self.draw = PIL.ImageDraw.Draw(self.image)

        self._reset_image()

        for x in range(drawing_size):
            for y in range(drawing_size):
                pixel = pixels[y][x]

                if pixel == (10, 10, 10):
                    pixel = (100, 100, 100)

                self.draw.rectangle([x*self.scale,
                                     y*self.scale,
                                     x*self.scale + self.pixel_size - 1,
                                     y*self.scale + self.pixel_size - 1],
                                    fill=pixel)
        return self.get_image()
