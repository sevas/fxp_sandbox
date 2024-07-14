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
def _demos_nb(im, bayer_pattern: BayerPattern, out):
    if bayer_pattern == BayerPattern.GRBG:
        # offset of each channel in the bayer pattern
        Gr = 0, 0
        R = 0, 1
        B = 1, 0
        Gb = 1, 1
    else:
        return

    h, w = im.shape
    for i in prange(0, h - 2, 2):
        for j in range(0, w - 2, 2):
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
            # (ignoring the first row and column, which need boundary check/padding)
            # The 3 location marked with "x" must be interpolated
            #          i
            #          |
            #          V
            #    .  R0 x  R1 <--- j
            #    .  .  x  x
            #    .  R2 .  R3
            #    .  .  .  .

            # fmt: off
            R0 = im[i, j - 1] if j > 0 else im[i, j + 1]
            R1 = im[i, j + 1]
            R2 = im[i + 2, j - 1] if j > 0 else im[i + 2, j + 1]
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

            #          i
            #          |
            #          V
            #    .  .  .  .  .
            #    .  .  B0 .  B1
            #    .  .  x  x  .    <--- j
            #    .  .  B2 x  B3

            # fmt: off
            B0 = im[i + B[0], j + B[1]]
            B1 = im[i + B[0], j + 2 + B[1]]
            B2 = im[i + 2 + B[0], j + B[1]]
            B3 = im[i + 2 + B[0], j + 2 + B[1]]
            # fmt: on

            out[i, j, 2] = (B0 + B1 + B2 + B3) / 4
            out[i, j + 1, 2] = (B0 + B1) / 2
            out[i + 1, j, 2] = B0
            out[i + 1, j + 1, 2] = B3


def demos(im, bayer_pattern: BayerPattern):
    global buffers
    if "demos" not in buffers:
        h, w = im.shape
        buffers["demos"] = np.zeros((h, w, 3), dtype=im.dtype)

    out = buffers["demos"]
    _demos_nb(im, bayer_pattern, out)
    return out


@njit
def _ccm_nb(im, ccm_mat, out):
    h, w, _ = im.shape
    out_f = out.reshape(-1, 3)
    ccm_t = ccm_mat

    for i in range(h*w):
        # out_f[i][0] = im[i][0] * ccm_t[0][0] + im[i][1] * ccm_t[1][0] + im[i][2] * ccm_t[2][0]
        # out_f[i][1] = im[i][0] * ccm_t[0][1] + im[i][1] * ccm_t[1][1] + im[i][2] * ccm_t[2][1]
        # out_f[i][2] = im[i][0] * ccm_t[0][2] + im[i][1] * ccm_t[1][2] + im[i][2] * ccm_t[2][2]

        out_f[i][0] = 1
        out_f[i][1] = 2
        out_f[i][2] = 3

        # clipping, 10bits
        for j in range(3):
            if out_f[i][j] < 0:
                out_f[i][j] = 0

            if out_f[i][j] > 1023:
                out_f[i][j] = 1023


def ccm(im, ccm_mat):
    global buffers
    if "ccm" not in buffers:
        h, w, _ = im.shape
        buffers["ccm"] = np.zeros((h, w, 3), dtype=im.dtype)

    out = buffers["ccm"]
    _ccm_nb(im, ccm_mat, out)
    return out


def reset():
    buffers.clear()
    return


__all__ = ["awb", "wb", "demos", "ccm", "reset"]
