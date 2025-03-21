# Generated with github copilot
import math
import sys
from typing import Iterable, List, Tuple
from xml.etree import ElementTree as et

from kk_plap_generator.generator.utils import keyframe_get

MAX_POSSIBLE_FLOAT: float = sys.float_info.max


def convert_tangent_to_slope(tangent):
    return math.tan(math.radians(tangent))


def cubic_hermite_spline(t, p0, p1, m0, m1):
    t2 = t * t
    t3 = t2 * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1


def evaluate_curve_keyframes(
    curve_keyframes: List[Tuple[float, float, float, float]], num_points: int = 200
) -> Tuple[List[float], List[float]]:
    times = [kf[0] for kf in curve_keyframes]
    values = [kf[1] for kf in curve_keyframes]
    try:
        in_tangents = []
        for kf in curve_keyframes:
            in_tangents.append(convert_tangent_to_slope(kf[2]))
    except ValueError as e:
        raise ValueError(f"convert_tangent_to_slope failed with message {e}: {kf}")

    try:
        out_tangents = []
        for kf in curve_keyframes:
            out_tangents.append(convert_tangent_to_slope(kf[3]))
    except ValueError as e:
        raise ValueError(f"convert_tangent_to_slope failed with message {e}: {kf}")

    evaluated_times = []
    evaluated_values = []

    try:
        for i in range(len(times) - 1):
            t0, t1 = times[i], times[i + 1]
            p0, p1 = values[i], values[i + 1]
            m0, m1 = out_tangents[i], in_tangents[i + 1]

            for j in range(num_points):
                t = j / num_points
                time = t0 + t * (t1 - t0)
                value = cubic_hermite_spline(t, p0, p1, m0, m1)
                evaluated_times.append(time)
                evaluated_values.append(value)
    except IndexError:
        raise IndexError(f"{times} {values} {in_tangents} {out_tangents}")

    return evaluated_times, evaluated_values


def evaluate_curve(
    curve_keyframes: Iterable[et.Element],
) -> Tuple[List[float], List[float]]:
    cleaned_curve_keyframes = []
    for ckf in curve_keyframes:
        value = keyframe_get(ckf, "value")
        if value == math.inf:
            value = MAX_POSSIBLE_FLOAT
        time = keyframe_get(ckf, "time")
        if time == math.inf:
            time = MAX_POSSIBLE_FLOAT
        in_tangent = keyframe_get(ckf, "inTangent")
        if in_tangent == math.inf:
            in_tangent = MAX_POSSIBLE_FLOAT
        out_tangent = keyframe_get(ckf, "outTangent")
        if out_tangent == math.inf:
            out_tangent = MAX_POSSIBLE_FLOAT

        cleaned_curve_keyframes.append((time, value, in_tangent, out_tangent))

    return evaluate_curve_keyframes(cleaned_curve_keyframes)
