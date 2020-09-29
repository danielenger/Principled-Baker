import numpy as np


def get_invert_image(img) -> np.ndarray:
    n = 4
    size = img.size[0] * img.size[1]
    a = np.array(img.pixels).reshape(size, n)
    a[:, 0:3] = 1 - a[:, 0:3]
    return a.reshape(size * n)
