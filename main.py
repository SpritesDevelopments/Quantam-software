import os
import tkinter as tk
from settings_panel import SettingsPanel
from code_editor import CodeEditor
from api_tester import APITester
from git_manager import GitManager
from task_list import TaskList
from ux_ui_designer import CanvasUI, ComponentLibrary
from sftp_manager import SFTPManager
from info_panel import InfoPanel

class DeveloperToolApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Check if the icon exists
        icon_path = "allinonedevelopertool.ico"
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print("Icon file not found, using default window icon.")

        self.title("All-in-One Developer Tool")
        self.geometry("1200x800")
        self.config(bg="#F9F9F9")

        # Application settings
        self.app_settings = {
            'theme': "Light",
            'font_size': 12,
            'font_family': "Helvetica",
            'bg_color': "white",
            'text_color': "black",
            'console_bg_color': "#f4f4f4",
            'console_text_color': "#000",
            'word_wrap': True,
            'auto_save': False,
            'syntax_colors': {
                'keyword': '#0000ff',
                'string': '#a31515',
                'comment': '#008000',
                'function': '#795E26',
                'builtin': '#0000ff',
            },
        }

        # Create the main content area
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Create all panels with self.main_frame as the master
        self.code_editor = CodeEditor(self.main_frame, self.app_settings)
        self.api_tester = APITester(self.main_frame, self.app_settings)
        self.git_manager = GitManager(self.main_frame, self.app_settings)
        self.task_list = TaskList(self.main_frame, self.app_settings)
        self.info_panel = InfoPanel(self.main_frame, self.app_settings)
        self.settings_panel = SettingsPanel(self.main_frame, self.app_settings, self.apply_settings_to_app)
        self.canvas_frame = CanvasUI(self.main_frame, self.app_settings)
        self.library_frame = ComponentLibrary(self.main_frame, self.canvas_frame, self.app_settings)
        self.sftp_manager = SFTPManager(self.main_frame, self.app_settings)

        # List of panels to apply settings
        self.panels = [
            self.code_editor,
            self.api_tester,
            self.git_manager,
            self.task_list,
            self.info_panel,
            self.canvas_frame,
            self.library_frame,
            self.sftp_manager,
        ]

        # Menubar for the entire app
        self.menubar = tk.Menu(self)
        self.create_menu()
        self.config(menu=self.menubar)

        # Navigation Menu (Left Sidebar)
        self.nav_frame = tk.Frame(self, bg="#424242", width=200)
        self.nav_frame.pack(side="left", fill="y")

        # Create navigation buttons
        self.create_navigation_buttons()

        # Start by showing the Code Editor panel
        self.hide_all_panels()
        self.code_editor.pack(fill="both", expand=True)

    def create_menu(self):
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Save Code", command=self.code_editor.save_file)
        file_menu.add_command(label="Open Code", command=self.code_editor.open_file)
        file_menu.add_command(label="Save All", command=self.code_editor.save_all_files)
        self.menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.code_editor.undo_action)
        edit_menu.add_command(label="Redo", command=self.code_editor.redo_action)
        edit_menu.add_command(label="Copy", command=self.code_editor.copy_text)
        edit_menu.add_command(label="Cut", command=self.code_editor.cut_text)
        edit_menu.add_command(label="Paste", command=self.code_editor.paste_text)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        git_menu = tk.Menu(self.menubar, tearoff=0)
        git_menu.add_command(label="Commit", command=self.code_editor.git_commit)
        git_menu.add_command(label="Push", command=self.code_editor.git_push)
        git_menu.add_command(label="Pull", command=self.code_editor.git_pull)
        self.menubar.add_cascade(label="Git", menu=git_menu)

        settings_menu = tk.Menu(self.menubar, tearoff=0)
        settings_menu.add_command(label="Settings", command=self.show_settings)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)

    def create_navigation_buttons(self):
        # Sidebar navigation buttons
        buttons_data = [
            ("Code Editor", self.show_code_editor),
            ("API Tester", self.show_api_tester),
            ("Settings", self.show_settings),
            ("Git Manager", self.show_git_manager),
            ("Task List", self.show_task_list),
            ("UX/UI Design", self.show_canvas_ui),
            ("SFTP Manager", self.show_sftp_manager),
            ("Info", self.show_info_panel),
        ]

        for text, command in buttons_data:
            btn = tk.Button(
                self.nav_frame,
                text=text,
                font=("Helvetica", 14),
                bg="#424242",
                fg="white",
                bd=0,
                relief=tk.FLAT,
                command=command,
            )
            btn.pack(pady=10, padx=10, fill="x")

    def hide_all_panels(self):
        # Hide all panels by forgetting their packing
        for panel in self.panels:
            panel.pack_forget()
        self.settings_panel.pack_forget()
        self.canvas_frame.pack_forget()
        self.library_frame.pack_forget()

    # Panel show functions
    def show_code_editor(self):
        self.hide_all_panels()
        self.code_editor.pack(fill="both", expand=True)

    def show_api_tester(self):
        self.hide_all_panels()
        self.api_tester.pack(fill="both", expand=True)

    def show_settings(self):
        self.hide_all_panels()
        self.settings_panel.pack(fill="both", expand=True)
        self.apply_settings_to_app()

    def apply_settings_to_app(self):
        """Apply settings like theme, font size, etc. to all components where relevant."""
        selected_theme = self.app_settings['theme']
        font_family = self.app_settings['font_family']
        font_size = self.app_settings['font_size']

        # Apply the theme to the entire app (light or dark)
        if selected_theme == "Dark":
            self.config(bg="#333")
            self.nav_frame.config(bg="#333")
            self.main_frame.config(bg="#222")
            fg_color = "white"
        else:
            self.config(bg="#F9F9F9")
            self.nav_frame.config(bg="#424242")
            self.main_frame.config(bg="white")
            fg_color = "black"

        # Update navigation buttons' colors
        for child in self.nav_frame.winfo_children():
            if isinstance(child, tk.Button):
                child.config(bg=self.nav_frame.cget('bg'), fg=fg_color)

        # Apply font settings to the code editor and other components
        for panel in self.panels:
            panel.apply_settings()

    def show_git_manager(self):
        self.hide_all_panels()
        self.git_manager.pack(fill="both", expand=True)

    def show_task_list(self):
        self.hide_all_panels()
        self.task_list.pack(fill="both", expand=True)

    def show_canvas_ui(self):
        self.hide_all_panels()
        self.library_frame.pack(side="left", fill="y")
        self.canvas_frame.pack(side="left", expand=True, fill="both")

    def show_info_panel(self):
        """Show the Info Panel with details about the tool."""
        self.hide_all_panels()
        self.info_panel.pack(fill="both", expand=True)

    def show_sftp_manager(self):
        """Show the SFTP Manager panel."""
        self.hide_all_panels()
        self.sftp_manager.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = DeveloperToolApp()
    app.mainloop()
