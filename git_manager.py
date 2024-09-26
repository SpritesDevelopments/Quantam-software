import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

class GitManager(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.app_settings = app_settings

        self.label = tk.Label(self, text="Git Manager", font=("Helvetica", 16))
        self.label.pack(pady=10)

        # Git Configurations
        config_frame = tk.Frame(self)
        config_frame.pack(pady=10, fill="x")

        self.repo_label = tk.Label(config_frame, text="Repository Path:")
        self.repo_label.grid(row=0, column=0, padx=5, sticky="w")

        self.repo_entry = tk.Entry(config_frame, width=50)
        self.repo_entry.grid(row=0, column=1, padx=5, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        self.browse_button = tk.Button(
            config_frame, text="Browse", command=self.browse_repo
        )
        self.browse_button.grid(row=0, column=2, padx=5)

        # Authentication Status
        self.auth_status_label = tk.Label(self, text="Not Signed In", fg="red")
        self.auth_status_label.pack(pady=5)

        # Authentication Button
        self.auth_button = tk.Button(
            self, text="Sign In with GitHub", command=self.show_coming_soon
        )
        self.auth_button.pack(pady=5)

        # Commit Message
        self.commit_label = tk.Label(self, text="Commit Message:")
        self.commit_label.pack(pady=5)
        self.commit_message = tk.Entry(self, width=50)
        self.commit_message.pack(pady=5, fill="x", padx=10)

        # Buttons for Git Operations
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        self.commit_button = tk.Button(
            button_frame, text="Commit", command=self.commit_changes, state="disabled"
        )
        self.commit_button.grid(row=0, column=0, padx=5)

        self.pull_button = tk.Button(
            button_frame, text="Pull", command=self.pull_changes, state="disabled"
        )
        self.pull_button.grid(row=0, column=1, padx=5)

        self.push_button = tk.Button(
            button_frame, text="Push", command=self.push_changes, state="disabled"
        )
        self.push_button.grid(row=0, column=2, padx=5)

        # Branch Management
        branch_frame = tk.Frame(self)
        branch_frame.pack(pady=10, fill="x")

        self.branch_label = tk.Label(branch_frame, text="Branch:")
        self.branch_label.grid(row=0, column=0, padx=5, sticky="w")

        self.branch_entry = tk.Entry(branch_frame, width=30)
        self.branch_entry.grid(row=0, column=1, padx=5, sticky="w")

        self.switch_button = tk.Button(
            branch_frame, text="Switch Branch", command=self.switch_branch, state="disabled"
        )
        self.switch_button.grid(row=0, column=2, padx=5)

        self.create_button = tk.Button(
            branch_frame, text="Create Branch", command=self.create_branch, state="disabled"
        )
        self.create_button.grid(row=1, column=1, padx=5, pady=5)

        self.delete_button = tk.Button(
            branch_frame, text="Delete Branch", command=self.delete_branch, state="disabled"
        )
        self.delete_button.grid(row=1, column=2, padx=5, pady=5)

        # Git Status and Log Viewer
        self.status_button = tk.Button(
            self, text="Show Git Status", command=self.show_status, state="disabled"
        )
        self.status_button.pack(pady=5)

        self.log_button = tk.Button(
            self, text="Show Git Log", command=self.show_git_log, state="disabled"
        )
        self.log_button.pack(pady=5)

        self.log_text = tk.Text(self, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True)

        self.pack(fill="both", expand=True)

        # Apply app settings
        self.apply_settings()

    def apply_settings(self):
        # Apply settings to this panel
        widgets = self.winfo_children()
        for widget in widgets:
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    self.apply_widget_settings(child)
            else:
                self.apply_widget_settings(widget)

    def apply_widget_settings(self, widget):
        widget_type = widget.winfo_class()
        if widget_type == 'Button':
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )
        elif widget_type == 'Label':
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )
        elif widget_type in ('Entry', 'Text'):
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                insertbackground=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )

    def browse_repo(self):
        repo_path = filedialog.askdirectory()
        if repo_path:
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, repo_path)

    def show_coming_soon(self):
        messagebox.showinfo("Coming Soon", "GitHub authentication is coming soon!")

    # Disable git operations as authentication is not available
    def commit_changes(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def pull_changes(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def push_changes(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def switch_branch(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def create_branch(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def delete_branch(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def show_status(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

    def show_git_log(self):
        messagebox.showwarning("Authentication Required", "Please sign in to GitHub first.")

