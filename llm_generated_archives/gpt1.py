import matplotlib.pyplot as plt
import numpy as np

penguin_bitmap = np.array([
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 2, 2, 1, 1, 1, 0],
    [1, 1, 1, 2, 2, 2, 2, 1, 1, 1],
    [1, 1, 2, 2, 2, 2, 2, 2, 1, 1],
    [1, 1, 2, 2, 3, 3, 2, 2, 1, 1],
    [1, 2, 2, 2, 3, 3, 2, 2, 2, 1],
    [0, 1, 2, 2, 3, 3, 2, 2, 1, 0],
    [0, 0, 1, 2, 2, 2, 2, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 0, 0, 0]
])

plt.figure()
plt.imshow(penguin_bitmap, cmap='gray')
plt.show()
