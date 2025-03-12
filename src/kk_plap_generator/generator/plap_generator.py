import copy
import math
import os
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from xml.etree import ElementTree as et

from kk_plap_generator import settings
from kk_plap_generator.generator.models import KeyframeReference, Section
from kk_plap_generator.generator.utils import (
    InfiniteIterator,
    convert_KKtime_to_seconds,
    convert_seconds_to_KKtime,
    keyframe_get,
)
from kk_plap_generator.generator.xml_node_finder import (
    NODE_NOT_FOUND,
    NodeNotFoundError,
    deep_find_interpolable,
    find_interpolable,
)
from kk_plap_generator.models import (
    ActivableComponentConfig,
    ComponentConfig,
    MultiActivableComponentConfig,
    PregPlusComponentConfig,
)


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

    class Error(Exception):
        pass

    class ReferenceNotFoundError(Error):
        def __init__(self, time: str):
            self.time = time
            self.message = f"Reference keyframe not found at {time}."
            super().__init__(self.message)

    class NotSupportedInterpolableType(Error):
        def __init__(self, type: str):
            self.type = type
            self.message = f"Interpolable type {type} is not supported."
            super().__init__(self.message)

    class ValueError(Error):
        pass

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
        interpolable_path: str,
        time_ranges: List[Tuple[str, str]],
        component_configs: List[ComponentConfig],
        offset: float = 0.0,
        min_pull_out: float = 0.2,
        min_push_in: float = 0.8,
        template_path: str = settings.TEMPLATE_FILE,
    ):
        self.interpolable_path = interpolable_path
        self.time_ranges = time_ranges
        self.offset = float(offset)  # Just in case we receive a string
        if not 0.0 <= min_pull_out <= 1.0 or not 0.0 <= min_push_in <= 1.0:
            raise PlapGenerator.ValueError(
                f"min_pull_out and min_push_in must be between 0.0 and 1.0, got {min_pull_out} and {min_push_in}."
            )
        self.min_pull_out = float(min_pull_out)
        self.min_push_in = float(min_push_in)
        self.component_configs: List[ComponentConfig] = component_configs
        self.template_path = template_path

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
        if ref_interpolable is NODE_NOT_FOUND:
            ref_interpolable = find_interpolable(
                timeline_xml_tree.getroot(), self.interpolable_path
            )

        # Separate the keyframes into sections based on the time ranges
        sections: List[Section] = self.make_sections(ref_interpolable)

        # Get the base nodes from template
        template_tree = et.parse(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), self.template_path)
        )

        # Generate the keyframes for each component
        results: List[PlapGenerator.GeneratorResult] = []
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
        self,
        root: et.Element,
        sections: List["Section"],
        pc: PregPlusComponentConfig,
    ) -> "PlapGenerator.GeneratorResult":
        base_interpolable, in_keyframe, out_keyframe = self.make_preg_plus_nodes(root, pc)
        first_keyframe = copy.deepcopy(in_keyframe)
        first_keyframe.set("time", str(0.0))
        first_keyframe.set("value", str(0))
        base_interpolable.append(first_keyframe)

        # For each keyframe in the sections, we assign a value between pc.min_value and pc.max_value
        # based on the distance from the reference keyframe.
        for section in sections:
            reference = section.reference
            is_plap = True

            for keyframe in section.keyframes:
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

                if new_keyframe.get("alias") == "Same as reference":
                    for curve_keyframe in list(keyframe):
                        new_keyframe.append(copy.deepcopy(curve_keyframe))

                is_plap = not is_plap
                base_interpolable.append(new_keyframe)

        base_interpolable.set("alias", f"{pc.name}")
        return PlapGenerator.GeneratorResult(
            [base_interpolable],
            len(list(base_interpolable)),  # Keyframes count
            (  # Time range
                convert_seconds_to_KKtime(keyframe_get(sections[0].keyframes[0], "time")),
                convert_seconds_to_KKtime(
                    keyframe_get(sections[-1].keyframes[-1], "time")
                ),
            ),
        )

    def generate_activable_component_xml(
        self,
        root: et.Element,
        sections: List["Section"],
        ac: ActivableComponentConfig,
    ) -> "PlapGenerator.GeneratorResult":
        base_sfx, sfx_keyframe = self.make_activable_nodes(root, ac)

        # Create the patern
        if isinstance(ac, MultiActivableComponentConfig):
            sequence = self.generate_sequence(ac.pattern, len(ac.item_configs))
        else:
            sequence = self.generate_sequence(self.VALID_PATTERN_CHARS[0], 1)

        # We find at what time the activable component should be triggered
        keyframe_times: List[float] = []
        for section in sections:
            keyframe_times += self.get_plaps_from_keyframes(
                section.reference, section.keyframes
            )[1]

        # Create the interpolables
        interpolables: List[et.Element] = []
        item_configs: List[ActivableComponentConfig] = (
            ac.item_configs if isinstance(ac, MultiActivableComponentConfig) else [ac]
        )
        offset = self.offset + ac.offset
        cutoff = ac.cutoff

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

    def get_plaps_from_keyframes(
        self,
        reference: "KeyframeReference",
        keyframes: List[et.Element],
        curve_reference: Optional[et.Element] = None,
    ) -> Tuple[bool, List[float]]:
        keyframe_times: List[float] = []
        did_plap = False
        pull_out_dist = reference.estimated_pull_out
        # out direction 1 means the reference is pulling away by increasing his axis value
        # (ex. out direction 1) impact at X:0.0, pulling away to X:1.0
        # (ex. out direction -1) impact at X:0.0, pulling away to X:-1.0
        # (ex. out direction 1) impact at X:-2.0, pulling away to X:7.0
        # (ex. out direction -1) impact at X:-2.0, pulling away to X:-9.0
        out_direction = reference.out_direction
        prev_keyframe: et.Element = et.Element("base")

        for keyframe in keyframes:
            if curve_reference is not None:
                # When in curve mode, it means we found a plap keyframe and are currently
                # checking if at any point in the interpolation curve of the previous
                # keyframe there was one or more plaps. (can happen in custom curves)
                value_diff = reference.value - keyframe_get(
                    curve_reference, reference.axis
                )
                value = self._round(
                    reference.value - value_diff * (1.0 - keyframe_get(keyframe, "value"))
                )
            else:
                value = keyframe_get(keyframe, reference.axis)

            distance = abs(reference.value - value)

            if did_plap:
                # Only re-enable plapping after a minimum distance in the out direction is reached.
                # This is to avoid spam during rapid micro movements, like during orgams and such.
                if (
                    value * out_direction > reference.value * out_direction
                    # Round to avoid floating point errors
                    and distance >= self._round(self.min_pull_out * pull_out_dist)
                ):
                    did_plap = False

            # Only plap if we did not plap on the last keyframe and are close enough to the reference keyframe.
            elif (
                value * out_direction <= reference.value * out_direction
                or distance < self._round((1.0 - self.min_push_in) * pull_out_dist)
            ):
                if curve_reference is not None:
                    time_diff = reference.time - keyframe_get(curve_reference, "time")
                    time_offset = time_diff * (1.0 - keyframe_get(keyframe, "time"))
                    keyframe_times.append(self._round(reference.time - time_offset))
                else:
                    did_plap, curve_keyframe_times = self.get_plaps_from_keyframes(
                        KeyframeReference(
                            keyframe,
                            axis=reference.axis,
                            out_direction=reference.out_direction,
                            estimated_pull_out=reference.estimated_pull_out,
                        ),
                        list(prev_keyframe),
                        curve_reference=prev_keyframe,
                    )
                    keyframe_times += curve_keyframe_times

                    if not did_plap:
                        keyframe_times.append(keyframe_get(keyframe, "time"))

                did_plap = True

            # Else we are probably not completely pulled out or in a spasm, so we do nothing.

            prev_keyframe = keyframe

        return did_plap, keyframe_times

    def make_sections(self, ref_interpolable: et.Element) -> List["Section"]:
        sections: List[Section] = []

        for time_start, time_end in self.get_time_ranges_sec():
            kfs = []
            # Will be used to check curve keyframes preceding the reference.
            before_start_keyframe = None

            # Get the keyframes that are within the time range
            for kf in list(ref_interpolable):
                time = keyframe_get(kf, "time")
                if (
                    self._std_time(time_start) - 0.00001 <= time
                    and self._std_time(time) <= time_end + 0.00001
                ):
                    kfs.append(kf)
                elif len(kfs) == 0:
                    before_start_keyframe = kf
                else:
                    break  # We are done with the time range

            reference = self.get_reference(kfs)
            if before_start_keyframe is not None:
                kfs.insert(0, before_start_keyframe)

            sections.append(Section(reference, kfs))

        return sections

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
        # The first keyframe of a time range should be a keyframe where the two bodies collide.
        ref_index = 0
        reference = node_list[0]

        # We check the next keyframe and calculate the difference between reference and next_keyframe.
        # The axis with the biggest difference will be our axis reference.
        # We also use the difference to determnine the direction of the pull out as 1 or -1.
        next_frame = None
        try:
            next_frame = node_list[ref_index + 1]
        except IndexError:
            raise IndexError("The reference keyframe cannot be the last keyframe.")

        x = keyframe_get(next_frame, "valueX") - keyframe_get(reference, "valueX")
        y = keyframe_get(next_frame, "valueY") - keyframe_get(reference, "valueY")
        z = keyframe_get(next_frame, "valueZ") - keyframe_get(reference, "valueZ")

        if abs(z) < abs(x) > abs(y):
            axis = "valueX"
            out_direction = x / abs(x)
        elif abs(z) < abs(y) > abs(x):
            axis = "valueY"
            out_direction = y / abs(y)
        else:
            axis = "valueZ"
            out_direction = z / abs(z)

        # We then try and estimate the pull out distance by taking the biggest difference
        # between the reference keyframe and (up too) the next 5 keyframes.
        estimated_pull_out = max(
            abs(keyframe_get(node_list[j], axis) - keyframe_get(reference, axis))
            for j in range(ref_index, min(ref_index + 6, len(node_list)))
        )

        return KeyframeReference(
            reference,
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

    def make_preg_plus_nodes(
        self, root: et.Element, pc: PregPlusComponentConfig
    ) -> Tuple[et.Element, et.Element, et.Element]:
        base_interpolable = root.find("""interpolable[@alias='Preg+']""")
        if base_interpolable is None:
            raise NodeNotFoundError(
                "interpolable", tag="alias", value="Preg+", xml_path=self.template_path
            )
        else:
            base_interpolable.set("alias", f"{pc.name}")

        in_keyframe = (
            base_interpolable.find(f"keyframe[@alias='{pc.in_curve}']") or NODE_NOT_FOUND
        )
        if in_keyframe is NODE_NOT_FOUND:
            raise NodeNotFoundError(
                f"keyframe[@alias='{pc.in_curve}']", xml_path=self.template_path
            )
        else:
            in_keyframe.set("value", str(pc.min_value))

        out_keyframe = (
            base_interpolable.find(f"keyframe[@alias='{pc.out_curve}']") or NODE_NOT_FOUND
        )
        if out_keyframe is NODE_NOT_FOUND:
            raise NodeNotFoundError(
                f"keyframe[@alias='{pc.out_curve}']", xml_path=self.template_path
            )
        else:
            out_keyframe.set("value", str(pc.max_value))

        # Remove the template keyframes from our base node
        for child in list(base_interpolable):
            base_interpolable.remove(child)

        root.remove(base_interpolable)

        return base_interpolable, in_keyframe, out_keyframe

    def make_activable_nodes(
        self, root: et.Element, ac: ActivableComponentConfig
    ) -> Tuple[et.Element, et.Element]:
        base_sfx: et.Element = (
            root.find("""interpolable[@alias='3DSE']""") or NODE_NOT_FOUND
        )
        if base_sfx is NODE_NOT_FOUND:
            raise NodeNotFoundError(
                "interpolable", tag="alias", value="3DSE", xml_path=self.template_path
            )
        else:
            base_sfx.set("alias", f"{ac.name}")

        sfx_keyframe = base_sfx.find("keyframe") or NODE_NOT_FOUND
        if sfx_keyframe is NODE_NOT_FOUND:
            raise NodeNotFoundError("keyframe", xml_path=self.template_path)
        else:
            sfx_keyframe.set("value", "false")

        # Remove the template keyframes from our base plap node
        for child in list(base_sfx):
            base_sfx.remove(child)

        root.remove(base_sfx)

        return base_sfx, sfx_keyframe

    def _round(self, value: float) -> float:
        return round(value, 5)

    def _truncate(self, value: float) -> float:
        factor = 10.0**5
        return int(value * factor) / factor

    def _std_time(self, time: Union[str, int, float]) -> float:
        return self._truncate(float(time))
