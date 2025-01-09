import tkinter as tk
from tkinter import ttk, messagebox
from styles import apply_light_theme, apply_dark_theme  # Import theme functions

class Settings(ttk.Frame):
    def __init__(self, parent, theme, main_app):
        super().__init__(parent)
        self.theme = theme
        self.main_app = main_app  # Store reference to MainApplication
        self.create_widgets()

    def create_widgets(self):
        # GitHub settings
        github_frame = ttk.LabelFrame(self, text="GitHub Settings", padding=10)
        github_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(github_frame, text="Sign Out of GitHub", command=self.sign_out_github).pack(pady=5)

        # Editor settings
        editor_frame = ttk.LabelFrame(self, text="Editor Settings", padding=10)
        editor_frame.pack(fill='x', padx=10, pady=5)

        self.wrap_text_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(editor_frame, text="Wrap Text", variable=self.wrap_text_var).pack(anchor='w')

        self.show_line_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(editor_frame, text="Show Line Numbers", variable=self.show_line_numbers_var).pack(anchor='w')

        self.auto_save_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(editor_frame, text="Auto Save", variable=self.auto_save_var).pack(anchor='w')

        # API Tester settings
        api_tester_frame = ttk.LabelFrame(self, text="API Tester Settings", padding=10)
        api_tester_frame.pack(fill='x', padx=10, pady=5)

        self.follow_redirects_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(api_tester_frame, text="Follow Redirects", variable=self.follow_redirects_var).pack(anchor='w')

        self.verify_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(api_tester_frame, text="Verify SSL", variable=self.verify_ssl_var).pack(anchor='w')

        # Discord Bot settings
        discord_frame = ttk.LabelFrame(self, text="Discord Bot Settings", padding=10)
        discord_frame.pack(fill='x', padx=10, pady=5)

        self.enable_logging_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(discord_frame, text="Enable Logging", variable=self.enable_logging_var).pack(anchor='w')

        self.auto_reconnect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(discord_frame, text="Auto Reconnect", variable=self.auto_reconnect_var).pack(anchor='w')

        # Theme settings
        theme_frame = ttk.LabelFrame(self, text="Theme Settings", padding=10)
        theme_frame.pack(fill='x', padx=10, pady=5)

        self.theme_var = tk.StringVar(value="Light")
        ttk.Radiobutton(theme_frame, text="Light", value="Light", variable=self.theme_var).pack(anchor='w')
        ttk.Radiobutton(theme_frame, text="Dark (Coming Soon)", value="Dark", variable=self.theme_var, command=self.show_coming_soon).pack(anchor='w')

        # Other settings
        other_frame = ttk.LabelFrame(self, text="Other Settings", padding=10)
        other_frame.pack(fill='x', padx=10, pady=5)

        self.enable_notifications_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(other_frame, text="Enable Notifications", variable=self.enable_notifications_var).pack(anchor='w')

        self.auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(other_frame, text="Auto Update", variable=self.auto_update_var).pack(anchor='w')

        # Save button
        ttk.Button(self, text="Save Settings", command=self.save_settings).pack(pady=10)

    def sign_out_github(self):
        # Logic to sign out of GitHub
        if messagebox.askyesno("Confirm", "Are you sure you want to sign out of GitHub?"):
            # Clear GitHub token and user data
            self.main_app.git_manager.github.token = None
            self.main_app.git_manager.github.user_data = None
            messagebox.showinfo("Success", "Signed out of GitHub successfully!")

    def save_settings(self):
        # Save settings logic
        settings = {
            "wrap_text": self.wrap_text_var.get(),
            "show_line_numbers": self.show_line_numbers_var.get(),
            "auto_save": self.auto_save_var.get(),
            "follow_redirects": self.follow_redirects_var.get(),
            "verify_ssl": self.verify_ssl_var.get(),
            "enable_logging": self.enable_logging_var.get(),
            "auto_reconnect": self.auto_reconnect_var.get(),
            "theme": self.theme_var.get(),
            "enable_notifications": self.enable_notifications_var.get(),
            "auto_update": self.auto_update_var.get()
        }
        # Apply settings to all tabs
        self.apply_settings_to_tabs(settings)
        messagebox.showinfo("Success", "Settings saved successfully!")

    def apply_settings_to_tabs(self, settings):
        # Apply settings to Code Editor
        for editor in self.main_app.code_editor.editors:
            editor.text_area.config(wrap='word' if settings["wrap_text"] else 'none')
            editor.line_numbers.pack_forget() if not settings["show_line_numbers"] else editor.line_numbers.pack(side='left', fill='y')

        # Apply settings to API Tester
        self.main_app.api_tester.follow_redirects = settings["follow_redirects"]
        self.main_app.api_tester.verify_ssl = settings["verify_ssl"]

        # Apply settings to Discord Bot Maker
        self.main_app.discord_maker.enable_logging = settings["enable_logging"]
        self.main_app.discord_maker.auto_reconnect = settings["auto_reconnect"]

        # Apply theme settings
        if settings["theme"] == "Light":
            self.main_app.theme = apply_light_theme(self.main_app.root)
        else:
            self.show_coming_soon()

        # Apply other settings
        self.main_app.enable_notifications = settings["enable_notifications"]
        self.main_app.auto_update = settings["auto_update"]

    def show_coming_soon(self):
        messagebox.showinfo("Coming Soon", "Dark mode is coming soon!")
