import itertools
import os
import re
from typing import Generator, Iterable, Optional, Tuple
from xml.etree import ElementTree as et


def int_to_bytes(number: int) -> bytes:
    # Calculate the minimum number of bytes required to represent the integer
    min_bytes = (number.bit_length() + 7) // 8
    # Convert the integer to a big-endian byte string of the minimum length
    return number.to_bytes(min_bytes, byteorder="big")


def flag_to_int_array(flag: bytes) -> Tuple[int, int]:
    return int.from_bytes(flag[0:1], byteorder="big"), int.from_bytes(
        flag[1:], byteorder="big"
    )


def sfx_terms() -> "Generator[bytes]":
    for term in ("sound", "audio", "voice", "moan"):
        yield term.encode("utf-8")
        yield term.capitalize().encode("utf-8")
        yield term.upper().encode("utf-8")
    for term in ["3DSE"]:
        yield term.encode("utf-8")


def sfx_extra_terms() -> "Generator[bytes]":
    for term in ["sfx"]:
        yield term.encode("utf-8")
        yield term.capitalize().encode("utf-8")
        yield term.upper().encode("utf-8")
    for term in ("SE", "VA"):
        yield term.encode("utf-8")


def animation_terms() -> "Generator[bytes]":
    for term in ("animation", "motion", "move"):
        yield term.encode("utf-8")
        yield term.capitalize().encode("utf-8")
        yield term.upper().encode("utf-8")


def body_terms() -> "Generator[bytes]":
    for term in (
        "body",
        "hips",
        "waist",
        "chest",
        "thigh",
        "head",
        "neck",
        "shoulder",
        "hand",
        "finger",
        "knee",
        "foot",
        "elbow",
    ):
        yield term.encode("utf-8")
        yield term.capitalize().encode("utf-8")
        yield term.upper().encode("utf-8")


def body_extra_terms() -> "Generator[bytes]":
    for term in ("arm", "leg"):
        yield term.encode("utf-8")
        yield term.capitalize().encode("utf-8")
        yield term.upper().encode("utf-8")


def make_terms_regex(terms: "Iterable[bytes]") -> "re.Pattern":
    # For a term to be considered "found" it must be surrounded by non-ASCII characters or spaces
    return re.compile(
        rb"(?<=[\x00-\x1F\x7F-\x9F])("
        + b"|".join(re.escape(term) for term in terms)
        + rb")(?=[\x00-\x1F\x7F-\x9F])",
    )


