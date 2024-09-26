# info_panel.py

import tkinter as tk

class InfoPanel(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)  # Use master directly
        self.app_settings = app_settings

        info_text = (
            "All-in-One Developer Tool\n"
            "Version: 1.0.0\n\n"
            "This tool integrates multiple utilities for developers, including:\n"
            "- Code Editor with syntax highlighting and execution support.\n"
            "- API Tester for testing HTTP requests.\n"
            "- Git Manager for version control operations.\n"
            "- Task List to keep track of your tasks.\n"
            "- UX/UI Designer to design interfaces.\n"
            "- SFTP Manager for file transfers.\n\n"
            "Developed by Your Name\n"
            "Contact: your.email@example.com"
        )

        self.info_label = tk.Label(
            self, text=info_text, justify="left",
            font=(self.app_settings['font_family'], self.app_settings['font_size']),
            bg=self.app_settings['bg_color'],
            fg=self.app_settings['text_color']
        )
        self.info_label.pack(padx=20, pady=20)

        self.pack(fill="both", expand=True)

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        self.info_label.config(
            bg=self.app_settings['bg_color'],
            fg=self.app_settings['text_color'],
            font=(self.app_settings['font_family'], self.app_settings['font_size'])
        )
