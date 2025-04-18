import tkinter as tk


class CustomMessageBox(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("660x440")  # Set the initial size of the message box

        self.message_frame = tk.Frame(self)
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(self.message_frame, wrap=tk.WORD)
        self.text.insert(tk.END, message)
        self.text.config(state=tk.DISABLED, padx=10, pady=10)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.message_frame, command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=self.scrollbar.set)

        self.ok_button = tk.Button(self, text="✖", command=self.destroy)
        self.ok_button.pack(pady=10)

        self.transient(parent)  # Set the dialog to be transient to the parent window
        self.lift()  # Bring the dialog to the front

        # Center the dialog on the screen
        self.update_idletasks()

        self_width = max(self.winfo_width(), 660)
        self_height = max(self.winfo_height(), 460)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width // 2) - (self_width // 2)
        y = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{x}+{y}")

        self.update_idletasks()  # Ensure the geometry is updated
