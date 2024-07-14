from pathlib import Path

import pytest
import numpy as np

import isp_datasets


@pytest.fixture
def grgb_image():
    data = isp_datasets.infinite_isp()["Indoor1_2592x1536_10bit_GRBG"]
    raw_data, config = data["raw"], data["config_data"]
    h, w = config["sensor_info"]["height"], config["sensor_info"]["width"]
    yield raw_data.reshape(h, w)


class TestAWBSpec:
    @staticmethod
    def test_numpy_and_numba_gains_are_equivalent(grgb_image):
        from isp_np import awb as awb_np
        from isp_nb import awb as awb_nb
        from isp_types import BayerPattern
        im = grgb_image
        bayer_pattern = BayerPattern.GRBG
        gains_np = awb_np(im, bayer_pattern)
        gains_nb = awb_nb(im, bayer_pattern)
        np.testing.assert_equal(gains_np, gains_nb)
