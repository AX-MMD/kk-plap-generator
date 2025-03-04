import copy
import math
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, OrderedDict, Tuple, Union, cast
from xml.etree import ElementTree as et

from kk_plap_generator import settings
from kk_plap_generator.generator.utils import InfiniteIterator
from kk_plap_generator.models import (
    ActivableComponentConfig,
    ComponentConfig,
    MultiActivableComponentConfig,
    PregPlusComponentConfig,
)

if TYPE_CHECKING:
    Section = Tuple["KeyframeReference", List[et.Element]]


class PlapGenerator:
    """
    Generate sound sequences for animations based on a given pattern and keyframe data.

    Parameters
    ----------
    interpolable_path : str
        The path to the interpolable to use as reference for the SFX.
    ref_keyframe_time : str
        The reference keyframe time where the subject is fully inserted.
    offset : float, optional
        Offset in seconds, positive or negative, to adjust the timing of the SFX.
    min_pull_out : float, optional
        Minimum percent distance (0.0 to 1.0) the subject needs to pull away from the contact point before re-enabling plaps.
    min_push_in : float, optional
        Minimum percent distance (0.0 to 1.0) the subject needs to push toward the contact point for a plap to register.
    time_ranges : list of tuple of str, optional
        Optional list of time ranges for the SFX, each range is a pair of strings (MM:SS.SS).
    pattern_string : str, optional
        The pattern string to generate the plap sequence.
    sound_components : list of str, optional
        List of names of the components to use (Those containing the sound items).
        Default is ["Plap1", "Plap2", "Plap3", "Plap4"].
    template_path : str, optional
        Path to the template XML file.

    Attributes
    ----------
    valid_patern_chars : list of str
        Valid characters for the pattern string.

    Methods
    -------
    generate_plap_xml(self, timeline_xml_tree: et.ElementTree) -> et.Element:
        Generates the plap XML nodes based on the given timeline XML tree.
    """

    VALID_PATTERN_CHARS = ["V", "A", "W", "M", "\\", "/"]

    class ReferenceNotFoundError(Exception):
        def __init__(self, time: str):
            self.time = time
            self.message = f"Reference keyframe not found at {time}."
            super().__init__(self.message)

    class NotSupportedInterpolableType(Exception):
        def __init__(self, type: str):
            self.type = type
            self.message = f"Interpolable type {type} is not supported."
            super().__init__(self.message)

    class GeneratorResult:
        def __init__(
            self,
            interpolables: List[et.Element],
            keyframes_count: int,
            time_range: Tuple[str, str],
        ):
            self.interpolables = interpolables
            self.keyframes_count = keyframes_count
            self.time_range = time_range

    def __init__(
        self,
        # config file params START ###
        interpolable_path: str,
        time_ranges: List[Tuple[str, str]],
        component_configs: List[ComponentConfig],
        offset: float = 0.0,
        min_pull_out: float = 0.2,
        min_push_in: float = 0.8,
        template_path: str = settings.TEMPLATE_FILE,
        # config file params END ###
    ):
        # config file params START ###
        self.interpolable_path = interpolable_path
        self.time_ranges = time_ranges
        self.offset = float(offset)  # Just in case we receive a string
        self.min_pull_out = float(min_pull_out)
        self.min_push_in = float(min_push_in)
        # self.pattern_string = pattern_string.upper()
        # for pattern_char in self.pattern_string:
        #     if pattern_char not in self.VALID_PATTERN_CHARS:
        #         raise ValueError(
        #             f"Invalid pattern {self.pattern_string}, valid characters are {', '.join(self.VALID_PATTERN_CHARS)} or a combination of them."
        #         )

        self.component_configs: List[ComponentConfig] = component_configs
        self.template_path = template_path
        # config file params END ###

    # @property
    # def ref_keyframe_time(self):
    #     return self._ref_keyframe_time

    # @ref_keyframe_time.setter
    # def ref_keyframe_time(self, value):
    #     self._ref_keyframe_time = value
    #     self._ref_kf_seconds = self._std_time(convert_KKtime_to_seconds(value))

    def get_time_ranges_sec(self) -> List[Tuple[float, float]]:
        if self.time_ranges:
            ranges = [
                [convert_KKtime_to_seconds(tg[0]), convert_KKtime_to_seconds(tg[1])]
                for tg in self.time_ranges
            ]
            # Make sure the ranges are sorted and don't overlap
            ranges.sort(key=lambda x: x[0])
            for i in range(0, len(ranges) - 1):
                if ranges[i][1] > ranges[i + 1][0]:
                    ranges[i][1] = ranges[i + 1][0] - 0.00001

            return [(ranges[i][0], ranges[i][1]) for i in range(0, len(ranges))]

        else:
            return [(0.0, math.inf)]

    def generate_xml(
        self, timeline_xml_tree: et.ElementTree
    ) -> List["PlapGenerator.GeneratorResult"]:
        # Get the rythm from source single_file, will use parameters from the config to locate the node
        ref_interpolable = deep_find_interpolable(
            list(timeline_xml_tree.getroot()), self.interpolable_path.split(".")[-1]
        )
        if ref_interpolable is NOT_FOUND:
            print(f"Interpolable {self.interpolable_path} not found in the timeline.")
            ref_interpolable = find_interpolable(
                timeline_xml_tree.getroot(), self.interpolable_path
            )

        keyframes_dict: OrderedDict[float, et.Element] = OrderedDict(
            [(keyframe_get(k, "time"), k) for k in list(ref_interpolable)]
        )
        sections: List["Section"] = []
        for time_start, time_end in self.get_time_ranges_sec():
            # Get the keyframes that are within the time range
            kfs = [
                kf
                for time, kf in keyframes_dict.items()
                if self._round(time_start) - 0.00001 <= time
                and self._round(time) <= time_end + 0.00001
            ]
            sections.append((self.get_reference(kfs), kfs))

        # Get the base nodes from template
        template_tree = et.parse(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), self.template_path)
        )

        results: List["PlapGenerator.GeneratorResult"] = []
        for ac in (
            cc
            for cc in self.component_configs
            if isinstance(cc, ActivableComponentConfig)
        ):
            results.append(
                self.generate_activable_component_xml(
                    copy.deepcopy(template_tree.getroot()), sections, ac
                )
            )

        for ppc in (
            cc for cc in self.component_configs if isinstance(cc, PregPlusComponentConfig)
        ):
            results.append(
                self.generate_preg_plus_component_xml(
                    copy.deepcopy(template_tree.getroot()), sections, ppc
                )
            )

        return results

    def generate_preg_plus_component_xml(
        self, root: et.Element, sections: List["Section"], pc: PregPlusComponentConfig
    ) -> "PlapGenerator.GeneratorResult":
        base_interpolable = root.find("""interpolable[@alias='Preg+']""")
        if base_interpolable is None:
            raise NodeNotFoundError(
                "interpolable", tag="alias", value="Preg+", xml_path=self.template_path
            )
        else:
            base_interpolable.set("alias", f"{pc.name}")

        in_keyframe = (
            base_interpolable.find(f"keyframe[@alias='{pc.in_curve}']") or NOT_FOUND
        )
        if in_keyframe is NOT_FOUND:
            raise NodeNotFoundError(
                f"keyframe[@alias='{pc.in_curve}']", xml_path=self.template_path
            )
        else:
            in_keyframe.set("value", str(pc.min_value))

        out_keyframe = (
            base_interpolable.find(f"keyframe[@alias='{pc.out_curve}']") or NOT_FOUND
        )
        if out_keyframe is NOT_FOUND:
            raise NodeNotFoundError(
                f"keyframe[@alias='{pc.out_curve}']", xml_path=self.template_path
            )
        else:
            out_keyframe.set("value", str(pc.max_value))

        # Remove the template keyframes from our base plap node
        for child in list(base_interpolable):
            base_interpolable.remove(child)

        root.remove(base_interpolable)

        first_keyframe = copy.deepcopy(in_keyframe)
        first_keyframe.set("time", str(0.0))
        first_keyframe.set("value", str(0))
        base_interpolable.append(first_keyframe)

        # For each keyframe in the sections, we assign a value between pc.min_value and pc.max_value based on the distance from the reference keyframe.
        for section in sections:
            reference = section[0]
            is_plap = True
            for keyframe in section[1]:
                value = keyframe_get(keyframe, reference.axis)
                distance = abs(value - reference.value)
                if (
                    reference.out_direction == -1
                    and value > reference.value
                    or reference.out_direction == 1
                    and value < reference.value
                ):
                    preg_value = pc.max_value
                    is_plap = True
                elif distance > reference.estimated_pull_out:
                    preg_value = pc.min_value
                    is_plap = False
                else:
                    preg_value = int(
                        (reference.estimated_pull_out - distance)
                        / reference.estimated_pull_out
                        * pc.max_value
                    )
                    preg_value = max(preg_value, pc.min_value)

                new_keyframe = (
                    copy.deepcopy(out_keyframe) if is_plap else copy.deepcopy(in_keyframe)
                )
                new_keyframe.set(
                    "time", str(keyframe_get(keyframe, "time") + self.offset + pc.offset)
                )
                new_keyframe.set("value", str(preg_value))
                base_interpolable.append(new_keyframe)
                is_plap = not is_plap

        return PlapGenerator.GeneratorResult(
            [base_interpolable],
            len(list(base_interpolable)),
            (
                convert_seconds_to_KKtime(keyframe_get(sections[0][1][0], "time")),
                convert_seconds_to_KKtime(keyframe_get(sections[-1][1][-1], "time")),
            ),
        )

    def generate_activable_component_xml(
        self, root: et.Element, sections: List["Section"], ac: ActivableComponentConfig
    ) -> "PlapGenerator.GeneratorResult":
        base_sfx: et.Element = root.find("""interpolable[@alias='3DSE']""") or NOT_FOUND
        if base_sfx is NOT_FOUND:
            raise NodeNotFoundError(
                "interpolable", tag="alias", value="3DSE", xml_path=self.template_path
            )
        else:
            base_sfx.set("alias", f"{ac.name}")

        sfx_keyframe = base_sfx.find("keyframe") or NOT_FOUND
        if sfx_keyframe is NOT_FOUND:
            raise NodeNotFoundError("keyframe", xml_path=self.template_path)
        else:
            sfx_keyframe.set("value", "false")

        # Remove the template keyframes from our base plap node
        for child in list(base_sfx):
            base_sfx.remove(child)

        root.remove(base_sfx)

        # Create the patern
        if isinstance(ac, MultiActivableComponentConfig):
            sequence = self.generate_sequence(ac.pattern, len(ac.item_configs))
        else:
            sequence = self.generate_sequence(self.VALID_PATTERN_CHARS[0], 1)

        # We find at what time the activable component should be triggered
        keyframe_times: List[float] = []
        for section in sections:
            did_plap = False
            reference = section[0]
            for keyframe in section[1]:
                value = keyframe_get(keyframe, reference.axis)
                distance = abs(reference.value - value)
                if did_plap:
                    # Only re-enable plapping after a minimum out distance is reached
                    if (
                        reference.out_direction == 1
                        and value > reference.value
                        or reference.out_direction == -1
                        and value < reference.value
                    ) and distance >= self._round(  # Round to avoid floating point errors
                        self.min_pull_out * reference.estimated_pull_out
                    ):
                        did_plap = False
                else:
                    if (
                        reference.out_direction == 1
                        and value <= reference.value
                        or reference.out_direction == -1
                        and value >= reference.value
                    ) or distance < self._round(
                        (1.0 - self.min_push_in) * reference.estimated_pull_out
                    ):
                        keyframe_times.append(keyframe_get(keyframe, "time"))
                        did_plap = True

        # Create the interpolables
        interpolables: List[et.Element] = []
        item_configs: List[ActivableComponentConfig] = (
            ac.item_configs if isinstance(ac, MultiActivableComponentConfig) else [ac]
        )
        offset = (
            self.offset + ac.offset
            if isinstance(ac, MultiActivableComponentConfig)
            else self.offset
        )
        cutoff = ac.cutoff if isinstance(ac, MultiActivableComponentConfig) else math.inf

        for i, ic in enumerate(item_configs):
            plap: et.Element = copy.deepcopy(base_sfx)
            plap.set("alias", f"{ic.name}")
            plap.set("objectIndex", f"{plap.get('objectIndex')}{i + 1}")
            interpolables.append(plap)

        # Generate the keyframes
        pattern_iter = InfiniteIterator(sequence)
        for time in keyframe_times:
            i = next(pattern_iter)
            plap = interpolables[i]
            pc = item_configs[i]
            mute_keyframe = copy.deepcopy(sfx_keyframe)
            mute_keyframe.set("time", str(time - 0.1 + offset + pc.offset))
            mute_keyframe.set("value", "false")
            plap.append(mute_keyframe)
            new_keyframe = copy.deepcopy(sfx_keyframe)
            new_keyframe.set("time", str(time + offset + pc.offset))
            new_keyframe.set("value", "true")
            plap.append(new_keyframe)
            cutoff = pc.cutoff + cutoff if cutoff < math.inf else pc.cutoff
            if cutoff < math.inf:
                cutoff_keyframe = copy.deepcopy(sfx_keyframe)
                cutoff_keyframe.set("time", str(time + offset + pc.offset + cutoff))
                cutoff_keyframe.set("value", "false")
                plap.append(cutoff_keyframe)

        return PlapGenerator.GeneratorResult(
            interpolables,
            len(keyframe_times),
            (
                convert_seconds_to_KKtime(keyframe_times[0]),
                convert_seconds_to_KKtime(keyframe_times[-1]),
            ),
        )

    def generate_sequence(self, pattern_string: str, count: int) -> List[int]:
        last_index = len(pattern_string) - 1
        pattern = self.generate_patterns(count)
        sequence = []
        for p, char in enumerate(pattern_string):
            pattern_chunk = pattern[char]
            sequence += pattern_chunk
            if p != last_index:
                sequence.append(pattern_chunk[0])

        return sequence

    def get_reference(self, node_list: List[et.Element]) -> "KeyframeReference":
        # We itterate instead of an exact search because the "time" attribute can have a higher precision than what the user can provide.
        ref_keyframe = node_list[0]
        ref_index = 0
        reference = Keyframe(
            node=ref_keyframe,
            time=keyframe_get(ref_keyframe, "time"),
            valueX=keyframe_get(ref_keyframe, "valueX"),
            valueY=keyframe_get(ref_keyframe, "valueY"),
            valueZ=keyframe_get(ref_keyframe, "valueZ"),
        )

        # Once we found the reference keyframe, we check the next keyframe and calculate the difference between reference and next_keyframe.
        # The axis with the biggest difference will be our axis reference.
        # We also use the difference to determnine the direction of the pull out as 1 or -1.
        next_frame = None
        try:
            next_frame = node_list[ref_index + 1]
        except IndexError:
            raise IndexError("The reference keyframe cannot be the last keyframe.")

        x = keyframe_get(next_frame, "valueX") - reference.valueX
        y = keyframe_get(next_frame, "valueY") - reference.valueY
        z = keyframe_get(next_frame, "valueZ") - reference.valueZ

        if abs(z) < abs(x) > abs(y):
            axis = "valueX"
            out_direction = x / abs(x)
        elif abs(z) < abs(y) > abs(x):
            axis = "valueY"
            out_direction = y / abs(y)
        else:
            axis = "valueZ"
            out_direction = z / abs(z)

        # We then try and estimate the pull out distance by taking the biggest difference between the reference keyframe and (up too) the next 5 keyframes.
        estimated_pull_out = max(
            abs(keyframe_get(node_list[j], axis) - getattr(reference, axis))
            for j in range(ref_index, min(ref_index + 6, len(node_list)))
        )

        return KeyframeReference(
            node=reference.node,
            time=reference.time,
            valueX=reference.valueX,
            valueY=reference.valueY,
            valueZ=reference.valueZ,
            axis=axis,
            out_direction=out_direction,
            estimated_pull_out=estimated_pull_out,
        )

    def generate_patterns(self, count) -> Dict[str, List[int]]:
        # fmt: off
        return {
            "W": [i for i in range(count)] \
                + [i for i in range(count - 2, int(math.ceil(count / 2)) - 1, -1)] \
                + [i for i in range(int(math.ceil(count / 2)) - 1, count - 1)] \
                + [i for i in range(count - 1, 0, -1)],
            "M": [i for i in range(count - 1, -1, -1)] \
                + [i for i in range(1, int(math.ceil(count / 2)) + 1)] \
                + [i for i in range(int(math.ceil(count / 2)) - 1, 0, -1)] \
                + [i for i in range(count - 1)],
            "V": [i for i in range(count)] + [i for i in range(count - 2, 0, -1)],
            "A": [i for i in range(count - 1, 0, -1)] + [i for i in range(count - 1)],
            "/": [i for i in range(count - 1, -1, -1)],
            "\\": [i for i in range(count)],
        }
        # fmt: on

    def _round(self, value: float) -> float:
        factor = 10.0**5
        return int(value * factor) / factor

    def _std_time(self, time: Union[str, int, float]) -> float:
        return self._round(float(time))


