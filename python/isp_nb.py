from numba import njit, prange
from isp_types import BayerPattern

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
            r_avg += im[i+R[0], j+R[1]]
            g_avg += (im[i+Gr[0], j+Gr[1]] + im[i+Gb[0], j+Gb[1]]) / 2
            b_avg += im[i+B[0], j+B[1]]

    return g_avg / r_avg, g_avg / b_avg