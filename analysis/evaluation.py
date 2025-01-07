import sys
import timeit
import secrets
import rosslt
from dataclasses import dataclass
from functools import partial
from random import Random


@dataclass
class Entry:
    name: str
    setup: callable
    cb: callable
    cb_range: range
    repeat: int = 0
    number: int = 0
    config: dict = None


def plot_graph(path_base, file_name, label_x, label_y, scale_y, entries, bench=False):

    # import pyplot
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing")
        return

    # create figure
    print(f"creating {file_name}")
    fig = plt.figure()

    # add entries
    for entry in entries:
        print(f"  adding {entry.name}")

        # configure library
        rosslt.config_load()
        if entry.config:
            rosslt.config_parse(entry.config)

        # generate datapoints
        data_x = []
        data_y = []
        for x in entry.cb_range:
            data_x.append(x)
            if bench:
                data_y.append(scale_y * min(timeit.Timer(
                    partial(entry.cb, x, entry.setup(x))
                ).repeat(entry.repeat, entry.number)) / entry.number)
            else:
                data_y.append(scale_y * entry.cb(x, entry.setup(x)))

        # add to figure
        plt.plot(data_x, data_y, label=entry.name)

    # configure plot
    plt.legend(loc="upper left")
    plt.xlabel(label_x)
    plt.ylabel(label_y)

    # get path
    file_format = "svg"
    path = f"{path_base}/{file_name}.{file_format}"

    # write to file
    print(f"  writing to {path}")
    plt.savefig(f"{path}", format=file_format, dpi=1200)

    # finalize
    plt.clf()
    plt.close(fig)


