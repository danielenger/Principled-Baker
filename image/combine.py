import numpy as np

from principled_baker.image.prefix import get_image_prefix


def get_combined_images(img1, img2, from_channel, to_channel) -> np.ndarray:
    n = 4
    size = img1.size[0] * img1.size[1]
    a = np.array(img1.pixels).reshape(size, n)
    b = np.array(img2.pixels).reshape(size, n)
    a[:, to_channel] = b[:, from_channel]  # numpy magic happens here
    return a.reshape(size * n)


def combine_channels_to_image(target_image, R=None, G=None, B=None, A=None, channel_r=0, channel_g=0, channel_b=0, channel_a=0):
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
    target_image.pixels = t
