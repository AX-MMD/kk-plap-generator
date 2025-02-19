import math
import tkinter as tk
from tkinter import simpledialog, ttk
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

from kk_plap_generator.generator.plap_generator import PlapGenerator
from kk_plap_generator.gui import info_text
from kk_plap_generator.gui.info_message import InfoMessageFrame
from kk_plap_generator.gui.widgets.base import PlapWidget
from kk_plap_generator.models import (
    STRING_TO_COMPONENT_CONFIG,
    ActivableComponentConfig,
    ComponentConfig,
    MultiActivableComponentConfig,
    PregPlusComponentConfig,
)
from kk_plap_generator.utils import get_curve_types

if TYPE_CHECKING:
    from kk_plap_generator.gui.main_menu import PlapUI


class ComponentConfigsWidget(PlapWidget):
    def __init__(self, app: "PlapUI", masterframe):
        super().__init__(app, masterframe)

        self.components_frame = tk.Frame(masterframe, bd=2, relief="solid")
        self.components_frame.grid(row=0, column=0, sticky="nsew")

        # Top
        self.top_frame = tk.Frame(self.components_frame)
        self.top_frame.grid_columnconfigure(0, weight=90)
        self.top_frame.grid_columnconfigure(1, weight=10)
        self.top_frame.pack(fill=tk.X)

        # Components
        self.top_left_frame = tk.Frame(self.top_frame)
        self.top_left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.components_label = tk.Label(self.top_left_frame, text="Components")
        self.components_label.pack()

        info_message = info_text.SOUND_FOLDERS
        self.top_right_frame = InfoMessageFrame(self.top_frame, info_message)

        self.components_listbox = tk.Listbox(self.components_frame)
        self.components_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.components_listbox.bind("<Double-Button-1>", self.edit_component)

        self.components_scrollbar = tk.Scrollbar(self.components_frame, orient="vertical")
        self.components_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.components_listbox.config(yscrollcommand=self.components_scrollbar.set)
        self.components_scrollbar.config(command=self.components_listbox.yview)

        self.update()

        self.add_component_name_button = tk.Button(
            self.components_frame, text="+", command=self.add_component
        )
        self.add_component_name_button.pack(fill=tk.X)

        self.remove_component_name_button = tk.Button(
            self.components_frame,
            text="-",
            command=self.remove_selected_component,
        )
        self.remove_component_name_button.pack(fill=tk.X)

    def update(self):
        self.components_listbox.delete(0, tk.END)
        for sc in self.app.store.component_configs:
            if isinstance(sc, ActivableComponentConfig):
                if isinstance(sc, MultiActivableComponentConfig):
                    items = f"  ({len(sc.item_configs)})"
                else:
                    items = "  "

                offset_str = f"({'+' if sc.offset >= 0 else '-'}{abs(sc.offset)}s)"
                cutoff_str = f"(end:{sc.cutoff}s)" if sc.cutoff != math.inf else ""
                self.components_listbox.insert(
                    tk.END, f"{sc.name}{items}{offset_str}{cutoff_str}"
                )
            elif isinstance(sc, PregPlusComponentConfig):
                self.components_listbox.insert(
                    tk.END,
                    f"{sc.name}  (min:{sc.min_value} max:{sc.max_value})  ({'+' if sc.offset >= 0 else '-'}{abs(sc.offset)}s)",
                )

    def edit_component(self, event=None):
        selected_index = self.components_listbox.curselection()
        if not selected_index:
            return

        index: int = selected_index[0]
        component = self.app.store.component_configs[index]

        dialog = ComponentConfigDialog(
            self,
            component,
            is_edit=True,
            title="Edit Sound Component",
        )

        if dialog.is_valid():
            self.app.store.component_configs[index] = dialog.component_config
            self.update()

    def add_component(self):
        dialog = ComponentConfigDialog(self, title="Add Component")
        if dialog.is_valid():
            self.app.store.component_configs.append(dialog.component_config)
            self.update()

    def remove_selected_component(self):
        selected_index = self.components_listbox.curselection()
        if selected_index:
            self.app.store.component_configs.pop(selected_index[0])
            self.update()


