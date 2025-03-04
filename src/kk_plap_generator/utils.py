import xml.etree.ElementTree as et
from typing import List

from kk_plap_generator import settings


def get_curve_types() -> List[str]:
    if not settings.TIMELINE_CURVE_TYPES:
        xml_tree = et.ElementTree()
        xml_tree.parse(settings.TEMPLATE_FILE)
        settings.TIMELINE_CURVE_TYPES = [
            keyframe.get("alias") or "<Missing alias>"
            for keyframe in xml_tree.find("interpolable[@alias='Preg+']") or []
        ]

    return list(settings.TIMELINE_CURVE_TYPES)
