# discord_bot_runner.py
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys

class BotFrame(tk.Frame):
    SUPPORTED_LANGUAGES = {
        "Python": {
            "command": "python",
            "dependency_manager": "pip",
            "dependency_install_cmd": lambda path: [sys.executable, "-m", "pip", "install", "-r", os.path.join(path, "requirements.txt")]
        },
        "Node.js": {
            "command": "node",
            "dependency_manager": "npm",
            "dependency_install_cmd": lambda path: ["npm", "install"]
        },
        "Ruby": {
            "command": "ruby",
            "dependency_manager": "bundler",
            "dependency_install_cmd": lambda path: ["bundle", "install"]
        },
        "Go": {
            "command": "go",
            "dependency_manager": None,  # Go manages dependencies differently
            "dependency_install_cmd": None
        },
        # Add more languages here as needed
    }

    def __init__(self, master, bot_id, settings, remove_callback, *args, **kwargs):
        super().__init__(master, bg=settings.get('bg_color', 'white'), bd=2, relief=tk.GROOVE, *args, **kwargs)
        self.bot_id = bot_id
        self.settings = settings
        self.remove_callback = remove_callback
        self.process = None
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        # Header Frame with Bot Name and Remove Button
        header_frame = tk.Frame(self, bg=self.settings.get('bg_color', 'white'))
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        self.name_var = tk.StringVar(value=f"Bot {self.bot_id}")
        self.name_entry = tk.Entry(header_frame, textvariable=self.name_var, font=("Helvetica", 14, "bold"))
        self.name_entry.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)

        remove_btn = tk.Button(header_frame, text="Remove Bot", command=self.remove_bot, bg="#f44336", fg="white")
        remove_btn.pack(side=tk.RIGHT)

        # Language Selection
        lang_frame = tk.Frame(self, bg=self.settings.get('bg_color', 'white'))
        lang_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(lang_frame, text="Language:", bg=self.settings.get('bg_color', 'white'),
                 fg=self.settings.get('text_color', 'black')).pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value="Python")
        lang_options = list(self.SUPPORTED_LANGUAGES.keys())
        self.language_menu = tk.OptionMenu(lang_frame, self.language_var, *lang_options, command=self.on_language_change)
        self.language_menu.pack(side=tk.LEFT, padx=5)

        # Bot Script Selection
        script_frame = tk.Frame(self, bg=self.settings.get('bg_color', 'white'))
        script_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(script_frame, text="Bot Script:", bg=self.settings.get('bg_color', 'white'),
                 fg=self.settings.get('text_color', 'black')).pack(side=tk.LEFT, padx=5)
        self.script_path_var = tk.StringVar()
        self.script_entry = tk.Entry(script_frame, textvariable=self.script_path_var, width=40)
        self.script_entry.pack(side=tk.LEFT, padx=5)
        browse_btn = tk.Button(script_frame, text="Browse", command=self.browse_script)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # Dependency Installation Option
        dep_frame = tk.Frame(self, bg=self.settings.get('bg_color', 'white'))
        dep_frame.pack(fill=tk.X, padx=5, pady=5)

        self.install_deps_var = tk.BooleanVar(value=True)
        self.install_deps_check = tk.Checkbutton(dep_frame, text="Install Dependencies",
                                                variable=self.install_deps_var,
                                                bg=self.settings.get('bg_color', 'white'),
                                                fg=self.settings.get('text_color', 'black'))
        self.install_deps_check.pack(side=tk.LEFT, padx=5)

        # Start and Stop Buttons
        button_frame = tk.Frame(self, bg=self.settings.get('bg_color', 'white'))
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_btn = tk.Button(button_frame, text="Start Bot", command=self.start_bot, bg="#4CAF50", fg="white")
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(button_frame, text="Stop Bot", command=self.stop_bot, bg="#f44336", fg="white", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        # Output Console
        console_label = tk.Label(self, text="Console Output:", bg=self.settings.get('bg_color', 'white'),
                                 fg=self.settings.get('text_color', 'black'))
        console_label.pack(anchor=tk.W, padx=5, pady=(10, 0))

        self.console_text = tk.Text(self, height=10, bg=self.settings.get('console_bg_color', '#f4f4f4'),
                                    fg=self.settings.get('console_text_color', '#000'), wrap=tk.WORD, state=tk.DISABLED)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar for the console
        scrollbar = tk.Scrollbar(self.console_text, command=self.console_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=scrollbar.set)

    def on_language_change(self, selected_language):
        # Reset script path and dependencies when language changes
        self.script_path_var.set("")
        if selected_language not in self.SUPPORTED_LANGUAGES:
            self.install_deps_var.set(False)
            self.install_deps_check.config(state=tk.DISABLED)
        else:
            self.install_deps_check.config(state=tk.NORMAL)
            default = True if self.SUPPORTED_LANGUAGES[selected_language]['dependency_manager'] else False
            self.install_deps_var.set(default)

    def browse_script(self):
        language = self.language_var.get()
        if language not in self.SUPPORTED_LANGUAGES:
            messagebox.showerror("Error", f"Unsupported language: {language}")
            return

        if self.SUPPORTED_LANGUAGES[language]['dependency_manager'] == "pip":
            file_types = [("Python Files", "*.py")]
        elif self.SUPPORTED_LANGUAGES[language]['dependency_manager'] == "npm":
            file_types = [("JavaScript Files", "*.js")]
        elif self.SUPPORTED_LANGUAGES[language]['dependency_manager'] == "bundler":
            file_types = [("Ruby Files", "*.rb")]
        elif self.SUPPORTED_LANGUAGES[language]['dependency_manager'] == "go":
            file_types = [("Go Files", "*.go")]
        else:
            file_types = [("All Files", "*.*")]
        
        script_path = filedialog.askopenfilename(title="Select Bot Script", filetypes=file_types)
        if script_path:
            self.script_path_var.set(script_path)

    def start_bot(self):
        script_path = self.script_path_var.get()
        if not script_path or not os.path.isfile(script_path):
            messagebox.showerror("Error", "Please select a valid bot script.")
            return

        language = self.language_var.get()
        if language not in self.SUPPORTED_LANGUAGES:
            messagebox.showerror("Error", f"Unsupported language: {language}")
            return

        # Install dependencies if required
        if self.install_deps_var.get():
            dep_manager = self.SUPPORTED_LANGUAGES[language]['dependency_manager']
            if dep_manager:
                install_cmd = self.SUPPORTED_LANGUAGES[language]['dependency_install_cmd']
                if install_cmd:
                    script_dir = os.path.dirname(script_path)
                    # Check if dependency files exist
                    if language == "Python" and not os.path.exists(os.path.join(script_dir, "requirements.txt")):
                        messagebox.showwarning("Warning", "requirements.txt not found. Skipping dependency installation.")
                    elif language == "Node.js" and not os.path.exists(os.path.join(script_dir, "package.json")):
                        messagebox.showwarning("Warning", "package.json not found. Skipping dependency installation.")
                    elif language == "Ruby" and not os.path.exists(os.path.join(script_dir, "Gemfile")):
                        messagebox.showwarning("Warning", "Gemfile not found. Skipping dependency installation.")
                    # Add more language-specific checks as needed
                    else:
                        try:
                            self.append_console("Installing dependencies...\n")
                            subprocess.check_call(install_cmd(script_dir), cwd=script_dir)
                            self.append_console("Dependencies installed successfully.\n")
                        except subprocess.CalledProcessError as e:
                            messagebox.showerror("Error", f"Failed to install dependencies: {e}")
                            return

        command = [self.SUPPORTED_LANGUAGES[language]['command'], script_path]

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.is_running = True
            self.append_console("Bot started...\n")
            threading.Thread(target=self.monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start bot: {e}")

    def stop_bot(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.is_running = False
            self.append_console("Bot stopped.\n")

    def monitor_process(self):
        try:
            for line in self.process.stdout:
                if line:
                    self.append_console(line)
        except Exception as e:
            self.append_console(f"Error reading bot output: {e}\n")
        finally:
            if self.process.poll() is not None:
                self.append_console("Bot process has exited.\n")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.is_running = False

    def append_console(self, text):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, text)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def remove_bot(self):
        if self.is_running:
            if not messagebox.askyesno("Confirm", "Bot is running. Do you want to stop and remove it?"):
                return
            self.stop_bot()
        self.remove_callback(self)
        self.destroy()

    def apply_settings(self):
        # Update colors and fonts based on settings
        self.config(bg=self.settings.get('bg_color', 'white'))
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.settings.get('bg_color', 'white'), fg=self.settings.get('text_color', 'black'))
            elif isinstance(widget, tk.Button):
                widget.config(bg=widget.cget('bg'), fg=widget.cget('fg'))
            elif isinstance(widget, tk.Entry):
                widget.config(bg="white", fg=self.settings.get('text_color', 'black'))
            elif isinstance(widget, tk.Text):
                widget.config(bg=self.settings.get('console_bg_color', '#f4f4f4'), fg=self.settings.get('console_text_color', '#000'))
            elif isinstance(widget, tk.Frame):
                widget.config(bg=self.settings.get('bg_color', 'white'))
        # Update dependency installation checkbox based on language
        language = self.language_var.get()
        dep_manager = self.SUPPORTED_LANGUAGES.get(language, {}).get('dependency_manager')
        if dep_manager:
            self.install_deps_check.config(state=tk.NORMAL)
            default = True
            self.install_deps_var.set(default)
        else:
            self.install_deps_var.set(False)
            self.install_deps_check.config(state=tk.DISABLED)


class DiscordBotRunner(tk.Frame):
    def __init__(self, master, settings):
        super().__init__(master, bg=settings.get('bg_color', 'white'))
        self.settings = settings
        self.pack_propagate(False)

        self.bot_counter = 0
        self.bots = []

        self.create_widgets()

    def create_widgets(self):
        # Title
        title = tk.Label(self, text="Discord Bot Runner", font=("Helvetica", 16, "bold"),
                         bg=self.settings.get('bg_color', 'white'), fg=self.settings.get('text_color', 'black'))
        title.pack(pady=10)

        # Add Bot Button
        add_bot_btn = tk.Button(self, text="Add Bot", command=self.add_bot, bg="#2196F3", fg="white")
        add_bot_btn.pack(pady=5)

        # Canvas with Scrollbar to hold multiple BotFrames
        self.canvas = tk.Canvas(self, bg=self.settings.get('bg_color', 'white'))
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.settings.get('bg_color', 'white'))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        self.scrollbar.pack(side="right", fill="y", pady=10)

    def add_bot(self):
        self.bot_counter += 1
        bot = BotFrame(self.scrollable_frame, self.bot_counter, self.settings, self.remove_bot)
        bot.pack(fill=tk.X, padx=10, pady=5, anchor="n")
        self.bots.append(bot)

    def remove_bot(self, bot):
        if bot in self.bots:
            self.bots.remove(bot)

    def apply_settings(self):
        # Update colors and fonts for the main frame
        self.config(bg=self.settings.get('bg_color', 'white'))
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.settings.get('bg_color', 'white'), fg=self.settings.get('text_color', 'black'))
            elif isinstance(widget, tk.Button):
                widget.config(bg=widget.cget('bg'), fg=widget.cget('fg'))
            elif isinstance(widget, tk.Canvas):
                widget.config(bg=self.settings.get('bg_color', 'white'))
            elif isinstance(widget, tk.Frame):
                widget.config(bg=self.settings.get('bg_color', 'white'))

        # Apply settings to all BotFrames
        for bot in self.bots:
            bot.apply_settings()
