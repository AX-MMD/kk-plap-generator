import copy
import itertools
import math
import os
from typing import (
    Dict,
    List,
    Sequence,
    Tuple,
    Union,
)
from xml.etree import ElementTree as et

from kk_plap_generator import settings
from kk_plap_generator.generator.curve_ops import evaluate_curve
from kk_plap_generator.generator.models import (
    KeyframeReference,
    PlapAxis,
    PlapFrame,
    Section,
)
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
    deep_find_possible_matches,
    find_node,
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
        def __init__(self, time: Union[str, float]):
            self.time = time
            if isinstance(time, float):
                self.message = (
                    f"Reference keyframe not found at {convert_seconds_to_KKtime(time)}."
                )
            else:
                self.message = f"Reference keyframe not found at {time}."
            super().__init__(self.message)

    class NotSupportedInterpolableType(Error):
        def __init__(self, type: str):
            self.type = type
            self.message = f"Interpolable type {type} is not supported."
            super().__init__(self.message)

    class ValueError(Error):
        pass

    class NodeNotFoundError(Error):
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
        time_ranges: List[Tuple[str, str, str]],
        component_configs: List[ComponentConfig],
        offset: float = 0.0,
        min_pull_out: float = 0.2,
        min_push_in: float = 0.8,
        invert_direction: bool = False,
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
        self.invert_direction = invert_direction
        self.component_configs: List[ComponentConfig] = component_configs
        self.template_path = template_path

    def generate_xml(
        self, timeline_xml_tree: et.ElementTree
    ) -> List["PlapGenerator.GeneratorResult"]:
        # Get the rythm from source single_file, will use parameters from the config to locate the node
        root_nodes = list(timeline_xml_tree.getroot())
        if self.interpolable_path == "":
            ref_interpolable = NODE_NOT_FOUND
        else:
            ref_interpolable = deep_find_interpolable(root_nodes, self.interpolable_path)

        while ref_interpolable is NODE_NOT_FOUND and root_nodes:
            if len(root_nodes) == 1:
                if root_nodes[0].tag == "interpolable":
                    ref_interpolable = root_nodes[0]
                else:
                    root_nodes = list(root_nodes[0])
            else:
                root_nodes = []

        if ref_interpolable is NODE_NOT_FOUND:
            possible_matches = deep_find_possible_matches(
                list(timeline_xml_tree.getroot()), "alias"
            )
            raise NodeNotFoundError(
                "interpolable",
                "alias",
                self.interpolable_path,
                suggestions=possible_matches,
            )

        # Separate the keyframes into sections based on the time ranges
        sections: List[Section] = self.make_sections(ref_interpolable)

        # Get the base nodes from template
        template_tree = et.parse(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), self.template_path)
        )
        self._clean_xml(template_tree.getroot())

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
        base_interpolable.set("alias", f"{pc.name}")

        # For each keyframe in the sections, we assign a value between pc.min_value and pc.max_value
        # based on the distance from the reference keyframe.
        for section in sections:
            reference = section.reference
            is_plap = False
            plaps: List[et.Element] = []

            for keyframe in section.keyframes:
                value = keyframe_get(keyframe, reference.axis)
                distance = self._calculate_distance(
                    reference.value, value, reference.out_direction
                )
                # if (
                #     value * reference.out_direction
                #     < reference.value * reference.out_direction
                # ):
                #     preg_value = pc.max_value
                #     is_plap = True
                if distance > reference.estimated_pull_out:
                    preg_value = pc.min_value
                    is_plap = False
                else:
                    preg_value = int(
                        max(reference.estimated_pull_out - distance, 0.0)
                        / reference.estimated_pull_out
                        * pc.max_value
                    )
                    preg_value = max(preg_value, pc.min_value)
                    is_plap = self.evaluate_is_plap(reference, value, is_plap)

                time_actual = keyframe_get(keyframe, "time") + self.offset + pc.offset
                # Remove overlapping keyframes
                for prev_index in range(len(plaps) - 1, -1, -1):
                    if keyframe_get(plaps[prev_index], "time") >= time_actual - 0.05:
                        plaps.pop(prev_index)
                    else:
                        break

                new_keyframe = (
                    copy.deepcopy(out_keyframe) if is_plap else copy.deepcopy(in_keyframe)
                )

                new_keyframe.set("time", str(time_actual))
                new_keyframe.set("value", str(preg_value))

                if len(list(new_keyframe)) == 0:
                    for curve_keyframe in list(keyframe):
                        new_keyframe.append(copy.deepcopy(curve_keyframe))

                is_plap = not is_plap
                plaps.append(new_keyframe)

            base_interpolable.extend(plaps)

        for child in list(base_interpolable):
            if keyframe_get(child, "time") > 0.5:
                first_keyframe = copy.deepcopy(in_keyframe)
                first_keyframe.set("time", str(0.0))
                first_keyframe.set("value", str(0))
                base_interpolable.insert(0, first_keyframe)

            break

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
            )

        item_configs: List[ActivableComponentConfig] = (
            ac.item_configs if isinstance(ac, MultiActivableComponentConfig) else [ac]
        )
        keyframes_groups: List[List[et.Element]] = [[] for _ in range(len(item_configs))]
        offset = self.offset + ac.offset

        # Generate the keyframes
        for i, time in zip(InfiniteIterator(sequence), keyframe_times):
            plaps = keyframes_groups[i]
            pc = item_configs[i]
            time_actual = time + offset + pc.offset
            # Remove overlapping keyframes
            for prev_index in range(len(plaps) - 1, -1, -1):
                if keyframe_get(plaps[prev_index], "time") >= time_actual - 0.1:
                    plaps.pop(prev_index)
                else:
                    break

            mute_keyframe = copy.deepcopy(sfx_keyframe)
            mute_keyframe.set("time", str(time_actual - 0.05))
            mute_keyframe.set("value", "false")
            new_keyframe = copy.deepcopy(sfx_keyframe)
            new_keyframe.set("time", str(time_actual))
            new_keyframe.set("value", "true")

            plaps.append(mute_keyframe)
            plaps.append(new_keyframe)

            if 0 < ac.cutoff < math.inf:
                cutoff = (ac.cutoff + pc.cutoff) if pc.cutoff < math.inf else ac.cutoff
            else:
                cutoff = pc.cutoff

            if 0 < cutoff < math.inf:
                cutoff_keyframe = copy.deepcopy(sfx_keyframe)
                cutoff_keyframe.set("time", str(time + offset + pc.offset + cutoff))
                cutoff_keyframe.set("value", "false")
                plaps.append(cutoff_keyframe)

        # Create the interpolables
        interpolables: List[et.Element] = []
        for i, ic in enumerate(item_configs):
            p: et.Element = copy.deepcopy(base_sfx)
            p.set("alias", f"{ic.name}")
            p.set("objectIndex", f"{p.get('objectIndex')}{i + 1}")
            p.extend(keyframes_groups[i])
            interpolables.append(p)

        return PlapGenerator.GeneratorResult(
            interpolables,
            len(keyframe_times),
            (
                convert_seconds_to_KKtime(keyframe_times[0]),
                convert_seconds_to_KKtime(keyframe_times[-1]),
            )
            if keyframe_times
            else ("00:00:00", "00:00:00"),
        )

    def get_plaps_from_keyframes(
        self,
        reference: "KeyframeReference",
        keyframes: Sequence[et.Element],
    ) -> List[float]:
        keyframe_times: List[float] = []
        did_plap = False
        # out direction 1 means the reference is pulling away by increasing his axis value
        # (ex. out direction 1) impact at X:0.0, pulling away to X:1.0
        # (ex. out direction -1) impact at X:0.0, pulling away to X:-1.0
        # (ex. out direction 1) impact at X:-2.0, pulling away to X:7.0
        # (ex. out direction -1) impact at X:-2.0, pulling away to X:-9.0

        for keyframe, next_kf in zip(keyframes, itertools.islice(keyframes, 1, None)):
            plapframes = self._convert_to_plapframes(
                [keyframe, next_kf], PlapAxis(reference.axis)
            )
            for plapframe in plapframes:
                will_plap = self.evaluate_is_plap(reference, plapframe.value, did_plap)
                if did_plap and not will_plap:
                    did_plap = False
                elif not did_plap and will_plap:
                    keyframe_times.append(plapframe.time)
                    did_plap = True

        return keyframe_times

    def get_plaps_from_curve_keyframes(
        self,
        reference: "KeyframeReference",
        curve_keyframes: List[et.Element],
        curve_reference: et.Element,
    ) -> Tuple[bool, List[float]]:
        # We will evaluate the curve keyframes to see if there are any plaps in the interpolation curve.
        keyframe_times: List[float] = []
        did_plap = False
        if not curve_keyframes:
            return did_plap, keyframe_times

        evaluated_times, evaluated_values = evaluate_curve(curve_keyframes)

        for i in range(0, len(evaluated_values) - 1):
            # We found a plap keyframe and are currently checking if at any point in the
            # interpolation curve of the previous keyframe there was one or more plaps.
            # (can happen in custom curves)
            time = evaluated_times[i]
            value = evaluated_values[i]
            value_diff = reference.value - keyframe_get(curve_reference, reference.axis)
            value = self._round(reference.value - value_diff * (1.0 - value))
            will_plap = self.evaluate_is_plap(reference, value, did_plap)
            if not did_plap and will_plap:
                if (
                    evaluated_values[i] > evaluated_values[i + 1]
                    or value * reference.out_direction
                    >= reference.value * reference.out_direction
                ):
                    time_diff = reference.time - keyframe_get(curve_reference, "time")
                    time_offset = time_diff * (1.0 - time)
                    keyframe_times.append(self._round(reference.time - time_offset))
                    did_plap = True
            elif did_plap and not will_plap:
                did_plap = False

        return did_plap, keyframe_times

    def evaluate_is_plap(
        self, reference: "KeyframeReference", value: float, did_plap: bool
    ) -> bool:
        distance = self._calculate_distance(
            reference.value, value, reference.out_direction
        )
        if did_plap:
            # Only say not plapping after a minimum distance in the out direction is reached.
            # This is to avoid spam during rapid micro movements, like during orgams and such.
            if (
                value * reference.out_direction
                > reference.value * reference.out_direction
                and distance
                >= self._round(self.min_pull_out * reference.estimated_pull_out)
                # Round to avoid floating point errors
            ):
                if settings.IS_DEV:
                    print(
                        f"ref{reference.value} reftime{reference.time} value{value} distance{distance} pull{reference.estimated_pull_out} v{self.min_pull_out}, {self._round(self.min_pull_out * reference.estimated_pull_out)}"
                    )
                return False
            else:
                return did_plap

        # Only says plapping if close enough to the reference keyframe.
        elif (
            value * reference.out_direction <= reference.value * reference.out_direction
            or distance
            < self._round((1.0 - self.min_push_in) * reference.estimated_pull_out)
        ):
            return True
        else:
            return did_plap

    def make_sections(self, ref_interpolable: et.Element) -> List["Section"]:
        sections: List[Section] = []
        keyframes = list(ref_interpolable)
        if not keyframes:
            return sections

        for time_start, time_end, ref_time in self.get_time_ranges_sec():
            kfs: List[et.Element] = []
            ref_kfs = None
            prev_kf = keyframes[0]

            if ref_time < keyframe_get(prev_kf, "time"):
                ref_time = keyframe_get(prev_kf, "time")
            if time_start < keyframe_get(prev_kf, "time"):
                time_start = keyframe_get(prev_kf, "time")

            # Get the keyframes that are within the time range
            for i, kf in enumerate(keyframes):
                time = keyframe_get(kf, "time")
                if (
                    self._std_time(time_start) - 0.00001 <= time
                    and self._std_time(time) <= time_end + 0.00001
                ):
                    if not kfs:
                        kfs.append(prev_kf)

                    kfs.append(kf)

                if ref_time >= self._std_time(time) - 0.00001:
                    ref_kfs = (prev_kf, kf, keyframes[i + 1])

                prev_kf = kf

            if kfs:
                if self._std_time(ref_time) == self._std_time(time_start):
                    try:
                        ref_kfs = (kfs[0], kfs[1], kfs[2])
                    except IndexError:
                        raise IndexError(
                            "The reference keyframe cannot be the last or only keyframe in the Time Range."
                        )
                elif ref_kfs is None:
                    raise self.ReferenceNotFoundError(convert_seconds_to_KKtime(ref_time))
                if settings.IS_DEV:
                    print(
                        f"k0: {keyframe_get(kfs[0], 'time')} k1: {keyframe_get(kfs[1], 'time')} k2: {keyframe_get(kfs[2], 'time')}"
                    )
                    print(
                        f"ref_time: {ref_time} ref_kfs0: {keyframe_get(ref_kfs[0], 'time')} ref_kfs1: {keyframe_get(ref_kfs[1], 'time')} ref_kfs2: {keyframe_get(ref_kfs[2], 'time')}"
                    )
                reference = self.get_reference(ref_kfs, ref_time, kfs)
                sections.append(Section(reference, kfs))

        return sections

    def generate_sequence(self, pattern_string: str, count: int) -> List[int]:
        last_index = len(pattern_string) - 1
        pattern = self.generate_patterns(count)
        sequence = []
        for i, char in enumerate(pattern_string):
            sequence += pattern[char]
            if i != last_index and pattern_string[i + 1] != char:
                sequence.append(pattern[char][0])

        return sequence

    def get_reference(
        self,
        ref_nodes: Tuple[et.Element, et.Element, et.Element],
        ref_time: float,
        node_list: Sequence[et.Element],
    ) -> "KeyframeReference":
        # The first keyframe of a time range should be a keyframe where the two bodies collide.
        # Here it's second because we add the preceding frame for curve evaluation.
        axis = PlapAxis()
        plap_frames = self._convert_to_plapframes(ref_nodes[:2], axis)
        reference: PlapFrame = plap_frames[-1]
        for frame in plap_frames:
            if frame.time <= ref_time:
                reference = frame
            else:
                break

        if settings.IS_DEV:
            print(
                f"ref time{ref_time} ref_nodes1:{ref_nodes[0].get('time')} ref_nodes2:{ref_nodes[1].get('time')} ref_nodes3:{ref_nodes[2].get('time')} plap{reference.time}"
            )
            print(
                f"ref_node_X{ref_nodes[1].get('valueX')} ref_node_Y{ref_nodes[1].get('valueY')} ref_node_Z{ref_nodes[1].get('valueZ')}"
            )
            print(
                f"ref_next_X{ref_nodes[2].get('valueX')} ref_next_Y{ref_nodes[2].get('valueY')} ref_next_Z{ref_nodes[2].get('valueZ')}"
            )

            print(
                f"plap_X{reference.valueX} plap_Y{reference.valueY} plap_Z{reference.valueZ}"
            )
        # We check the next keyframe and calculate the difference between reference and next_keyframe.
        # The axis with the biggest difference will be our axis reference.
        # We also use the difference to determnine the direction of the pull out as 1 or -1.
        next_frame = ref_nodes[2]

        x = keyframe_get(next_frame, "valueX") - keyframe_get(ref_nodes[1], "valueX")
        y = keyframe_get(next_frame, "valueY") - keyframe_get(ref_nodes[1], "valueY")
        z = keyframe_get(next_frame, "valueZ") - keyframe_get(ref_nodes[1], "valueZ")

        if abs(z) < abs(x) > abs(y):
            axis.value = "valueX"
            # out_direction = x / abs(x)
            # value_diff = keyframe_get(ref_nodes[1], "valueX") - keyframe_get(next_frame, "valueX")
        elif abs(z) < abs(y) > abs(x):
            axis.value = "valueY"
            # out_direction = y / abs(y)
            # value_diff = keyframe_get(ref_nodes[1], "valueY") - keyframe_get(next_frame, "valueY")
        else:
            axis.value = "valueZ"
            # out_direction = z / abs(z)
            # value_diff = keyframe_get(ref_nodes[1], "valueZ") - keyframe_get(next_frame, "valueZ")

        if keyframe_get(next_frame, axis.value) > keyframe_get(ref_nodes[1], axis.value):
            out_direction = 1.0
        else:
            out_direction = -1.0

        if self.invert_direction:
            out_direction *= -1.0

        # We then try and estimate the pull out distance by taking the biggest difference
        # between the reference keyframe other keyframes, using the curve keyframes
        compare_func = min if out_direction == -1 else max
        estimated_pull_out = 0.0
        for i in range(len(node_list) - 1):
            kf = node_list[i]
            value = keyframe_get(kf, axis.value)
            value_diff = keyframe_get(node_list[i + 1], axis.value) - value
            value = compare_func(
                (
                    value,
                    *(
                        value + value_diff * v
                        for v in evaluate_curve(list(node_list[i]))[1]
                    ),
                )
            )
            estimated_pull_out = max(estimated_pull_out, abs(value - reference.value))

        reference.value = self._round(reference.value)

        if estimated_pull_out == 0.0:
            raise ValueError(
                "Could not estimate the pull out distance with available data"
                + f"\n> node_list length: {len(node_list)}"
                + f"\n> axis: {axis}"
                + f"\n> ref_value: {reference.value}"
            )
        elif settings.IS_DEV:
            print(
                f"Estimated pull out distance for {axis} at {reference.time}: {estimated_pull_out}"
                + f"\n> ref_value: {reference.value}"
                + f"\n> out_direction: {out_direction}"
                + f"\n> axis: {axis}"
            )

        return KeyframeReference(
            value=reference.value,
            time=reference.time,
            axis=axis.value,
            out_direction=out_direction,
            estimated_pull_out=self._round(estimated_pull_out),
        )

    def generate_patterns(self, count) -> Dict[str, List[int]]:
        # fmt: off
        return {
            "W": [i for i in range(count)] \
                + [i for i in range(count - 2, int(math.ceil(count / 2.0)) - 1, -1)] \
                + [i for i in range(int(math.ceil(count / 2.0)) - 1, count - 1)] \
                + [i for i in range(count - 1, 0, -1)],
            "M": [i for i in range(count - 1, -1, -1)] \
                + [i for i in range(1, int(math.ceil(count / 2.0)) + 1)] \
                + [i for i in range(int(math.ceil(count / 2.0)) - 1, 0, -1)] \
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
        base_interpolable = find_node(root, "interpolable[@alias='Preg+']")
        base_interpolable.set("alias", f"{pc.name}")

        in_keyframe = find_node(base_interpolable, f"keyframe[@alias='{pc.in_curve}']")
        in_keyframe.set("value", str(pc.min_value))

        out_keyframe = find_node(base_interpolable, f"keyframe[@alias='{pc.out_curve}']")
        out_keyframe.set("value", str(pc.max_value))

        # Remove the template keyframes from our base node
        for child in list(base_interpolable):
            base_interpolable.remove(child)

        root.remove(base_interpolable)

        return base_interpolable, in_keyframe, out_keyframe

    def make_activable_nodes(
        self, root: et.Element, ac: ActivableComponentConfig
    ) -> Tuple[et.Element, et.Element]:
        base_sfx: et.Element = find_node(root, "interpolable[@alias='3DSE']")
        base_sfx.set("alias", f"{ac.name}")

        sfx_keyframe = find_node(base_sfx, "keyframe")
        sfx_keyframe.set("value", "false")

        # Remove the template keyframes from our base plap node
        for child in list(base_sfx):
            base_sfx.remove(child)

        root.remove(base_sfx)

        return base_sfx, sfx_keyframe

    def get_time_ranges_sec(self) -> List[Tuple[float, float, float]]:
        if self.time_ranges:
            ranges = []
            first: float
            # Convert the time ranges from KKtime to seconds
            for tg in self.time_ranges:
                ranges.append(
                    [
                        (first := convert_KKtime_to_seconds(tg[0])),
                        convert_KKtime_to_seconds(tg[1]),
                        convert_KKtime_to_seconds(tg[2]) if tg[2] else first,
                    ]
                )
            # Make sure the ranges are sorted and don't overlap
            ranges.sort(key=lambda x: x[0])
            for i in range(0, len(ranges) - 1):
                if ranges[i][1] > ranges[i + 1][0]:
                    ranges[i][1] = ranges[i + 1][0] - 0.00001

            return [
                (ranges[i][0], ranges[i][1], ranges[i][2]) for i in range(0, len(ranges))
            ]

        else:
            return [(0.0, math.inf, 0.0)]

    def _round(self, value: float) -> float:
        return round(value, 5)

    def _truncate(self, value: float) -> float:
        factor = 10.0**5
        return int(value * factor) / factor

    def _std_time(self, time: Union[str, int, float]) -> float:
        return self._truncate(float(time))

    def _clean_xml(self, xml: et.Element) -> None:
        # Remove all formatting (strip whitespace and newlines)
        for element in list(xml):
            self._clean_xml(element)
            if element.text:
                element.text = element.text.strip()
            if element.tail:
                element.tail = element.tail.strip()

    def _calculate_distance(
        self, reference_value: float, value: float, out_direction: float
    ) -> float:
        if value * out_direction <= reference_value * out_direction:
            return 0.0
        else:
            return self._round(abs(reference_value - value))

    def _convert_to_plapframes(
        self, keyframes: Sequence[et.Element], shared_axis: PlapAxis
    ) -> List[PlapFrame]:
        plapframes: List[PlapFrame] = []
        for keyframe, next_keyframe in zip(keyframes, keyframes[1:]):
            frame_left = PlapFrame(
                keyframe_get(keyframe, "time"),
                keyframe_get(keyframe, "valueX"),
                keyframe_get(keyframe, "valueY"),
                keyframe_get(keyframe, "valueZ"),
                shared_axis,
            )
            frame_right = PlapFrame(
                keyframe_get(next_keyframe, "time"),
                keyframe_get(next_keyframe, "valueX"),
                keyframe_get(next_keyframe, "valueY"),
                keyframe_get(next_keyframe, "valueZ"),
                shared_axis,
            )
            plapframes.append(frame_left)

            for c_time, c_value in zip(*evaluate_curve(list(keyframe))):
                # print(
                #     f"T: {c_time} V: {c_value} Left: {frame_left.time} Right: {frame_right.time} LV: {frame_left.valueY} RV: {frame_right.valueY}"
                # )
                # print(
                #     frame_left.valueY + (frame_right.valueY - frame_left.valueY) * c_value
                # )
                plapframes.append(
                    PlapFrame(
                        self._round(
                            frame_left.time
                            + c_time * (frame_right.time - frame_left.time)
                        ),
                        self._round(
                            frame_left.valueX
                            + (frame_right.valueX - frame_left.valueX) * c_value
                        ),
                        self._round(
                            frame_left.valueY
                            + (frame_right.valueY - frame_left.valueY) * c_value
                        ),
                        self._round(
                            frame_left.valueZ
                            + (frame_right.valueZ - frame_left.valueZ) * c_value
                        ),
                        shared_axis,
                    )
                )

        return plapframes
