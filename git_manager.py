import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import webbrowser
import requests
import json
import os

class GitManager(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.app_settings = app_settings
        self.github_token = None

        self.label = ttk.Label(self, text="Git Manager", font=("Helvetica", 16))
        self.label.pack(pady=10)

        # Git Configurations
        config_frame = ttk.Frame(self)
        config_frame.pack(pady=10, fill="x")

        self.repo_label = ttk.Label(config_frame, text="Repository Path:")
        self.repo_label.grid(row=0, column=0, padx=5, sticky="w")

        self.repo_entry = ttk.Entry(config_frame, width=50)
        self.repo_entry.grid(row=0, column=1, padx=5, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        self.browse_button = ttk.Button(
            config_frame, text="Browse", command=self.browse_repo
        )
        self.browse_button.grid(row=0, column=2, padx=5)

        # Authentication Status
        self.auth_status_label = ttk.Label(self, text="Not Signed In", foreground="red")
        self.auth_status_label.pack(pady=5)

        # Authentication Button
        self.auth_button = ttk.Button(
            self, text="Sign In with GitHub", command=self.github_auth
        )
        self.auth_button.pack(pady=5)

        # Commit Message
        self.commit_label = ttk.Label(self, text="Commit Message:")
        self.commit_label.pack(pady=5)
        self.commit_message = ttk.Entry(self, width=50)
        self.commit_message.pack(pady=5, fill="x", padx=10)

        # Buttons for Git Operations
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        self.commit_button = ttk.Button(
            button_frame, text="Commit", command=self.commit_changes, state="disabled"
        )
        self.commit_button.grid(row=0, column=0, padx=5)

        self.pull_button = ttk.Button(
            button_frame, text="Pull", command=self.pull_changes, state="disabled"
        )
        self.pull_button.grid(row=0, column=1, padx=5)

        self.push_button = ttk.Button(
            button_frame, text="Push", command=self.push_changes, state="disabled"
        )
        self.push_button.grid(row=0, column=2, padx=5)

        # Branch Management
        branch_frame = ttk.Frame(self)
        branch_frame.pack(pady=10, fill="x")

        self.branch_label = ttk.Label(branch_frame, text="Branch:")
        self.branch_label.grid(row=0, column=0, padx=5, sticky="w")

        self.branch_entry = ttk.Entry(branch_frame, width=30)
        self.branch_entry.grid(row=0, column=1, padx=5, sticky="w")

        self.switch_button = ttk.Button(
            branch_frame, text="Switch Branch", command=self.switch_branch, state="disabled"
        )
        self.switch_button.grid(row=0, column=2, padx=5)

        self.create_button = ttk.Button(
            branch_frame, text="Create Branch", command=self.create_branch, state="disabled"
        )
        self.create_button.grid(row=1, column=1, padx=5, pady=5)

        self.delete_button = ttk.Button(
            branch_frame, text="Delete Branch", command=self.delete_branch, state="disabled"
        )
        self.delete_button.grid(row=1, column=2, padx=5, pady=5)

        # Git Status and Log Viewer
        self.status_button = ttk.Button(
            self, text="Show Git Status", command=self.show_status, state="disabled"
        )
        self.status_button.pack(pady=5)

        self.log_button = ttk.Button(
            self, text="Show Git Log", command=self.show_git_log, state="disabled"
        )
        self.log_button.pack(pady=5)

        self.log_text = tk.Text(self, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True)

        self.pack(fill="both", expand=True)

        # Apply app settings
        self.apply_settings()

    def apply_settings(self):
        style = ttk.Style()
        style.configure("TButton", 
                        background=self.app_settings['bg_color'],
                        foreground=self.app_settings['text_color'],
                        font=(self.app_settings['font_family'], self.app_settings['font_size']))
        style.configure("TLabel", 
                        background=self.app_settings['bg_color'],
                        foreground=self.app_settings['text_color'],
                        font=(self.app_settings['font_family'], self.app_settings['font_size']))
        style.configure("TEntry", 
                        fieldbackground=self.app_settings['bg_color'],
                        foreground=self.app_settings['text_color'],
                        font=(self.app_settings['font_family'], self.app_settings['font_size']))

        self.log_text.config(
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

    def github_auth(self):
        client_id = "YOUR_GITHUB_CLIENT_ID"
        redirect_uri = "http://localhost:8000/callback"
        auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo"
        webbrowser.open(auth_url)
        
        # Start a simple HTTP server to handle the callback
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Authentication successful! You can close this window.")
                
                query = urllib.parse.urlparse(self.path).query
                query_components = urllib.parse.parse_qs(query)
                code = query_components["code"][0]
                
                # Exchange the code for an access token
                token_url = "https://github.com/login/oauth/access_token"
                data = {
                    "client_id": client_id,
                    "client_secret": "YOUR_GITHUB_CLIENT_SECRET",
                    "code": code,
                    "redirect_uri": redirect_uri
                }
                headers = {"Accept": "application/json"}
                response = requests.post(token_url, data=data, headers=headers)
                token_data = json.loads(response.text)
                
                self.server.access_token = token_data["access_token"]

        server = HTTPServer(('localhost', 8000), CallbackHandler)
        server.handle_request()
        
        self.github_token = server.access_token
        self.update_auth_status()

    def update_auth_status(self):
        if self.github_token:
            self.auth_status_label.config(text="Signed In", foreground="green")
            self.enable_git_operations()
        else:
            self.auth_status_label.config(text="Not Signed In", foreground="red")
            self.disable_git_operations()

    def enable_git_operations(self):
        self.commit_button.config(state="normal")
        self.pull_button.config(state="normal")
        self.push_button.config(state="normal")
        self.switch_button.config(state="normal")
        self.create_button.config(state="normal")
        self.delete_button.config(state="normal")
        self.status_button.config(state="normal")
        self.log_button.config(state="normal")

    def disable_git_operations(self):
        self.commit_button.config(state="disabled")
        self.pull_button.config(state="disabled")
        self.push_button.config(state="disabled")
        self.switch_button.config(state="disabled")
        self.create_button.config(state="disabled")
        self.delete_button.config(state="disabled")
        self.status_button.config(state="disabled")
        self.log_button.config(state="disabled")

    def commit_changes(self):
        repo_path = self.repo_entry.get()
        commit_message = self.commit_message.get()
        if not repo_path or not commit_message:
            messagebox.showerror("Error", "Please provide both repository path and commit message.")
            return
        
        try:
            subprocess.run(["git", "-C", repo_path, "add", "."], check=True)
            subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
            messagebox.showinfo("Success", "Changes committed successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to commit changes: {str(e)}")

    def pull_changes(self):
        repo_path = self.repo_entry.get()
        if not repo_path:
            messagebox.showerror("Error", "Please provide the repository path.")
            return
        
        try:
            result = subprocess.run(["git", "-C", repo_path, "pull"], capture_output=True, text=True, check=True)
            messagebox.showinfo("Pull Result", result.stdout)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to pull changes: {e.stderr}")

    def push_changes(self):
        repo_path = self.repo_entry.get()
        if not repo_path:
            messagebox.showerror("Error", "Please provide the repository path.")
            return
        
        try:
            result = subprocess.run(["git", "-C", repo_path, "push"], capture_output=True, text=True, check=True)
            messagebox.showinfo("Push Result", result.stdout)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to push changes: {e.stderr}")

    def switch_branch(self):
        repo_path = self.repo_entry.get()
        branch_name = self.branch_entry.get()
        if not repo_path or not branch_name:
            messagebox.showerror("Error", "Please provide both repository path and branch name.")
            return
        
        try:
            subprocess.run(["git", "-C", repo_path, "checkout", branch_name], check=True)
            messagebox.showinfo("Success", f"Switched to branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to switch branch: {str(e)}")

    def create_branch(self):
        repo_path = self.repo_entry.get()
        branch_name = self.branch_entry.get()
        if not repo_path or not branch_name:
            messagebox.showerror("Error", "Please provide both repository path and branch name.")
            return
        
        try:
            subprocess.run(["git", "-C", repo_path, "checkout", "-b", branch_name], check=True)
            messagebox.showinfo("Success", f"Created and switched to new branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to create branch: {str(e)}")

    def delete_branch(self):
        repo_path = self.repo_entry.get()
        branch_name = self.branch_entry.get()
        if not repo_path or not branch_name:
            messagebox.showerror("Error", "Please provide both repository path and branch name.")
            return
        
        try:
            subprocess.run(["git", "-C", repo_path, "branch", "-d", branch_name], check=True)
            messagebox.showinfo("Success", f"Deleted branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to delete branch: {str(e)}")

    def show_status(self):
        repo_path = self.repo_entry.get()
        if not repo_path:
            messagebox.showerror("Error", "Please provide the repository path.")
            return
        
        try:
            result = subprocess.run(["git", "-C", repo_path, "status"], capture_output=True, text=True, check=True)
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, result.stdout)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to get git status: {str(e)}")

    def show_git_log(self):
        repo_path = self.repo_entry.get()
        if not repo_path:
            messagebox.showerror("Error", "Please provide the repository path.")
            return
        
        try:
            result = subprocess.run(["git", "-C", repo_path, "log", "--oneline", "-n", "10"], capture_output=True, text=True, check=True)
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, result.stdout)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to get git log: {str(e)}")
