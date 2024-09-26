import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import json
import re

class SettingsPanel(tk.Frame):
    def __init__(self, master, app_settings, apply_settings_callback):
        super().__init__(master)
        self.app_settings = app_settings
        self.apply_settings_callback = apply_settings_callback

        # Theme Selection
        self.theme_label = tk.Label(self, text="Select Theme:", font=("Arial", 12))
        self.theme_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.theme_var = tk.StringVar(value=self.app_settings.get('theme', 'Light'))
        self.theme_menu = ttk.Combobox(
            self,
            textvariable=self.theme_var,
            values=["Light", "Dark", "Solarized", "Custom"],
            font=("Arial", 12),
            state="readonly",
        )
        self.theme_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.theme_menu.bind("<<ComboboxSelected>>", self.apply_theme)

        # Font Family Selection
        self.font_family_label = tk.Label(self, text="Font Family:", font=("Arial", 12))
        self.font_family_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.font_family_var = tk.StringVar(value=self.app_settings.get('font_family', 'Helvetica'))
        self.font_family_menu = ttk.Combobox(
            self,
            textvariable=self.font_family_var,
            values=["Helvetica", "Arial", "Courier", "Times", "Consolas", "Monaco"],
            font=("Arial", 12),
            state="readonly",
        )
        self.font_family_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.font_family_menu.bind("<<ComboboxSelected>>", self.apply_font_settings)

        # Font Size Selection
        self.font_size_label = tk.Label(self, text="Font Size:", font=("Arial", 12))
        self.font_size_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.font_size_var = tk.IntVar(value=self.app_settings.get('font_size', 12))
        self.font_size_spinbox = tk.Spinbox(
            self, from_=8, to=40, textvariable=self.font_size_var, font=("Arial", 12), command=self.apply_font_settings
        )
        self.font_size_spinbox.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.font_size_spinbox.bind("<Return>", self.apply_font_settings)

        # Font Style Options
        self.bold_var = tk.BooleanVar(value=self.app_settings.get('font_bold', False))
        self.italic_var = tk.BooleanVar(value=self.app_settings.get('font_italic', False))
        self.underline_var = tk.BooleanVar(value=self.app_settings.get('font_underline', False))
        self.overstrike_var = tk.BooleanVar(value=self.app_settings.get('font_overstrike', False))

        self.bold_checkbutton = tk.Checkbutton(
            self, text="Bold", variable=self.bold_var, command=self.apply_font_settings, font=("Arial", 12)
        )
        self.bold_checkbutton.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.italic_checkbutton = tk.Checkbutton(
            self, text="Italic", variable=self.italic_var, command=self.apply_font_settings, font=("Arial", 12)
        )
        self.italic_checkbutton.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.underline_checkbutton = tk.Checkbutton(
            self, text="Underline", variable=self.underline_var, command=self.apply_font_settings, font=("Arial", 12)
        )
        self.underline_checkbutton.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.overstrike_checkbutton = tk.Checkbutton(
            self, text="Overstrike", variable=self.overstrike_var, command=self.apply_font_settings, font=("Arial", 12)
        )
        self.overstrike_checkbutton.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Background Color Picker
        self.bg_color_button = tk.Button(
            self,
            text="Select Background Color",
            command=self.select_bg_color,
            font=("Arial", 12),
        )
        self.bg_color_button.grid(
            row=5, column=0, columnspan=2, pady=5, padx=10, sticky="ew"
        )

        # Text Color Picker
        self.text_color_button = tk.Button(
            self,
            text="Select Text Color",
            command=self.select_text_color,
            font=("Arial", 12),
        )
        self.text_color_button.grid(
            row=6, column=0, columnspan=2, pady=5, padx=10, sticky="ew"
        )

        # Syntax Highlighting Colors
        self.syntax_colors_button = tk.Button(
            self,
            text="Customize Syntax Highlighting",
            command=self.customize_syntax_colors,
            font=("Arial", 12),
        )
        self.syntax_colors_button.grid(
            row=7, column=0, columnspan=2, pady=5, padx=10, sticky="ew"
        )

        # Word Wrap Toggle
        self.wrap_var = tk.BooleanVar(value=self.app_settings.get('word_wrap', True))
        self.wrap_checkbutton = tk.Checkbutton(
            self,
            text="Enable Word Wrap",
            variable=self.wrap_var,
            command=self.toggle_word_wrap,
            font=("Arial", 12),
        )
        self.wrap_checkbutton.grid(
            row=8, column=0, columnspan=2, pady=5, padx=10, sticky="w"
        )

        # Auto-Save Toggle
        self.auto_save_var = tk.BooleanVar(value=self.app_settings.get('auto_save', False))
        self.auto_save_checkbutton = tk.Checkbutton(
            self,
            text="Enable Auto-Save",
            variable=self.auto_save_var,
            command=self.toggle_auto_save,
            font=("Arial", 12),
        )
        self.auto_save_checkbutton.grid(
            row=9, column=0, columnspan=2, pady=5, padx=10, sticky="w"
        )

        # Save Settings Button
        self.save_button = tk.Button(
            self,
            text="Save Settings",
            command=self.save_settings,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
        )
        self.save_button.grid(
            row=10, column=0, columnspan=2, pady=10, padx=10, sticky="ew"
        )

        # Load Settings Button
        self.load_button = tk.Button(
            self,
            text="Load Settings",
            command=self.load_settings,
            font=("Arial", 12),
        )
        self.load_button.grid(
            row=11, column=0, columnspan=2, pady=5, padx=10, sticky="ew"
        )

        # Reset Button
        self.reset_button = tk.Button(
            self,
            text="Reset to Default",
            command=self.reset_settings,
            font=("Arial", 12),
        )
        self.reset_button.grid(
            row=12, column=0, columnspan=2, pady=5, padx=10, sticky="ew"
        )

        # Preview area
        self.preview_label = tk.Label(
            self, text="Preview:", font=("Arial", 12, "bold")
        )
        self.preview_label.grid(row=13, column=0, columnspan=2, pady=10)

        self.preview_area = tk.Text(
            self, height=8, width=60, font=("Helvetica", 12), wrap="word"
        )
        self.preview_area.grid(
            row=14, column=0, columnspan=2, padx=10, pady=10, sticky="ew"
        )
        self.preview_code_snippet = '''def hello_world():
    print("Hello, World!")
# This is a sample code snippet.'''
        self.preview_area.insert("1.0", self.preview_code_snippet)
        self.preview_area.config(state="disabled")

        # Configure grid resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(14, weight=1)

        self.pack(fill="both", expand=True)

        # Apply initial settings to preview
        self.update_preview()

    def apply_theme(self, event=None):
        selected_theme = self.theme_var.get()
        self.app_settings['theme'] = selected_theme
        if selected_theme == "Dark":
            self.app_settings['bg_color'] = "#1e1e1e"
            self.app_settings['text_color'] = "#d4d4d4"
            self.app_settings['syntax_colors'] = {
                'keyword': '#569cd6',
                'string': '#ce9178',
                'comment': '#6a9955',
                'builtin': '#4ec9b0',
            }
        elif selected_theme == "Solarized":
            self.app_settings['bg_color'] = "#fdf6e3"
            self.app_settings['text_color'] = "#657b83"
            self.app_settings['syntax_colors'] = {
                'keyword': '#859900',
                'string': '#2aa198',
                'comment': '#93a1a1',
                'builtin': '#268bd2',
            }
        elif selected_theme == "Custom":
            # Use current settings
            pass
        else:  # Default to Light theme
            self.app_settings['bg_color'] = "white"
            self.app_settings['text_color'] = "black"
            self.app_settings['syntax_colors'] = {
                'keyword': '#0000ff',
                'string': '#a31515',
                'comment': '#008000',
                'builtin': '#0000ff',
            }
        self.update_preview()
        self.apply_settings_callback()

    def apply_font_settings(self, event=None):
        self.app_settings['font_family'] = self.font_family_var.get()
        self.app_settings['font_size'] = self.font_size_var.get()
        self.app_settings['font_bold'] = self.bold_var.get()
        self.app_settings['font_italic'] = self.italic_var.get()
        self.app_settings['font_underline'] = self.underline_var.get()
        self.app_settings['font_overstrike'] = self.overstrike_var.get()
        self.update_preview()
        self.apply_settings_callback()

    def select_bg_color(self):
        color = colorchooser.askcolor(color=self.app_settings.get('bg_color', 'white'))[1]
        if color:
            self.app_settings['bg_color'] = color
            self.update_preview()
            self.apply_settings_callback()

    def select_text_color(self):
        color = colorchooser.askcolor(color=self.app_settings.get('text_color', 'black'))[1]
        if color:
            self.app_settings['text_color'] = color
            self.update_preview()
            self.apply_settings_callback()

    def customize_syntax_colors(self):
        SyntaxColorCustomizer(self, self.app_settings, self.update_preview)

    def toggle_word_wrap(self):
        self.app_settings['word_wrap'] = self.wrap_var.get()
        self.apply_settings_callback()

    def toggle_auto_save(self):
        self.app_settings['auto_save'] = self.auto_save_var.get()
        self.apply_settings_callback()

    def save_settings(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Settings"
        )
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.app_settings, f, indent=4)
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")

    def load_settings(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Load Settings"
        )
        if file_path:
            with open(file_path, 'r') as f:
                self.app_settings.update(json.load(f))
            self.apply_loaded_settings()
            messagebox.showinfo("Settings Loaded", "Your settings have been loaded successfully!")

    def apply_loaded_settings(self):
        # Update UI elements with loaded settings
        self.theme_var.set(self.app_settings.get('theme', 'Light'))
        self.font_family_var.set(self.app_settings.get('font_family', 'Helvetica'))
        self.font_size_var.set(self.app_settings.get('font_size', 12))
        self.bold_var.set(self.app_settings.get('font_bold', False))
        self.italic_var.set(self.app_settings.get('font_italic', False))
        self.underline_var.set(self.app_settings.get('font_underline', False))
        self.overstrike_var.set(self.app_settings.get('font_overstrike', False))
        self.wrap_var.set(self.app_settings.get('word_wrap', True))
        self.auto_save_var.set(self.app_settings.get('auto_save', False))
        self.update_preview()
        self.apply_settings_callback()

    def reset_settings(self):
        self.app_settings.update({
            'theme': "Light",
            'font_family': "Helvetica",
            'font_size': 12,
            'font_bold': False,
            'font_italic': False,
            'font_underline': False,
            'font_overstrike': False,
            'bg_color': "white",
            'text_color': "black",
            'syntax_colors': {
                'keyword': '#0000ff',
                'string': '#a31515',
                'comment': '#008000',
                'builtin': '#0000ff',
            },
            'word_wrap': True,
            'auto_save': False
        })
        self.apply_loaded_settings()
        messagebox.showinfo("Settings Reset", "Settings have been reset to default values.")

    def update_preview(self):
        self.preview_area.config(state="normal")
        self.preview_area.delete(1.0, tk.END)
        self.preview_area.insert(tk.END, self.preview_code_snippet)

        # Apply font settings
        font_family = self.font_family_var.get()
        font_size = self.font_size_var.get()
        font_weight = 'bold' if self.bold_var.get() else 'normal'
        font_slant = 'italic' if self.italic_var.get() else 'roman'

        # Build a dictionary for font options
        font_options = {
            'family': font_family,
            'size': font_size,
            'weight': font_weight,
            'slant': font_slant,
        }
        if self.underline_var.get():
            font_options['underline'] = True
        if self.overstrike_var.get():
            font_options['overstrike'] = True

        self.preview_area.config(
            font=font_options,
            bg=self.app_settings['bg_color'],
            fg=self.app_settings['text_color'],
            wrap='word' if self.wrap_var.get() else 'none',
        )

        # Apply syntax highlighting
        self.highlight_syntax()

        self.preview_area.config(state="disabled")

    def highlight_syntax(self):
        # Simple syntax highlighter for the preview area
        code = self.preview_area.get("1.0", tk.END)
        self.preview_area.tag_delete("keyword", "string", "comment", "builtin")
        syntax_colors = self.app_settings.get('syntax_colors', {})

        # Define simple patterns for demonstration
        patterns = {
            'keyword': r'\b(def|class|if|else|elif|return|import|from|for|while|try|except|with|as|pass|break|continue|lambda|yield|in|is|and|or|not|None|True|False)\b',
            'string': r'(\".*?\"|\'.*?\')',
            'comment': r'(#.*?$)',
            'builtin': r'\b(print|len|range|open|input|str|int|float|list|dict|set|tuple|super|self)\b',
        }

        for tag, pattern in patterns.items():
            regex = re.compile(pattern, re.MULTILINE)
            for match in regex.finditer(code):
                start_index = f"1.0+{match.start()}c"
                end_index = f"1.0+{match.end()}c"
                self.preview_area.tag_add(tag, start_index, end_index)
                self.preview_area.tag_config(tag, foreground=syntax_colors.get(tag, 'black'))

