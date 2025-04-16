import tkinter as tk
import typing
from copy import deepcopy
from tkinter import messagebox

from kk_plap_generator.gui.utils import load_config_file
from kk_plap_generator.gui.validators import ValidationError
from kk_plap_generator.gui.widgets.base import PlapWidget

if typing.TYPE_CHECKING:
    from kk_plap_generator.gui.main_menu import PlapUI


class RefSwitcherWidget(PlapWidget):
    def __init__(self, app: "PlapUI", masterframe):
        super().__init__(app, masterframe)

        self.max_pages = 8
        self.button_frame = tk.Frame(masterframe)
        self.button_frame.pack(fill=tk.X, padx=(20, 5), pady=5)
        self.create_plap_group_buttons()

    def create_plap_group_buttons(self):
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Create buttons for plap_group
        for i, _ in enumerate(self.app.plap_config):
            if i >= self.max_pages:
                break

            def update_current_page(i=i):
                self.update_current_page(i)

            button = tk.Button(
                self.button_frame,
                text=str(i + 1),
                command=update_current_page,
                bg="lightblue" if i == self.app.current_page else "SystemButtonFace",
            )
            button.pack(side=tk.LEFT, padx=1)

        # Reset Button
        reset_button = tk.Button(
            self.button_frame,
            text="⟲",
            font=self.app.symbol_font,
            command=self.reset_button_action,
        )
        reset_button.pack(side=tk.RIGHT)
        # Add + and delete buttons
        delete_button = tk.Button(
            self.button_frame,
            text="✖",
            fg="red",
            font=self.app.symbol_font,
            command=self.delete_plap_group,
        )
        delete_button.pack(side=tk.RIGHT)
        add_button = tk.Button(
            self.button_frame,
            text="✚",
            fg="green",
            font=self.app.symbol_font,
            command=self.add_plap_group,
        )
        add_button.pack(side=tk.RIGHT)
        delete_button.pack(side=tk.RIGHT)
        # Add copy button
        copy_button = tk.Button(
            self.button_frame,
            text="⧉",
            font=self.app.symbol_font,
            command=self.copy_plap_group,
        )
        copy_button.pack(side=tk.RIGHT, padx=(0, 0))

    def update_current_page(self, page_number):
        self.app.widgets_save()
        self.app.current_page = page_number
        self.create_plap_group_buttons()
        self.app.update_widgets()

    def add_plap_group(self):
        try:
            self.app.widgets_save()
            if len(self.app.plap_config) < self.max_pages:
                default_entry = load_config_file(self.app.default_config_path)[0]
                default_entry.ref_interpolable = self.app.store.ref_interpolable
                default_entry.last_single_file_folder = (
                    self.app.store.last_single_file_folder
                )
                self.app.plap_config.append(default_entry)
                self.app.current_page = len(self.app.plap_config) - 1
                self.create_plap_group_buttons()
                self.app.update_widgets()
        except ValidationError as e:
            messagebox.showerror("ValidationError", e.get_err_str())

    def delete_plap_group(self):
        try:
            self.app.widgets_save()
            if len(self.app.plap_config) > 1:
                self.app.plap_config.pop(self.app.current_page)
                self.app.current_page = min(
                    self.app.current_page, len(self.app.plap_config) - 1
                )
                self.create_plap_group_buttons()
                self.app.update_widgets()
        except ValidationError as e:
            messagebox.showerror("ValidationError", e.get_err_str())

    def copy_plap_group(self):
        try:
            self.app.widgets_save()
            if len(self.app.plap_config) < self.max_pages:
                current_entry = deepcopy(self.app.store)
                self.app.plap_config.append(current_entry)
                self.app.current_page = len(self.app.plap_config) - 1
                self.create_plap_group_buttons()
                self.app.update_widgets()
        except ValidationError as e:
            messagebox.showerror("ValidationError", e.get_err_str())

    def reset_button_action(self):
        default_entry = load_config_file(self.app.default_config_path)[0]
        default_entry.ref_interpolable = self.app.store.ref_interpolable
        default_entry.last_single_file_folder = self.app.store.last_single_file_folder
        self.app.store = default_entry

    def update(self):
        self.create_plap_group_buttons()
