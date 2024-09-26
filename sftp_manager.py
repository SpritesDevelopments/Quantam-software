import tkinter as tk
from tkinter import filedialog, messagebox
try:
    import paramiko
except ImportError:
    paramiko = None

class SFTPManager(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)  # Use master directly
        self.app_settings = app_settings

        if paramiko is None:
            self.install_paramiko()
            return

        # SFTP Configuration
        config_frame = tk.Frame(self)
        config_frame.pack(pady=10, fill="x")

        self.host_label = tk.Label(config_frame, text="Host:")
        self.host_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.host_entry = tk.Entry(config_frame)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.port_label = tk.Label(config_frame, text="Port:")
        self.port_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.port_entry = tk.Entry(config_frame)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.username_label = tk.Label(config_frame, text="Username:")
        self.username_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = tk.Entry(config_frame)
        self.username_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.password_label = tk.Label(config_frame, text="Password:")
        self.password_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = tk.Entry(config_frame, show="*")
        self.password_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        config_frame.grid_columnconfigure(1, weight=1)

        # Connect Button
        self.connect_button = tk.Button(
            self, text="Connect", command=self.connect_to_server
        )
        self.connect_button.pack(pady=10)

        # File Operations
        file_ops_frame = tk.Frame(self)
        file_ops_frame.pack(pady=10, fill="x")

        self.local_file_button = tk.Button(
            file_ops_frame, text="Select Local File", command=self.select_local_file
        )
        self.local_file_button.grid(row=0, column=0, padx=5, pady=5)

        self.remote_path_label = tk.Label(file_ops_frame, text="Remote Path:")
        self.remote_path_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.remote_path_entry = tk.Entry(file_ops_frame)
        self.remote_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.upload_button = tk.Button(
            file_ops_frame, text="Upload", command=self.upload_file
        )
        self.upload_button.grid(row=2, column=0, padx=5, pady=5)

        self.download_button = tk.Button(
            file_ops_frame, text="Download", command=self.download_file
        )
        self.download_button.grid(row=2, column=1, padx=5, pady=5)

        file_ops_frame.grid_columnconfigure(1, weight=1)

        self.sftp = None

        self.pack(fill="both", expand=True)

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        self.recursive_apply_settings(self)

    def recursive_apply_settings(self, parent_widget):
        for widget in parent_widget.winfo_children():
            self.apply_widget_settings(widget)
            if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.PanedWindow)):
                self.recursive_apply_settings(widget)

    def apply_widget_settings(self, widget):
        from tkinter import ttk

        widget_type = widget.winfo_class()
        config_options = {
            'font': (self.app_settings['font_family'], self.app_settings['font_size']),
        }

        # Skip ttk widgets
        if not isinstance(widget, ttk.Widget):
            config_options['bg'] = self.app_settings['bg_color']
            config_options['fg'] = self.app_settings['text_color']

            # Apply insertbackground only to Entry and Text widgets
            if widget_type in ['Entry', 'Text']:
                config_options['insertbackground'] = self.app_settings['text_color']

        try:
            widget.config(**config_options)
        except tk.TclError:
            # Some widgets might not accept certain options; we can safely ignore these
            pass

    def install_paramiko(self):
        messagebox.showwarning(
            "Paramiko Not Found",
            "Paramiko is not installed. Please install it using 'pip install paramiko' and restart the application."
        )

    def connect_to_server(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not all([host, port, username, password]):
            messagebox.showerror("Error", "Please fill in all connection details.")
            return

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(transport)
            messagebox.showinfo("Success", "Connected to the server.")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def select_local_file(self):
        self.local_file_path = filedialog.askopenfilename()
        if self.local_file_path:
            messagebox.showinfo("File Selected", self.local_file_path)

    def upload_file(self):
        if not self.sftp:
            messagebox.showerror("Error", "Please connect to the server first.")
            return
        if not hasattr(self, 'local_file_path'):
            messagebox.showerror("Error", "Please select a local file to upload.")
            return
        remote_path = self.remote_path_entry.get()
        if not remote_path:
            messagebox.showerror("Error", "Please specify a remote path.")
            return
        try:
            self.sftp.put(self.local_file_path, remote_path)
            messagebox.showinfo("Success", "File uploaded successfully.")
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))

    def download_file(self):
        if not self.sftp:
            messagebox.showerror("Error", "Please connect to the server first.")
            return
        remote_path = self.remote_path_entry.get()
        if not remote_path:
            messagebox.showerror("Error", "Please specify a remote path.")
            return
        local_path = filedialog.asksaveasfilename()
        if not local_path:
            return
        try:
            self.sftp.get(remote_path, local_path)
            messagebox.showinfo("Success", "File downloaded successfully.")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
