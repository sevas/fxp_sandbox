import contextlib
import time
import atexit

timings = {}


@contextlib.contextmanager
def time_this(name: str):
    global timings
    t0 = time.perf_counter_ns()
    if name not in timings:
        timings[name] = []
    try:
        yield
    finally:
        elapsed = time.perf_counter_ns() - t0
        timings[name].append(elapsed / 1e6)


@atexit.register
def print_timings():
    from pandas import DataFrame

    df = DataFrame(timings)
    print("Timings: (units: ms)")
    print(df[1:].describe())
    try:
        from matplotlib import pyplot as plt
        df[1:].plot()
        plt.show()
    except ImportError:
        pass


def save_plot(filename):
    from pandas import DataFrame

    try:
        from matplotlib import pyplot as plt
        df = DataFrame(timings)
        df[1:].plot()
        plt.savefig(filename)
    except ImportError:
        pass