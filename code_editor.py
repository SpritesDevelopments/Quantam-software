import tkinter as tk
from tkinter import ttk, filedialog
import pygments
from pygments.lexers import get_lexer_for_filename, PythonLexer
from pygments.styles import get_style_by_name
import re
import subprocess
import os
from pathlib import Path
import platform

class EditorTab(ttk.Frame):
    """Class to handle individual editor tabs"""
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.modified = False
        self.filename = "Untitled"
        self.create_editor()
        self.configure_tags()  # Move tags configuration here
        self.setup_keyboard_shortcuts()  # Move shortcuts to EditorTab

    def create_editor(self):
        # Editor container with gutter
        editor_container = ttk.Frame(self)
        editor_container.pack(fill='both', expand=True)

        # Left gutter for line numbers
        gutter = ttk.Frame(editor_container, width=50)
        gutter.pack(side='left', fill='y')
        gutter.pack_propagate(False)

        # Line numbers
        self.line_numbers = tk.Text(gutter,
            width=4,
            padx=5,
            pady=5,
            bg=self.theme['bg'],
            fg='#858585',
            relief='flat',
            state='disabled',
            font=('Consolas', 12))
        self.line_numbers.pack(fill='both', expand=True)

        # Editor area
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(fill='both', expand=True, side='left')

        # Text area
        self.text_area = tk.Text(editor_frame,
            wrap='none',
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#d4d4d4',
            relief='flat',
            padx=12,
            pady=8,
            font=('Consolas', 12),
            spacing1=2,
            undo=True)
        self.text_area.pack(fill='both', expand=True, side='left')

        # Scrollbars
        v_scroll = ttk.Scrollbar(editor_container, orient='vertical', 
                               command=self.text_area.yview)
        v_scroll.pack(side='right', fill='y')
        
        h_scroll = ttk.Scrollbar(self, orient='horizontal', 
                               command=self.text_area.xview)
        h_scroll.pack(side='bottom', fill='x')
        
        # Configure scrolling
        self.text_area.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        self.line_numbers.configure(yscrollcommand=v_scroll.set)
        v_scroll.configure(command=self.sync_scroll)

    def sync_scroll(self, *args):
        """Synchronize scrolling between line numbers and text area"""
        self.line_numbers.yview_moveto(args[1])
        self.text_area.yview_moveto(args[1])

    def update_line_numbers(self):
        """Update the line numbers"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        text_content = self.text_area.get('1.0', tk.END)
        num_lines = text_content.count('\n') + 1
        line_numbers = '\n'.join(str(i).rjust(3) for i in range(1, num_lines))
        
        self.line_numbers.insert('1.0', line_numbers)
        self.line_numbers.config(state='disabled')

    def configure_tags(self):
        """Configure syntax highlighting tags"""
        self.text_area.tag_configure('keyword', foreground='#569cd6')
        self.text_area.tag_configure('string', foreground='#ce9178')
        self.text_area.tag_configure('comment', foreground='#6a9955')
        self.text_area.tag_configure('function', foreground='#dcdcaa')
        self.text_area.tag_configure('class', foreground='#4ec9b0')
        self.text_area.tag_configure('number', foreground='#b5cea8')
        self.text_area.tag_configure('current_line', background='#282828')
        self.text_area.tag_configure('matching_bracket', background='#48485c')

    def highlight_current_line(self, event=None):
        self.text_area.tag_remove('current_line', '1.0', tk.END)
        current_line = self.text_area.index('insert').split('.')[0]
        self.text_area.tag_add('current_line', f'{current_line}.0', f'{current_line}.end+1c')

    def apply_syntax_highlighting(self):
        """Apply syntax highlighting to the current content"""
        content = self.text_area.get('1.0', tk.END)
        # Add syntax highlighting implementation here
        pass

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for this editor tab"""
        self.text_area.bind('<Control-s>', lambda e: self.master.master.save_file())
        self.text_area.bind('<Control-o>', lambda e: self.master.master.open_file())
        self.text_area.bind('<Control-f>', lambda e: self.master.master.show_find_dialog())
        self.text_area.bind('<Control-z>', lambda e: self.text_area.edit_undo())
        self.text_area.bind('<Control-y>', lambda e: self.text_area.edit_redo())


