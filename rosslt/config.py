import os
import json


class Config:

    # expression
    expr_chain = True

    # message
    msg_str = False

    # compression
    zlib_enable = True
    zlib_level = 1
    zlib_threshold = 1024


# static instance
config = Config()


def config_parse(data):

    # apply values
    for k, v in data.items():
        setattr(config, k, v)


def config_load(path="rosslt_py.json"):

    # check if file existing
    if os.path.exists(path):

        # parse from json file
        with open(path, "r", encoding="UTF-8") as f:
            config_parse(json.loads(f.read()))

    else:

        # fall back to defaults
        for attr in filter(lambda e: not e.startswith("_"), dir(Config)):
            setattr(config, attr, getattr(Config, attr))


# load config on library init
# noinspection PyBroadException
try:
    config_load()
except Exception:
    pass
