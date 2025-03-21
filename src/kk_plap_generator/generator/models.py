from typing import Iterator, List, Optional, Union, cast
from xml.etree import ElementTree as et

from kk_plap_generator.generator.utils import keyframe_get


class PositionKeyframe:
    node: et.Element

    def __init__(self, node: et.Element):
        self.node = node

    def get_axis_value(self, axis: str) -> float:
        return keyframe_get(self.node, axis)

    @property
    def time(self) -> float:
        return keyframe_get(self.node, "time")

    @property
    def valueX(self) -> float:
        return keyframe_get(self.node, "valueX")

    @property
    def valueY(self) -> float:
        return keyframe_get(self.node, "valueY")

    @property
    def valueZ(self) -> float:
        return keyframe_get(self.node, "valueZ")

    def get(self, field_name: str, default=None):
        return self.node.get(field_name, default)

    def set(self, field_name: str, value):
        self.node.set(field_name, value)

    def __iter__(self) -> Iterator[et.Element]:
        return iter(list(self.node))


class KeyframeReference(PositionKeyframe):
    axis: str
    out_direction: float
    estimated_pull_out: float

    def __init__(
        self,
        node: et.Element,
        *,
        axis: str,
        out_direction: float,
        estimated_pull_out: float,
    ):
        super().__init__(node)
        self.axis = axis
        self.out_direction = out_direction
        self.estimated_pull_out = estimated_pull_out

    @property
    def value(self) -> float:
        return keyframe_get(self.node, self.axis)


class Section:
    reference: "KeyframeReference"
    keyframes: List[et.Element]

    def __init__(self, reference: "KeyframeReference", keyframes: List[et.Element]):
        self.reference = reference
        self.keyframes = keyframes


class PlapAxis:
    value: str

    def __init__(self, value: Optional[Union[str, "PlapAxis"]] = None):
        if isinstance(value, PlapAxis):
            self.value = value.value
        else:
            self.value = cast(str, value) or "to_be_set"

    def __repr__(self):
        return f"PlapAxis({self.value})"


class PlapFrame:
    time: float
    valueX: float
    valueY: float
    valueZ: float
    axis: PlapAxis

    def __init__(
        self, time: float, valueX: float, valueY: float, valueZ: float, axis: PlapAxis
    ):
        self.time = time
        self.valueX = valueX
        self.valueY = valueY
        self.valueZ = valueZ
        self.axis = axis

    @property
    def value(self) -> float:
        if self.axis.value == "valueX":
            return self.valueX
        elif self.axis.value == "valueY":
            return self.valueY
        elif self.axis.value == "valueZ":
            return self.valueZ
        else:
            raise ValueError(f"Invalid axis: {self.axis.value}")

    def __repr__(self):
        return f"PlapFrame({self.time}, {self.valueX}, {self.valueY}, {self.valueZ}, {self.axis})"


class PlapFrameReference(PlapFrame):
    out_direction: float
    estimated_pull_out: float

    def __init__(
        self,
        time: float,
        valueX: float,
        valueY: float,
        valueZ: float,
        axis: PlapAxis,
        out_direction: float,
        estimated_pull_out: float,
    ):
        super().__init__(time, valueX, valueY, valueZ, axis)
        self.out_direction = out_direction
        self.estimated_pull_out = estimated_pull_out
