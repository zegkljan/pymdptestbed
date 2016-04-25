import itertools


def prod(a: int, b: int):
    return itertools.product(range(a), range(b))
