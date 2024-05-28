import matplotlib.pyplot as plt
import numpy as np

penguin_bitmap_128 = np.zeros((128, 128))

# Function to draw a block of pixels
def draw_block(bitmap, start_x, start_y, size, value):
    for i in range(size):
        for j in range(size):
            bitmap[start_y + i][start_x + j] = value

# Scaling factor
# scale = 12
scale = 11

# Draw the penguin based on the original 10x10 design
# Each block will be size 'scale'

# Black background (already initialized to 0)

# Dark gray pixels (body)
dark_gray_coords = [
    (4, 1), (5, 1), (6, 1), (7, 1),
    (2, 2), (3, 2), (4, 2), (7, 2), (8, 2),
    (1, 3), (2, 3), (7, 3), (8, 3), (9, 3),
    (1, 4), (2, 4), (8, 4), (9, 4),
    (1, 5), (2, 5), (8, 5), (9, 5),
    (0, 6), (1, 6), (9, 6), (10, 6),
    (0, 7), (1, 7), (10, 7),
    (0, 8), (9, 8), (10, 8),
    (4, 9), (5, 9), (6, 9), (7, 9)
]
for x, y in dark_gray_coords:
    draw_block(penguin_bitmap_128, x * scale, y * scale, scale, 1)

# White pixels (belly and face)
white_coords = [
    (5, 2), (6, 2),
    (3, 3), (4, 3), (5, 3), (6, 3),
    (4, 4), (5, 4), (6, 4), (7, 4),
    (4, 5), (5, 5), (6, 5), (7, 5),
    (3, 6), (4, 6), (5, 6), (6, 6), (7, 6), (8, 6),
    (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7),
    (4, 8), (5, 8), (6, 8), (7, 8)
]
for x, y in white_coords:
    draw_block(penguin_bitmap_128, x * scale, y * scale, scale, 2)

# Orange pixels (beak and feet)
orange_coords = [
    (4, 6), (5, 6),
    (4, 7), (5, 7)
]
for x, y in orange_coords:
    draw_block(penguin_bitmap_128, x * scale, y * scale, scale, 3)

# Add the penguin's eye
draw_block(penguin_bitmap_128, 6 * scale, 3 * scale, scale, 0)

plt.figure()
plt.imshow(penguin_bitmap_128, cmap='gray')
plt.show()
