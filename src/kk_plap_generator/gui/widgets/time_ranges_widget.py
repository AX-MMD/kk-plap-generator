import re
import tkinter as tk
import typing
from tkinter import simpledialog

from kk_plap_generator.generator.utils import convert_KKtime_to_seconds
from kk_plap_generator.gui import info_text
from kk_plap_generator.gui.info_message import InfoMessageFrame
from kk_plap_generator.gui.validators import validate_time
from kk_plap_generator.gui.widgets.base import PlapWidget

if typing.TYPE_CHECKING:
    from kk_plap_generator.gui.main_menu import PlapUI


class TimeRangesWidget(PlapWidget):
    def __init__(self, app: "PlapUI", masterframe):
        super().__init__(app, masterframe)

        self.time_ranges_frame = tk.Frame(masterframe, bd=2, relief="solid")
        self.time_ranges_frame.grid(row=1, column=0, sticky="nsew")

        # Top
        self.top_frame = tk.Frame(self.time_ranges_frame)
        self.top_frame.grid_columnconfigure(0, weight=90)
        self.top_frame.grid_columnconfigure(1, weight=10)
        self.top_frame.pack(fill=tk.X)

        # Time Ranges
        self.top_left_frame = tk.Frame(self.top_frame)
        self.top_left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.time_ranges_label = tk.Label(self.top_left_frame, text="Time Ranges")
        self.time_ranges_label.pack()

        info_message = info_text.TIME_RANGES
        self.top_right_frame = InfoMessageFrame(self.top_frame, info_message)

        self.time_ranges_listbox = tk.Listbox(self.time_ranges_frame)
        self.time_ranges_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.time_ranges_listbox.bind("<Double-Button-1>", self.edit_time_range)

        self.time_ranges_scrollbar = tk.Scrollbar(
            self.time_ranges_frame, orient="vertical"
        )
        self.time_ranges_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.time_ranges_listbox.config(yscrollcommand=self.time_ranges_scrollbar.set)
        self.time_ranges_scrollbar.config(command=self.time_ranges_listbox.yview)

        self.update()

        self.add_time_range_button = tk.Button(
            self.time_ranges_frame, text="+", command=self.add_time_range
        )
        self.add_time_range_button.pack(fill=tk.X)

        self.remove_time_range_button = tk.Button(
            self.time_ranges_frame, text="-", command=self.remove_selected_time_range
        )
        self.remove_time_range_button.pack(fill=tk.X)

    def update(self):
        self.time_ranges_listbox.delete(0, tk.END)
        for start, stop, ref in self.app.store.time_ranges:
            if start == ref:
                self.time_ranges_listbox.insert(tk.END, f"{start} - {stop}")
            else:
                self.time_ranges_listbox.insert(tk.END, f"{start} - {stop} ({ref})")

    def edit_time_range(self, event):
        selected_index: typing.Tuple[int] = self.time_ranges_listbox.curselection()
        if not selected_index:
            return

        start, stop, ref = self.app.store.time_ranges[selected_index[0]]

        dialog = TimeRangeDialog(
            self.masterframe,
            title="Edit Time Range",
            start_time=start,
            stop_time=stop,
            ref_time=ref,
        )

        if dialog.is_cancelled:
            return
        elif dialog.is_valid():
            self.app.store.time_ranges[selected_index[0]] = (
                dialog.start_time,
                dialog.stop_time,
                dialog.ref_time,
            )
            self.update()
        elif not dialog.is_valid_range():
            tk.messagebox.showerror(
                "Validation Error",
                "Invalid time range. Start time must be less than Stop time.",
            )
        else:
            tk.messagebox.showerror(
                "Validation Error", "Invalid time format. Expected MM:SS.SS"
            )

    def remove_selected_time_range(self):
        selected_index = self.time_ranges_listbox.curselection()
        if selected_index:
            selected_time_range: str = self.time_ranges_listbox.get(selected_index)
            if "(" in selected_time_range:
                match = re.match(
                    r"(\d{2}:\d{2}\.\d+) - (\d{2}:\d{2}\.\d+) \((\d{2}:\d{2}\.\d+)\)",
                    selected_time_range,
                )
                if match:
                    start, stop, ref = match.groups()
                else:
                    raise ValueError(f"Invalid time range format: {selected_time_range}")
            else:
                start, stop = selected_time_range.split(" - ")
                ref = start

            self.app.store.time_ranges.remove((start, stop, ref))
            self.update()

    def add_time_range(self):
        dialog = TimeRangeDialog(self.masterframe, title="Add Time Range")
        if dialog.is_cancelled:
            return
        elif dialog.is_valid():
            self.app.store.time_ranges.append(
                (dialog.start_time, dialog.stop_time, dialog.ref_time)
            )
            self.update()
        elif not dialog.is_valid_range():
            tk.messagebox.showerror(
                "Validation Error",
                "Invalid time range. Start time must be less than Stop time.",
            )
        else:
            tk.messagebox.showerror(
                "Validation Error", "Invalid time format. Expected MM:SS.SS"
            )