class SceneData:
    class Error(Exception):
        pass

    class ContentError(Error):
        pass

    class TimelineDoesNotExist(Error):
        pass

    class MemoryError(Error):
        pass

    class ValueError(Error):
        pass

    file_path: str
    timeline_regex: "re.Pattern"
    timeline_status: str
    sfx_status: bool
    image_type: Optional[str]

    _TIMELINE_PATTERN = re.compile(
        rb"timeline.+?sceneInfo(?P<flag>.*?)(?P<data><root\b[^>/]*?/>|<root\b[^>]*?>(?P<inner>.*?)</root>)",
        re.DOTALL,
    )
    _DURATION_PATTERN = re.compile(rb'duration="([\d\.]+)"')
    _ANIMATION_PATTERN = re.compile(rb'guideObjectPath="([^"]*)"')
    _SFX_TERMS = make_terms_regex(sfx_terms())
    _SFX_EXTRA_TERMS = make_terms_regex(itertools.chain(sfx_terms(), sfx_extra_terms()))
    _ANIMATION_TERMS = make_terms_regex(animation_terms())
    _BODY_TERMS = make_terms_regex(body_terms())
    _BODY_EXTRA_TERMS = make_terms_regex(
        itertools.chain(body_terms(), body_extra_terms())
    )
    _THREENODENAMING_PATTERN = re.compile(
        rb"org.njaecha.plugins.treenodenaming(?P<workspace>.+?)org.njaecha.plugins",
        re.DOTALL,
    )

    # Timeline data starts with b'timeline[somebytes_I_dont_know]sceneInfo[bytes(length_flag + bit_length_of_data_lenght)][bytes(data_lenght)]'
    # right before the xml data, the known flags must be updated on every change.
    _timeline_length_flag: int = 216

    def __init__(self, file_path: str, timeline_regex: Optional[str] = None):
        self.file_path = file_path
        self.timeline_regex = (
            re.compile(timeline_regex) if timeline_regex else self._TIMELINE_PATTERN
        )
        try:
            with open(file_path, "rb") as filekk:
                self._content = filekk.read()
        except MemoryError:
            raise SceneData.MemoryError("File is to big, file.read() failed")

        if not self._is_scene_data():
            raise SceneData.ContentError("Not a scene data file")

        self._cached_timeline: Optional[bytes] = None

        (
            self.timeline_status,
            self.image_type,
            self.sfx_status,
            self._duration,
        ) = self._check_timeline()

    @property
    def content_str(self) -> str:
        try:
            return self._content.decode("utf-8", errors="ignore")
        except MemoryError:
            raise SceneData.MemoryError(
                "File content is too big, content.decode('utf-8', errors='ignore') failed"
            )

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def duration(self) -> Optional[float]:
        return self._duration

    @duration.setter
    def duration(self, value: float):
        raise NotImplementedError("Modification of the timeline is not supported (yet)")

        if not self.has_timeline():
            raise SceneData.ValueError("Scene data does not have a timeline")
        elif self.image_type == "static":
            raise SceneData.ValueError(
                "Scene data is Static and does not have a duration"
            )
        elif value <= 0:
            raise SceneData.ValueError("Duration must be greater than 0")
        elif value == self._duration:
            return
        else:
            # replace "duration={value}" by value in the timeline string
            modified_timeline = re.sub(
                self._DURATION_PATTERN,
                f'duration="{value}"'.encode("utf-8"),
                self.get_timeline_xml(),
            )
            self.replace_timeline(modified_timeline)
            self._duration = value
        return self

    def get_timeline_info(self) -> Tuple[str, Optional[str], bool, Optional[float]]:
        return self.timeline_status, self.image_type, self.sfx_status, self.duration

    def get_timeline_xml(self, raise_exception: bool = False) -> Optional[bytes]:
        if self._cached_timeline:
            return self._cached_timeline
        elif match := self.timeline_regex.search(self._content):
            if match.group("inner") is not None:
                self._cached_timeline = match.group("data")
                return self._cached_timeline
            elif raise_exception:
                raise SceneData.TimelineDoesNotExist("Timeline data not found")

        return None

    def get_timeline_xml_tree(
        self, raise_exception: bool = False
    ) -> Optional[et.ElementTree]:
        xml_str = self.get_timeline_xml(raise_exception=raise_exception)
        return et.ElementTree(et.fromstring(xml_str)) if xml_str else None

    def get_treenodenaming(self, raise_exception: bool = False) -> Optional[bytes]:
        if match := self._THREENODENAMING_PATTERN.search(self._content):
            return match.group("workspace")
        elif raise_exception:
            raise SceneData.TimelineDoesNotExist("Treenodenaming data not found")
        else:
            return None

    def replace_timeline(self, new_timeline: str):
        """Replace the timeline data with a new one"""

        raise NotImplementedError("Modification of the timeline is not supported (yet)")

        length_flag, timeline_byte_legth = self._get_timeline_byte_vars(new_timeline)

        def replace(match):
            return (
                match.group(0)
                .replace(match.group("data"), new_timeline)
                .replace(match.group("flag"), length_flag + timeline_byte_legth)
            )

        self._content = re.sub(self.timeline_regex, replace, self._content)
        self._cached_timeline = new_timeline

    def has_timeline(self) -> bool:
        return self.timeline_status == "has_timeline"

    def save(self, overwrite: bool = False):
        filename, ext = os.path.splitext(self.file_path)
        if not overwrite and os.path.exists(self.file_path):
            filename = filename + "_new"

        file_path = os.path.join(os.path.dirname(self.file_path), f"{filename}{ext}")
        with open(file_path, "wb") as filekk:
            filekk.write(self._content)

        self.file_path = file_path

    def _get_timeline_byte_vars(self, timeline) -> Tuple[bytes, bytes]:
        """Return the length flag and the timeline byte length"""
        num_bytes = (len(timeline).bit_length() + 7) // 8
        length_flag = (
            self._timeline_length_flag + (num_bytes if num_bytes <= 3 else 3)
        ).to_bytes(1, byteorder="big")
        timeline_byte_length = len(timeline).to_bytes(num_bytes, byteorder="big")
        return length_flag, timeline_byte_length

    def _is_scene_data(self) -> bool:
        """檢查是否為scene data :: Check if the file is a scene data"""
        return (
            os.path.splitext(self.file_path)[1] == ".png" and b"KStudio" in self._content
        )

    def _traverse_tree(
        self, node: et.Element, min_required: int = 3, stop: int = 0
    ) -> int:
        """
        Count how many interpolables of type 'guideObjectPath' have a number of keyframes >= min_required.
        """
        found: int = 0
        for child in node:
            if child.tag == "interpolableGroup":
                found += self._traverse_tree(child)
            elif child.tag == "interpolable":
                if (
                    "body" in child.get("guideObjectPath", "")
                    or child.get("guideObjectPath") is not None
                    and len(child) >= min_required
                ):
                    found += 1
            if stop and found >= stop:
                break

        return found

    def _check_timeline(self) -> Tuple[str, Optional[str], bool, float]:
        """
        Returns:
            tuple (timeline_status, image_type, sfx_status, duration)
            timeline_status: "has_timeline", "no_timeline"
            image_type: "animation", "dynamic", "static", None
            sfx_status: bool
            duration: float
        """
        timeline_xml = self.get_timeline_xml()

        if not timeline_xml:  # Check if there is a timeline
            return "no_timeline", None, False, None
        elif b"Timeline" not in timeline_xml:
            return "has_timeline", "static", False, 0.0

        workspace = self.get_treenodenaming() or b"empty"
        if workspace == b"empty":
            # If the scene does not use the treenodenaming plugin, check for 4+ letter sfx terms in the content
            sfx_status = re.search(self._SFX_TERMS, self.content) is not None
        else:
            # If it uses the plugin, check for 2+ letter sfx terms in the workspace
            sfx_status = re.search(self._SFX_EXTRA_TERMS, workspace) is not None

        timeline = et.ElementTree(et.fromstring(timeline_xml)).getroot()

        duration = float(timeline.get("duration", 0.0))
        if not duration:
            return "has_timeline", "dynamic", sfx_status, 0.0

        # Iterate over timeline and all its children until you find 3 or more children that fufill these 2 conditions:
        # - They each have the "guideObjectPath" attribute.
        # - They have 3 or more children/keyframes.
        # If the conditions are met return "animation" else return "dynamic"
        min_required = 3
        if self._traverse_tree(timeline, min_required, 3) >= 3:
            return "has_timeline", "animation", sfx_status, duration
        else:
            # No guideObjectPath means no motion, except face motions and cameras
            return "has_timeline", "dynamic", sfx_status, duration
