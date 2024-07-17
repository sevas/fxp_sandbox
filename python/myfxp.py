from dataclasses import dataclass
from typing import Callable, Self


@dataclass
class fxp():
    stored_int: int
    n_int: int
    n_frac: int
    signed: bool

    def nbits(self):
        return self.n_int + self.n_frac + int(self.signed)

    def val(self) -> int | float:
        s = -1 if self.signed else 1
        return s * (f.stored_int >> f.n_frac) + (f.stored_int & (0xffff >> (16-f.n_frac))) / 2**f.n_frac

    def int_range(self):
        return 2**(self.n_int + self.n_frac)

    def __add__(self, other: Self) -> Self:
        return make_fxp(self.val()+other.val(), self.n_frac, self.n_int+2, self.signed)

def make_fxp(rawval: float | int, n_frac: int, n_int: int, signed: bool = False) -> fxp:

    stored_int = int(rawval)
    if stored_int > 2**(n_int):
        raise ValueError(f"Value {rawval} is too large for n_frac={n_frac} and n_int={n_int}")

    stored_frac = int((rawval - stored_int) * 2**n_frac)
    stored_int = stored_int << n_frac
    return fxp(stored_int + stored_frac, n_int, n_frac, signed)

#
# def U(n: int, f: int) -> Callable[[fxp], int|float]:
#
#     def wrapped(x):
#          return fxp(x, n, f)
#     return wrapped
#
#
# a = U(12, 2)(3.4)
#

def scalar_from_fxp(f: fxp) -> float|int:

    return (f.stored_int >> f.n_frac) + (f.stored_int & (0xffff >> (16-f.n_frac)) ) / 2**f.n_frac


if __name__ == '__main__':

    f = fxp(12, 3, 3, False)
    print(fxp(12, 3, 2, False).val())
    print(fxp(21, 3, 2, False).val())
    print(fxp(31, 3, 2, False).val())

    for i in range(f.int_range()+1):
        b = bin(i)
        f = fxp(i, 3, 3, False)
        s = scalar_from_fxp(f)
        print(f"{b=} {s=}")
