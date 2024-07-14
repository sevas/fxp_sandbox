import yaml


def load_config(fpath):
    with open(fpath, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config