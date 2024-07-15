import numpy as np
from numba import njit, prange
from isp_types import BayerPattern

buffers = {}


@njit
def awb(im, bayer_pattern: BayerPattern):
    if bayer_pattern == BayerPattern.GRBG:
        Gr = 0, 0
        R = 0, 1
        B = 1, 0
        Gb = 1, 1
    else:
        return 0, 0

    h, w = im.shape
    r_avg = g_avg = b_avg = 0

    for i in prange(0, h, 2):
        for j in range(0, w, 2):
            r_avg += im[i + R[0], j + R[1]]
            g_avg += (im[i + Gr[0], j + Gr[1]] + im[i + Gb[0], j + Gb[1]]) / 2
            b_avg += im[i + B[0], j + B[1]]

    return g_avg / r_avg, g_avg / b_avg


@njit
def _wb_nb(im, r_gain, b_gain, bayer_pattern: BayerPattern, out):
    if bayer_pattern == BayerPattern.GRBG:
        h, w = im.shape
        for i in prange(0, h, 2):
            for j in range(0, w, 2):
                out[i, j + 1] *= r_gain
                out[i + 1, j] *= b_gain
    else:
        return out

    return out


def wb(im, r_gain, b_gain, bayer_pattern: BayerPattern):
    global buffers
    if "wb" not in buffers:
        buffers["wb"] = im.copy()

    out = buffers["wb"]
    return _wb_nb(im, r_gain, b_gain, bayer_pattern, out)


@njit
def _demos_nb_grgb(im, bayer_pattern: BayerPattern, out):

    # offset of each channel in the bayer pattern
    Gr = 0, 0
    R = 0, 1
    B = 1, 0
    Gb = 1, 1

    h, w = im.shape
    # ignore 2px border for now, so we don't need to deal with padding
    for i in prange(2, h - 2, 2):
        for j in range(2, w - 2, 2):
            # interpolate R channel, with the 4 nearest neighbors
            #
            # Given:
            #
            #    Gr R  Gr R  Gr  R  Gr R
            #    B  Gb B  Gb B  Gb B  Gb
            #    Gr R  Gr R  Gr  R  Gr R
            #    B  Gb B  Gb B  Gb B  Gb
            #
            # We look for 4 neighbors of each 2x2 block
            # The 3 locations marked with "x" must be interpolated
            #           j
            #           |
            #           V
            #     .  .  .  .  .  .
            #     .  .  .  .  .  .
            #     .  R0 x  R1 .  .   <--- i
            #     .  .  x  x  .  .
            #     .  R2 .  R3 .  .
            #     .  .  .  .  .  .
            #     .  .  .  .  .  .

            # fmt: off
            R0 = im[i, j - 1]
            R1 = im[i, j + 1]
            R2 = im[i + 2, j - 1]
            R3 = im[i + 2, j + 1]
            # fmt: on

            out[i, j, 0] = (R0 + R1) / 2
            out[i, j + 1, 0] = R1
            out[i + 1, j + 1, 0] = (R1 + R3) / 2
            out[i + 1, j, 0] = (R0 + R1 + R2 + R3) / 4

            # interpolate G channel, with value on the same row
            out[i, j, 1] = im[i + Gr[0], j + Gr[1]]
            out[i, j + 1, 1] = im[i + Gr[0], j + Gr[1]]
            out[i + 1, j, 1] = im[i + Gb[0], j + Gb[1]]
            out[i + 1, j + 1, 1] = im[i + Gb[0], j + Gb[1]]

            # interpolate B channel, with the 4 nearest neighbors
            #          j
            #          |
            #          V
            #    .  .  .  .  .  .
            #    .  .  B0 .  B2 .
            #    .  .  x  x  .  .   <--- i
            #    .  .  B1 x  B3 .
            #    .  .  .  .  .  .

            # fmt: off
            B0 = im[i - 1, j]
            B1 = im[i + 1, j]
            B2 = im[i - 1, j + 2]
            B3 = im[i + 1, j + 2]
            # fmt: on

            out[i, j, 2] = (B0 + B1) / 2
            out[i, j + 1, 2] = (B0 + B2 + B1 + B3) / 4
            out[i + 1, j, 2] = B1
            out[i + 1, j + 1, 2] = (B1 + B3) / 2


def demos(im, bayer_pattern: BayerPattern):
    global buffers
    if "demos" not in buffers:
        h, w = im.shape
        buffers["demos"] = np.zeros((h, w, 3), dtype=im.dtype)

    out = buffers["demos"]

    if bayer_pattern == BayerPattern.GRBG:
        _demos_nb_grgb(im, bayer_pattern, out)
    else:
        raise NotImplementedError()

    return out


@njit
def _ccm_nb(im, ccm_mat, out):
    h, w, _ = im.shape
    ccm_t = ccm_mat.T

    for i in range(h):
        for j in range(w):
            r, g, b = im[i, j]
            out[i, j, 0] = (r * ccm_t[0, 0] + g * ccm_t[1, 0] + b * ccm_t[2, 0]) / 1024
            out[i, j, 1] = (r * ccm_t[0, 1] + g * ccm_t[1, 1] + b * ccm_t[2, 1]) / 1024
            out[i, j, 2] = (r * ccm_t[0, 2] + g * ccm_t[1, 2] + b * ccm_t[2, 2]) / 1024

            # clipping, 10bits
            for k in range(3):
                if out[i][j][k] < 0.0:
                    out[i][j][k] = 0.0

                if out[i][j][k] > 1023.0:
                    out[i][j][k] = 1023.0


def ccm(im, ccm_mat):
    global buffers
    if "ccm" not in buffers:
        h, w, _ = im.shape
        buffers["ccm"] = np.zeros((h, w, 3), dtype=im.dtype)


    out = buffers["ccm"]
    _ccm_nb(im, ccm_mat, out)
    return out.astype(np.uint16)


def reset():
    buffers.clear()
    return


__all__ = ["awb", "wb", "demos", "ccm", "reset"]