def plot_message_runtime(path_base):

    def setup(x, is_float, to_msg=False):

        # build expression
        rng = Random(secrets.randbits(64))
        val = rosslt.Tracked(rng.random())
        for _ in range(x):
            val = rosslt.apply_random(
                val, rng, rng.random() if is_float else rng.randint(1, 9))

        # extract expression for benchmark
        param = val.get_expression()
        param.unpack()

        # pack to message
        if to_msg:
            param = param.to_message()

        # pass param
        return param

    def bench_serialize(_, param):
        param.to_message()

    def bench_serialize_size(_, param):
        msg = param.to_message()
        return len(msg.data) + len(msg.elements)

    def bench_deserialize(_, param):
        rosslt.Expression.from_message(param).unpack()

    plot_graph(path_base, "message_runtime_serialize", "Operator Count", "Time (ms)", 1000, [
        Entry(name="String (Float)", repeat=2, number=64,
              setup=partial(setup, is_float=True),
              cb=bench_serialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="String (Small Integer)", repeat=2, number=64,
              setup=partial(setup, is_float=False),
              cb=bench_serialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="Data Array (Float)", repeat=2, number=64,
              setup=partial(setup, is_float=True),
              cb=bench_serialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
        Entry(name="Data Array (Small Integer)", repeat=2, number=64,
              setup=partial(setup, is_float=False),
              cb=bench_serialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
    ], bench=True)

    plot_graph(path_base, "message_runtime_serialize_size", "Operator Count", "Size (KB)", 0.001, [
        Entry(name="String (Float)",
              setup=partial(setup, is_float=True),
              cb=bench_serialize_size, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="String (Small Integer)",
              setup=partial(setup, is_float=False),
              cb=bench_serialize_size, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="Data Array (Float)",
              setup=partial(setup, is_float=True),
              cb=bench_serialize_size, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
        Entry(name="Data Array (Small Integer)",
              setup=partial(setup, is_float=False),
              cb=bench_serialize_size, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
    ])

    plot_graph(path_base, "message_runtime_deserialize", "Operator Count", "Time (ms)", 1000, [
        Entry(name="String (Float)", repeat=2, number=64,
              setup=partial(setup, is_float=True, to_msg=True),
              cb=bench_deserialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="String (Small Integer)", repeat=2, number=64,
              setup=partial(setup, is_float=False, to_msg=True),
              cb=bench_deserialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": True}),
        Entry(name="Data Array (Float)", repeat=2, number=64,
              setup=partial(setup, is_float=True, to_msg=True),
              cb=bench_deserialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
        Entry(name="Data Array (Small Integer)", repeat=2, number=64,
              setup=partial(setup, is_float=False, to_msg=True),
              cb=bench_deserialize, cb_range=range(0, 10000+1, 200),
              config={"zlib_enable": False, "msg_str": False}),
    ], bench=True)


def plot_provenance_tree_runtime(path_base):

    # shared rng
    rng = Random(secrets.randbits(64))

    def setup(_, is_raw):
        return is_raw

    def bench(x, is_raw, single):

        # create tracked
        val = x if is_raw else rosslt.Tracked(x)

        # apply random operations
        for _ in range(x):
            if single:
                val += rng.random()
            else:
                val = rosslt.apply_random(val, rng, rng.random())

        # result for size measurement
        return val

    def bench_size(x, is_raw, single):

        # get processed value
        val = bench(x, is_raw, single)

        # object size
        if type(val) is not rosslt.Tracked:
            return sys.getsizeof(val)

        # serialized size
        expr = val.get_expression()
        msg = expr.to_message()
        return len(msg.data) + len(msg.elements)

    plot_graph(path_base, "provenance_tree_runtime", "Operator Count", "Time (ms)", 1000, [
        Entry(name="No Tracking", repeat=2, number=16,
              setup=partial(setup, is_raw=True),
              cb=partial(bench, single=False), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": False, "zlib_enable": False}),
        Entry(name="Tracking", repeat=2, number=16,
              setup=partial(setup, is_raw=False),
              cb=partial(bench, single=False), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": False, "zlib_enable": False}),
        Entry(name="Tracking (+=)", repeat=2, number=16,
              setup=partial(setup, is_raw=False),
              cb=partial(bench, single=True), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": False, "zlib_enable": False}),
        Entry(name="Tracking + Chaining", repeat=2, number=16,
              setup=partial(setup, is_raw=False),
              cb=partial(bench, single=False), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": True, "zlib_enable": False}),
        Entry(name="Tracking + Chaining (+=)", repeat=2, number=16,
              setup=partial(setup, is_raw=False),
              cb=partial(bench, single=True), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": True, "zlib_enable": False}),
    ], bench=True)

    plot_graph(path_base, "provenance_tree_runtime_size", "Operator Count", "Size (KB)", 0.001, [
        # Entry(name="No Tracking",
        #       setup=partial(setup, is_raw=True),
        #       cb=partial(bench_size, single=False), cb_range=range(0, 10000+1, 200),
        #       config={"expr_chain": False, "zlib_enable": False}),
        Entry(name="Tracking",
              setup=partial(setup, is_raw=False),
              cb=partial(bench_size, single=False), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": False, "zlib_enable": False}),
        # Entry(name="Tracking (+=)",
        #       setup=partial(setup, is_raw=False),
        #       cb=partial(bench_size, single=True), cb_range=range(0, 10000+1, 200),
        #       config={"expr_chain": False, "zlib_enable": False}),
        Entry(name="Tracking + Chaining",
              setup=partial(setup, is_raw=False),
              cb=partial(bench_size, single=False), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": True, "zlib_enable": False}),
        Entry(name="Tracking + Chaining (+=)",
              setup=partial(setup, is_raw=False),
              cb=partial(bench_size, single=True), cb_range=range(0, 10000+1, 200),
              config={"expr_chain": True, "zlib_enable": False}),
    ])


def plot_provenance_tree_data_size(path_base):

    def setup_int(x):
        return x

    def setup_float(x):
        return float(x)

    def size_get(x, param):

        # apply random operations
        rng = Random(secrets.randbits(64))
        val = rosslt.Tracked(param)
        for _ in range(x):
            if type(param) is float:
                val = rosslt.apply_random(val, rng, rng.random())
            else:
                val = rosslt.apply_random(val, rng, rng.randint(1, 9))

        # size of tree
        expr = val.get_expression()
        msg = expr.to_message()
        return len(msg.data) + len(msg.elements)

    plot_graph(path_base, "provenance_tree_data_size_int", "Operator Count", "Size (bytes)", 1, [
        Entry(name="String", setup=setup_int,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": True, "zlib_enable": False}),
        Entry(name="Data Array", setup=setup_int,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": False, "zlib_enable": False}),
        Entry(name="Compressed String", setup=setup_int,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": True, "zlib_enable": True, "zlib_threshold": 0}),
        Entry(name="Compressed Data Array", setup=setup_int,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": False, "zlib_enable": True, "zlib_threshold": 0}),
    ])

    plot_graph(path_base, "provenance_tree_data_size_float", "Operator Count", "Size (bytes)", 1, [
        Entry(name="String", setup=setup_float,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": True, "zlib_enable": False}),
        Entry(name="Data Array", setup=setup_float,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": False, "zlib_enable": False}),
        Entry(name="Compressed String", setup=setup_float,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": True, "zlib_enable": True, "zlib_threshold": 0}),
        Entry(name="Compressed Data Array", setup=setup_float,
              cb=size_get, cb_range=range(0, 100+1, 1),
              config={"expr_chain": False, "msg_str": False, "zlib_enable": True, "zlib_threshold": 0}),
    ])


def plot_all(path_base):

    # plot graphs
    plot_message_runtime(path_base)
    plot_provenance_tree_runtime(path_base)
    plot_provenance_tree_data_size(path_base)


if __name__ == "__main__":

    # plot into path of first argument
    plot_all(sys.argv[1] if len(sys.argv) > 1 else "/tmp")
