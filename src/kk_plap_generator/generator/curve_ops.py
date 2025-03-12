# Generated with github copilot
import math
from typing import List, Tuple


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


def evaluate_curve(
    curve_keyframes: List[Tuple[float, float, float, float]], num_points: int = 50
) -> Tuple[List[float], List[float]]:
    times = [kf[0] for kf in curve_keyframes]
    values = [kf[1] for kf in curve_keyframes]
    in_tangents = [convert_tangent_to_slope(kf[2]) for kf in curve_keyframes]
    out_tangents = [convert_tangent_to_slope(kf[3]) for kf in curve_keyframes]

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
