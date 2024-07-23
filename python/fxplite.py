from dataclasses import dataclass
from typing import Callable, Self


@dataclass
class Fxplite:
    stored_int: int
    n_int: int
    n_frac: int
    signed: bool

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
        self.n_int = n_int
        self.n_frac = n_frac
        return self

    def __add__(self, other: Self) -> Self:
        # return make_fxp(self.val() + other.val(), self.n_frac, self.n_int + 2, self.signed)
        self.stored_int += other.stored_int
        return self


def make_fxp(val: float | int, n_int: int, n_frac: int, signed: bool = False) -> Fxplite:
    stored_int = int(val)

    # tbd if we keep this check, to be timed
    if stored_int > 2 ** n_int:
        raise OverflowError(f"Value {val} is too large for n_frac={n_frac} and n_int={n_int}")

    stored_frac = int((val - stored_int) * 2 ** n_frac)
    stored_int = stored_int << n_frac
    return Fxplite(stored_int + stored_frac, n_int, n_frac, signed)


def U(n: int, f: int) -> Callable[[int | float], Fxplite]:
    def wrapped(x):
        return make_fxp(x, n_int=n, n_frac=f, signed=False)

    return wrapped




def scalar_from_fxp(f: Fxplite) -> float | int:
    return (f.stored_int >> f.n_frac) + (f.stored_int & (0xffff >> (16 - f.n_frac))) / 2 ** f.n_frac


def main():
    f = Fxplite(12, 3, 3, False)
    print(Fxplite(12, 2, 3, False).val())
    print(Fxplite(21, 2, 3, False).val())
    print(Fxplite(31, 2, 3, False).val())

    for i in range(f.int_range() + 1):
        b = bin(i)
        f = Fxplite(i, 3, 3, False)
        s = scalar_from_fxp(f)
        print(f"{b=} {s=}")

    a = U(12, 2)(3.4)
    assert a == make_fxp(3.4, 12, 2, False)

if __name__ == '__main__':
    main()
