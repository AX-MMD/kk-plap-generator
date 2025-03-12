import copy
from typing import List
from xml.etree import ElementTree as et

import pytest

from kk_plap_generator.generator.models import Section
from kk_plap_generator.generator.plap_generator import (
    PlapGenerator,
)
from kk_plap_generator.models import ActivableComponentConfig


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
        component_configs=interpolable_configs,
    )


@pytest.fixture
def keyframes_sets():
    r = {
        "simple": et.Element("interpolable"),
        "under_push": et.Element("interpolable"),
        "over_push": et.Element("interpolable"),
        "under_pull": et.Element("interpolable"),
        "over_pull": et.Element("interpolable"),
    }
    r["simple"].extend(
        [
            et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
            # reference
            et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="0.6", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
        ]
    )
    r["simple_w_curve"] = copy.deepcopy(r["simple"])
    for keyframe in r["simple_w_curve"]:
        keyframe.extend(
            [
                et.Element("curve", time="0", value="0.0"),
                et.Element("curve", time="0.5", value="1.0"),
                et.Element("curve", time="0.90", value="0.0"),
            ]
        )
    r["under_push"].extend(
        [
            et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
            # reference
            et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="0.6", valueX="0", valueY="0.12", valueZ="0"),
            et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="1.0", valueX="0", valueY="0.15", valueZ="0"),
            et.Element("keyframe", time="1.2", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="1.4", valueX="0", valueY="0.18", valueZ="0"),
            et.Element("keyframe", time="1.6", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="1.8", valueX="0", valueY="0.19", valueZ="0"),
        ]
    )
    r["over_push"].extend(
        [
            et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
            et.Element("keyframe", time="0.6", valueX="0", valueY="0.08", valueZ="0"),
            et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
        ]
    )
    r["under_pull"].extend(
        [
            et.Element("keyframe", time="0.0", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.2", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="0.3", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.35", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="0.4", valueX="0", valueY="0.08", valueZ="0"),
            et.Element("keyframe", time="0.6", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="0.8", valueX="0", valueY="0.05", valueZ="0"),
            et.Element("keyframe", time="1.0", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="1.2", valueX="0", valueY="0.02", valueZ="0"),
            et.Element("keyframe", time="1.4", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="1.6", valueX="0", valueY="0.01", valueZ="0"),
            et.Element("keyframe", time="1.8", valueX="0", valueY="0.0", valueZ="0"),
        ]
    )
    r["over_pull"].extend(
        [
            et.Element("keyframe", time="0.0", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.2", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="0.4", valueX="0", valueY="0.1", valueZ="0"),
            et.Element("keyframe", time="0.6", valueX="0", valueY="0.0", valueZ="0"),
            et.Element("keyframe", time="0.8", valueX="0", valueY="0.12", valueZ="0"),
            et.Element("keyframe", time="1.0", valueX="0", valueY="0.0", valueZ="0"),
        ]
    )

    return r


@pytest.fixture
def curve_keyframe_simple_sets():
    r = {
        "basic": et.Element("interpolable"),
        "one_plap_no_reset": et.Element("interpolable"),
        "one_plap_w_reset": et.Element("interpolable"),
        "multi_plap_w_reset": et.Element("interpolable"),
    }
    r["basic"].extend(
        [
            et.Element("curve", time="0", value="0.0"),
            et.Element("curve", time="1.0", value="1.0"),
        ]
    )
    r["one_plap_no_reset"].extend(
        [
            et.Element("curve", time="0", value="0.0"),
            et.Element("curve", time="0.5", value="1.0"),
            et.Element("curve", time="0.8", value="9.0"),
        ]
    )
    r["one_plap_w_reset"].extend(
        [
            et.Element("curve", time="0", value="0.0"),
            et.Element("curve", time="0.5", value="1.0"),
            et.Element("curve", time="0.8", value="0.0"),
        ]
    )
    r["multi_plap_w_reset"].extend(
        [
            et.Element("curve", time="0", value="0.0"),
            et.Element("curve", time="0.25", value="1.0"),
            et.Element("curve", time="0.5", value="0.0"),
            et.Element("curve", time="0.75", value="1.0"),
            et.Element("curve", time="0.90", value="0.0"),
        ]
    )
    return r


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
    )[1]
    expected_times: List[float] = []
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, min_push_in",
    [
        (0.2, 0.8),
        (0.2, 0.0),
        (0.0, 0.2),
        (0.2, 0.2),
        (0.5, 0.0),
        (0.0, 0.5),
        (0.5, 0.5),
        (1.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.5),
        (0.5, 1.0),
        (1.0, 1.0),
    ],
)
def test_simple(
    min_pull_out, min_push_in, plap_generator: "PlapGenerator", keyframes_sets
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["simple"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
    expected_times = [0.2, 0.6]
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "set_name, expected",
    [
        ("basic", True),
        ("one_plap_no_reset", True),
        ("one_plap_w_reset", False),
        ("multi_plap_w_reset", False),
    ],
)
def test_curve_mode_is_plap(
    plap_generator: "PlapGenerator",
    keyframes_sets,
    set_name,
    expected,
    curve_keyframe_simple_sets,
):
    sections = plap_generator.make_sections(keyframes_sets["simple"])
    did_plap = plap_generator.get_plaps_from_keyframes(
        sections[0].reference,
        list(curve_keyframe_simple_sets[set_name]),
        curve_reference=keyframes_sets["simple"][0],
    )[0]
    assert did_plap == expected


@pytest.mark.parametrize(
    "set_name, expected_times",
    [
        ("basic", [0.2]),
        ("one_plap_no_reset", [0.1]),
        ("one_plap_w_reset", [0.1]),
        ("multi_plap_w_reset", [0.05, 0.15]),
    ],
)
def test_curve_mode(
    plap_generator: "PlapGenerator",
    keyframes_sets,
    set_name,
    expected_times,
    curve_keyframe_simple_sets,
):
    sections = plap_generator.make_sections(keyframes_sets["simple"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference,
        list(curve_keyframe_simple_sets[set_name]),
        curve_reference=keyframes_sets["simple"][0],
    )[1]
    assert keyframe_times == expected_times


def test_simple_w_curve(plap_generator: "PlapGenerator", keyframes_sets):
    sections = plap_generator.make_sections(keyframes_sets["simple_w_curve"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
    assert keyframe_times == [0.1, 0.2, 0.5, 0.6]


@pytest.mark.parametrize(
    "min_push_in, expected_times",
    [
        (1.0, [0.2]),
        (0.8, [0.2, 0.6]),
        (0.5, [0.2, 0.6, 1.0]),
        (0.2, [0.2, 0.6, 1.0, 1.4]),
        (0.0, [0.2, 0.6, 1.0, 1.4, 1.8]),
    ],
)
def test_under_push(
    plap_generator: "PlapGenerator", keyframes_sets, min_push_in, expected_times
):
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["under_push"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
    assert keyframe_times == expected_times


@pytest.mark.parametrize(
    "min_pull_out, min_push_in",
    [
        (0.2, 0.8),
        (0.2, 0.0),
        (0.0, 0.2),
        (0.2, 0.2),
        (0.5, 0.0),
        (0.0, 0.5),
        (0.5, 0.5),
        (1.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.5),
        (0.5, 1.0),
        (1.0, 1.0),
    ],
)
def test_over_push(
    plap_generator: "PlapGenerator", keyframes_sets, min_pull_out, min_push_in
):
    plap_generator.min_push_in = min_push_in
    plap_generator.min_pull_out = min_pull_out
    sections = plap_generator.make_sections(keyframes_sets["over_push"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
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
def test_under_pull(
    plap_generator: "PlapGenerator", keyframes_sets, min_pull_out, expected_times
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = 0.0
    sections = plap_generator.make_sections(keyframes_sets["under_pull"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
    assert keyframe_times == expected_times


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
def test_over_pull(
    plap_generator: "PlapGenerator", keyframes_sets, min_pull_out, min_push_in
):
    plap_generator.min_pull_out = min_pull_out
    plap_generator.min_push_in = min_push_in
    sections = plap_generator.make_sections(keyframes_sets["over_pull"])
    keyframe_times = plap_generator.get_plaps_from_keyframes(
        sections[0].reference, sections[0].keyframes
    )[1]
    expected_times = [0.2, 0.6, 1.0]
    assert keyframe_times == expected_times
