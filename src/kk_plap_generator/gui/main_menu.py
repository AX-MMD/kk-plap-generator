import os
import tkinter as tk
import traceback
from tkinter import filedialog, font, messagebox
from typing import List, Optional

import tkinterdnd2
import toml

from kk_plap_generator import settings
from kk_plap_generator.generator import NodeNotFoundError, PlapGenerator
from kk_plap_generator.gui.output_mesage_box import CustomMessageBox
from kk_plap_generator.gui.utils import generate_plaps, load_config_file
from kk_plap_generator.gui.validators import ValidationError
from kk_plap_generator.gui.widgets import (
    ComponentConfigsWidget,
    DnDWidget,
    RefInterpolableWidget,
    SeqAdjustmentWidget,
    TimeRangesWidget,
)
from kk_plap_generator.gui.widgets.base import PlapWidget
from kk_plap_generator.gui.widgets.config_selector_widget import ConfigSelectorWidget
from kk_plap_generator.models import GroupConfig


class PlapUI(tk.Frame):
    def __init__(
        self,
        master: tkinterdnd2.Tk,
        config_path=settings.CONFIG_FILE,
        default_config_path=settings.DEFAULT_CONFIG_FILE,
    ):
        super().__init__(master)
        self.master = master
        self.config_path: str = config_path
        self.default_config_path = default_config_path
        self.symbol_font = font.Font(family="Arial", size=13)

        self.current_page = 0
        # First boot
        if not os.path.isfile(self.config_path):
            self.load_config(self.default_config_path)
        else:
            self.load_config()

        self.pack(fill=tk.BOTH, expand=True)
        self.widgets: List[PlapWidget] = []
        self.create_widgets()

        self.master.protocol("WM_DELETE_WINDOW", self.on_program_close)  # type: ignore

    @property
    def store(self) -> GroupConfig:
        return self._stores[self.current_page]

    @store.setter
    def store(self, value: GroupConfig):
        self._stores[self.current_page] = value
        self.update_widgets()

    @property
    def plap_config(self) -> List[GroupConfig]:
        return self._stores

    def load_config(self, path: Optional[str] = None):
        try:
            path = path or self.config_path
            self._stores: List[GroupConfig] = load_config_file(path)
            self.current_page = 0
            if hasattr(self, "widgets"):
                self.update_widgets()
        except FileNotFoundError as e:
            traceback.print_exc()
            self.wait_window(
                CustomMessageBox(
                    self,
                    "Error",
                    f"Could not find the config file at {path}.",
                )
            )
            raise e
        except toml.TomlDecodeError as e:
            traceback.print_exc()
            self.wait_window(
                CustomMessageBox(
                    self,
                    "Error",
                    f"Could not read the config file at {path}.\n" + str(e),
                )
            )
            raise e
        except KeyError as e:
            traceback.print_exc()
            self.wait_window(
                CustomMessageBox(
                    self,
                    "Error",
                    f"Could not find 'plap_group' in the config file at {path}.",
                )
            )
            raise e

    def save_config(self, path: Optional[str] = None):
        self.widgets_save()
        with open(path or self.config_path, "w", encoding="utf-8") as f:
            toml.dump({"plap_group": [gc.to_toml_dict() for gc in self._stores]}, f)

    def on_program_close(self):
        try:
            self.widgets_save()
            self.save_config()
        except Exception:
            traceback.print_exc()
        finally:
            self.master.destroy()

    def update_widgets(self):
        for widget in self.widgets:
            widget.update()

    def create_widgets(self):
        # Create the main 2x3 grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=90)
        self.grid_rowconfigure(1, weight=10)

        # Left frame with 2x1 grid
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=90)
        self.left_frame.grid_rowconfigure(1, weight=10)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Middle frame with 2x1 grid
        self.middle_frame = tk.Frame(self)
        self.middle_frame.grid(row=0, column=1, sticky="nsew")
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_rowconfigure(1, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)

        # Right frame with 2x1 grid
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Drop file
        self.dnd_widget = DnDWidget(self, self.left_frame)

        # Reference Interpolable
        self.ref_interpolable_widget = RefInterpolableWidget(self, self.left_frame)

        # Component Configs
        self.component_configs_widget = ComponentConfigsWidget(self, self.middle_frame)

        # Time Ranges
        self.time_ranges_widget = TimeRangesWidget(self, self.middle_frame)

        # Sound Pattern
        # self.sound_pattern_widget = SoundPatternWidget(self, self.middle_frame)

        # Global Offset and Min Pull Out/In
        self.seq_adjustment_widget = SeqAdjustmentWidget(self, self.right_frame)

        self.bottom_left_frame = tk.Frame(self)
        self.bottom_left_frame.grid(row=1, column=0, sticky="nsew")
        self.bottom_left_frame.grid_columnconfigure(0, weight=1)
        self.bottom_left_frame.grid_columnconfigure(1, weight=1)
        self.bottom_left_frame.grid_columnconfigure(2, weight=1)

        # Load Button
        self.config_loader_widget = ConfigSelectorWidget(self, self.bottom_left_frame)

        # Generate Button
        self.generate_button = tk.Button(
            self.bottom_left_frame, text="▶", fg="green", command=self.generate_plaps
        )
        self.generate_button.grid(row=0, column=1, sticky="nsew")

        # Save Button
        self.save_button = tk.Button(
            self.bottom_left_frame, text="Export 💾", command=self.save_button_action
        )
        self.save_button.grid(row=0, column=2, sticky="nsew")

    def save_button_action(self):
        self.save_config()
        file_path = filedialog.asksaveasfilename(
            initialdir=settings.CONFIG_FOLDER,
            title="Export Config File",
            filetypes=(("TOML files", "*.toml"),),
        )
        if file_path:
            # get the path and the path without the extension
            path, ext = os.path.splitext(file_path)
            path = path + ".toml"
            self.save_config(path)
            # check that the file was created
            if os.path.isfile(path):
                messagebox.showinfo("Success", f"Config file exported successfully to {path}.")
            else:
                messagebox.showerror("Error", f"Failed to export config file at {path}.")

        self.update_widgets()

    def widgets_save(self):
        errors: List[str] = []
        for widget in self.widgets:
            try:
                widget.save()
            except ValidationError as e:
                errors.extend(e.errors)
        if errors:
            raise ValidationError(errors=errors)

    def generate_plaps(self):
        if self.dnd_widget.get_single_file() is None:
            messagebox.showerror("Error", "Please select a file.xml")
        else:
            try:
                self.save_config()
                output = generate_plaps(self.plap_config)
                CustomMessageBox(
                    self, "Success ✔", "::: Success :::\n\n" + "\n".join(output)
                )
            except NodeNotFoundError as e:
                if e.xml_path is not None:
                    CustomMessageBox(self, "Failled ✖", traceback.format_exc())

                message = "::: Node not found :::\n"
                message += f"\n> Missing node: {e.get_node_string()}"
                if e.node_name == "interpolableGroup":
                    message += f'\n> Could not find the parent group\n    "{e.value}"\n  in the xml file.'
                    message += f'\n> Make sure the path\n    "{self.store.ref_interpolable}"\n is correct.'
                elif e.node_name == "interpolable":
                    message += f'\n> Could not find the interpolable\n    "{e.value}"\n  in the xml file.'
                    message += (
                        "\n> Make sure you renamed the interpolable in the Timeline."
                    )
                    message += "\n  This is needed so an alias is created."
                else:
                    message += f'\n> Could not find the node\n    "{e.node_name}"\n  in the xml file.'
                CustomMessageBox(self, "Failled ✖", message)
            except PlapGenerator.ReferenceNotFoundError as e:
                CustomMessageBox(
                    self,
                    "Failled ✖",
                    f"::: Reference not found :::\n\n> Could not find the reference keyframe at {e.time}",
                )
            except ValidationError as e:
                messagebox.showerror("ValidationError", e.get_err_str())
            except Exception:
                CustomMessageBox(self, "Failled ✖", traceback.format_exc())

    @classmethod
    def default_config(cls) -> tkinterdnd2.Tk:
        root = tkinterdnd2.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = max(640, min(854, screen_width // 3))
        window_height = max(360, min(480, screen_height // 3))
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        root.title("PLAP Generator")
        root.minsize(600, 360)
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        return root

    @classmethod
    def run(cls):
        try:
            app = cls(master=cls.default_config())
        except Exception:
            traceback.print_exc()
        else:
            try:
                app.mainloop()
            except Exception:
                traceback.print_exc()