class CodeEditor(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.current_file = None
        self.modified = False
        self.toolbar_buttons = []  # Store toolbar buttons
        self.current_project = None
        self.search_results = []
        self.problems = []
        self.terminal_process = None
        self.current_panel = None  # Track current visible panel
        self.editors = []  # Store editor tabs
        self.minimap = tk.Canvas(self, width=100, bg='#1e1e1e', highlightthickness=0)  # Initialize minimap attribute
        self.create_main_layout()
        self.file_label = ttk.Label(self)  # Initialize file_label to avoid AttributeError

    def create_main_layout(self):
        """Create VSCode-like layout with side panels"""
        # Main container with activity bar
        self.main_container = ttk.PanedWindow(self, orient='horizontal')
        self.main_container.pack(fill='both', expand=True)

        # Activity bar (left-most panel with icons)
        self.create_activity_bar()

        # Side panel (explorer, search, etc.)
        self.side_panel = ttk.Notebook(self.main_container, style='Side.TNotebook')
        self.main_container.add(self.side_panel, weight=1)

        # Create side panel tabs
        self.create_explorer_panel()
        self.create_search_panel()
        self.create_git_panel()
        self.create_debug_panel()
        self.create_extensions_panel()

        # Main editor area
        self.editor_container = ttk.PanedWindow(self.main_container, orient='vertical')
        self.main_container.add(self.editor_container, weight=4)

        # Create editor components
        self.create_editor_area()
        self.create_bottom_panel()

    def create_activity_bar(self):
        """Create left-side activity bar with icons"""
        activity_bar = ttk.Frame(self, style='ActivityBar.TFrame')
        activity_bar.pack(side='left', fill='y')

        # Activity bar buttons with improved styling
        activities = [
            ("📁", "Explorer", self.show_explorer, 'explorer'),
            ("🔍", "Search", self.show_search, 'search'),
            ("⑂", "Source Control", self.show_git, 'git'),
            ("▷", "Run and Debug", self.show_debug, 'debug'),
            ("⚡", "Extensions", self.show_extensions, 'extensions')
        ]

        self.activity_buttons = {}
        for icon, tooltip, command, name in activities:
            btn = ttk.Button(activity_bar, text=icon, 
                           command=command, 
                           style='Activity.TButton')
            btn.pack(pady=2)
            self.create_tooltip(btn, tooltip)
            self.activity_buttons[name] = btn
            
            # Add hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Activity.TButton.Hover'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(style='Activity.TButton'))

    def create_explorer_panel(self):
        """Create file explorer panel"""
        explorer = ttk.Frame(self.side_panel)
        self.side_panel.add(explorer, text="Explorer")

        # Project toolbar
        toolbar = ttk.Frame(explorer)
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text="Open Folder", command=self.open_project).pack(side='left')
        ttk.Button(toolbar, text="New File", command=self.new_file).pack(side='left')

        # File tree
        self.file_tree = ttk.Treeview(explorer, show='tree')
        self.file_tree.pack(fill='both', expand=True)
        self.file_tree.bind('<Double-1>', self.open_selected_file)

    def create_editor_area(self):
        """Create main editor area with tabs"""
        # Editor tabs
        self.editor_tabs = ttk.Notebook(self.editor_container)
        self.editor_container.add(self.editor_tabs, weight=3)

        # Welcome page
        self.create_welcome_page()

        # Initial editor
        self.create_new_editor_tab()

    def create_bottom_panel(self):
        """Create bottom panel with terminal, problems, output"""
        bottom_panel = ttk.Notebook(self.editor_container, height=150)
        self.editor_container.add(bottom_panel, weight=1)

        # Terminal
        self.terminal = self.create_terminal(bottom_panel)
        bottom_panel.add(self.terminal, text="Terminal")

        # Problems panel
        self.problems_panel = ttk.Frame(bottom_panel)
        bottom_panel.add(self.problems_panel, text="Problems")
        self.problems_list = ttk.Treeview(self.problems_panel, 
            columns=('severity', 'message', 'file', 'line'))
        self.problems_list.pack(fill='both', expand=True)

        # Output panel
        self.output = tk.Text(bottom_panel, height=8)
        bottom_panel.add(self.output, text="Output")

    def create_terminal(self, parent):
        """Create interactive terminal"""
        terminal_frame = ttk.Frame(parent)
        
        # Terminal output
        terminal_output = tk.Text(terminal_frame,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#d4d4d4',
            font=('Consolas', 10))
        terminal_output.pack(fill='both', expand=True)

        # Command input
        cmd_frame = ttk.Frame(terminal_frame)
        cmd_frame.pack(fill='x')
        
        prompt = ttk.Label(cmd_frame, text="➜")
        prompt.pack(side='left')
        
        cmd_input = ttk.Entry(cmd_frame)
        cmd_input.pack(side='left', fill='x', expand=True)
        cmd_input.bind('<Return>', lambda e: self.execute_terminal_command(cmd_input.get()))

        return terminal_frame

    def create_search_panel(self):
        """Create search in files panel"""
        search = ttk.Frame(self.side_panel)
        self.side_panel.add(search, text="Search")

        # Search input
        search_frame = ttk.Frame(search)
        search_frame.pack(fill='x')
        
        self.search_input = ttk.Entry(search_frame)
        self.search_input.pack(side='left', fill='x', expand=True)
        
        ttk.Button(search_frame, text="Find", 
                  command=self.search_in_files).pack(side='left')

        # Results
        self.search_results_tree = ttk.Treeview(search)
        self.search_results_tree.pack(fill='both', expand=True)

    def create_git_panel(self):
        """Create source control panel"""
        git = ttk.Frame(self.side_panel)
        self.side_panel.add(git, text="Source Control")
        
        # Changes list
        self.changes_list = ttk.Treeview(git, columns=('status', 'file'))
        self.changes_list.pack(fill='both', expand=True)
        
        # Commit area
        commit_frame = ttk.Frame(git)
        commit_frame.pack(fill='x')
        
        self.commit_msg = ttk.Entry(commit_frame)
        self.commit_msg.pack(side='left', fill='x', expand=True)
        
        ttk.Button(commit_frame, text="Commit", 
                  command=self.git_commit).pack(side='left')

    def create_extensions_panel(self):
        """Create extensions panel"""
        extensions = ttk.Frame(self.side_panel)
        self.side_panel.add(extensions, text="Extensions")
        # Add extensions panel implementation here
        pass

    def create_debug_panel(self):
        """Create debug panel"""
        debug = ttk.Frame(self.side_panel)
        self.side_panel.add(debug, text="Run and Debug")
        # Add debug panel implementation here
        pass

    def create_welcome_page(self):
        """Create welcome page"""
        welcome_frame = ttk.Frame(self.editor_tabs)
        self.editor_tabs.add(welcome_frame, text="Welcome")
        ttk.Label(welcome_frame, text="Welcome to the Code Editor!").pack(pady=20)
        ttk.Label(welcome_frame, text="This is still under heavy development.").pack(pady=10)

    def create_new_editor_tab(self):
        """Create a new editor tab"""
        editor = EditorTab(self.editor_tabs, self.theme)
        self.editor_tabs.add(editor, text="Untitled")
        self.editors.append(editor)
        
        # Bind events for the new editor
        self.bind_editor_events(editor)
        return editor

    def bind_editor_events(self, editor):
        """Bind events for a specific editor tab"""
        editor.text_area.bind('<<Modified>>', lambda e: self.on_text_modified(editor))
        editor.text_area.bind('<KeyPress>', lambda e: self.on_key_press(e, editor))
        editor.text_area.bind('<KeyRelease>', lambda e: self.on_key_release(e, editor))
        editor.text_area.bind('<Control-s>', lambda e: self.save_file())
        editor.text_area.bind('<Control-f>', lambda e: self.show_find_dialog())

    def get_current_editor(self):
        """Get the currently active editor tab"""
        current = self.editor_tabs.select()
        if current:
            tab_id = self.editor_tabs.index(current)
            if tab_id < len(self.editors):
                return self.editors[tab_id]
        return None

    def execute_terminal_command(self, command):
        """Execute command in terminal"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.terminal.insert('end', f"\n{result.stdout}")
            if result.stderr:
                self.terminal.insert('end', f"\nError: {result.stderr}")
        except Exception as e:
            self.terminal.insert('end', f"\nError: {str(e)}")

    def search_in_files(self):
        """Search text in all project files"""
        if not self.current_project:
            return
            
        query = self.search_input.get()
        self.search_results_tree.delete(*self.search_results_tree.get_children())
        
        for path in Path(self.current_project).rglob('*'):
            if path.is_file():
                try:
                    with open(path, 'r') as f:
                        for i, line in enumerate(f, 1):
                            if query in line:
                                self.search_results_tree.insert('', 'end', 
                                    values=(path.relative_to(self.current_project), 
                                           i, line.strip()))
                except:
                    continue

    def open_project(self):
        """Open a project folder"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.current_project = folder_path
            self.populate_file_tree()

    def populate_file_tree(self):
        """Populate file tree with project files"""
        self.file_tree.delete(*self.file_tree.get_children())
        root_node = self.file_tree.insert('', 'end', text=self.current_project, open=True)
        self.add_files_to_tree(root_node, self.current_project)

    def add_files_to_tree(self, parent, path):
        """Add files to the file tree"""
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            node = self.file_tree.insert(parent, 'end', text=item, open=False)
            if os.path.isdir(item_path):
                self.add_files_to_tree(node, item_path)

    def open_selected_file(self, event):
        """Open the selected file from the file tree"""
        selected_item = self.file_tree.selection()[0]
        file_path = self.file_tree.item(selected_item, 'text')
        full_path = os.path.join(self.current_project, file_path)
        self.open_file(full_path)

    def new_file(self):
        """Create a new file in the project"""
        new_file_path = filedialog.asksaveasfilename(initialdir=self.current_project)
        if new_file_path:
            open(new_file_path, 'w').close()
            self.populate_file_tree()

    def git_commit(self):
        """Commit changes to the repository"""
        commit_message = self.commit_msg.get()
        if commit_message:
            try:
                subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.current_project)
                self.commit_msg.delete(0, tk.END)
                self.populate_git_changes()
            except Exception as e:
                self.output.insert('end', f"\nError: {str(e)}")

    def populate_git_changes(self):
        """Populate the changes list with git status"""
        self.changes_list.delete(*self.changes_list.get_children())
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], cwd=self.current_project, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                status, file = line[:2], line[3:]
                self.changes_list.insert('', 'end', values=(status, file))
        except Exception as e:
            self.output.insert('end', f"\nError: {str(e)}")

    def create_widgets(self):
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True)

        # Editor container first
        editor_container = ttk.Frame(main_container)
        editor_container.pack(fill='both', expand=True)

        # Left gutter (line numbers + breakpoints)
        gutter = ttk.Frame(editor_container, width=50)
        gutter.pack(side='left', fill='y')
        gutter.pack_propagate(False)

        # Line numbers
        self.line_numbers = tk.Text(gutter,
            width=4,
            padx=5,
            pady=5,
            bg=self.theme['bg'],
            fg='#858585',
            relief='flat',
            state='disabled',
            font=('Consolas', 12))
        self.line_numbers.pack(fill='both', expand=True)

        # Main editor area
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(fill='both', expand=True, side='left')

        # Create text area first
        self.text_area = tk.Text(editor_frame,
            wrap='none',
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#d4d4d4',
            relief='flat',
            padx=12,
            pady=8,
            font=('Consolas', 12),
            spacing1=2,
            undo=True)
        self.text_area.pack(fill='both', expand=True, side='left')

        # Now create toolbar after text_area exists
        toolbar = self.create_toolbar(main_container)
        toolbar.pack(fill='x', pady=1, before=editor_container)

        # Minimap
        self.minimap = tk.Canvas(editor_frame, 
            width=100, 
            bg='#1e1e1e',
            highlightthickness=0)
        self.minimap.pack(fill='y', side='right')

        # Scrollbars
        self.create_scrollbars(editor_container)

        # Status bar
        self.create_status_bar()

        # Bind events
        self.bind_events()

    def create_toolbar(self, parent):
        toolbar = ttk.Frame(parent, style='VSCode.Toolbar.TFrame')
        
        # File operations
        self.add_toolbar_button(toolbar, "📂", "Open File", self.open_file)
        self.add_toolbar_button(toolbar, "💾", "Save", self.save_file)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', padx=5, fill='y')
        
        # Edit operations
        self.add_toolbar_button(toolbar, "⟲", "Undo", lambda: self.text_area.event_generate("<<Undo>>"))
        self.add_toolbar_button(toolbar, "⟳", "Redo", lambda: self.text_area.event_generate("<<Redo>>"))
        self.add_toolbar_button(toolbar, "🔍", "Find", self.show_find_dialog)
        
        return toolbar

    def add_toolbar_button(self, parent, text, tooltip, command):
        btn = ttk.Button(parent, text=text, command=command, style='Toolbar.TButton', width=3)
        btn.pack(side='left', padx=2)
        self.create_tooltip(btn, tooltip)
        self.toolbar_buttons.append(btn)
        return btn

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Create tooltip window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, background="#ffffe0", 
                            relief='solid', borderwidth=1)
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def create_scrollbars(self, container):
        """Create and configure scrollbars"""
        # Vertical scrollbar
        v_scroll = ttk.Scrollbar(container, orient='vertical', 
                               command=self.text_area.yview)
        v_scroll.pack(side='right', fill='y')
        
        # Horizontal scrollbar
        h_scroll = ttk.Scrollbar(self, orient='horizontal', 
                               command=self.text_area.xview)
        h_scroll.pack(side='bottom', fill='x')
        
        # Configure text widget scroll
        self.text_area.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        
        # Link line numbers to vertical scroll
        self.line_numbers.configure(yscrollcommand=v_scroll.set)
        v_scroll.configure(command=self.sync_scroll)

    def sync_scroll(self, *args):
        """Synchronize scrolling between line numbers and text area"""
        self.line_numbers.yview_moveto(args[1])
        self.text_area.yview_moveto(args[1])

    def create_status_bar(self):
        status_bar = ttk.Frame(self)
        status_bar.pack(fill='x', side='bottom')

        # File info
        self.file_label = ttk.Label(status_bar, text="No file opened")
        self.file_label.pack(side='left', padx=5)

        # Position info
        self.position_label = ttk.Label(status_bar, text="Ln 1, Col 1")
        self.position_label.pack(side='right', padx=5)

        # Language mode
        self.lang_label = ttk.Label(status_bar, text="Plain Text")
        self.lang_label.pack(side='right', padx=5)

        # Encoding
        ttk.Label(status_bar, text="UTF-8").pack(side='right', padx=5)

    def bind_events(self):
        # Text modification events
        self.text_area.bind('<<Modified>>', self.on_text_modified)
        self.text_area.bind('<KeyPress>', self.on_key_press)
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        
        # Selection and cursor events
        self.text_area.bind('<Button-1>', self.update_position)
        self.text_area.bind('<ButtonRelease-1>', self.update_position)
        self.text_area.bind('<B1-Motion>', self.update_position)
        
        # Line number updates
        self.text_area.bind('<Return>', lambda e: self.after(1, self.update_line_numbers))
        self.text_area.bind('<BackSpace>', lambda e: self.after(1, self.update_line_numbers))
        self.text_area.bind('<Delete>', lambda e: self.after(1, self.update_line_numbers))
        self.text_area.bind('<Control-v>', lambda e: self.after(1, self.update_line_numbers))
        self.text_area.bind('<Control-x>', lambda e: self.after(1, self.update_line_numbers))

    def configure_tags(self): pass  # Remove this method
    def highlight_current_line(self, event=None): pass  # Remove this method
    def apply_syntax_highlighting(self): pass  # Remove this method

    def auto_indent(self, event):
        # Get the current line's indentation
        current_line = self.text_area.get('insert linestart', 'insert')
        match = re.match(r'^(\s+)', current_line)
        indent = match.group(1) if match else ''
        
        # Add extra indent after colon
        if current_line.rstrip().endswith(':'):
            indent += '    '
        
        self.text_area.insert('insert', f'\n{indent}')
        return 'break'

    def show_find_dialog(self):
        editor = self.get_current_editor()
        if editor:
            dialog = tk.Toplevel(self)
            dialog.title("Find")
            dialog.geometry("300x100")
            
            ttk.Label(dialog, text="Find:").pack(pady=5)
            find_entry = ttk.Entry(dialog, width=40)
            find_entry.pack(pady=5)
            
            def find_text():
                text = find_entry.get()
                start = editor.text_area.search(text, '1.0', tk.END)
                if start:
                    end = f"{start}+{len(text)}c"
                    editor.text_area.tag_remove('sel', '1.0', tk.END)
                    editor.text_area.tag_add('sel', start, end)
                    editor.text_area.see(start)
            
            ttk.Button(dialog, text="Find Next", command=find_text).pack(pady=5)

    def update_position(self, event=None):
        pos = self.text_area.index(tk.INSERT)
        line, col = pos.split('.')
        self.position_label.config(text=f"Ln {line}, Col {int(col)+1}")
    def on_text_change(self):
        if not self.modified:
            self.modified = True
            self.update_title()
        self.update_minimap()
        self.update_minimap()

    def update_title(self):
        filename = self.current_file or "Untitled"
        modified = "*" if self.modified else ""
        self.file_label.config(text=f"{filename}{modified}")

    def initial_line_numbers(self):
        """Initialize line numbers"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', '1')
        self.line_numbers.config(state='disabled')

    def update_line_numbers(self, event=None):
        """Update the line numbers"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Get the total number of lines
        text_content = self.text_area.get('1.0', tk.END)
        num_lines = text_content.count('\n')
        if text_content.endsWith('\n'):
            num_lines += 1
        
        # Generate and insert line numbers
        line_numbers = '\n'.join(str(i).rjust(3) for i in range(1, num_lines + 1))
        self.line_numbers.insert('1.0', line_numbers)
        
        # Realign line numbers with text
        self.line_numbers.yview_moveto(self.text_area.yview()[0])
        self.line_numbers.config(state='disabled')

    def on_text_modified(self, editor):
        """Handle text modifications for a specific editor"""
        if editor.text_area.edit_modified():
            editor.update_line_numbers()
            editor.text_area.edit_modified(False)
            editor.apply_syntax_highlighting()

    def on_key_press(self, event, editor):
        """Handle key press events for a specific editor"""
        if event.keysym in ('Return', 'BackSpace', 'Delete'):
            self.after(1, editor.update_line_numbers)

    def on_key_release(self, event, editor):
        """Handle key release events for a specific editor"""
        if event.keysym in ('Return', 'BackSpace', 'Delete'):
            self.after(1, editor.update_line_numbers)
        self.on_text_change()

    # ...rest of existing methods...

    def open_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename()
        if file_path:
            editor = self.get_current_editor() or self.create_new_editor_tab()
            with open(file_path, 'r') as file:
                editor.text_area.delete('1.0', tk.END)
                editor.text_area.insert('1.0', file.read())
                editor.update_line_numbers()
                editor.filename = os.path.basename(file_path)
                self.editor_tabs.tab(self.editor_tabs.select(), text=editor.filename)
                editor.modified = False

    def save_file(self):
        editor = self.get_current_editor()
        if editor:
            file_path = filedialog.asksaveasfilename()
            if file_path:
                with open(file_path, 'w') as file:
                    file.write(editor.text_area.get('1.0', tk.END))
                editor.filename = os.path.basename(file_path)
                self.editor_tabs.tab(self.editor_tabs.select(), text=editor.filename)
                editor.modified = False

    def update_minimap(self):
        """Update minimap content"""
        self.minimap.delete('all')
        editor = self.get_current_editor()
        if editor:
            content = editor.text_area.get('1.0', tk.END)
            lines = content.split('\n')
            y = 0
            for line in lines:
                self.minimap.create_text(2, y, anchor='nw', text=line[:100], fill='#d4d4d4', font=('Consolas', 2))
                y += 3

    def check_brackets(self, event=None):
        """Match brackets"""
        self.text_area.tag_remove('matching_bracket', '1.0', tk.END)
        content = self.text_area.get('1.0', tk.END)
        stack = []
        brackets = {'(': ')', '[': ']', '{': '}'}
        for i, char in enumerate(content):
            if char in brackets.keys():
                stack.append((char, i))
            elif char in brackets.values():
                if stack and brackets[stack[-1][0]] == char:
                    opening_bracket, opening_index = stack.pop()
                    self.text_area.tag_add('matching_bracket', f'1.0+{opening_index}c', f'1.0+{opening_index+1}c')
                    self.text_area.tag_add('matching_bracket', f'1.0+{i}c', f'1.0+{i+1}c')

    def show_explorer(self):
        """Show explorer panel"""
        if self.current_panel == "explorer":
            self.side_panel.pack_forget()
            self.current_panel = None
        else:
            self.side_panel.pack(side='left', fill='y')
            self.side_panel.select(0)  # Explorer is the first tab
            self.current_panel = "explorer"

    def show_search(self):
        """Show search panel"""
        if self.current_panel == "search":
            self.side_panel.pack_forget()
            self.current_panel = None
        else:
            self.side_panel.pack(side='left', fill='y')
            self.side_panel.select(1)  # Search is the second tab
            self.current_panel = "search"
            self.search_input.focus()

    def show_git(self):
        """Show git panel"""
        if self.current_panel == "git":
            self.side_panel.pack_forget()
            self.current_panel = None
        else:
            self.side_panel.pack(side='left', fill='y')
            self.side_panel.select(2)  # Git is the third tab
            self.current_panel = "git"
            self.populate_git_changes()

    def show_debug(self):
        """Show debug panel"""
        if self.current_panel == "debug":
            self.side_panel.pack_forget()
            self.current_panel = None
        else:
            self.side_panel.pack(side='left', fill='y')
            self.side_panel.select(3)  # Debug is the fourth tab
            self.current_panel = "debug"

    def show_extensions(self):
        """Show extensions panel"""
        if self.current_panel == "extensions":
            self.side_panel.pack_forget()
            self.current_panel = None
        else:
            self.side_panel.pack(side='left', fill='y')
            self.side_panel.select(4)  # Extensions is the fifth tab
            self.current_panel = "extensions"
