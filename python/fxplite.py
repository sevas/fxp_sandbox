"""
fxplite - Fixed-point arithmetic for Python
===========================================

This module provides a lightweight implementation of fixed-point arithmetic for Python.
We try to be mostly compatible with the fxpmath package, but with a simpler implementation
that removes some of the more advanced features, focusing on speed.


Design Guidelines
=================
- no automatic scaling of the fixed-point number, user has to request it explicitly
  by setting the n_int and n_frac parameters
- we implement the minimal set of operations for fixed-point math. No automatic overflow
  or saturation
- we aim to make the API as close as possible to the Fxp class from the fxpmath package
- minimal use of functions within the fxplite object itself; mathematical operations
  are inlined where needed to avoid overhead of a function call. Do not hesitate to copy
  the contents of functions into another function if it makes the code faster. The top
  level functions are reference implementations.
- results from functions that, in C or C++, could be macros/templates/const expr depending
  on bit width are stored in a cache when they have been empirically measured to be slower
  than a dict lookup

"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Self


@lru_cache
def fxplite_half_val(n_frac: int) -> int:
    return 1 << (n_frac-1)




@dataclass
class Fxplite:
    # todo: unclear that dataclass is really faster;
    stored_int: int
    n_int: int
    n_frac: int
    signed: bool
    fract_mul: int

    def nbits(self):
        return self.n_int + self.n_frac + int(self.signed)

    def val(self) -> int | float:
        """Return the value of the fixed-point number to a regular python scalar"""
        s = -1 if self.signed else 1
        return s * (self.stored_int >> self.n_frac) + (
                self.stored_int & (0xffff >> (16 - self.n_frac))) / 2 ** self.n_frac

    def int_range(self):
        return 2 ** (self.n_int + self.n_frac)

    def frac_range(self):
        return 2 ** self.n_frac

    def u(self, n_int, n_frac) -> Self:
        """Change encoding without changing value

        This is to be used before performing the next arithmetic operation.
        User must ensure that the new encoding is sufficient to represent the result.
        """
        fracdiff = self.n_frac - n_frac
        if fracdiff < 0:
            fracdiff = -fracdiff
            self.stored_int <<= fracdiff
        elif fracdiff > 0:
            self.stored_int >>= fracdiff
        self.n_int = n_int
        self.n_frac = n_frac
        self.fract_mul = 2 ** n_frac

        return self

    def __add__(self, other: Self) -> Self:
        # return make_fxp(self.val() + other.val(), self.n_frac, self.n_int + 2, self.signed)
        return Fxplite(self.stored_int + other.stored_int, self.n_int, self.n_frac, self.signed, self.fract_mul)

    def __iadd__(self, other: Self) -> Self:
        # return make_fxp(self.val() + other.val(), self.n_frac, self.n_int + 2, self.signed)
        self.stored_int += other.stored_int
        return self

    def __isub__(self, other: Self) -> Self:
        self.stored_int -= other.stored_int
        return self

    def __mul__(self, other):
        val = (self.stored_int * other.stored_int) >> self.n_frac
        return Fxplite(val, self.n_int, self.n_frac, self.signed, self.fract_mul)

    def __imul__(self, other: Self) -> Self:
        self.stored_int *= other.stored_int
        self.stored_int >>= self.n_frac
        return self

    def __divmod__(self, other):
        raise NotImplementedError

    def __truediv__(self, other: Self) -> Self:
        self.stored_int /= other.stored_int
        return self

    def __eq__(self, other: Self) -> bool:
        return self.stored_int == other.stored_int

    def __ne__(self, other: Self) -> bool:
        return self.stored_int != other.stored_int

    def __lt__(self, other: Self) -> bool:
        return self.stored_int < other.stored_int

    def __le__(self, other: Self) -> bool:
        return self.stored_int <= other.stored_int

    def overflow(self):
        return self.stored_int > 2 ** (self.n_int + self.n_frac)

    def as_interim_t(self):
        self.n_frac *= 2
        self.n_int *= 2
        return self


def make_fxp(val: float | int, n_int: int, n_frac: int, signed: bool = False) -> Fxplite:
    # stored_int = int(val)
    # tbd if we keep this check, to be timed
    # if int(val) > 2 ** n_int:
    #     raise OverflowError(f"Value {val} is too large for n_frac={n_frac} and n_int={n_int}")
    fract_mul = 2 ** n_frac
    stored_int = int(val * fract_mul)
    return Fxplite(stored_int, n_int, n_frac, signed, fract_mul)


def U(n: int, f: int) -> Callable[[int | float], Fxplite]:
    def wrapped(x):
        return make_fxp(x, n_int=n, n_frac=f, signed=False)

    return wrapped


def scalar_from_fxp(f: Fxplite) -> float | int:
    return (f.stored_int >> f.n_frac) + (f.stored_int & (0xffff >> (16 - f.n_frac))) / 2 ** f.n_frac


def main():
    f = Fxplite(12, 3, 3, False, 2 ** 3)
    print(Fxplite(12, 2, 3, False, 2 ** 3).val())
    print(Fxplite(21, 2, 3, False, 2 ** 3).val())
    print(Fxplite(31, 2, 3, False, 2 ** 3).val())

    for i in range(f.int_range() + 1):
        b = bin(i)
        f = Fxplite(i, 3, 3, False, 2 ** 3)
        s = scalar_from_fxp(f)
        print(f"{b=} {s=}")

    a = U(12, 2)(3.4)
    assert a == make_fxp(3.4, 12, 2, False)


if __name__ == '__main__':
    main()
