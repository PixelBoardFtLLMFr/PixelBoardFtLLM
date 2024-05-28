import matplotlib.pyplot as plt
import numpy as np

penguin_bitmap_128 = [
    [0]*128 for _ in range(128)
]

# Function to draw a block of pixels
def draw_block(bitmap, start_x, start_y, width, height, value):
    for i in range(height):
        for j in range(width):
            bitmap[start_y + i][start_x + j] = value

# Penguin design
# Dark gray (1)
draw_block(penguin_bitmap_128, 32, 16, 64, 16, 1)
draw_block(penguin_bitmap_128, 24, 32, 80, 16, 1)
draw_block(penguin_bitmap_128, 16, 48, 96, 16, 1)
draw_block(penguin_bitmap_128, 16, 64, 96, 16, 1)
draw_block(penguin_bitmap_128, 8, 80, 112, 16, 1)
draw_block(penguin_bitmap_128, 8, 96, 112, 16, 1)
draw_block(penguin_bitmap_128, 0, 112, 128, 16, 1)

# White (2)
draw_block(penguin_bitmap_128, 40, 32, 48, 16, 2)
draw_block(penguin_bitmap_128, 32, 48, 64, 16, 2)
draw_block(penguin_bitmap_128, 32, 64, 64, 16, 2)
draw_block(penguin_bitmap_128, 24, 80, 80, 16, 2)
draw_block(penguin_bitmap_128, 24, 96, 80, 16, 2)
draw_block(penguin_bitmap_128, 16, 112, 96, 16, 2)

# Orange (3)
draw_block(penguin_bitmap_128, 48, 80, 32, 16, 3)
draw_block(penguin_bitmap_128, 48, 96, 32, 16, 3)
draw_block(penguin_bitmap_128, 40, 112, 48, 16, 3)

# Black (0)
draw_block(penguin_bitmap_128, 64, 40, 8, 8, 0)

plt.figure()
plt.imshow(penguin_bitmap_128, cmap='gray')
plt.show()
