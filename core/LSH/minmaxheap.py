import operator
from collections import namedtuple

class Heap:
    def __init__(self, kind='min'):
        operators_type = namedtuple('Operators', 'lt, lte, gt, gte')

        kinds = {
            'min': operators_type(
                        operator.lt,
                        operator.le,
                        operator.gt,
                        operator.ge),

            'max': operators_type(
                        operator.gt,
                        operator.ge,
                        operator.lt,
                        operator.le),
        }

        if kind not in kinds:
            raise ValueError('No such kind "%s"' % (kind))

        self.operators = kinds[kind]
        self.heap = [None]


    def __len__(self):
        return len(self.heap) - 1

    def empty(self):
        return len(self.heap) - 1 == 0

    @staticmethod
    def swap(_list, a, b):
        tmp = _list[a]
        _list[a] = _list[b]
        _list[b] = tmp

    def insert(self, value):
        if value is None:
            raise TypeError('"value" cannot be of NoneType')

        self.heap.append(value)
        self.bubble_up(len(self.heap) - 1)

    def bubble_up(self, i):
        lt, lte, gt, gte = self.operators

        while i > 1:
            h = i // 2
            if lt(self.heap[i], self.heap[h]):
                self.swap(self.heap, i, h)

            i = h

    def percolate_down(self, i):
        lt, lte, gt, gte = self.operators

        while (i * 2) < len(self.heap):
            d = i * 2
            if (d + 1 < len(self.heap) and gte(self.heap[d], self.heap[d + 1])):
                d += 1

            if gt(self.heap[i], self.heap[d]):
                self.swap(self.heap, i, d)

            i = d

    def head(self):
        if len(self.heap) == 1:
            return None

        return self.heap[1]

    def pop_head(self):
        if len(self.heap) == 1:
            return None

        item = self.heap[1]
        last = self.heap.pop(-1)

        if len(self.heap) > 1:
            self.heap[1] = last
            self.percolate_down(1)

        return item

    def get_items(self):
        return self.heap[1:]

    def __repr__(self):
        return self.heap[1:].__repr__()


class MaxKList:
    def __init__(self, maxsize):
        self.maxsize=maxsize
        self._arr = Heap(kind="min")

    def insert(self, ele):
        if len(self._arr) >= self.maxsize:
            if ele > self._arr.head():
                self._arr.pop_head()
                self._arr.insert(ele)
        else:
            self._arr.insert(ele)

    def get_items(self):
        return self._arr.get_items()

    def __repr__(self):
        return self._arr.__repr__()


class MinKList:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._arr = Heap(kind="max")

    def insert(self, ele):
        if len(self._arr) >= self.maxsize:
            if ele < self._arr.head():
                self._arr.pop_head()
                self._arr.insert(ele)
        else:
            self._arr.insert(ele)

    def get_items(self):
        return self._arr.get_items()

    def __repr__(self):
        return self._arr.__repr__()

