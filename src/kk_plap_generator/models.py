import math
from typing import Dict, List, Tuple, Type

from kk_plap_generator.utils import get_curve_types


class ComponentConfig:
    def __init__(self, name: str, *, offset: float = 0.0, **kwargs):
        self.name: str = name
        self.offset: float = offset

    def copy(self):
        return self.__class__.from_toml_dict(**self.to_toml_dict())

    def to_toml_dict(self):
        return {
            "name": self.name,
            "offset": self.offset,
            "type": self.__class__.get_conf_type(),
        }

    @classmethod
    def from_toml_dict(cls, **kwargs):
        return cls(**kwargs)

    @classmethod
    def get_conf_type(cls) -> str:
        return cls.__name__


class ActivableComponentConfig(ComponentConfig):
    def __init__(
        self,
        name: str = "activable",
        *,
        cutoff: float = math.inf,
        offset: float = 0.0,
        **kwargs,
    ):
        super().__init__(name=name, offset=offset, **kwargs)
        self.cutoff: float = cutoff

    def to_toml_dict(self):
        return dict(super().to_toml_dict(), cutoff=self.cutoff)


class MultiActivableComponentConfig(ActivableComponentConfig):
    def __init__(
        self,
        name: str = "multiactivable",
        *,
        item_configs: List[ActivableComponentConfig] = [],
        pattern: str = "V",
        cutoff: float = math.inf,
        offset: float = 0.0,
        **kwargs,
    ):
        super().__init__(name=name, offset=offset, cutoff=cutoff, **kwargs)
        self.pattern: str = pattern
        self.item_configs: List[ActivableComponentConfig] = item_configs

    def to_toml_dict(self):
        return dict(
            super().to_toml_dict(),
            item_configs=[ic.to_toml_dict() for ic in self.item_configs],
            pattern=self.pattern,
        )

    @classmethod
    def from_toml_dict(cls, **kwargs):
        return cls(
            item_configs=[
                ActivableComponentConfig(**ic) for ic in kwargs.pop("item_configs", [])
            ],
            **kwargs,
        )


class PregPlusComponentConfig(ComponentConfig):
    def __init__(
        self,
        name: str = "preg+",
        *,
        min_value: int = 0,
        max_value: int = 45,
        in_curve: str = get_curve_types()[0],
        out_curve: str = get_curve_types()[0],
        offset: float = 0.0,
        **kwargs,
    ):
        super().__init__(name=name, offset=offset, **kwargs)
        self.min_value: int = min_value
        self.max_value: int = max_value
        self.in_curve: str = in_curve
        self.out_curve: str = out_curve

    def to_toml_dict(self):
        return dict(
            super().to_toml_dict(),
            min_value=self.min_value,
            max_value=self.max_value,
            in_curve=self.in_curve,
            out_curve=self.out_curve,
        )


STRING_TO_COMPONENT_CONFIG: Dict[str, Type[ComponentConfig]] = {
    MultiActivableComponentConfig.get_conf_type(): MultiActivableComponentConfig,
    PregPlusComponentConfig.get_conf_type(): PregPlusComponentConfig,
    ActivableComponentConfig.get_conf_type(): ActivableComponentConfig,
}


def deserialize_component(data: dict) -> ComponentConfig:
    component = STRING_TO_COMPONENT_CONFIG.get(data["type"])
    if component is None:
        raise ValueError(f"Unknown component type: {data['type']}")
    else:
        return component(**data)


class GroupConfig:
    def __init__(
        self,
        *,
        ref_interpolable: str = "",
        ref_single_file: str = "",
        last_single_file_folder: str = "",
        time_ranges: List[Tuple[str, str]] = [("00:00.00", "END")],
        offset: float = 0.0,
        component_configs: List[dict] = [],
        min_pull_out: float = 0.2,
        min_push_in: float = 0.8,
    ):
        self.ref_interpolable: str = ref_interpolable
        self.ref_single_file: str = ref_single_file
        self.last_single_file_folder: str = last_single_file_folder
        self.time_ranges: List[Tuple[str, str]] = time_ranges
        self.offset: float = offset
        self.component_configs: List[ComponentConfig] = [
            self._deserialize_component(cc) for cc in component_configs
        ]
        self.min_pull_out: float = min_pull_out
        self.min_push_in: float = min_push_in

    def _deserialize_component(self, data: dict) -> ComponentConfig:
        component = STRING_TO_COMPONENT_CONFIG.get(data["type"])
        if component is None:
            raise ValueError(f"Unknown component type: {data['type']}")
        else:
            return component.from_toml_dict(**data)

    def to_toml_dict(self):
        return {
            "ref_interpolable": self.ref_interpolable,
            "ref_single_file": self.ref_single_file,
            "last_single_file_folder": self.last_single_file_folder,
            "time_ranges": self.time_ranges,
            "offset": self.offset,
            "component_configs": [cc.to_toml_dict() for cc in self.component_configs],
            "min_pull_out": self.min_pull_out,
            "min_push_in": self.min_push_in,
        }


def deserialize_group(data: dict) -> GroupConfig:
    for key, value in data.items():
        if value == "None":
            data[key] = None

    return GroupConfig(**data)
