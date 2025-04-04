import xml.etree.ElementTree as et
from typing import List

from kk_plap_generator import settings


def get_curve_types() -> List[str]:
    if not settings.TIMELINE_CURVE_TYPES:
        xml_tree = et.ElementTree()
        xml_tree.parse(settings.TEMPLATE_FILE)
        interpolable = xml_tree.find("interpolable[@alias='Preg+']")
        if interpolable is None:
            raise ValueError(
                "Could not find template interpolable node with alias 'Preg+'"
            )

        settings.TIMELINE_CURVE_TYPES = [
            keyframe.get("alias", "<Missing alias>") for keyframe in interpolable
        ]

    return list(settings.TIMELINE_CURVE_TYPES)
