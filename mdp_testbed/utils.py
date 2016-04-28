import itertools


def prod(a: int, b: int):
    return itertools.product(range(a), range(b))


class Container(object):
    def __init__(self, contents=None):
        self._contents = contents

    @property
    def val(self):
        return self._contents

    @val.setter
    def val(self, contents):
        self._contents = contents
