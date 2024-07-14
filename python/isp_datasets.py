from pathlib import Path
import numpy as np
from isp_io import load_config

THIS_DIR = Path(__file__).parent
INFINITE_ISP_PATH = THIS_DIR / "Infinite-ISP_ReferenceModel/in_frames/normal/data"


def infinite_isp():
    data = {}
    for each in INFINITE_ISP_PATH.glob("*.raw"):
        config_fpath = each.parent / each.with_name(each.stem + "-configs.yml")
        data[each.stem] = {
            "raw": np.fromfile(each, dtype=np.uint16),
            "config": config_fpath,
            "config_data": load_config(config_fpath),
        }

    return data


def infinite_isp_colorcharts():
    data = {
        "ColorChecker_2592x1536_10bit_GRBG.raw": {
            "raw": np.fromfile(INFINITE_ISP_PATH.parent / "ColorChecker_2592x1536_10bit_GRBG.raw", dtype=np.uint16),
            "config": INFINITE_ISP_PATH / "Indoor1_2592x1536_10bit_GRBG-configs.yml",
            "config_data": load_config(INFINITE_ISP_PATH / "Indoor1_2592x1536_10bit_GRBG-configs.yml"),
        },
    }

    return data