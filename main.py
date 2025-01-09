import tkinter as tk
from tkinter import ttk
from code_editor import CodeEditor
from api_tester import APITester
from git_manager import GitManager
from discord_maker import DiscordBotMaker
from styles import apply_light_theme  # Change import
from settings import Settings  # Add import
from updater import update_application  # Import updater
import os  # Add import

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("All-in-One Developer Tool")
        self.root.state('zoomed')
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), 'allinonedevelopertool.ico')
        self.root.iconbitmap(icon_path)
        
        # Apply light theme instead of dark
        self.theme = apply_light_theme(root)
        self.root.configure(bg=self.theme['bg'])
        
        # Create main container with padding
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.pack(fill='both', expand=True)
        
        # Create and style notebook
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Initialize components with theme
        self.code_editor = CodeEditor(self.notebook, self.theme)
        self.api_tester = APITester(self.notebook, self.theme)
        self.git_manager = GitManager(self.notebook, self.theme)
        self.discord_maker = DiscordBotMaker(self.notebook, self.theme)
        self.settings = Settings(self.notebook, self.theme, self)  # Pass MainApplication instance

        # Add tabs with icons (you'll need to add icon files)
        self.notebook.add(self.code_editor, text='  Code Editor  ')
        self.notebook.add(self.api_tester, text='  API Tester  ')
        self.notebook.add(self.git_manager, text='  Git Manager  ')
        self.notebook.add(self.discord_maker, text='  Discord Bot  ')
        self.notebook.add(self.settings, text='  Settings  ')  # Add settings tab

        # Add menu
        self.create_menu()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Check for Updates", command=update_application)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
