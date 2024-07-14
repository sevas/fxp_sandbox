import numpy as np
from isp_types import BayerPattern


def awb(im, bayer_pattern: BayerPattern):
    max_px_value = 2 ** 10
    pc = max_px_value / 100

    if bayer_pattern == BayerPattern.GRBG:
        Gr = im[0::2, 0::2]  # top left
        R = im[0::2, 1::2]  # top right
        B = im[1::2, 0::2]  # bottom left
        Gb = im[1::2, 1::2]  # bottom right
    else:
        raise NotImplementedError()

    r_avg = np.mean(R)
    g_avg = (np.mean(Gr) + np.mean(Gb)) / 2
    b_avg = np.mean(B)

    return g_avg / r_avg, g_avg / b_avg


def wb(im, r_gain, b_gain, bayer_pattern: BayerPattern):
    out = im.copy().astype("f4")

    if bayer_pattern == BayerPattern.GRBG:
        out[0::2, 1::2] *= r_gain
        out[1::2, 0::2] *= b_gain
    else:
        raise NotImplementedError

    return out


def demos(im, bayer_pattern):
    height, width = im.shape

    # Initialize the output color image with 3 channels (R, G, B)
    color_image = np.zeros((height, width, 3), dtype=im.dtype)

    # Extract R, G, B channels from the RGGB pattern
    G1 = im[0:height:2, 0:width:2]  # Red channel (even rows, even columns)
    R = im[0:height:2, 1:width:2]  # Green channel (even rows, odd columns)
    B = im[1:height:2, 0:width:2]  # Green channel (odd rows, even columns)
    G2 = im[1:height:2, 1:width:2]  # Blue channel (odd rows, odd columns)

    # Interpolate the Red channel
    color_image[0:height:2, 0:width:2, 0] = R
    color_image[0:height:2, 1:width - 1:2, 0] = (R[:, :-1] + R[:, 1:]) // 2
    color_image[1:height - 1:2, 0:width:2, 0] = (R[:-1, :] + R[1:, :]) // 2
    color_image[1:height - 1:2, 1:width - 1:2, 0] = (R[:-1, :-1] + R[:-1, 1:] + R[1:, :-1] + R[1:, 1:]) // 4

    # Interpolate the Green channel
    color_image[0:height:2, 0:width:2, 1] = G1
    color_image[0:height:2, 1:width:2, 1] = G1
    color_image[1:height:2, 0:width:2, 1] = G2
    color_image[1:height:2, 1:width:2, 1] = G2

    # Interpolate the Blue channel
    color_image[1:height:2, 1:width:2, 2] = B
    color_image[0:height:2, 1:width - 1:2, 2] = (B[:, :-1] + B[:, 1:]) // 2
    color_image[1:height - 1:2, 0:width:2, 2] = (B[:-1, :] + B[1:, :]) // 2
    color_image[0:height - 2:2, 0:width - 2:2, 2] = (B[:-1, :-1] + B[:-1, 1:] + B[1:, :-1] + B[1:, 1:]) // 4

    return color_image


def ccm(im, ccm):
    h, w, _ = im.shape
    im_ccm = (im.reshape(-1, 3) @ ccm.T) / 1024
    return np.clip(im_ccm.reshape(h, w, 3), 0, 1023).astype(np.uint16)


def reset():
    pass


__all__ = ["awb", "wb", "demos", "ccm", "reset"]
