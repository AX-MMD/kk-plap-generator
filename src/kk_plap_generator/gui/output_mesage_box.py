import tkinter as tk


class CustomMessageBox(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")  # Set the initial size of the message box

        self.message_frame = tk.Frame(self)
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(self.message_frame, wrap=tk.WORD, height=20, width=70)
        self.text.insert(tk.END, message)
        self.text.config(state=tk.DISABLED, padx=10, pady=10)
        self.text.pack(side=tk.LEFT)

        self.scrollbar = tk.Scrollbar(self.message_frame, command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=self.scrollbar.set)

        self.ok_button = tk.Button(self, text="✖", command=self.destroy)
        self.ok_button.pack(pady=10)

        self.transient(parent)  # Set the dialog to be transient to the parent window
        self.lift()  # Bring the dialog to the front
        self.grab_set()  # Make the dialog modal

        # Center the dialog on the screen
        self.update_idletasks()

        self_width = max(self.winfo_width(), 600)
        self_height = max(self.winfo_height(), 400)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self_width // 2)
        y = (screen_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{x}+{y}")

        self.update_idletasks()  # Ensure the geometry is updated
