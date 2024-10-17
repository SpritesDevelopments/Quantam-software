import os
import tkinter as tk
from tkinter import ttk
from settings_panel import SettingsPanel
from code_editor import CodeEditor
from api_tester import APITester
from git_manager import GitManager
from task_list import TaskList
from ux_ui_designer import CanvasUI, ComponentLibrary
from sftp_manager import SFTPManager
from info_panel import InfoPanel
from discord_bot_runner import DiscordBotRunner

class DeveloperToolApp(tk.Tk):
    def __init__(self):
        super().__init__()

        icon_path = "allinonedevelopertool.ico"
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print("Icon file not found, using default window icon.")

        self.title("All-in-One Developer Tool")
        self.geometry("1200x800")
        self.config(bg="#282c34")

        self.app_settings = {
            'theme': "Dark",
            'font_size': 12,
            'font_family': "Helvetica",
            'bg_color': "#222",
            'text_color': "#eee",
            'console_bg_color': "#333",
            'console_text_color': "#eee",
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

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.main_frame = ttk.Frame(self, style='Main.TFrame')
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.code_editor = CodeEditor(self.main_frame, self.app_settings)
        self.api_tester = APITester(self.main_frame, self.app_settings)
        self.git_manager = GitManager(self.main_frame, self.app_settings)
        self.task_list = TaskList(self.main_frame, self.app_settings)
        self.info_panel = InfoPanel(self.main_frame, self.app_settings)
        self.settings_panel = SettingsPanel(self.main_frame, self.app_settings, self.apply_settings_to_app)
        self.canvas_frame = CanvasUI(self.main_frame, self.app_settings)
        self.library_frame = ComponentLibrary(self.main_frame, self.canvas_frame, self.app_settings)
        self.sftp_manager = SFTPManager(self.main_frame, self.app_settings)
        self.discord_bot_runner = DiscordBotRunner(self.main_frame, self.app_settings)

        self.panels = [
            self.code_editor,
            self.api_tester,
            self.git_manager,
            self.task_list,
            self.info_panel,
            self.canvas_frame,
            self.library_frame,
            self.sftp_manager,
            self.discord_bot_runner,
        ]

        self.menubar = tk.Menu(self)
        self.create_menu()
        self.config(menu=self.menubar)

        self.nav_frame = ttk.Frame(self, style='Nav.TFrame', width=200)
        self.nav_frame.pack(side="left", fill="y")

        self.create_navigation_buttons()

        self.hide_all_panels()
        self.code_editor.pack(fill="both", expand=True)

    def configure_styles(self):
        self.style.configure('Main.TFrame', background='#222')
        self.style.configure('Nav.TFrame', background='#333')
        self.style.configure('TButton', 
                             background='#333', 
                             foreground='white', 
                             font=('Helvetica', 12),
                             borderwidth=0,
                             focuscolor='#555')
        self.style.map('TButton', 
                       background=[('active', '#555')],
                       foreground=[('active', 'white')])

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
        buttons_data = [
            ("Code Editor", self.show_code_editor),
            ("API Tester", self.show_api_tester),
            ("Settings", self.show_settings),
            ("Git Manager", self.show_git_manager),
            ("Task List", self.show_task_list),
            ("UX/UI Design", self.show_canvas_ui),
            ("SFTP Manager", self.show_sftp_manager),
            ("Discord Bot Runner", self.show_discord_bot_runner),
            ("Info", self.show_info_panel),
        ]

        for text, command in buttons_data:
            btn = ttk.Button(
                self.nav_frame,
                text=text,
                command=command,
                style='TButton'
            )
            btn.pack(pady=5, padx=10, fill="x")

    def hide_all_panels(self):
        for panel in self.panels:
            panel.pack_forget()
        self.settings_panel.pack_forget()
        self.canvas_frame.pack_forget()
        self.library_frame.pack_forget()

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
        selected_theme = self.app_settings['theme']
        font_family = self.app_settings['font_family']
        font_size = self.app_settings['font_size']

        if selected_theme == "Dark":
            self.style.configure('Main.TFrame', background='#222')
            self.style.configure('Nav.TFrame', background='#333')
            self.style.configure('TButton', background='#333', foreground='white')
            self.style.map('TButton', background=[('active', '#555')])
        else:
            self.style.configure('Main.TFrame', background='white')
            self.style.configure('Nav.TFrame', background='#424242')
            self.style.configure('TButton', background='#424242', foreground='black')
            self.style.map('TButton', background=[('active', '#666')])

        self.style.configure('TButton', font=(font_family, font_size))

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
        self.hide_all_panels()
        self.info_panel.pack(fill="both", expand=True)

    def show_sftp_manager(self):
        self.hide_all_panels()
        self.sftp_manager.pack(fill="both", expand=True)

    def show_discord_bot_runner(self):
        self.hide_all_panels()
        self.discord_bot_runner.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = DeveloperToolApp()
    app.mainloop()
