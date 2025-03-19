import copy
from typing import List
from xml.etree import ElementTree as et

import pytest

from kk_plap_generator.generator.models import Section
from kk_plap_generator.generator.plap_generator import (
    PlapGenerator,
)
from kk_plap_generator.models import ActivableComponentConfig
from kk_plap_generator.tests.test_plap_generator import data_sets


@pytest.fixture
def interpolable_configs():
    return [
        ActivableComponentConfig(
            name=f"Plap{i}",
            offset=0.0,
            cutoff=0.0,
        )
        for i in range(1, 5)
    ]


@pytest.fixture
def plap_generator(interpolable_configs) -> PlapGenerator:
    return PlapGenerator(
        interpolable_path="path/to/interpolable",
        time_ranges=[("00:00.20", "00:10.00")],
        component_configs=[],
    )


@pytest.fixture
def keyframes_sets():
    return copy.deepcopy(data_sets.keyframes_sets)


@pytest.fixture
def keyframes_w_curves_sets():
    return copy.deepcopy(data_sets.keyframes_w_curves_sets)


@pytest.fixture
def curve_keyframe_simple_sets():
    return copy.deepcopy(data_sets.curve_keyframe_simple_sets)


@pytest.fixture
def reference_simple(keyframes_sets, plap_generator: "PlapGenerator"):
    sections: List[Section] = plap_generator.make_sections(keyframes_sets["simple"])
    return sections[0].reference


def test_get_reference(plap_generator: "PlapGenerator", keyframes_sets):
    sections: List[Section] = plap_generator.make_sections(keyframes_sets["simple"])
    reference = sections[0].reference
    assert reference.axis == "valueY"
    assert reference.out_direction == 1
    assert reference.time == 0.2
    assert reference.value == 0.1
    assert reference.estimated_pull_out == 0.1


