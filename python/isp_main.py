import cv2
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt

import isp_types
import isp_datasets
from isp_timings import time_this

USE_BACKEND = "numpy"
WITH_PLOTS = True

if USE_BACKEND == "numpy":
    from isp_np import awb, wb, demos, ccm


def levels(im):
    return np.min(im), np.max(im)


def norm(im: NDArray):
    lo, hi = np.min(im), np.max(im)
    return (im - lo) / (hi - lo)


def imshow(im, title):
    if not WITH_PLOTS:
        return
    plt.imshow(im)
    plt.title("*** " + title)
    plt.colorbar()
    plt.show()


data1 = isp_datasets.infinite_isp()["Indoor1_2592x1536_10bit_GRBG"]
raw_image, config = data1["raw"], data1["config_data"]

w = width = config["sensor_info"]["width"]
h = height = config["sensor_info"]["height"]
bayer_pattern = isp_types.BayerPattern[config["sensor_info"]["bayer_pattern"].upper()]
lmx = np.array([
    config["color_correction_matrix"]["corrected_red"],
    config["color_correction_matrix"]["corrected_green"],
    config["color_correction_matrix"]["corrected_blue"],
]).astype(np.int16)

bayer_opencv_patterns = {
    isp_types.BayerPattern.GRBG: cv2.COLOR_BAYER_GRBG2RGB
}

# RAW
raw_image = raw_image.reshape(height, width)
imshow(raw_image, "RAW")
try_count = 1

for each in range(try_count):
    # WB
    with time_this("awb"):
        rgain, bgain = awb(raw_image, bayer_pattern)
        im_wb = wb(raw_image, rgain, bgain, bayer_pattern)

    # DEMOS
    with time_this("demos"):
        im_demos = demos(im_wb, bayer_pattern)
        # im_demos = cv2.cvtColor(im_wb.astype(np.uint16), bayer_opencv_patterns[bayer_pattern])
    imshow(im_demos.astype("u2"), "demos grbg -> rgb")

    # CCM
    with time_this("ccm"):
        im_ccm = ccm(im_demos, lmx)
    imshow(im_ccm, "rgb->ccm")
