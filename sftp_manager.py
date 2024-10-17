import tkinter as tk
from tkinter import filedialog, messagebox, ttk
try:
    import paramiko
except ImportError:
    paramiko = None

class SFTPManager(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.app_settings = app_settings

        if paramiko is None:
            self.install_paramiko()
            return

        self.create_widgets()
        self.sftp = None
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.apply_settings()
        self.selected_files = []

    def create_widgets(self):
        # SFTP Configuration
        config_frame = ttk.LabelFrame(self, text="SFTP Configuration")
        config_frame.pack(pady=10, fill="x")

        fields = [("Host:", "host"), ("Port:", "port"), ("Username:", "username"), ("Password:", "password")]
        for i, (label_text, attr_name) in enumerate(fields):
            ttk.Label(config_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(config_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            setattr(self, f"{attr_name}_entry", entry)

        self.port_entry.insert(0, "22")
        self.password_entry.config(show="*")

        config_frame.grid_columnconfigure(1, weight=1)

        # Connect Button
        self.connect_button = ttk.Button(
            self, text="Connect", command=self.connect_to_server
        )
        self.connect_button.pack(pady=10)

        # File Operations
        file_ops_frame = ttk.LabelFrame(self, text="File Operations")
        file_ops_frame.pack(pady=10, fill="x")

        self.local_file_button = ttk.Button(
            file_ops_frame, text="Select Local Files", command=self.select_local_files
        )
        self.local_file_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Label(file_ops_frame, text="Remote Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.remote_path_entry = ttk.Entry(file_ops_frame)
        self.remote_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        button_frame = ttk.Frame(file_ops_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.upload_button = ttk.Button(
            button_frame, text="Upload", command=self.upload_files
        )
        self.upload_button.pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        self.download_button = ttk.Button(
            button_frame, text="Download", command=self.download_file
        )
        self.download_button.pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        file_ops_frame.grid_columnconfigure(1, weight=1)

        # Selected Files List
        self.files_listbox = tk.Listbox(self, width=50, height=10)
        self.files_listbox.pack(pady=10, fill="both", expand=True)

        # Add scrollbar to listbox
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.files_listbox.config(yscrollcommand=scrollbar.set)

    def apply_settings(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=(self.app_settings['font_family'], self.app_settings['font_size']))
        style.configure('TLabel', foreground=self.app_settings['text_color'], background=self.app_settings['bg_color'])
        style.configure('TEntry', foreground=self.app_settings['text_color'], fieldbackground=self.app_settings['bg_color'])
        style.configure('TButton', foreground=self.app_settings['text_color'], background=self.app_settings['bg_color'])
        style.configure('TLabelframe', foreground=self.app_settings['text_color'], background=self.app_settings['bg_color'])
        style.configure('TLabelframe.Label', foreground=self.app_settings['text_color'], background=self.app_settings['bg_color'])

        self.configure(background=self.app_settings['bg_color'])
        self.files_listbox.configure(background=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])

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

    def select_local_files(self):
        self.selected_files = filedialog.askopenfilenames()
        self.update_files_list()

    def update_files_list(self):
        self.files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.files_listbox.insert(tk.END, file)

    def upload_files(self):
        if not self.sftp:
            messagebox.showerror("Error", "Please connect to the server first.")
            return
        if not self.selected_files:
            messagebox.showerror("Error", "Please select local files to upload.")
            return
        remote_path = self.remote_path_entry.get()
        if not remote_path:
            messagebox.showerror("Error", "Please specify a remote path.")
            return
        try:
            for local_file_path in self.selected_files:
                remote_file_path = f"{remote_path}/{local_file_path.split('/')[-1]}"
                self.sftp.put(local_file_path, remote_file_path)
            messagebox.showinfo("Success", "Files uploaded successfully.")
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
