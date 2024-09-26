import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import sys
import keyword
import re
import git
import jedi

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
        self.file_explorer = tk.Frame(self.paned_window)
        self.paned_window.add(self.file_explorer, minsize=200)

        self.explorer_label = tk.Label(self.file_explorer, text="File Explorer", font=("Arial", 12, "bold"))
        self.explorer_label.pack(side="top", fill="x")

        self.tree = ttk.Treeview(self.file_explorer)
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
        self.editor_panel = tk.Frame(self.paned_window)
        self.paned_window.add(self.editor_panel)

        # ------------------------------
        # Toolbar
        # ------------------------------
        self.toolbar = tk.Frame(self.editor_panel)
        self.toolbar.pack(side="top", fill="x")

        self.save_button = tk.Button(
            self.toolbar, text="Save", command=self.save_file
        )
        self.save_button.pack(side="left", padx=5, pady=5)

        self.save_all_button = tk.Button(
            self.toolbar, text="Save All", command=self.save_all_files
        )
        self.save_all_button.pack(side="left", padx=5, pady=5)

        self.run_button = tk.Button(
            self.toolbar, text="Run", command=self.run_code
        )
        self.run_button.pack(side="left", padx=5, pady=5)

        # Language Selection
        self.language_var = tk.StringVar(value="Python")
        self.language_menu = ttk.Combobox(
            self.toolbar,
            textvariable=self.language_var,
            values=["Python", "JavaScript", "C++"],
            width=10,
            state="readonly"
        )
        self.language_menu.pack(side="left", padx=5, pady=5)
        self.language_menu.bind("<<ComboboxSelected>>", self.change_language)

        # Debug Toggle
        self.debug_var = tk.BooleanVar()
        self.debug_check = tk.Checkbutton(
            self.toolbar, text="Debug Mode", variable=self.debug_var
        )
        self.debug_check.pack(side="left", padx=5, pady=5)

        # Auto-Save Toggle
        self.auto_save_var = tk.BooleanVar(value=self.app_settings.get('auto_save', False))
        self.auto_save_check = tk.Checkbutton(
            self.toolbar, text="Auto-Save", variable=self.auto_save_var, command=self.toggle_auto_save
        )
        self.auto_save_check.pack(side="left", padx=5, pady=5)

        # Search Bar
        self.search_entry = tk.Entry(self.toolbar)
        self.search_entry.pack(side="right", padx=5, pady=5)
        self.search_entry.bind("<Return>", self.search_text)

        self.search_button = tk.Button(
            self.toolbar, text="Search", command=self.search_text
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
        self.terminal_frame = tk.Frame(self.editor_panel)
        self.terminal_frame.pack(fill="x", padx=5, pady=5)

        self.terminal_label = tk.Label(self.terminal_frame, text="Terminal:")
        self.terminal_label.pack(side="top", anchor="w")

        self.terminal_area = ScrolledText(
            self.terminal_frame,
            height=10,
            state="disabled",
            bg=self.app_settings['console_bg_color'],
            fg=self.app_settings['console_text_color'],
            font=(self.app_settings['font_family'], self.app_settings['font_size'])
        )
        self.terminal_area.pack(fill="x", expand=False)

        self.terminal_input = tk.Entry(
            self.terminal_frame,
            bg=self.app_settings['console_bg_color'],
            fg=self.app_settings['console_text_color'],
            font=(self.app_settings['font_family'], self.app_settings['font_size'])
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
        for p in os.listdir(path):
            abspath = os.path.join(path, p)
            node = self.tree.insert(parent_node, 'end', text=p, open=False)
            if os.path.isdir(abspath):
                self.tree.insert(node, 'end')  # Dummy child
                self.tree.item(node, open=False)

    def on_tree_double_click(self, event):
        item_id = self.tree.focus()
        file_path = self.get_full_path(item_id)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def on_tree_expand(self, event):
        item_id = self.tree.focus()
        path = self.get_full_path(item_id)
        if os.path.isdir(path):
            self.populate_tree(item_id, path)

    def get_full_path(self, item_id):
        path = ""
        while item_id:
            item = self.tree.item(item_id)
            path = os.path.join(item['text'], path)
            item_id = self.tree.parent(item_id)
        return os.path.join(os.getcwd(), path)

    # ------------------------------
    # Settings Methods
    # ------------------------------
    def apply_settings(self):
        # Update colors and fonts
        for file_info in self.open_files.values():
            text_widget = file_info['widget']
            text_widget.config(
                font=(self.app_settings['font_family'], self.app_settings['font_size']),
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                insertbackground=self.app_settings['text_color'],
                wrap='word' if self.app_settings['word_wrap'] else 'none',
            )

        self.terminal_area.config(
            bg=self.app_settings['console_bg_color'],
            fg=self.app_settings['console_text_color'],
            font=(self.app_settings['font_family'], self.app_settings['font_size'])
        )

        self.terminal_input.config(
            bg=self.app_settings['console_bg_color'],
            fg=self.app_settings['console_text_color'],
            insertbackground=self.app_settings['console_text_color'],
            font=(self.app_settings['font_family'], self.app_settings['font_size'])
        )

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
            with open(file_path, "r") as file:
                content = file.read()
            # Create a new tab
            tab = tk.Frame(self.notebook)
            text_widget = tk.Text(
                tab,
                wrap="none",
                undo=True,
                font=(self.app_settings['font_family'], self.app_settings['font_size']),
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                insertbackground=self.app_settings['text_color']
            )
            text_widget.pack(fill="both", expand=True)
            text_widget.insert(tk.END, content)
            text_widget.bind("<KeyRelease>", self.on_key_release)
            text_widget.bind("<KeyRelease>", self.highlight_syntax)
            text_widget.bind("<Key>", self.autocomplete)
            text_widget.bind("<Tab>", self.insert_tab)
            text_widget.bind("<Button-3>", self.show_context_menu)
            # Store the file info
            self.open_files[file_path] = {
                'widget': text_widget,
                'modified': False,
                'autocomplete': False
            }
            self.notebook.add(tab, text=os.path.basename(file_path))
            self.notebook.select(tab)
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
            with open(self.current_file, "w") as file:
                file.write(content)
            self.open_files[self.current_file]['modified'] = False
            self.update_tab_title()

    def save_all_files(self):
        for file_path in self.open_files:
            content = self.open_files[file_path]['widget'].get(1.0, tk.END)
            with open(file_path, "w") as file:
                file.write(content)
            self.open_files[file_path]['modified'] = False
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
            if hasattr(self, 'auto_save_job'):
                self.after_cancel(self.auto_save_job)

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

        threading.Thread(target=self.execute_code, args=(code, language, debug)).start()

    def execute_code(self, code, language, debug):
        if language == "Python":
            self.run_python_code(code, debug)
        elif language == "JavaScript":
            self.run_javascript_code(code)
        elif language == "C++":
            self.run_cpp_code(code)
        else:
            self.print_to_terminal(f"Unsupported language: {language}\n")

    def run_python_code(self, code, debug):
        try:
            with open("temp_code.py", "w") as f:
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
            threading.Thread(target=self.read_process_output, args=(process,)).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_javascript_code(self, code):
        try:
            with open("temp_code.js", "w") as f:
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
            threading.Thread(target=self.read_process_output, args=(process,)).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def run_cpp_code(self, code):
        try:
            with open("temp_code.cpp", "w") as f:
                f.write(code)
            compile_result = subprocess.run(["g++", "temp_code.cpp", "-o", "temp_code"], capture_output=True, text=True)
            if compile_result.returncode != 0:
                self.print_to_terminal(compile_result.stderr)
                return
            cmd = ["./temp_code"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            threading.Thread(target=self.read_process_output, args=(process,)).start()
        except Exception as e:
            self.print_to_terminal(f"Error: {e}\n")

    def read_process_output(self, process):
        for line in process.stdout:
            self.print_to_terminal(line)
        error_output = process.stderr.read()
        if error_output:
            self.print_to_terminal(error_output, error=True)

    # ------------------------------
    # Terminal Methods
    # ------------------------------
    def send_terminal_command(self, event=None):
        command = self.terminal_input.get()
        if command.strip():
            threading.Thread(target=self.execute_terminal_command, args=(command,)).start()
            self.terminal_input.delete(0, tk.END)

    def execute_terminal_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            output = result.stdout
            error = result.stderr
            self.print_to_terminal(f"$ {command}\n")
            if output:
                self.print_to_terminal(output)
            if error:
                self.print_to_terminal(error, error=True)
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

        if language == "Python":
            self.highlight_python_syntax(text_widget, code)
        elif language == "JavaScript":
            self.highlight_javascript_syntax(text_widget, code)
        elif language == "C++":
            self.highlight_cpp_syntax(text_widget, code)

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
            if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                # Unmatched quotes
                start = f"{idx + 1}.0"
                end = f"{idx + 1}.end"
                text_widget.tag_add("error", start, end)
                text_widget.tag_config("error", underline=True, foreground='red')

    def autocomplete(self, event):
        if event.keysym == "Tab":
            return
        if not self.current_file or self.current_file not in self.open_files:
            return
        text_widget = self.open_files[self.current_file]['widget']
        cursor_pos = text_widget.index(tk.INSERT)
        if self.language_var.get() == "Python":
            script = jedi.Script(code=text_widget.get("1.0", tk.END), path=self.current_file)
            try:
                completions = script.complete(line=int(cursor_pos.split('.')[0]), column=int(cursor_pos.split('.')[1])-1)
                if completions:
                    self.show_autocomplete_menu(text_widget, completions, cursor_pos)
            except Exception as e:
                pass  # Handle exceptions silently for now

    def show_autocomplete_menu(self, text_widget, completions, cursor_pos):
        menu = tk.Menu(self.master, tearoff=0)
        for completion in completions:
            menu.add_command(label=completion.name_with_symbols, command=lambda c=completion: self.insert_completion(text_widget, c))
        menu.post(self.winfo_pointerx(), self.winfo_pointery())

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
        context_menu.add_command(label="Copy", command=lambda: self.copy_text())
        context_menu.add_command(label="Cut", command=lambda: self.cut_text())
        context_menu.add_command(label="Paste", command=lambda: self.paste_text())
        context_menu.add_separator()
        context_menu.add_command(label="Undo", command=lambda: self.undo_action())
        context_menu.add_command(label="Redo", command=lambda: self.redo_action())
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
        widget.edit_undo()

    def redo_action(self):
        widget = self.open_files[self.current_file]['widget']
        widget.edit_redo()

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
        try:
            self.repo = git.Repo(os.getcwd())
        except git.exc.InvalidGitRepositoryError:
            self.repo = None

    def git_commit(self):
        if self.repo:
            self.repo.git.add('--all')
            self.repo.index.commit("Auto-commit from code editor")
            self.print_to_terminal("Changes committed to the repository.\n")
        else:
            self.print_to_terminal("No Git repository found.\n")

    def git_push(self):
        if self.repo:
            origin = self.repo.remote(name='origin')
            origin.push()
            self.print_to_terminal("Changes pushed to the remote repository.\n")
        else:
            self.print_to_terminal("No Git repository found.\n")

    def git_pull(self):
        if self.repo:
            origin = self.repo.remote(name='origin')
            origin.pull()
            self.print_to_terminal("Latest changes pulled from the remote repository.\n")
        else:
            self.print_to_terminal("No Git repository found.\n")

    # ------------------------------
    # Language Change
    # ------------------------------
    def change_language(self, event=None):
        self.highlight_syntax()

