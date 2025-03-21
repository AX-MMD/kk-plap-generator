import math
from typing import Any, List, cast
from xml.etree import ElementTree as et


class InfiniteIterator:
    def __init__(self, data):
        self.data: List[int] = data
        self.index: int = 0

    def preview_next(self) -> int:
        if not self.data:
            raise StopIteration("The data list is empty.")

        return self.data[(self.index + 1) % len(self.data)]

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if not self.data:
            raise StopIteration("The data list is empty.")
        value = self.data[self.index]
        self.index = (self.index + 1) % len(self.data)
        return value


def keyframe_get(keyframe: et.Element, key: str) -> float:
    return round(float(cast(str, keyframe.get(key))), 5)


def keyframe_set(keyframe: et.Element, key: str, value: Any):
    keyframe.set(key, str(value))


def convert_string_to_nested_list(s: str):
    parts = s.split(".")
    nested_list = None
    for part in reversed(parts):
        nested_list = ["alias" if nested_list is None else "name", part, nested_list]
    return nested_list


def convert_KKtime_to_seconds(time_str: str) -> float:
    """Convert a time string of format 'MM:SS.SS' to seconds in float"""
    if time_str.upper() == "END":
        return math.inf
    else:
        minutes, seconds_fraction = time_str.split(":")
        seconds, fraction = seconds_fraction.split(".")
        return int(minutes) * 60 + int(seconds) + float(f"0.{fraction}")


def convert_seconds_to_KKtime(secs: float) -> str:
    """Convert seconds to a time string of format 'MM:SS.SS'"""
    minutes = int(secs // 60)
    seconds = int(secs % 60)
    fraction = int((secs % 1) * 100)
    return f"{minutes:02}:{seconds:02}.{fraction:02}"
