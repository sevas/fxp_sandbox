import numpy as np
import pytest

from fxplite import Fxplite, make_fxp, U
from fxpmath import Fxp


class TestFXPLiteSpec:

    @staticmethod
    def test_addition_no_overflow():
        a = make_fxp(1, 2, 2, False)
        b = make_fxp(1, 2, 2, False)
        c = make_fxp(2, 2, 2, False)
        assert a + b == c

    @staticmethod
    def test_addition_mixed_sizes():
        a = make_fxp(2.5, 3, 3, False)
        b = make_fxp(1.75, 3, 2, False)

        assert a + b.u(3,3) == make_fxp(4.25, 3, 3, False)

    @staticmethod
    def test_internal_repr():
        a = make_fxp(1, 2, 2, False)
        assert a.stored_int == 0b01_00

        a = make_fxp(1, 2, 3, False)
        assert a.stored_int == 0b10_00

        a = make_fxp(12, 5, 3, False)
        assert a.stored_int == 0b1100_000

        # a = make_fxp(3.2, 3, 2, False)
        a = U(3, 2)(3.2)
        assert a.stored_int == 0b011_00

        a = U(3, 2)(5.4)
        assert a.stored_int == 0b101_01

        a = U(3, 2)(7.9)
        assert a.stored_int == 0b111_11


@pytest.mark.benchmark(group="create")
class TestBenchmarkCreate:
    @staticmethod
    def test_benchmark_fxplite(benchmark):
        benchmark(lambda: make_fxp(1, 2, 2, False))

    @staticmethod
    def test_benchmark_fxp(benchmark):
        benchmark(lambda: Fxp(1, n_int=2, n_frac=2, signed=False))

    @staticmethod
    def test_benchmark_scalar_int(benchmark):
        benchmark(lambda: 1)

    @staticmethod
    def test_benchmark_scalar_npint(benchmark):
        benchmark(lambda: np.uint32(1))


@pytest.mark.benchmark(group="add")
class TestBenchmarkAdd:
    @staticmethod
    def test_benchmark_fxplite(benchmark):
        a = make_fxp(1, 2, 2, False)
        b = make_fxp(1, 2, 2, False)

        benchmark(lambda: a + b)

    @staticmethod
    def test_benchmark_fxp(benchmark):
        a = Fxp(1, n_int=2, n_frac=2, signed=False)
        b = Fxp(1, n_int=2, n_frac=2, signed=False)

        benchmark(lambda: a + b)

    @staticmethod
    def test_benchmark_scalar_int(benchmark):
        a = 1
        b = 1

        benchmark(lambda: a + b)

    @staticmethod
    def test_benchmark_scalar_npint(benchmark):
        a = np.uint32(1)
        b = np.uint32(1)

        benchmark(lambda: a + b)
