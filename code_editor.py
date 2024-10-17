import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import keyword
import re

# Attempt to import external libraries and handle if not installed
try:
    import git
except ImportError:
    git = None

try:
    import jedi
except ImportError:
    jedi = None

try:
    import paramiko
except ImportError:
    paramiko = None  # Handled in SFTPManager if implemented


class CodeEditor(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.master = master
        self.app_settings = app_settings

        self.open_files = {}
        self.current_file = None
        self.auto_save_job = None
        self.process = None  # To keep track of the subprocess

        # ------------------------------
        # Create Paned Window
        # ------------------------------
        self.paned_window = tk.PanedWindow(self, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)

        # ------------------------------
        # File Explorer Panel
        # ------------------------------
        self.file_explorer = tk.Frame(self.paned_window, bg=self.app_settings.get('bg_color', 'white'))
        self.paned_window.add(self.file_explorer, minsize=200)

        self.explorer_label = tk.Label(
            self.file_explorer,
            text="File Explorer",
            font=("Arial", 12, "bold"),
            bg=self.app_settings.get('bg_color', 'white'),
            fg=self.app_settings.get('text_color', 'black')
        )
        self.explorer_label.pack(side="top", fill="x")

        self.tree = ttk.Treeview(self.file_explorer, selectmode='browse')
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

        # Scrollbars for the treeview
        self.tree_scrollbar = ttk.Scrollbar(self.file_explorer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.pack(side="right", fill="y")

        # Populate the tree with the current directory
        self.populate_tree()

        # ------------------------------
        # Editor Panel
        # ------------------------------
        self.editor_panel = tk.Frame(self.paned_window, bg=self.app_settings.get('bg_color', 'white'))
        self.paned_window.add(self.editor_panel)

        # ------------------------------
        # Toolbar
        # ------------------------------
        self.toolbar = tk.Frame(self.editor_panel, bg=self.app_settings.get('bg_color', 'white'))
        self.toolbar.pack(side="top", fill="x")

        self.save_button = tk.Button(
            self.toolbar, text="Save", command=self.save_file, bg="#4CAF50", fg="white"
        )
        self.save_button.pack(side="left", padx=5, pady=5)

        self.save_all_button = tk.Button(
            self.toolbar, text="Save All", command=self.save_all_files, bg="#2196F3", fg="white"
        )
        self.save_all_button.pack(side="left", padx=5, pady=5)

        self.run_button = tk.Button(
            self.toolbar, text="Run", command=self.run_code, bg="#FF9800", fg="white"
        )
        self.run_button.pack(side="left", padx=5, pady=5)

        # Language Selection
        self.language_var = tk.StringVar(value="Python")
        self.language_menu = ttk.Combobox(
            self.toolbar,
            textvariable=self.language_var,
            values=["Python", "JavaScript", "C++", "Lua", "Rust"],
            width=12,
            state="readonly"
        )
        self.language_menu.pack(side="left", padx=5, pady=5)
        self.language_menu.bind("<<ComboboxSelected>>", self.change_language)

        # Debug Toggle
        self.debug_var = tk.BooleanVar()
        self.debug_check = tk.Checkbutton(
            self.toolbar, text="Debug Mode", variable=self.debug_var,
            bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black')
        )
        self.debug_check.pack(side="left", padx=5, pady=5)

        # Auto-Save Toggle
        self.auto_save_var = tk.BooleanVar(value=self.app_settings.get('auto_save', False))
        self.auto_save_check = tk.Checkbutton(
            self.toolbar, text="Auto-Save", variable=self.auto_save_var, command=self.toggle_auto_save,
            bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black')
        )
        self.auto_save_check.pack(side="left", padx=5, pady=5)

        # Search Bar
        self.search_entry = tk.Entry(self.toolbar)
        self.search_entry.pack(side="right", padx=5, pady=5)
        self.search_entry.bind("<Return>", self.search_text)

        self.search_button = tk.Button(
            self.toolbar, text="Search", command=self.search_text, bg="#9E9E9E", fg="white"
        )
        self.search_button.pack(side="right", padx=5, pady=5)

        # ------------------------------
        # Notebook for Multiple Tabs
        # ------------------------------
        self.notebook = ttk.Notebook(self.editor_panel)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # ------------------------------
        # Integrated Terminal
        # ------------------------------
        self.terminal_frame = tk.Frame(self.editor_panel, bg=self.app_settings.get('bg_color', 'white'))
        self.terminal_frame.pack(fill="x", padx=5, pady=5)

        self.terminal_label = tk.Label(
            self.terminal_frame,
            text="Terminal:",
            bg=self.app_settings.get('bg_color', 'white'),
            fg=self.app_settings.get('text_color', 'black')
        )
        self.terminal_label.pack(side="top", anchor="w")

        self.terminal_area = ScrolledText(
            self.terminal_frame,
            height=10,
            state="disabled",
            bg=self.app_settings.get('console_bg_color', '#1e1e1e'),
            fg=self.app_settings.get('console_text_color', 'lightgreen'),
            font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12)),
            wrap="word"
        )
        self.terminal_area.pack(fill="x", expand=False)

        self.terminal_input = tk.Entry(
            self.terminal_frame,
            bg=self.app_settings.get('console_bg_color', '#1e1e1e'),
            fg=self.app_settings.get('console_text_color', 'lightgreen'),
            insertbackground=self.app_settings.get('console_text_color', 'lightgreen'),
            font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12))
        )
        self.terminal_input.pack(fill="x")
        self.terminal_input.bind("<Return>", self.send_terminal_command)

        # Git Repository Initialization
        self.repo = None
        self.initialize_git_repo()

        # Start auto-save timer if enabled
        if self.auto_save_var.get():
            self.start_auto_save()

        # Apply initial settings
        self.apply_settings()

    # ------------------------------
    # File Explorer Methods
    # ------------------------------
    def populate_tree(self, parent_node="", path=os.getcwd()):
        self.tree.delete(*self.tree.get_children(parent_node))
        try:
            for p in os.listdir(path):
                abspath = os.path.join(path, p)
                node = self.tree.insert(parent_node, 'end', text=p, open=False)
                if os.path.isdir(abspath):
                    self.tree.insert(node, 'end')  # Dummy child
        except PermissionError:
            pass  # Skip directories that cannot be accessed

    def on_tree_double_click(self, event):
        item_id = self.tree.focus()
        file_path = self.get_full_path(item_id)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def on_tree_expand(self, event):
        item_id = self.tree.focus()
        path = self.get_full_path(item_id)
        if os.path.isdir(path):
            # Check if the node is already populated
            if not self.tree.get_children(item_id):
                self.populate_tree(item_id, path)

    def get_full_path(self, item_id):
        path = ""
        while item_id:
            item = self.tree.item(item_id)
            path = os.path.join(item['text'], path)
            item_id = self.tree.parent(item_id)
        return os.path.abspath(os.path.join(os.getcwd(), path))

    # ------------------------------
    # Settings Methods
    # ------------------------------
    def apply_settings(self):
        # Update colors and fonts for open files
        for file_info in self.open_files.values():
            text_widget = file_info['widget']
            text_widget.config(
                font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12)),
                bg=self.app_settings.get('bg_color', 'white'),
                fg=self.app_settings.get('text_color', 'black'),
                insertbackground=self.app_settings.get('text_color', 'black'),
                wrap='word' if self.app_settings.get('word_wrap', True) else 'none',
            )

        # Update terminal area
        self.terminal_area.config(
            bg=self.app_settings.get('console_bg_color', '#1e1e1e'),
            fg=self.app_settings.get('console_text_color', 'lightgreen'),
            font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12))
        )

        # Update terminal input
        self.terminal_input.config(
            bg=self.app_settings.get('console_bg_color', '#1e1e1e'),
            fg=self.app_settings.get('console_text_color', 'lightgreen'),
            insertbackground=self.app_settings.get('console_text_color', 'lightgreen'),
            font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12))
        )

        # Update File Explorer colors
        self.file_explorer.config(bg=self.app_settings.get('bg_color', 'white'))
        self.explorer_label.config(bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black'))
        self.tree.tag_configure('directory', foreground=self.app_settings.get('text_color', 'black'))
        self.tree.tag_configure('file', foreground=self.app_settings.get('text_color', 'black'))

        # Update Toolbar colors
        self.toolbar.config(bg=self.app_settings.get('bg_color', 'white'))
        for child in self.toolbar.winfo_children():
            if isinstance(child, tk.Button) or isinstance(child, ttk.Combobox) or isinstance(child, tk.Checkbutton):
                try:
                    child.config(bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black'))
                except tk.TclError:
                    pass  # Some widgets like ttk.Combobox might not support bg and fg

        # Update Terminal Frame colors
        self.terminal_frame.config(bg=self.app_settings.get('bg_color', 'white'))
        self.terminal_label.config(bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black'))

        # Update Notebook tabs
        for tab_id in self.notebook.tabs():
            tab = self.nametowidget(tab_id)
            tab.config(bg=self.app_settings.get('bg_color', 'white'))
            for widget in tab.winfo_children():
                widget.config(bg=self.app_settings.get('bg_color', 'white'), fg=self.app_settings.get('text_color', 'black'))

    # ------------------------------
    # File Operations
    # ------------------------------
    def open_file(self, file_path=None):
        if not file_path:
            filetypes = [("All Files", "*.*")]
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
                filetypes=filetypes
            )
        if file_path and file_path not in self.open_files:
            try:
                with open(file_path, "r", encoding='utf-8') as file:
                    content = file.read()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
                return

            # Create a new tab
            tab = tk.Frame(self.notebook, bg=self.app_settings.get('bg_color', 'white'))
            self.notebook.add(tab, text=os.path.basename(file_path))
            self.notebook.select(tab)

            text_widget = tk.Text(
                tab,
                wrap="none",
                undo=True,
                font=(self.app_settings.get('font_family', 'Helvetica'), self.app_settings.get('font_size', 12)),
                bg=self.app_settings.get('bg_color', 'white'),
                fg=self.app_settings.get('text_color', 'black'),
                insertbackground=self.app_settings.get('text_color', 'black')
            )
            text_widget.pack(fill="both", expand=True)
            text_widget.insert(tk.END, content)
            text_widget.bind("<KeyRelease>", self.on_key_release)
            text_widget.bind("<KeyRelease>", self.highlight_syntax)
            text_widget.bind("<Key>", self.autocomplete)
            text_widget.bind("<Tab>", self.insert_tab)
            text_widget.bind("<Button-3>", self.show_context_menu)
            # Bind mouse wheel for scrolling if needed
            text_widget.bind("<MouseWheel>", lambda event: None)  # Placeholder for potential future use

            # Store the file info
            self.open_files[file_path] = {
                'widget': text_widget,
                'modified': False,
                'autocomplete': False
            }

            self.current_file = file_path
            self.highlight_syntax()
        elif file_path in self.open_files:
            # Switch to the tab if it's already open
            index = list(self.open_files.keys()).index(file_path)
            self.notebook.select(index)
            self.current_file = file_path

    def save_file(self):
        if self.current_file and self.current_file in self.open_files:
            content = self.open_files[self.current_file]['widget'].get(1.0, tk.END)
            try:
                with open(self.current_file, "w", encoding='utf-8') as file:
                    file.write(content)
                self.open_files[self.current_file]['modified'] = False
                self.update_tab_title()
                self.print_to_terminal(f"File saved: {self.current_file}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def save_all_files(self):
        for file_path in self.open_files:
            content = self.open_files[file_path]['widget'].get(1.0, tk.END)
            try:
                with open(file_path, "w", encoding='utf-8') as file:
                    file.write(content)
                self.open_files[file_path]['modified'] = False
                self.print_to_terminal(f"File saved: {file_path}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file {file_path}: {e}")
        self.update_tab_title()

    def update_tab_title(self):
        for idx, file_path in enumerate(self.open_files):
            modified = self.open_files[file_path]['modified']
            title = os.path.basename(file_path) + (" *" if modified else "")
            self.notebook.tab(idx, text=title)

    # ------------------------------
    # Auto-Save Functionality
    # ------------------------------
    def toggle_auto_save(self):
        if self.auto_save_var.get():
            self.start_auto_save()
        else:
            if self.auto_save_job:
                self.after_cancel(self.auto_save_job)
                self.auto_save_job = None

    def start_auto_save(self):
        self.save_all_files()
        self.auto_save_job = self.after(5000, self.start_auto_save)  # Auto-save every 5 seconds

    # ------------------------------
    # Run Code
    # ------------------------------
    def run_code(self):
        if not self.current_file or self.current_file not in self.open_files:
            messagebox.showwarning("Run Code", "No file selected to run.")
            return
        code = self.open_files[self.current_file]['widget'].get(1.0, tk.END)
        language = self.language_var.get()
        debug = self.debug_var.get()

        # Reset terminal area
        self.terminal_area.config(state="normal")
        self.terminal_area.delete(1.0, tk.END)
        self.terminal_area.config(state="disabled")

        threading.Thread(target=self.execute_code, args=(code, language, debug), daemon=True).start()

    def execute_code(self, code, language, debug):
        if language == "Python":
            self.run_python_code(code, debug)
        elif language == "JavaScript":
            self.run_javascript_code(code)
        elif language == "C++":
            self.run_cpp_code(code)
        elif language == "Lua":
            self.run_lua_code(code)
        elif language == "Rust":
            self.run_rust_code(code)
        else:
            self.print_to_terminal(f"Unsupported language: {language}\n")

    def run_python_code(self, code, debug):
        try:
            with open("temp_code.py", "w", encoding='utf-8') as f:
                f.write(code)
            if debug:
                cmd = ["python", "-m", "pdb", "temp_code.py"]
            else:
                cmd = ["python", "temp_code.py"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.process = process
            threading.Thread(target=self.read_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_javascript_code(self, code):
        try:
            with open("temp_code.js", "w", encoding='utf-8') as f:
                f.write(code)
            cmd = ["node", "temp_code.js"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.process = process
            threading.Thread(target=self.read_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_cpp_code(self, code):
        try:
            with open("temp_code.cpp", "w", encoding='utf-8') as f:
                f.write(code)
            compile_result = subprocess.run(["g++", "temp_code.cpp", "-o", "temp_code"], capture_output=True, text=True)
            if compile_result.returncode != 0:
                self.print_to_terminal(compile_result.stderr)
                return
            cmd = ["./temp_code"] if os.name != 'nt' else ["temp_code.exe"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.process = process
            threading.Thread(target=self.read_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_lua_code(self, code):
        try:
            with open("temp_code.lua", "w", encoding='utf-8') as f:
                f.write(code)
            cmd = ["lua", "temp_code.lua"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.process = process
            threading.Thread(target=self.read_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_rust_code(self, code):
        try:
            with open("temp_code.rs", "w", encoding='utf-8') as f:
                f.write(code)
            # Compile the Rust code
            compile_result = subprocess.run(["rustc", "temp_code.rs", "-o", "temp_code"], capture_output=True, text=True)
            if compile_result.returncode != 0:
                self.print_to_terminal(compile_result.stderr)
                return
            cmd = ["./temp_code"] if os.name != 'nt' else ["temp_code.exe"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.process = process
            threading.Thread(target=self.read_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def read_process_output(self, process):
        try:
            for line in iter(process.stdout.readline, ''):
                self.print_to_terminal(line)
            error_output = process.stderr.read()
            if error_output:
                self.print_to_terminal(error_output, error=True)
            process.stdout.close()
            process.stderr.close()
            process.wait()
        except Exception as e:
            self.print_to_terminal(f"Error reading process output: {e}\n", error=True)

    # ------------------------------
    # Terminal Methods
    # ------------------------------
    def send_terminal_command(self, event=None):
        command = self.terminal_input.get()
        if command.strip():
            threading.Thread(target=self.execute_terminal_command, args=(command,), daemon=True).start()
            self.terminal_input.delete(0, tk.END)

    def execute_terminal_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            self.print_to_terminal(f"$ {command}\n")
            if stdout:
                self.print_to_terminal(stdout)
            if stderr:
                self.print_to_terminal(stderr, error=True)
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n", error=True)

    def print_to_terminal(self, message, error=False):
        self.terminal_area.config(state="normal")
        if error:
            self.terminal_area.insert(tk.END, message, 'error')
            self.terminal_area.tag_config('error', foreground='red')
        else:
            self.terminal_area.insert(tk.END, message)
        self.terminal_area.config(state="disabled")
        self.terminal_area.see(tk.END)

    # ------------------------------
    # Editor Events
    # ------------------------------
    def on_key_release(self, event=None):
        if self.current_file and self.current_file in self.open_files:
            self.open_files[self.current_file]['modified'] = True
            self.update_tab_title()
        self.highlight_syntax()

    def on_tab_change(self, event):
        selected_tab = event.widget.select()
        idx = event.widget.index(selected_tab)
        file_path = list(self.open_files.keys())[idx]
        self.current_file = file_path
        self.highlight_syntax()

    # ------------------------------
    # Syntax Highlighting and Autocomplete
    # ------------------------------
    def highlight_syntax(self, event=None):
        if not self.current_file or self.current_file not in self.open_files:
            return
        text_widget = self.open_files[self.current_file]['widget']
        code = text_widget.get("1.0", tk.END)
        language = self.language_var.get()

        # Remove previous tags
        text_widget.tag_remove("keyword", "1.0", tk.END)
        text_widget.tag_remove("string", "1.0", tk.END)
        text_widget.tag_remove("comment", "1.0", tk.END)
        text_widget.tag_remove("function", "1.0", tk.END)
        text_widget.tag_remove("error", "1.0", tk.END)
        text_widget.tag_remove("fold", "1.0", tk.END)

        if language == "Python":
            self.highlight_python_syntax(text_widget, code)
        elif language == "JavaScript":
            self.highlight_javascript_syntax(text_widget, code)
        elif language == "C++":
            self.highlight_cpp_syntax(text_widget, code)
        elif language == "Lua":
            self.highlight_lua_syntax(text_widget, code)
        elif language == "Rust":
            self.highlight_rust_syntax(text_widget, code)

        # Error Highlighting
        self.highlight_errors(text_widget, code, language)

    def highlight_python_syntax(self, text_widget, code):
        # Keywords
        keywords = keyword.kwlist
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self.apply_pattern(text_widget, keyword_pattern, "keyword", "blue")

        # Strings
        string_pattern = r'(\".*?\"|\'.*?\')'
        self.apply_pattern(text_widget, string_pattern, "string", "green")

        # Comments
        comment_pattern = r'(#.*?$)'
        self.apply_pattern(text_widget, comment_pattern, "comment", "grey")

        # Function names
        function_pattern = r'\bdef\s+(\w+)\s*\('
        self.apply_pattern(text_widget, function_pattern, "function", "purple")

    def highlight_javascript_syntax(self, text_widget, code):
        # JavaScript keywords
        keywords = [
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default',
            'delete', 'do', 'else', 'export', 'extends', 'finally', 'for', 'function', 'if',
            'import', 'in', 'instanceof', 'let', 'new', 'return', 'super', 'switch', 'this',
            'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield'
        ]
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self.apply_pattern(text_widget, keyword_pattern, "keyword", "blue")

        # Strings
        string_pattern = r'(\".*?\"|\'.*?\'|\`.*?\`)'
        self.apply_pattern(text_widget, string_pattern, "string", "green")

        # Comments
        comment_pattern = r'(//.*?$|/\*[\s\S]*?\*/)'
        self.apply_pattern(text_widget, comment_pattern, "comment", "grey")

        # Function names
        function_pattern = r'\bfunction\s+(\w+)\s*\('
        self.apply_pattern(text_widget, function_pattern, "function", "purple")

    def highlight_cpp_syntax(self, text_widget, code):
        # C++ keywords
        keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'inline',
            'int', 'long', 'register', 'restrict', 'return', 'short', 'signed', 'sizeof',
            'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void',
            'volatile', 'while', 'class', 'public', 'private', 'protected', 'virtual',
            'friend', 'namespace', 'using', 'try', 'catch', 'throw', 'include', 'define'
        ]
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self.apply_pattern(text_widget, keyword_pattern, "keyword", "blue")

        # Strings
        string_pattern = r'(\".*?\"|\'.*?\')'
        self.apply_pattern(text_widget, string_pattern, "string", "green")

        # Comments
        comment_pattern = r'(//.*?$|/\*[\s\S]*?\*/)'
        self.apply_pattern(text_widget, comment_pattern, "comment", "grey")

        # Function names
        function_pattern = r'\b(\w+)\s*(?=\()'
        self.apply_pattern(text_widget, function_pattern, "function", "purple")

    def highlight_lua_syntax(self, text_widget, code):
        # Lua keywords
        keywords = [
            'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function',
            'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then',
            'true', 'until', 'while'
        ]
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self.apply_pattern(text_widget, keyword_pattern, "keyword", "blue")

        # Strings
        string_pattern = r'(\".*?\"|\'.*?\'|\[\[.*?\]\])'
        self.apply_pattern(text_widget, string_pattern, "string", "green")

        # Comments
        comment_pattern = r'(--.*?$|--\[\[.*?\]\])'
        self.apply_pattern(text_widget, comment_pattern, "comment", "grey")

        # Function names
        function_pattern = r'\bfunction\s+(\w+)\s*\('
        self.apply_pattern(text_widget, function_pattern, "function", "purple")

    def highlight_rust_syntax(self, text_widget, code):
        # Rust keywords
        keywords = [
            'as', 'break', 'const', 'continue', 'crate', 'else', 'enum', 'extern',
            'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop', 'match',
            'mod', 'move', 'mut', 'pub', 'ref', 'return', 'self', 'Self', 'static',
            'struct', 'trait', 'type', 'unsafe', 'use', 'where', 'while', 'async',
            'await', 'dyn'
        ]
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self.apply_pattern(text_widget, keyword_pattern, "keyword", "blue")

        # Strings
        string_pattern = r'(\".*?\"|\'.*?\')'
        self.apply_pattern(text_widget, string_pattern, "string", "green")

        # Comments
        comment_pattern = r'(//.*?$|/\*[\s\S]*?\*/)'
        self.apply_pattern(text_widget, comment_pattern, "comment", "grey")

        # Function names
        function_pattern = r'\bfn\s+(\w+)\s*\('
        self.apply_pattern(text_widget, function_pattern, "function", "purple")

    def apply_pattern(self, text_widget, pattern, tag, color):
        start = "1.0"
        code = text_widget.get("1.0", tk.END)
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            text_widget.tag_add(tag, start_idx, end_idx)
            text_widget.tag_config(tag, foreground=color)

    def highlight_errors(self, text_widget, code, language):
        # Basic error detection and highlighting
        lines = code.split('\n')
        for idx, line in enumerate(lines):
            # Unmatched quotes
            if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                start = f"{idx + 1}.0"
                end = f"{idx + 1}.end"
                text_widget.tag_add("error", start, end)
                text_widget.tag_config("error", underline=True, foreground='red')
            # Unmatched braces
            open_braces = line.count('{') + line.count('(')
            close_braces = line.count('}') + line.count(')')
            if open_braces != close_braces:
                start = f"{idx + 1}.0"
                end = f"{idx + 1}.end"
                text_widget.tag_add("error", start, end)
                text_widget.tag_config("error", underline=True, foreground='red')

    def autocomplete(self, event):
        if event.keysym in ("BackSpace", "Left", "Right", "Up", "Down"):
            return
        if not self.current_file or self.current_file not in self.open_files:
            return
        if not jedi:
            return  # Autocomplete not available without jedi
        text_widget = self.open_files[self.current_file]['widget']
        cursor_pos = text_widget.index(tk.INSERT)
        line, column = map(int, cursor_pos.split('.'))
        script = jedi.Script(code=text_widget.get("1.0", tk.END), line=line, column=column, path=self.current_file)
        try:
            completions = script.complete()
            if completions:
                self.show_autocomplete_menu(text_widget, completions, cursor_pos)
        except Exception as e:
            pass  # Handle exceptions silently for now

    def show_autocomplete_menu(self, text_widget, completions, cursor_pos):
        menu = tk.Menu(self.master, tearoff=0)
        for completion in completions:
            menu.add_command(label=completion.name_with_symbols, command=lambda c=completion: self.insert_completion(text_widget, c))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def insert_completion(self, text_widget, completion):
        cursor_pos = text_widget.index(tk.INSERT)
        line_start = text_widget.index(f"{cursor_pos} linestart")
        current_line = text_widget.get(line_start, cursor_pos)
        last_word = re.findall(r'\b\w+\b$', current_line)
        if last_word:
            text_widget.delete(f"{cursor_pos} - {len(last_word[0])}c", cursor_pos)
        text_widget.insert(tk.INSERT, completion.name)

    def insert_tab(self, event):
        self.open_files[self.current_file]['widget'].insert(tk.INSERT, "    ")
        return "break"

    # ------------------------------
    # Context Menu
    # ------------------------------
    def show_context_menu(self, event):
        context_menu = tk.Menu(self.master, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_text)
        context_menu.add_command(label="Cut", command=self.cut_text)
        context_menu.add_command(label="Paste", command=self.paste_text)
        context_menu.add_separator()
        context_menu.add_command(label="Undo", command=self.undo_action)
        context_menu.add_command(label="Redo", command=self.redo_action)
        context_menu.add_separator()
        context_menu.add_command(label="Select All", command=self.select_all)
        context_menu.add_command(label="Find", command=self.find_text)
        context_menu.add_separator()
        context_menu.add_command(label="Fold/Unfold Function", command=self.toggle_fold)
        context_menu.tk_popup(event.x_root, event.y_root)

    def copy_text(self):
        widget = self.open_files[self.current_file]['widget']
        try:
            widget.clipboard_clear()
            widget.clipboard_append(widget.selection_get())
        except tk.TclError:
            pass

    def cut_text(self):
        widget = self.open_files[self.current_file]['widget']
        try:
            self.copy_text()
            widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def paste_text(self):
        widget = self.open_files[self.current_file]['widget']
        try:
            widget.insert(tk.INSERT, widget.clipboard_get())
        except tk.TclError:
            pass

    def undo_action(self):
        widget = self.open_files[self.current_file]['widget']
        try:
            widget.edit_undo()
        except tk.TclError:
            pass

    def redo_action(self):
        widget = self.open_files[self.current_file]['widget']
        try:
            widget.edit_redo()
        except tk.TclError:
            pass

    def select_all(self):
        widget = self.open_files[self.current_file]['widget']
        widget.tag_add('sel', '1.0', 'end')

    def find_text(self):
        find_popup = tk.Toplevel(self)
        find_popup.title("Find")
        find_popup.geometry("300x100")
        find_popup.transient(self)
        find_popup.grab_set()

        tk.Label(find_popup, text="Find:").pack(pady=5)
        find_entry = tk.Entry(find_popup, width=30)
        find_entry.pack(pady=5)
        find_entry.focus_set()

        def do_find():
            text_widget = self.open_files[self.current_file]['widget']
            text_widget.tag_remove('found', '1.0', tk.END)
            search_term = find_entry.get()
            if search_term:
                idx = '1.0'
                while True:
                    idx = text_widget.search(search_term, idx, nocase=1, stopindex=tk.END)
                    if not idx:
                        break
                    lastidx = f"{idx}+{len(search_term)}c"
                    text_widget.tag_add('found', idx, lastidx)
                    idx = lastidx
                text_widget.tag_config('found', background='yellow')
            find_popup.destroy()

        tk.Button(find_popup, text="Find All", command=do_find).pack(pady=5)

    # ------------------------------
    # Search Functionality
    # ------------------------------
    def search_text(self, event=None):
        if not self.current_file or self.current_file not in self.open_files:
            return
        text_widget = self.open_files[self.current_file]['widget']
        text_widget.tag_remove('search', '1.0', tk.END)
        search_query = self.search_entry.get()
        if search_query:
            idx = '1.0'
            while True:
                idx = text_widget.search(search_query, idx, nocase=1, stopindex=tk.END)
                if not idx:
                    break
                lastidx = f"{idx}+{len(search_query)}c"
                text_widget.tag_add('search', idx, lastidx)
                idx = lastidx
            text_widget.tag_config('search', background='yellow')

    # ------------------------------
    # Git Integration
    # ------------------------------
    def initialize_git_repo(self):
        if not git:
            self.print_to_terminal("GitPython is not installed. Git features are disabled.\n", error=True)
            return
        try:
            self.repo = git.Repo(os.getcwd())
            self.print_to_terminal("Git repository initialized.\n")
        except git.exc.InvalidGitRepositoryError:
            self.repo = None
            self.print_to_terminal("No Git repository found.\n")

    def git_commit(self):
        if self.repo:
            try:
                self.repo.git.add('--all')
                self.repo.index.commit("Auto-commit from code editor")
                self.print_to_terminal("Changes committed to the repository.\n")
            except git.exc.GitCommandError as e:
                self.print_to_terminal(f"Git Commit Error: {e}\n", error=True)
        else:
            self.print_to_terminal("No Git repository found.\n", error=True)

    def git_push(self):
        if self.repo:
            try:
                origin = self.repo.remote(name='origin')
                origin.push()
                self.print_to_terminal("Changes pushed to the remote repository.\n")
            except Exception as e:
                self.print_to_terminal(f"Git Push Error: {e}\n", error=True)
        else:
            self.print_to_terminal("No Git repository found.\n", error=True)

    def git_pull(self):
        if self.repo:
            try:
                origin = self.repo.remote(name='origin')
                origin.pull()
                self.print_to_terminal("Latest changes pulled from the remote repository.\n")
            except Exception as e:
                self.print_to_terminal(f"Git Pull Error: {e}\n", error=True)
        else:
            self.print_to_terminal("No Git repository found.\n", error=True)

    # ------------------------------
    # Language Change
    # ------------------------------
    def change_language(self, event=None):
        self.highlight_syntax()

    # ------------------------------
    # Code Folding Functionality
    # ------------------------------
    def toggle_fold(self):
        if not self.current_file or self.current_file not in self.open_files:
            return
        text_widget = self.open_files[self.current_file]['widget']
        cursor_pos = text_widget.index(tk.INSERT)
        line_num = int(cursor_pos.split('.')[0])

        # Detect if current line is a function definition
        language = self.language_var.get()
        line_text = text_widget.get(f"{line_num}.0", f"{line_num}.end")

        if language == "Python":
            match = re.match(r'\s*def\s+\w+\s*\(.*\):', line_text)
        elif language == "JavaScript":
            match = re.match(r'\s*function\s+\w+\s*\(.*\)\s*\{', line_text)
        elif language == "C++":
            match = re.match(r'\s*\w+\s+\w+\s*\(.*\)\s*\{', line_text)
        elif language == "Lua":
            match = re.match(r'\s*function\s+\w+\s*\(.*\)', line_text)
        elif language == "Rust":
            match = re.match(r'\s*fn\s+\w+\s*\(.*\)\s*\{', line_text)
        else:
            match = None

        if match:
            start_line = line_num
            # Find the closing brace or 'end' based on language
            if language == "Python" or language == "Lua":
                closing_keyword = 'end'
            else:
                closing_keyword = '}'

            end_line = self.find_closing(text_widget, start_line, language, closing_keyword)

            if end_line:
                # Check if the region is already folded
                tag_name = f"fold_{start_line}"
                if text_widget.tag_nextrange(tag_name, f"{start_line}.0", f"{start_line}.end"):
                    # Unfold
                    text_widget.tag_remove(tag_name, f"{start_line}.0", f"{end_line}.end")
                else:
                    # Fold
                    text_widget.tag_add(tag_name, f"{start_line + 1}.0", f"{end_line}.end")
                    text_widget.tag_config(tag_name, elide=True)

    def find_closing(self, text_widget, start_line, language, closing_keyword):
        # Simple method to find the closing '}' or 'end'
        total_lines = int(text_widget.index('end-1c').split('.')[0])
        open_braces = 0
        for line in range(start_line, total_lines + 1):
            line_text = text_widget.get(f"{line}.0", f"{line}.end")
            if language in ["Python", "Lua"]:
                if re.search(r'\bdef\b|\bfunction\b', line_text):
                    open_braces += 1
                if re.search(r'\bend\b', line_text):
                    open_braces -= 1
            else:
                open_braces += line_text.count('{')
                open_braces -= line_text.count('}')
            if open_braces == 0:
                return line
        return None

    # ------------------------------
    # Utility Methods
    # ------------------------------
    def print_to_terminal(self, message, error=False):
        self.terminal_area.config(state="normal")
        if error:
            self.terminal_area.insert(tk.END, message, 'error')
            self.terminal_area.tag_config('error', foreground='red')
        else:
            self.terminal_area.insert(tk.END, message)
        self.terminal_area.config(state="disabled")
        self.terminal_area.see(tk.END)
