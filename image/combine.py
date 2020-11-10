import numpy as np

from ..image.prefix import get_image_prefix


def get_combined_images(img1, img2, from_channel, to_channel) -> np.ndarray:
    n = 4
    size = img1.size[0] * img1.size[1]
    a = np.array(img1.pixels).reshape(size, n)
    b = np.array(img2.pixels).reshape(size, n)
    a[:, to_channel] = b[:, from_channel]  # numpy magic happens here
    return a.reshape(size * n)


def combine_channels_to_image(target_image,
                              R=None, G=None, B=None, A=None,
                              channel_r=0, channel_g=0, channel_b=0, channel_a=0,
                              invert_r=False, invert_g=False, invert_b=False, invert_a=False):
    """Combine image channels into RGBA-channels of target image."""

    n = 4
    t = np.array(target_image.pixels)

    if R:
        t[0::n] = np.array(R.pixels)[channel_r::n]
    if G:
        t[1::n] = np.array(G.pixels)[channel_g::n]
    if B:
        t[2::n] = np.array(B.pixels)[channel_b::n]
    if A:
        t[3::n] = np.array(A.pixels)[channel_a::n]

    if invert_r:
        t[0::n] = 1 - t[0::n]
    if invert_g:
        t[1::n] = 1 - t[1::n]
    if invert_b:
        t[2::n] = 1 - t[2::n]
    if invert_a:
        t[3::n] = 1 - t[3::n]

    target_image.pixels = t
