from typing import List


class InfiniteIterator:
    def __init__(self, data):
        self.data: List[int] = data
        self.index: int = 0

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if not self.data:
            raise StopIteration("The data list is empty.")
        value = self.data[self.index]
        self.index = (self.index + 1) % len(self.data)
        return value
