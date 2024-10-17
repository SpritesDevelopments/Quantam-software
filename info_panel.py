import tkinter as tk
from tkinter import ttk

class InfoPanel(ttk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master, style='TFrame')
        self.app_settings = app_settings

        self.info_text = (
            "All-in-One Developer Tool\n"
            "Version: 2.0.0\n\n"
            "This tool integrates multiple utilities for developers, including:\n"
            "- Code Editor with syntax highlighting and execution support.\n"
            "- API Tester for testing HTTP requests.\n"
            "- Git Manager for version control operations.\n"
            "- Task List to keep track of your tasks.\n"
            "- UX/UI Designer to design interfaces.\n"
            "- SFTP Manager for file transfers.\n\n"
            "Developed by SpritesDevelopments\n"
            "Contact: https://discord.gg/pPm29ECmNV"
        )

        self.create_widgets()
        self.apply_settings()

    def create_widgets(self):
        self.title_label = ttk.Label(
            self,
            text="All-in-One Developer Tool",
            style='Title.TLabel'
        )
        self.title_label.pack(pady=(20, 10))

        self.version_label = ttk.Label(
            self,
            text="Version: 2.0.0",
            style='Version.TLabel'
        )
        self.version_label.pack(pady=(0, 20))

        self.info_text_widget = tk.Text(
            self,
            wrap=tk.WORD,
            height=12,
            width=50,
            font=(self.app_settings['font_family'], self.app_settings['font_size']),
            bg=self.app_settings['bg_color'],
            fg=self.app_settings['text_color'],
            relief=tk.FLAT
        )
        self.info_text_widget.insert(tk.END, self.info_text)
        self.info_text_widget.config(state=tk.DISABLED)
        self.info_text_widget.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.contact_button = ttk.Button(
            self,
            text="Contact Us",
            command=self.open_contact_link,
            style='Contact.TButton'
        )
        self.contact_button.pack(pady=20)

    def apply_settings(self):
        style = ttk.Style()
        style.configure('TFrame', background=self.app_settings['bg_color'])
        style.configure('Title.TLabel',
                        font=(self.app_settings['font_family'], self.app_settings['font_size'] + 4, 'bold'),
                        foreground=self.app_settings['text_color'],
                        background=self.app_settings['bg_color'])
        style.configure('Version.TLabel',
                        font=(self.app_settings['font_family'], self.app_settings['font_size'], 'italic'),
                        foreground=self.app_settings['text_color'],
                        background=self.app_settings['bg_color'])
        style.configure('Contact.TButton',
                        font=(self.app_settings['font_family'], self.app_settings['font_size']),
                        background=self.app_settings['bg_color'],
                        foreground=self.app_settings['text_color'])

        self.info_text_widget.config(
            font=(self.app_settings['font_family'], self.app_settings['font_size']),
            bg=self.app_settings['bg_color'],
            fg=self.app_settings['text_color']
        )

    def open_contact_link(self):
        import webbrowser
        webbrowser.open("https://discord.gg/pPm29ECmNV")
