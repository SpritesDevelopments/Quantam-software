import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import git
import requests
import json
import os
import webbrowser
from datetime import datetime

class GitHubAuth:
    """Handle GitHub authentication"""
    def __init__(self):
        self.token = None
        self.user_data = None
        self.api_base = "https://api.github.com"

    def authenticate(self, token):
        headers = {"Authorization": f"token {token}"}
        response = requests.get(f"{self.api_base}/user", headers=headers)
        if response.status_code == 200:
            self.token = token
            self.user_data = response.json()
            return True
        return False

    def get_repos(self):
        if not self.token:
            return []
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(f"{self.api_base}/user/repos", headers=headers)
        return response.json() if response.status_code == 200 else []

    def create_repo(self, name, description="", private=False):
        if not self.token:
            return None
        headers = {"Authorization": f"token {self.token}"}
        data = {
            "name": name,
            "description": description,
            "private": private
        }
        response = requests.post(f"{self.api_base}/user/repos", 
                               headers=headers, json=data)
        return response.json() if response.status_code == 201 else None

class GitManager(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.github = GitHubAuth()
        self.repo = None
        self.create_widgets()

    def create_widgets(self):
        # Create notebook for different Git functions
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.create_login_tab()
        self.create_repo_tab()
        self.create_branches_tab()
        self.create_commits_tab()
        self.create_pr_tab()

    def create_login_tab(self):
        login_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(login_frame, text="GitHub Login")

        # GitHub token entry
        token_frame = ttk.LabelFrame(login_frame, text="Authentication", padding=10)
        token_frame.pack(fill='x', pady=5)

        ttk.Label(token_frame, text="GitHub Token:").pack()
        self.token_entry = ttk.Entry(token_frame, width=50, show='*')
        self.token_entry.pack(fill='x', pady=5)

        btn_frame = ttk.Frame(token_frame)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(btn_frame, text="Get Token", 
                  command=self.open_github_token_page).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Login", 
                  command=self.github_login).pack(side='left', padx=5)

        # User info frame
        self.user_frame = ttk.LabelFrame(login_frame, text="User Info", padding=10)
        self.user_frame.pack(fill='x', pady=5)

    def create_repo_tab(self):
        repo_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(repo_frame, text="Repository")

        # Repository actions
        actions_frame = ttk.LabelFrame(repo_frame, text="Repository Actions", padding=10)
        actions_frame.pack(fill='x', pady=5)

        # Local repository
        ttk.Label(actions_frame, text="Local Repository:").pack()
        path_frame = ttk.Frame(actions_frame)
        path_frame.pack(fill='x', pady=5)

        self.repo_path = ttk.Entry(path_frame, width=50)
        self.repo_path.pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text="Browse", 
                  command=self.browse_repo).pack(side='right', padx=5)

        # Repository operations buttons
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill='x', pady=5)

        operations = [
            ("🏗️ Clone", self.clone_repo),
            ("📂 Init", self.git_init),
            ("➕ Add All", self.git_add),
            ("💾 Commit", self.git_commit),
            ("⬆️ Push", self.git_push),
            ("⬇️ Pull", self.git_pull)
        ]

        for text, cmd in operations:
            ttk.Button(btn_frame, text=text, command=cmd).pack(side='left', padx=2)

        # Repository list
        self.repo_list = ttk.Treeview(repo_frame, columns=('name', 'updated'), 
                                     show='headings', height=10)
        self.repo_list.heading('name', text='Repository')
        self.repo_list.heading('updated', text='Last Updated')
        self.repo_list.pack(fill='both', expand=True, pady=5)

        ttk.Button(repo_frame, text="Create New Repository", 
                  command=self.show_create_repo_dialog).pack(pady=5)

    def create_branches_tab(self):
        branches_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(branches_frame, text="Branches")

        # Branch operations
        ops_frame = ttk.LabelFrame(branches_frame, text="Branch Operations", padding=10)
        ops_frame.pack(fill='x', pady=5)

        # New branch
        branch_frame = ttk.Frame(ops_frame)
        branch_frame.pack(fill='x', pady=5)
        ttk.Label(branch_frame, text="New Branch:").pack(side='left')
        self.new_branch = ttk.Entry(branch_frame, width=30)
        self.new_branch.pack(side='left', padx=5)
        ttk.Button(branch_frame, text="Create", 
                  command=self.create_branch).pack(side='left')

        # Branch list
        self.branch_list = ttk.Treeview(branches_frame, columns=('name', 'current'), 
                                       show='headings', height=10)
        self.branch_list.heading('name', text='Branch Name')
        self.branch_list.heading('current', text='Status')
        self.branch_list.pack(fill='both', expand=True, pady=5)

        # Branch operations buttons
        btn_frame = ttk.Frame(branches_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Checkout", 
                  command=self.checkout_branch).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", 
                  command=self.delete_branch).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Merge", 
                  command=self.merge_branch).pack(side='left', padx=2)

    def create_commits_tab(self):
        commits_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(commits_frame, text="Commits")

        # Commit history
        self.commit_list = ttk.Treeview(commits_frame, 
                                       columns=('hash', 'message', 'author', 'date'),
                                       show='headings', height=15)
        self.commit_list.heading('hash', text='Hash')
        self.commit_list.heading('message', text='Message')
        self.commit_list.heading('author', text='Author')
        self.commit_list.heading('date', text='Date')
        self.commit_list.pack(fill='both', expand=True, pady=5)

        # Commit operations
        btn_frame = ttk.Frame(commits_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="View Details", 
                  command=self.view_commit).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Revert", 
                  command=self.revert_commit).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Cherry Pick", 
                  command=self.cherry_pick).pack(side='left', padx=2)

    def create_pr_tab(self):
        pr_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(pr_frame, text="Pull Requests")

        # PR List
        self.pr_list = ttk.Treeview(pr_frame, 
                                   columns=('number', 'title', 'status', 'author'),
                                   show='headings', height=10)
        self.pr_list.heading('number', text='#')
        self.pr_list.heading('title', text='Title')
        self.pr_list.heading('status', text='Status')
        self.pr_list.heading('author', text='Author')
        self.pr_list.pack(fill='both', expand=True, pady=5)

        # PR operations
        btn_frame = ttk.Frame(pr_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Create PR", 
                  command=self.create_pr).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="View PR", 
                  command=self.view_pr).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Refresh", 
                  command=self.refresh_prs).pack(side='left', padx=2)

    # GitHub authentication methods
    def github_login(self):
        token = self.token_entry.get()
        if self.github.authenticate(token):
            self.update_user_info()
            self.refresh_repos()
            messagebox.showinfo("Success", "GitHub login successful!")
        else:
            messagebox.showerror("Error", "Invalid GitHub token")

    def open_github_token_page(self):
        webbrowser.open("https://github.com/settings/tokens")

    def update_user_info(self):
        for widget in self.user_frame.winfo_children():
            widget.destroy()
        
        if self.github.user_data:
            ttk.Label(self.user_frame, 
                     text=f"Name: {self.github.user_data['name']}").pack()
            ttk.Label(self.user_frame, 
                     text=f"Login: {self.github.user_data['login']}").pack()
            ttk.Label(self.user_frame, 
                     text=f"Repos: {self.github.user_data['public_repos']}").pack()

    # Repository methods
    def browse_repo(self):
        path = filedialog.askdirectory()
        if path:
            self.repo_path.delete(0, tk.END)
            self.repo_path.insert(0, path)
            self.load_repo()

    def load_repo(self):
        try:
            self.repo = git.Repo(self.repo_path.get())
            self.refresh_branches()
            self.refresh_commits()
            self.refresh_prs()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load repository: {str(e)}")

    def clone_repo(self):
        """Clone a remote repository"""
        dialog = tk.Toplevel(self)
        dialog.title("Clone Repository")
        dialog.geometry("500x200")

        # URL entry
        url_frame = ttk.Frame(dialog, padding=5)
        url_frame.pack(fill='x')
        ttk.Label(url_frame, text="Repository URL:").pack(side='left')
        url_entry = ttk.Entry(url_frame, width=50)
        url_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Destination path
        path_frame = ttk.Frame(dialog, padding=5)
        path_frame.pack(fill='x')
        ttk.Label(path_frame, text="Destination:").pack(side='left')
        path_entry = ttk.Entry(path_frame, width=40)
        path_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(path_frame, text="Browse", 
                  command=lambda: path_entry.insert(0, filedialog.askdirectory())
                  ).pack(side='right')

        def do_clone():
            try:
                url = url_entry.get()
                path = path_entry.get()
                git.Repo.clone_from(url, path)
                self.repo_path.delete(0, tk.END)
                self.repo_path.insert(0, path)
                self.load_repo()
                dialog.destroy()
                messagebox.showinfo("Success", "Repository cloned successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clone repository: {str(e)}")

        ttk.Button(dialog, text="Clone", command=do_clone).pack(pady=10)

    def git_init(self):
        """Initialize a new git repository"""
        try:
            path = self.repo_path.get()
            if not os.path.exists(path):
                os.makedirs(path)
            self.repo = git.Repo.init(path)
            self.load_repo()
            messagebox.showinfo("Success", "Repository initialized successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize repository: {str(e)}")

    def git_add(self):
        """Add all changes to the staging area"""
        try:
            self.repo.git.add(A=True)
            messagebox.showinfo("Success", "All changes added to staging area!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add changes: {str(e)}")

    def git_commit(self):
        """Commit changes"""
        dialog = tk.Toplevel(self)
        dialog.title("Commit Changes")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Commit Message:").pack(pady=5)
        message_entry = ttk.Entry(dialog, width=50)
        message_entry.pack(pady=5)

        def do_commit():
            try:
                message = message_entry.get()
                self.repo.index.commit(message)
                self.refresh_commits()
                dialog.destroy()
                messagebox.showinfo("Success", "Changes committed successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to commit changes: {str(e)}")

        ttk.Button(dialog, text="Commit", command=do_commit).pack(pady=10)

    def git_push(self):
        """Push changes to the remote repository"""
        try:
            self.repo.remote().push()
            messagebox.showinfo("Success", "Changes pushed to remote repository!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to push changes: {str(e)}")

    def git_pull(self):
        """Pull changes from the remote repository"""
        try:
            self.repo.remote().pull()
            self.refresh_commits()
            messagebox.showinfo("Success", "Changes pulled from remote repository!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to pull changes: {str(e)}")

    def show_create_repo_dialog(self):
        """Show dialog for creating a new repository"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Repository")
        dialog.geometry("400x300")
        
        # Repository details frame
        details_frame = ttk.LabelFrame(dialog, text="Repository Details", padding=10)
        details_frame.pack(fill='x', padx=10, pady=5)

        # Name
        ttk.Label(details_frame, text="Name:").pack(anchor='w')
        name_entry = ttk.Entry(details_frame, width=40)
        name_entry.pack(fill='x', pady=(0, 5))

        # Description
        ttk.Label(details_frame, text="Description:").pack(anchor='w')
        desc_entry = ttk.Entry(details_frame, width=40)
        desc_entry.pack(fill='x', pady=(0, 5))

        # Privacy setting
        private_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(details_frame, text="Private Repository", 
                       variable=private_var).pack(anchor='w')

        # Local path
        path_frame = ttk.Frame(details_frame)
        path_frame.pack(fill='x', pady=5)
        ttk.Label(path_frame, text="Local Path:").pack(side='left')
        path_entry = ttk.Entry(path_frame)
        path_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(path_frame, text="Browse", 
                  command=lambda: path_entry.insert(0, filedialog.askdirectory())
                  ).pack(side='right')

        def create_repository():
            try:
                # Create on GitHub if authenticated
                if self.github.token:
                    repo_data = self.github.create_repo(
                        name=name_entry.get(),
                        description=desc_entry.get(),
                        private=private_var.get()
                    )
                    if repo_data:
                        # Initialize local repository
                        local_path = path_entry.get()
                        if not local_path:
                            local_path = os.path.join(os.path.expanduser("~"), name_entry.get())
                        
                        # Clone the repository
                        git.Repo.clone_from(repo_data['clone_url'], local_path)
                        
                        # Update UI
                        self.repo_path.delete(0, tk.END)
                        self.repo_path.insert(0, local_path)
                        self.load_repo()
                        self.refresh_repos()
                        
                        dialog.destroy()
                        messagebox.showinfo("Success", "Repository created successfully!")
                else:
                    # Create local only
                    local_path = path_entry.get()
                    if not local_path:
                        messagebox.showerror("Error", "Please specify a local path")
                        return
                    
                    git.Repo.init(local_path)
                    self.repo_path.delete(0, tk.END)
                    self.repo_path.insert(0, local_path)
                    self.load_repo()
                    dialog.destroy()
                    messagebox.showinfo("Success", "Local repository created successfully!")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create repository: {str(e)}")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Create", 
                  command=create_repository).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=dialog.destroy).pack(side='right', padx=5)

    def refresh_repos(self):
        """Refresh the repository list"""
        self.repo_list.delete(*self.repo_list.get_children())
        
        if self.github.token:
            repos = self.github.get_repos()
            for repo in repos:
                self.repo_list.insert('', 'end', values=(
                    repo['name'],
                    repo['updated_at'][:10]
                ))

    def create_branch(self):
        """Create a new branch"""
        try:
            branch_name = self.new_branch.get()
            if not branch_name:
                messagebox.showerror("Error", "Please enter a branch name")
                return
                
            self.repo.git.branch(branch_name)
            self.refresh_branches()
            messagebox.showinfo("Success", f"Branch '{branch_name}' created!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create branch: {str(e)}")

    def checkout_branch(self):
        """Checkout selected branch"""
        selected = self.branch_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a branch")
            return
            
        try:
            branch_name = self.branch_list.item(selected[0])['values'][0]
            self.repo.git.checkout(branch_name)
            self.refresh_branches()
            messagebox.showinfo("Success", f"Switched to branch '{branch_name}'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to checkout branch: {str(e)}")

    def delete_branch(self):
        """Delete selected branch"""
        selected = self.branch_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a branch")
            return
            
        try:
            branch_name = self.branch_list.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Delete branch '{branch_name}'?"):
                self.repo.git.branch('-D', branch_name)
                self.refresh_branches()
                messagebox.showinfo("Success", f"Branch '{branch_name}' deleted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete branch: {str(e)}")

    def merge_branch(self):
        """Merge selected branch into current branch"""
        selected = self.branch_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a branch to merge")
            return
            
        try:
            branch_name = self.branch_list.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Merge branch '{branch_name}' into current branch?"):
                self.repo.git.merge(branch_name)
                self.refresh_commits()
                messagebox.showinfo("Success", f"Branch '{branch_name}' merged!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge branch: {str(e)}")

    def refresh_branches(self):
        """Refresh the branches list"""
        self.branch_list.delete(*self.branch_list.get_children())
        if not self.repo:
            return
            
        try:
            # Get current branch
            current = self.repo.active_branch.name
            
            # List all branches
            for branch in self.repo.heads:
                status = "Current" if branch.name == current else ""
                self.branch_list.insert('', 'end', values=(branch.name, status))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh branches: {str(e)}")

    def refresh_commits(self):
        """Refresh the commit history"""
        self.commit_list.delete(*self.commit_list.get_children())
        if not self.repo:
            return
            
        try:
            for commit in self.repo.iter_commits():
                self.commit_list.insert('', 'end', values=(
                    commit.hexsha[:7],
                    commit.message.split('\n')[0],
                    commit.author.name,
                    commit.committed_datetime.strftime('%Y-%m-%d %H:%M')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh commits: {str(e)}")

    def view_commit(self):
        """View selected commit details"""
        selected = self.commit_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a commit to view")
            return
            
        try:
            commit_hash = self.commit_list.item(selected[0])['values'][0]
            commit = self.repo.commit(commit_hash)
            
            # Create details window
            details = tk.Toplevel(self)
            details.title(f"Commit {commit_hash}")
            details.geometry("800x600")
            
            # Commit info section
            info_frame = ttk.LabelFrame(details, text="Commit Information", padding=10)
            info_frame.pack(fill='x', padx=5, pady=5)
            
            info_text = (
                f"Hash: {commit.hexsha}\n"
                f"Author: {commit.author.name} <{commit.author.email}>\n"
                f"Date: {commit.committed_datetime}\n"
                f"Message:\n{commit.message}"
            )
            
            info = tk.Text(info_frame, height=6, wrap='word')
            info.insert('1.0', info_text)
            info.config(state='disabled')
            info.pack(fill='x')
            
            # Changes section
            changes_frame = ttk.LabelFrame(details, text="Changes", padding=10)
            changes_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Create treeview for changes
            changes_tree = ttk.Treeview(changes_frame, 
                columns=('status', 'path'),
                show='headings')
            changes_tree.heading('status', text='Status')
            changes_tree.heading('path', text='File')
            changes_tree.pack(fill='both', expand=True)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(changes_frame, 
                                    orient='vertical', 
                                    command=changes_tree.yview)
            scrollbar.pack(side='right', fill='y')
            changes_tree.configure(yscrollcommand=scrollbar.set)
            
            # Populate changes
            changes = self.view_commit_changes(commit)
            for status, path in changes:
                changes_tree.insert('', 'end', values=(status, path))
            
            # Add buttons
            btn_frame = ttk.Frame(details)
            btn_frame.pack(fill='x', pady=5)
            
            ttk.Button(btn_frame, text="Revert This Commit",
                      command=lambda: self.revert_specific_commit(commit_hash)
                      ).pack(side='left', padx=5)
            
            ttk.Button(btn_frame, text="Cherry-Pick to Current Branch",
                      command=lambda: self.cherry_pick_specific_commit(commit_hash)
                      ).pack(side='left', padx=5)
            
            ttk.Button(btn_frame, text="Close",
                      command=details.destroy).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view commit: {str(e)}")

    def revert_commit(self):
        """Revert the selected commit"""
        selected = self.commit_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a commit to revert")
            return
            
        try:
            commit_hash = self.commit_list.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Revert commit {commit_hash}?"):
                self.repo.git.revert(commit_hash, no_commit=False)
                self.refresh_commits()
                messagebox.showinfo("Success", f"Commit {commit_hash} reverted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to revert commit: {str(e)}")

    def cherry_pick(self):
        """Cherry pick the selected commit"""
        selected = self.commit_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a commit to cherry-pick")
            return
            
        try:
            commit_hash = self.commit_list.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Cherry-pick commit {commit_hash}?"):
                self.repo.git.cherry_pick(commit_hash)
                self.refresh_commits()
                messagebox.showinfo("Success", f"Commit {commit_hash} cherry-picked!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cherry-pick commit: {str(e)}")

    def view_commit_changes(self, commit):
        """Show the changes in a commit"""
        changes = []
        for parent in commit.parents:
            diff = parent.diff(commit)
            for change in diff:
                status = change.change_type
                path = change.a_path or change.b_path
                changes.append((status, path))
        return changes

    def revert_specific_commit(self, commit_hash):
        """Revert a specific commit"""
        try:
            self.repo.git.revert(commit_hash, no_commit=False)
            self.refresh_commits()
            messagebox.showinfo("Success", f"Commit {commit_hash} reverted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to revert commit: {str(e)}")

    def cherry_pick_specific_commit(self, commit_hash):
        """Cherry pick a specific commit"""
        try:
            self.repo.git.cherry_pick(commit_hash)
            self.refresh_commits()
            messagebox.showinfo("Success", f"Commit {commit_hash} cherry-picked!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cherry-pick commit: {str(e)}")

    def create_pr(self):
        """Create a new pull request"""
        if not self.github.token:
            messagebox.showerror("Error", "Please login to GitHub first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Create Pull Request")
        dialog.geometry("500x400")

        # PR details
        details_frame = ttk.LabelFrame(dialog, text="Pull Request Details", padding=10)
        details_frame.pack(fill='x', padx=10, pady=5)

        # Title
        ttk.Label(details_frame, text="Title:").pack(anchor='w')
        title_entry = ttk.Entry(details_frame, width=50)
        title_entry.pack(fill='x', pady=(0, 5))

        # Description
        ttk.Label(details_frame, text="Description:").pack(anchor='w')
        desc_text = tk.Text(details_frame, height=5)
        desc_text.pack(fill='x', pady=(0, 5))

        # Branch selection
        branch_frame = ttk.Frame(details_frame)
        branch_frame.pack(fill='x', pady=5)

        # Source branch
        ttk.Label(branch_frame, text="From:").pack(side='left')
        source_var = tk.StringVar()
        source_menu = ttk.OptionMenu(branch_frame, source_var, 
                                   self.repo.active_branch.name,
                                   *[b.name for b in self.repo.heads])
        source_menu.pack(side='left', padx=5)

        # Target branch
        ttk.Label(branch_frame, text="To:").pack(side='left', padx=(10, 0))
        target_var = tk.StringVar(value='main')
        target_menu = ttk.OptionMenu(branch_frame, target_var,
                                   'main',
                                   *[b.name for b in self.repo.heads])
        target_menu.pack(side='left', padx=5)

        def submit_pr():
            try:
                # Get repository info from remote URL
                remote_url = self.repo.remote().url
                repo_info = self.parse_github_url(remote_url)
                
                if not repo_info:
                    raise ValueError("Invalid GitHub repository URL")

                # Create PR through GitHub API
                headers = {"Authorization": f"token {self.github.token}"}
                data = {
                    "title": title_entry.get(),
                    "body": desc_text.get('1.0', tk.END),
                    "head": source_var.get(),
                    "base": target_var.get()
                }
                
                response = requests.post(
                    f"{self.github.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/pulls",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 201:
                    pr_data = response.json()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Pull request #{pr_data['number']} created!")
                    self.refresh_prs()
                else:
                    messagebox.showerror("Error", f"Failed to create PR: {response.text}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create pull request: {str(e)}")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Create", 
                  command=submit_pr).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=dialog.destroy).pack(side='right', padx=5)

    def view_pr(self):
        """View selected pull request"""
        selected = self.pr_list.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a pull request")
            return

        try:
            pr_number = self.pr_list.item(selected[0])['values'][0]
            remote_url = self.repo.remote().url
            repo_info = self.parse_github_url(remote_url)
            
            if not repo_info:
                raise ValueError("Invalid GitHub repository URL")

            # Get PR details from GitHub API
            headers = {"Authorization": f"token {self.github.token}"}
            response = requests.get(
                f"{self.github.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/pulls/{pr_number}",
                headers=headers
            )
            
            if response.status_code == 200:
                pr_data = response.json()
                self.show_pr_details(pr_data)
            else:
                messagebox.showerror("Error", f"Failed to fetch PR details: {response.text}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view pull request: {str(e)}")

    def show_pr_details(self, pr_data):
        """Show pull request details in a new window"""
        details = tk.Toplevel(self)
        details.title(f"Pull Request #{pr_data['number']}")
        details.geometry("800x600")

        # PR info section
        info_frame = ttk.LabelFrame(details, text="Pull Request Information", padding=10)
        info_frame.pack(fill='x', padx=5, pady=5)

        info_text = (
            f"Title: {pr_data['title']}\n"
            f"Status: {pr_data['state']}\n"
            f"Author: {pr_data['user']['login']}\n"
            f"Source: {pr_data['head']['label']}\n"
            f"Target: {pr_data['base']['label']}\n"
            f"\nDescription:\n{pr_data['body']}"
        )

        info = tk.Text(info_frame, height=10, wrap='word')
        info.insert('1.0', info_text)
        info.config(state='disabled')
        info.pack(fill='x')

        # Changes section
        changes_frame = ttk.LabelFrame(details, text="Changes", padding=10)
        changes_frame.pack(fill='both', expand=True, padx=5, pady=5)

        changes_tree = ttk.Treeview(changes_frame, 
            columns=('file', 'changes'),
            show='headings')
        changes_tree.heading('file', text='File')
        changes_tree.heading('changes', text='Changes')
        changes_tree.pack(fill='both', expand=True)

        # Get file changes
        headers = {"Authorization": f"token {self.github.token}"}
        files_response = requests.get(pr_data['url'] + '/files', headers=headers)
        
        if files_response.status_code == 200:
            for file in files_response.json():
                changes_tree.insert('', 'end', values=(
                    file['filename'],
                    f"+{file['additions']} -{file['deletions']}"
                ))

        # Action buttons
        btn_frame = ttk.Frame(details)
        btn_frame.pack(fill='x', pady=5)

        if pr_data['state'] == 'open':
            ttk.Button(btn_frame, text="Merge PR",
                      command=lambda: self.merge_pr(pr_data['number'])
                      ).pack(side='left', padx=5)
            
            ttk.Button(btn_frame, text="Close PR",
                      command=lambda: self.close_pr(pr_data['number'])
                      ).pack(side='left', padx=5)

        ttk.Button(btn_frame, text="View on GitHub",
                  command=lambda: webbrowser.open(pr_data['html_url'])
                  ).pack(side='left', padx=5)

        ttk.Button(btn_frame, text="Close",
                  command=details.destroy).pack(side='right', padx=5)

    def refresh_prs(self):
        """Refresh the pull requests list"""
        self.pr_list.delete(*self.pr_list.get_children())
        
        try:
            if not self.github.token or not self.repo:
                return

            remote_url = self.repo.remote().url
            repo_info = self.parse_github_url(remote_url)
            
            if not repo_info:
                return

            headers = {"Authorization": f"token {self.github.token}"}
            response = requests.get(
                f"{self.github.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/pulls",
                headers=headers
            )
            
            if response.status_code == 200:
                for pr in response.json():
                    self.pr_list.insert('', 'end', values=(
                        pr['number'],
                        pr['title'],
                        pr['state'],
                        pr['user']['login']
                    ))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh pull requests: {str(e)}")

    def parse_github_url(self, url):
        """Parse GitHub repository URL to get owner and repo name"""
        import re
        match = re.search(r'github\.com[:/]([^/]+)/([^/]+)(?:\.git)?$', url)
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2)
            }
        return None

    def merge_pr(self, pr_number):
        """Merge a pull request"""
        if messagebox.askyesno("Confirm", "Are you sure you want to merge this pull request?"):
            try:
                remote_url = self.repo.remote().url
                repo_info = self.parse_github_url(remote_url)
                
                headers = {"Authorization": f"token {self.github.token}"}
                response = requests.put(
                    f"{self.github.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/pulls/{pr_number}/merge",
                    headers=headers
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Pull request merged successfully!")
                    self.refresh_prs()
                else:
                    messagebox.showerror("Error", f"Failed to merge PR: {response.text}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to merge pull request: {str(e)}")

    def close_pr(self, pr_number):
        """Close a pull request"""
        if messagebox.askyesno("Confirm", "Are you sure you want to close this pull request?"):
            try:
                remote_url = self.repo.remote().url
                repo_info = self.parse_github_url(remote_url)
                
                headers = {"Authorization": f"token {self.github.token}"}
                response = requests.patch(
                    f"{self.github.api_base}/repos/{repo_info['owner']}/{repo_info['repo']}/pulls/{pr_number}",
                    headers=headers,
                    json={"state": "closed"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Pull request closed successfully!")
                    self.refresh_prs()
                else:
                    messagebox.showerror("Error", f"Failed to close PR: {response.text}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to close pull request: {str(e)}")

    # ...rest of existing methods...
