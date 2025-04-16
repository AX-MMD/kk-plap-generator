import os
import typing
import xml.etree.ElementTree as et
from typing import Dict, List, Tuple

import toml

from kk_plap_generator.generator.plap_generator import PlapGenerator
from kk_plap_generator.generator.utils import keyframe_get
from kk_plap_generator.models import (
    GroupConfig,
)


def load_config_file(path: str) -> List[GroupConfig]:
    with open(path, "r", encoding="UTF-8") as f:
        data = toml.load(f)

    return [GroupConfig(**group) for group in data.get("plap_group", [])]


def log_print(message: str, output: List[str]):
    output.append(message)
    print(output[-1])


def generate_plaps(groups: typing.List[GroupConfig]):
    interpolables: Dict[str, Tuple[et.Element, str]] = {}
    output: typing.List[str] = []

    names = {f"{sc.name}" for group in groups for sc in group.component_configs}
    log_print(
        f"Generating xml for ({', '.join(names)})\n",
        output,
    )

    for group in groups:
        plap_generator = PlapGenerator(
            interpolable_path=group.ref_interpolable,
            offset=group.offset,
            min_pull_out=group.min_pull_out,
            min_push_in=group.min_push_in,
            time_ranges=group.time_ranges,
            component_configs=group.component_configs,
        )
        xml_tree = et.ElementTree()
        xml_tree.parse(group.ref_single_file)
        results = plap_generator.generate_xml(xml_tree)
        for result in results:
            for interpolable in result.interpolables:
                alias = interpolable.get("alias", "")
                if alias in interpolables:
                    ref_time = keyframe_get(list(interpolables[alias][0])[-1], "time")
                    index = next(
                        (
                            i
                            for i, kf in enumerate(interpolable)
                            if keyframe_get(kf, "time") > ref_time + 0.01
                        ),
                        -1,  # Default value if no match is found
                    )
                    if index == -1:
                        log_print(
                            f"Warning: No new keyframes found for {alias} in {group.ref_single_file}.",
                            output,
                        )

                    interpolables[alias][0].extend(interpolable[index:])
                    op_type = "Added"
                else:
                    interpolables[alias] = (interpolable, group.ref_single_file)
                    op_type = "Generated"

                log_print(
                    f"{alias}:: {op_type} {result.keyframes_count} keyframes from {result.time_range[0]} to {result.time_range[1]}",
                    output,
                )
    log_print(
        "==================================================================", output
    )

    for alias, (interpolable, ref_single_file_path) in interpolables.items():
        tree = et.ElementTree(et.Element("root"))
        tree.getroot().append(interpolable)
        filename = os.path.join(os.path.dirname(ref_single_file_path), f"{alias}.xml")
        tree.write(filename, method="xml", encoding="UTF-8", xml_declaration=False)
        log_print(f"> Generated '{filename}'", output)

    return output
