from typing import List, Optional
from xml.etree import ElementTree as et

from kk_plap_generator.generator.utils import convert_string_to_nested_list

NODE_NOT_FOUND = et.Element("notfound")


class NodeNotFoundError(Exception):
    def __init__(
        self,
        node_name,
        tag: Optional[str] = None,
        value: Optional[str] = None,
        *args,
        path: Optional[str] = None,
        xml_path: Optional[str] = None,
    ):
        self.node_name = node_name
        self.tag = tag
        self.value = value
        self.path = path
        self.xml_path = xml_path
        self.message = f"Node not found: {self.get_node_string()}"
        super().__init__(self.message, *args)

    def get_node_string(self):
        s = f"<{self.node_name}"
        s += (
            f" {self.tag}{("='" + self.value + "'") if self.value else ''}"
            if self.tag
            else ""
        )
        s += ">"
        return s


def deep_find_interpolable(node_list: List[et.Element], target: str) -> et.Element:
    for node in node_list:
        if node.tag == "interpolable" and node.get("alias") == target:
            return node
        else:
            found = deep_find_interpolable(list(node), target)
            if found is not NODE_NOT_FOUND:
                return found

    return NODE_NOT_FOUND


def find_interpolable(root: et.Element, target: str) -> et.Element:
    node: et.Element = root
    tag, value, child = convert_string_to_nested_list(target)
    path = []
    while child is not None:
        path.append(value)
        node = node.find(f"""interpolableGroup[@{tag}='{value}']""") or NODE_NOT_FOUND
        if node is NODE_NOT_FOUND:
            raise NodeNotFoundError("interpolableGroup", tag, value, path=".".join(path))

        tag, value, child = child

    node = node.find(f"""interpolable[@{tag}='{value}']""") or NODE_NOT_FOUND
    if node is NODE_NOT_FOUND:
        raise NodeNotFoundError("interpolable", tag, value)

    return node