class TimeRangeDialog(simpledialog.Dialog):
    def __init__(
        self,
        parent,
        title=None,
        start_time: str = "00:00.00",
        stop_time: str = "00:00.00",
        ref_time: str = "00:00.00",
    ):
        self.ok_text = "✔"
        self.cancel_text = "✖"
        self.start_time = start_time
        self.old_start_time = start_time
        self.stop_time = stop_time
        self.ref_time = ref_time
        self.is_cancelled = True
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Start Time").grid(row=2, column=0)
        self.start_time_entry = tk.Entry(master, justify="center")
        self.start_time_entry.grid(row=2, column=1)
        self.start_time_entry.insert(0, self.start_time)
        tk.Label(master, text="MM:SS.SS").grid(row=2, column=2)

        self.start_time_entry.bind("<KeyRelease>", self.on_start_time_change)

        tk.Label(master, text="Stop Time").grid(row=3, column=0)
        self.stop_time_entry = tk.Entry(master, justify="center")
        self.stop_time_entry.grid(row=3, column=1)
        self.stop_time_entry.insert(0, self.stop_time)
        tk.Label(master, text="MM:SS.SS").grid(row=3, column=2)

        tk.Label(master, text="Reference Time").grid(row=4, column=0)
        self.ref_time_entry = tk.Entry(master, justify="center")
        self.ref_time_entry.grid(row=4, column=1)
        self.ref_time_entry.insert(0, self.ref_time)
        tk.Label(master, text="MM:SS.SS").grid(row=4, column=2)

        return self.start_time_entry  # initial focus

    def on_start_time_change(self, event):
        """Update ref_time_entry when start_time_entry changes."""
        new_start_time = self.start_time_entry.get()
        ref_time = self.ref_time_entry.get()

        if not ref_time or ref_time == self.old_start_time:
            self.ref_time_entry.delete(0, tk.END)
            self.ref_time_entry.insert(0, new_start_time)

        self.old_start_time = new_start_time

    def buttonbox(self):
        box = tk.Frame(self)

        self.ok_button = tk.Button(
            box,
            text=self.ok_text,
            width=10,
            fg="green",
            command=self.ok,
            default=tk.ACTIVE,
        )
        self.ok_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.cancel_button = tk.Button(
            box, text=self.cancel_text, width=10, fg="red", command=self.cancel
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def is_valid(self):
        return (
            validate_time(self.start_time)
            and (self.stop_time == "END" or validate_time(self.stop_time))
            and validate_time(self.ref_time)
            and self.is_valid_range()
        )

    def is_valid_range(self):
        return convert_KKtime_to_seconds(self.start_time) < convert_KKtime_to_seconds(
            self.stop_time
        )

    def apply(self):
        self.start_time = self.start_time_entry.get()
        self.stop_time = self.stop_time_entry.get().upper()
        self.ref_time = self.ref_time_entry.get().upper() or self.start_time
        self.is_cancelled = False
