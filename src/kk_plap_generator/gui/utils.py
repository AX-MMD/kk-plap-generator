import os
import typing
import xml.etree.ElementTree as et
from typing import List, Set

import toml

from kk_plap_generator.generator.plap_generator import PlapGenerator
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


def generate_plaps(ref_single_file_path: str, groups: typing.List[GroupConfig]):
    xml_tree = et.ElementTree()
    xml_tree.parse(ref_single_file_path)
    interpolables: typing.List[et.Element] = []
    output: typing.List[str] = []

    for group in groups:
        plap_generator = PlapGenerator(
            interpolable_path=group.ref_interpolable,
            offset=group.offset,
            min_pull_out=group.min_pull_out,
            min_push_in=group.min_push_in,
            time_ranges=group.time_ranges,
            component_configs=group.component_configs,
        )
        names = (f"{sc.name}" for sc in plap_generator.component_configs)
        log_print(
            f"Generating xml for ({' '.join(names)})\n",
            output,
        )

        results = plap_generator.generate_xml(xml_tree)
        for result in results:
            for interpolable in result.interpolables:
                log_print(
                    f"{interpolable.get('alias')}:: Generated {result.keyframes_count} keyframes from {result.time_range[0]} to {result.time_range[1]}",
                    output,
                )
                interpolables.append(interpolable)
        log_print(
            "==================================================================", output
        )

    for interpolable in interpolables:
        tree = et.ElementTree(et.Element("root"))
        tree.getroot().append(interpolable)
        filename = os.path.join(
            os.path.dirname(ref_single_file_path), f"{interpolable.get('alias')}.xml"
        )
        tree.write(filename)
        log_print(f"> Generated '{filename}'", output)

    return output