def test_get_keyframe_times_with_empty_keyframes(
    plap_generator: "PlapGenerator", keyframes_sets
):
    sections = plap_generator.make_sections(keyframes_sets["simple"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, list(et.Element("keyframe"))
    )
    expected_times: List[float] = []
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, min_push_in",
    [
        (0.2, 0.8),
        (0.2, 0.0001),
        (0.0, 0.2),
        (0.2, 0.2),
        (0.5, 0.0001),
        (0.0, 0.5),
        (0.5, 0.5),
        (1.0, 0.0001),
        (0.0, 1.0),
        (1.0, 0.5),
        (0.5, 1.0),
        (1.0, 1.0),
    ],
)
def test_simple_get_plaps_from_keyframes(
    min_pull_out, min_push_in, plap_generator: "PlapGenerator", keyframes_sets
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["simple"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].plapframes
    )
    expected_times = [0.2, 0.6]
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_push_in, expected_times",
    [
        (1.0, [0.2]),
        (0.8, [0.2, 0.6]),
        (0.5, [0.2, 0.6, 1.0]),
        (0.2, [0.2, 0.6, 1.0, 1.4]),
        (0.0001, [0.2, 0.6, 1.0, 1.4, 1.8]),
    ],
)
def test_get_plaps_from_keyframes_under_push(
    plap_generator: "PlapGenerator",
    reference_simple,
    keyframes_sets,
    min_push_in,
    expected_times,
):
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["under_push"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, min_push_in",
    [
        (0.2, 0.8),
        (0.2, 0.0001),
        (0.0, 0.2),
        (0.2, 0.2),
        (0.5, 0.0001),
        (0.0, 0.5),
        (0.5, 0.5),
        (1.0, 0.0001),
        (0.0, 1.0),
        (1.0, 0.5),
        (0.5, 1.0),
        (1.0, 1.0),
    ],
)
def test_get_plaps_from_keyframes_over_push(
    plap_generator: "PlapGenerator",
    reference_simple,
    keyframes_sets,
    min_pull_out,
    min_push_in,
):
    plap_generator.min_push_in = min_push_in
    plap_generator.min_pull_out = min_pull_out
    sections = plap_generator.make_sections(keyframes_sets["over_push"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    expected_times = [0.2, 0.6]
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, expected_times",
    [
        (1.0, [0.2, 0.35]),
        (0.8, [0.2, 0.35, 0.6]),
        (0.5, [0.2, 0.35, 0.6, 1.0]),
        (0.2, [0.2, 0.35, 0.6, 1.0, 1.4]),
        (0.0, [0.2, 0.35, 0.6, 1.0, 1.4, 1.8]),
    ],
)
def test_get_plaps_from_keyframes_under_pull(
    plap_generator: "PlapGenerator",
    reference_simple,
    keyframes_sets,
    min_pull_out,
    expected_times,
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = 0.2
    sections = plap_generator.make_sections(keyframes_sets["under_pull"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, expected_times",
    [
        (1.1, [0.2, 0.35]),
        (0.9, [0.2, 0.35, 0.6]),
        (0.6, [0.2, 0.35, 0.6, 1.0]),
        (0.3, [0.2, 0.35, 0.6, 1.0, 1.4]),
        (0.11, [0.2, 0.35, 0.6, 1.0, 1.4, 1.8]),
    ],
)
def test_fail_get_plaps_from_keyframes_under_pull(
    plap_generator: "PlapGenerator",
    reference_simple,
    keyframes_sets,
    min_pull_out,
    expected_times,
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = 0.2
    sections = plap_generator.make_sections(keyframes_sets["under_pull"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    assert keyframe_times != expected_times


@pytest.mark.parametrize(
    "min_pull_out, min_push_in",
    [
        (0.0, 1.0),
        (0.2, 1.0),
        (0.5, 1.0),
        (0.8, 1.0),
        (0.8, 0.2),
    ],
)
def test_get_plaps_from_keyframes_over_pull(
    plap_generator: "PlapGenerator",
    reference_simple,
    keyframes_sets,
    min_pull_out,
    min_push_in,
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["over_pull"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    expected_times = [0.2, 0.6, 1.0]
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "set_name, expected_times, expected_did_plap",
    [
        ("basic_2frames", [], False),
        ("one_plap_no_reset", [0.1], True),
        ("one_plap_w_reset", [0.1], False),
        ("multi_plap_w_reset", [0.05, 0.15], False),
        ("multi_plap_over_push", [0.05, 0.15], False),
        ("multi_plap_under_push", [0.05, 0.15], False),
        ("multi_plap_over_pull", [0.05, 0.15], False),
        ("multi_plap_under_pull", [0.05, 0.15], False),
    ],
)
def test_get_plaps_from_curve_keyframes(
    plap_generator: "PlapGenerator",
    keyframes_sets,
    set_name,
    expected_times,
    expected_did_plap,
    curve_keyframe_simple_sets,
    reference_simple,
):
    did_plap, curve_keyframe_times = plap_generator.get_plaps_from_curve_keyframes(
        reference_simple,
        list(curve_keyframe_simple_sets[set_name]),
        curve_reference=keyframes_sets["simple"][0],
    )
    assert did_plap == expected_did_plap
    assert curve_keyframe_times == expected_times


def test_simple_w_curve(plap_generator: "PlapGenerator", keyframes_sets):
    sections = plap_generator.make_sections(keyframes_sets["simple_w_curve"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].plapframes
    )
    assert keyframe_times == [0.1, 0.2, 0.5, 0.6]


def test_simple_w_curve_first_keyframe_is_reference(
    plap_generator: "PlapGenerator", keyframes_sets
):
    plap_generator.time_ranges = [("00:00.00", "00:10.00")]
    sections = plap_generator.make_sections(keyframes_sets["simple_w_curve"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].plapframes
    )
    assert keyframe_times == [0.0, 0.3, 0.4, 0.7, 0.8]


@pytest.mark.parametrize(
    "kf_set, expected_times",
    [(key, [0.1, 0.2, 0.5, 0.6]) for key in data_sets.keyframes_w_curves_sets.keys()],
)
def test_all_scenarios(
    plap_generator: "PlapGenerator",
    reference_simple,
    kf_set,
    expected_times,
    keyframes_w_curves_sets,
):
    sections = plap_generator.make_sections(keyframes_w_curves_sets[kf_set])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        reference_simple, sections[0].plapframes
    )
    assert keyframe_times == expected_times