def keyframe_get(keyframe: et.Element, key: str) -> float:
    return float(cast(str, keyframe.get(key)))


@dataclass
class Keyframe:
    node: et.Element
    time: float
    valueX: float
    valueY: float
    valueZ: float


@dataclass
class KeyframeReference(Keyframe):
    axis: str
    out_direction: float
    estimated_pull_out: float

    @property
    def value(self) -> float:
        return getattr(self, self.axis)


NOT_FOUND = et.Element("notfound")


class NodeNotFoundError(Exception):
    def __init__(
        self,
        node_name,
        tag: Optional[str] = None,
        value: Optional[str] = None,
        *args,
        path: Optional[str] = None,
        xml_path: Optional[str] = None,
    ):
        self.node_name = node_name
        self.tag = tag
        self.value = value
        self.path = path
        self.xml_path = xml_path
        self.message = f"Node not found: {self.get_node_string()}"
        super().__init__(self.message, *args)

    def get_node_string(self):
        s = f"<{self.node_name}"
        s += (
            f" {self.tag}{("='" + self.value + "'") if self.value else ''}"
            if self.tag
            else ""
        )
        s += ">"
        return s


def deep_find_interpolable(node_list: List[et.Element], target: str) -> et.Element:
    for node in node_list:
        if node.tag == "interpolable" and node.get("alias") == target:
            return node
        else:
            found = deep_find_interpolable(list(node), target)
            if found is not NOT_FOUND:
                return found

    return NOT_FOUND


def find_interpolable(root: et.Element, target: str) -> et.Element:
    node: et.Element = root
    tag, value, child = convert_string_to_nested_list(target)
    path = []
    while child is not None:
        path.append(value)
        node = node.find(f"""interpolableGroup[@{tag}='{value}']""") or NOT_FOUND
        if node is NOT_FOUND:
            raise NodeNotFoundError("interpolableGroup", tag, value, path=".".join(path))

        tag, value, child = child

    node = node.find(f"""interpolable[@{tag}='{value}']""") or NOT_FOUND
    if node is NOT_FOUND:
        raise NodeNotFoundError("interpolable", tag, value)

    return node


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