class SyntaxColorCustomizer(tk.Toplevel):
    def __init__(self, master, app_settings, update_preview_callback):
        super().__init__(master)
        self.title("Customize Syntax Highlighting")
        self.app_settings = app_settings
        self.update_preview_callback = update_preview_callback

        self.syntax_elements = ['keyword', 'string', 'comment', 'builtin']
        self.color_vars = {}

        for idx, element in enumerate(self.syntax_elements):
            tk.Label(self, text=element.capitalize() + " Color:", font=("Arial", 12)).grid(
                row=idx, column=0, padx=10, pady=5, sticky="w"
            )
            color_var = tk.StringVar(value=self.app_settings['syntax_colors'].get(element, '#000000'))
            color_entry = tk.Entry(self, textvariable=color_var, font=("Arial", 12))
            color_entry.grid(row=idx, column=1, padx=10, pady=5, sticky="ew")
            color_button = tk.Button(
                self,
                text="Select Color",
                command=lambda e=element, v=color_var: self.select_color(e, v),
                font=("Arial", 12),
            )
            color_button.grid(row=idx, column=2, padx=10, pady=5)
            self.color_vars[element] = color_var

        # Apply and Cancel buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(self.syntax_elements), column=0, columnspan=3, pady=10)

        apply_btn = tk.Button(btn_frame, text="Apply", command=self.apply_changes, font=("Arial", 12))
        apply_btn.pack(side="left", padx=5)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.destroy, font=("Arial", 12))
        cancel_btn.pack(side="left", padx=5)

        self.columnconfigure(1, weight=1)
        self.resizable(False, False)

    def select_color(self, element, color_var):
        color = colorchooser.askcolor(color=color_var.get())[1]
        if color:
            color_var.set(color)

    def apply_changes(self):
        for element, color_var in self.color_vars.items():
            self.app_settings['syntax_colors'][element] = color_var.get()
        self.update_preview_callback()
        self.destroy()
