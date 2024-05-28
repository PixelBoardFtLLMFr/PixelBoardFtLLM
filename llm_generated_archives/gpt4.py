import matplotlib.pyplot as plt
import numpy as np

penguin_bitmap_asym_128 = [
    [0]*128 for _ in range(128)
]

# Function to draw a block of pixels
def draw_block(bitmap, start_x, start_y, width, height, value):
    for i in range(height):
        for j in range(width):
            bitmap[start_y + i][start_x + j] = value

# Penguin design
# Dark gray (1)
draw_block(penguin_bitmap_asym_128, 40, 16, 56, 16, 1)
draw_block(penguin_bitmap_asym_128, 32, 32, 72, 16, 1)
draw_block(penguin_bitmap_asym_128, 24, 48, 88, 16, 1)
draw_block(penguin_bitmap_asym_128, 24, 64, 88, 16, 1)
draw_block(penguin_bitmap_asym_128, 16, 80, 104, 16, 1)
draw_block(penguin_bitmap_asym_128, 16, 96, 104, 16, 1)
draw_block(penguin_bitmap_asym_128, 8, 112, 120, 16, 1)

# White (2)
draw_block(penguin_bitmap_asym_128, 48, 32, 48, 16, 2)
draw_block(penguin_bitmap_asym_128, 40, 48, 64, 16, 2)
draw_block(penguin_bitmap_asym_128, 40, 64, 64, 16, 2)
draw_block(penguin_bitmap_asym_128, 32, 80, 80, 16, 2)
draw_block(penguin_bitmap_asym_128, 32, 96, 80, 16, 2)
draw_block(penguin_bitmap_asym_128, 24, 112, 96, 16, 2)

# Orange (3)
draw_block(penguin_bitmap_asym_128, 56, 80, 32, 16, 3)
draw_block(penguin_bitmap_asym_128, 56, 96, 32, 16, 3)
draw_block(penguin_bitmap_asym_128, 48, 112, 48, 16, 3)

# Black (0) for eye
draw_block(penguin_bitmap_asym_128, 72, 40, 8, 8, 0)

plt.figure()
plt.imshow(penguin_bitmap_asym_128, cmap='gray')
plt.show()