class ComponentConfigDialog(simpledialog.Dialog):
    def __init__(
        self,
        parent: PlapWidget,
        component_config: Optional[ComponentConfig] = None,
        title=None,
        is_edit: bool = False,
    ):
        self.parent = parent
        self.is_cancelled = True
        self.is_edit = is_edit
        self.component_config: ComponentConfig = (
            component_config
            or MultiActivableComponentConfig(
                name="MAC", item_configs=[ActivableComponentConfig("MAC-Item1")]
            )
        )
        self.type_var = tk.StringVar(
            value=self.component_config.__class__.get_conf_type()
        )
        self.item_entries: List[Tuple[tk.Entry, tk.Entry, tk.Entry, tk.Button]] = []
        super().__init__(parent.masterframe, title)

    def body(self, master):
        tk.Label(master, text="Type:").grid(row=0, column=0)
        self.type_selector = ttk.Combobox(
            master,
            textvariable=self.type_var,
            values=list(STRING_TO_COMPONENT_CONFIG.keys()),
            state="disabled" if self.is_edit else "normal",
        )
        self.type_selector.grid(row=0, column=1)
        self.type_selector.bind("<<ComboboxSelected>>", self.on_type_change)

        tk.Label(master, text="Name:").grid(row=1, column=0)
        self.name_entry = tk.Entry(master)
        self.name_entry.grid(row=1, column=1)
        self.name_entry.insert(0, self.component_config.name)

        tk.Label(master, text="Offset (sec):").grid(row=2, column=0)
        self.offset_entry = tk.Entry(master)
        self.offset_entry.grid(row=2, column=1)
        self.offset_entry.insert(0, str(self.component_config.offset))

        self.extra_fields_frame = tk.Frame(master)
        self.extra_fields_frame.grid(row=3, column=0, columnspan=2)
        self.update_extra_fields()

        return self.name_entry

    def update_extra_fields(self):
        for widget in self.extra_fields_frame.winfo_children():
            widget.destroy()

        if self.type_var.get() == ActivableComponentConfig.get_conf_type():
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "AC")
            self.component_config.name = "AC"
            ac_config = ActivableComponentConfig.from_toml_dict(
                **self.component_config.to_toml_dict()
            )
            self.component_config = ac_config

            def name_entry_change(event):
                self.component_config.name = self.name_entry.get()

            self.name_entry.bind("<KeyRelease>", name_entry_change)

            tk.Label(self.extra_fields_frame, text="Offset (sec):").grid(row=1, column=0)
            self.offset_entry = tk.Entry(self.extra_fields_frame)
            self.offset_entry.grid(row=1, column=1)
            self.offset_entry.insert(0, str(ac_config.offset))

            tk.Label(self.extra_fields_frame, text="Cutoff (sec):").grid(row=0, column=0)
            self.cutoff_entry = tk.Entry(self.extra_fields_frame)
            self.cutoff_entry.grid(row=0, column=1)
            self.cutoff_entry.insert(
                0, str(ac_config.cutoff) if ac_config.cutoff != math.inf else ""
            )

        elif self.type_var.get() == MultiActivableComponentConfig.get_conf_type():
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "MAC")
            self.component_config.name = "MAC"
            mac_config = MultiActivableComponentConfig.from_toml_dict(
                **self.component_config.to_toml_dict()
            )
            self.component_config = mac_config

            def name_entry_change(event):
                old_name = self.component_config.name
                self.component_config.name = self.name_entry.get()
                for name_entry, _, _, _ in self.item_entries:
                    old_item_name = name_entry.get()
                    name_entry.delete(0, tk.END)
                    name_entry.insert(
                        0, old_item_name.replace(old_name, self.component_config.name)
                    )

            self.name_entry.bind("<KeyRelease>", name_entry_change)

            tk.Label(self.extra_fields_frame, text="Cutoff (sec):").grid(row=0, column=0)
            self.cutoff_entry = tk.Entry(self.extra_fields_frame)
            self.cutoff_entry.grid(row=0, column=1)
            self.cutoff_entry.insert(
                0, str(mac_config.cutoff) if mac_config.cutoff != math.inf else ""
            )

            # Pattern value display
            self.pattern_string_frame = tk.Frame(self.extra_fields_frame)
            self.pattern_string_frame.grid(row=1, column=0, columnspan=2)
            self.pattern_string_value = tk.Label(
                self.pattern_string_frame,
                text=mac_config.pattern,
            )
            self.pattern_string_value.pack()

            self.pattern_buttons_frame = tk.Frame(self.pattern_string_frame)
            self.pattern_buttons_frame.pack()
            for char in PlapGenerator.VALID_PATTERN_CHARS:

                def button_action(c=char):
                    self.add_to_pattern_string(c, mac_config)

                button = tk.Button(
                    self.pattern_buttons_frame,
                    text=char,
                    command=button_action,
                )
                button.pack(side=tk.LEFT)

            def clear_pattern_string():
                self.clear_pattern_string(mac_config)

            self.clear_pattern_string_button = tk.Button(
                self.pattern_string_frame,
                text="Clear ✖",
                command=clear_pattern_string,
            )
            self.clear_pattern_string_button.pack()

            # Create the table
            self.table_frame = tk.Frame(self.extra_fields_frame)
            self.table_frame.grid(row=2, column=0, columnspan=2)

            headers = ["Name", "Offset (sec)", "Cutoff (sec)", "Delete"]
            for col, header in enumerate(headers):
                tk.Label(self.table_frame, text=header).grid(row=0, column=col)

            self.item_entries = []
            for i, item in enumerate(mac_config.item_configs):
                self.add_table_row(i, item)

            add_button = tk.Button(
                self.extra_fields_frame, text="Add", command=self.add_table_row
            )
            add_button.grid(row=3, column=0, columnspan=2)

        elif self.type_var.get() == PregPlusComponentConfig.get_conf_type():
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "Preg+")
            self.component_config.name = "Preg+"
            preg_config: PregPlusComponentConfig = PregPlusComponentConfig(
                **self.component_config.to_toml_dict()
            )
            self.component_config = preg_config

            def name_entry_change(event):
                self.component_config.name = self.name_entry.get()

            self.name_entry.bind("<KeyRelease>", name_entry_change)

            tk.Label(self.extra_fields_frame, text="Min Value:").grid(row=0, column=0)
            self.min_value_entry = tk.Entry(self.extra_fields_frame)
            self.min_value_entry.grid(row=0, column=1)
            self.min_value_entry.insert(0, str(preg_config.min_value))

            tk.Label(self.extra_fields_frame, text="Max Value:").grid(row=1, column=0)
            self.max_value_entry = tk.Entry(self.extra_fields_frame)
            self.max_value_entry.grid(row=1, column=1)
            self.max_value_entry.insert(0, str(preg_config.max_value))

            # Label and entry for the curve of PregPlusComponentConfig
            tk.Label(self.extra_fields_frame, text="In Curve:").grid(row=2, column=0)
            self.in_curve_selector = ttk.Combobox(
                self.extra_fields_frame,
                textvariable=preg_config.in_curve,
                values=get_curve_types(),
            )
            self.in_curve_selector.grid(row=2, column=1)

            tk.Label(self.extra_fields_frame, text="In Curve:").grid(row=3, column=0)
            self.out_curve_selector = ttk.Combobox(
                self.extra_fields_frame,
                textvariable=preg_config.out_curve,
                values=get_curve_types(),
            )
            self.out_curve_selector.grid(row=3, column=1)

    def add_table_row(self, i=None, item=None):
        if i is None:
            i = len(self.item_entries)
            offset = float(self.item_entries[-1][1].get() if self.item_entries else 0)
            item = ActivableComponentConfig(
                f"{self.component_config.name}-Item{i + 1}", offset=offset
            )

        name_entry = tk.Entry(self.table_frame)
        name_entry.grid(row=i + 1, column=0)
        name_entry.insert(0, item.name)

        offset_entry = tk.Entry(self.table_frame)
        offset_entry.grid(row=i + 1, column=1)
        offset_entry.insert(0, str(item.offset))

        cutoff_entry = tk.Entry(self.table_frame)
        cutoff_entry.grid(row=i + 1, column=2)
        cutoff_entry.insert(0, "" if item.cutoff == math.inf else str(item.cutoff))

        def delete_table_row(row=i):
            self.delete_table_row(row)

        delete_button = tk.Button(self.table_frame, text="-", command=delete_table_row)
        delete_button.grid(row=i + 1, column=3)

        self.item_entries.append((name_entry, offset_entry, cutoff_entry, delete_button))

    def delete_table_row(self, row):
        for widget in self.item_entries[row]:
            cast(Union[tk.Entry, tk.Button], widget).grid_forget()
        self.item_entries.pop(row)
        self.update_table_indices()

    def update_table_indices(self):
        for i, (name_entry, offset_entry, cutoff_entry, delete_button) in enumerate(
            self.item_entries
        ):
            name_entry.grid(row=i + 1, column=0)
            offset_entry.grid(row=i + 1, column=1)
            cutoff_entry.grid(row=i + 1, column=2)
            delete_button.grid(row=i + 1, column=3)
            name_entry.delete(0, tk.END)
            name_entry.insert(0, f"{self.component_config.name}-Item{i + 1}")

    def add_to_pattern_string(self, char, mac_config: MultiActivableComponentConfig):
        mac_config.pattern += char
        self.pattern_string_value.config(text=mac_config.pattern)

    def clear_pattern_string(self, mac_config: MultiActivableComponentConfig):
        mac_config.pattern = ""
        self.pattern_string_value.config(text="")

    def on_type_change(self, event):
        self.update_extra_fields()

    def apply(self):
        if self.type_var.get() == ActivableComponentConfig.get_conf_type():
            self.component_config = ActivableComponentConfig(
                name=self.name_entry.get() if self.name_entry.get() else "AC",
            )
            if cutoff := self.cutoff_entry.get():
                self.component_config.cutoff = float(cutoff)
            if offset := self.offset_entry.get():
                self.component_config.offset = float(offset)

        elif self.type_var.get() == MultiActivableComponentConfig.get_conf_type():
            self.component_config = MultiActivableComponentConfig(
                name=self.name_entry.get() if self.name_entry.get() else "MAC",
                pattern=self.pattern_string_value.cget("text"),
            )
            if cutoff := self.cutoff_entry.get():
                self.component_config.cutoff = float(cutoff)
            if offset := self.offset_entry.get():
                self.component_config.offset = float(offset)

            for i, (name_entry, offset_entry, cutoff_entry, _) in enumerate(
                self.item_entries
            ):
                item = ActivableComponentConfig(
                    name=name_entry.get()
                    if name_entry.get()
                    else f"{self.component_config.name}-Item{i + 1}",
                )
                if cutoff := cutoff_entry.get():
                    item.cutoff = float(cutoff)
                if offset := offset_entry.get():
                    item.offset = float(offset)

                self.component_config.item_configs.append(item)

        elif self.type_var.get() == PregPlusComponentConfig.get_conf_type():
            self.component_config = PregPlusComponentConfig(
                name=self.name_entry.get() if self.name_entry.get() else "Preg+",
            )
            if offset := self.offset_entry.get():
                self.component_config.offset = float(offset)
            if min_value := int(self.min_value_entry.get()):
                self.component_config.min_value = min_value
            if max_value := int(self.max_value_entry.get()):
                self.component_config.max_value = max_value
            if in_curve := self.in_curve_selector.get():
                self.component_config.in_curve = in_curve
            if out_curve := self.out_curve_selector.get():
                self.component_config.out_curve = out_curve

        self.is_cancelled = False

    def is_valid(self):
        return (
            not self.is_cancelled
            and self.component_config is not None
            and self.component_config.name != ""
        )

    # class ItemConfigsWidget(PlapWidget):
    #     def __init__(self, app: "PlapUI", masterframe):
    #         super().__init__(app, masterframe)

    #         self.item_configs_frame = tk.Frame(masterframe, bd=2, relief="solid")
    #         self.item_configs_frame.grid(row=0, column=0, sticky="nsew")

    #         tk.Label(self.item_configs_frame, text="Name:").grid(row=1, column=0)
    #         self.name_entry = tk.Entry(self.item_configs_frame)
    #         self.name_entry.grid(row=1, column=1)
    #         self.name_entry.insert(0, self.component_config.name)

    #         tk.Label(self.item_configs_frame, text="Offset:").grid(row=2, column=0)
    #         self.offset_entry = tk.Entry(self.item_configs_frame)
    #         self.offset_entry.grid(row=2, column=1)
    #         self.offset_entry.insert(0, str(self.component_config.offset))

    #         self.components_listbox = tk.Listbox(self.item_configs_frame)
    #         self.components_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    #         self.components_listbox.bind("<Double-Button-1>", self.edit_component)

    #         self.components_scrollbar = tk.Scrollbar(self.item_configs_frame, orient="vertical")
    #         self.components_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    #         self.components_listbox.config(yscrollcommand=self.components_scrollbar.set)
    #         self.components_scrollbar.config(command=self.components_listbox.yview)

    #         self.update()

    #         self.add_component_name_button = tk.Button(
    #             self.item_configs_frame, text="+", command=self.add_component
    #         )
    #         self.add_component_name_button.pack(fill=tk.X)

    #         self.remove_component_name_button = tk.Button(
    #             self.item_configs_frame,
    #             text="-",
    #             command=self.remove_selected_component,
    #         )
    #         self.remove_component_name_button.pack(fill=tk.X)

    #     def update(self):
    #         self.components_listbox.delete(0, tk.END)
    #         for sc in self.app.store.interpolable_configs:
    #             if isinstance(sc, ActivableComponentConfig):
    #                 if isinstance(sc, MultiActivableComponentConfig):
    #                     items = f"  ({len(sc.item_configs)})"
    #                 else:
    #                     items = "  "

    #                 offset_str = f"({'+' if sc.offset >= 0 else '-'}{abs(sc.offset
