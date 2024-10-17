import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading

class APITester(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.app_settings = app_settings

        self.create_widgets()
        self.apply_settings()

    def create_widgets(self):
        self.create_config_frame()
        self.create_send_button()
        self.create_response_frame()
        self.create_progress_bar()

    def create_config_frame(self):
        config_frame = ttk.LabelFrame(self, text="Request Configuration")
        config_frame.pack(pady=10, fill="x", padx=10)

        self.create_method_selection(config_frame)
        self.create_url_entry(config_frame)
        self.create_text_areas(config_frame)

        config_frame.grid_columnconfigure(1, weight=1)

    def create_method_selection(self, parent):
        ttk.Label(parent, text="HTTP Method:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.method_var = tk.StringVar(value="GET")
        self.method_menu = ttk.Combobox(
            parent,
            textvariable=self.method_var,
            values=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            state="readonly",
            width=10
        )
        self.method_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def create_url_entry(self, parent):
        ttk.Label(parent, text="URL:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(parent, width=50)
        self.url_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    def create_text_areas(self, parent):
        for row, label in enumerate(["Headers (JSON):", "Parameters (JSON):", "Body (JSON):"], start=2):
            self.create_text_area(parent, label, row)

    def create_text_area(self, parent, label, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="nw")
        text_area = scrolledtext.ScrolledText(parent, height=4, wrap=tk.WORD)
        text_area.grid(row=row, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        setattr(self, f"{label.split()[0].lower()}_text", text_area)

    def create_send_button(self):
        self.send_button = ttk.Button(
            self, text="Send Request", command=self.send_request_threaded
        )
        self.send_button.pack(pady=10)

    def create_response_frame(self):
        response_frame = ttk.LabelFrame(self, text="Response")
        response_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.response_text = scrolledtext.ScrolledText(response_frame, wrap=tk.WORD)
        self.response_text.pack(fill="both", expand=True)

    def create_progress_bar(self):
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=5)

    def apply_settings(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=(self.app_settings['font_family'], self.app_settings['font_size']))
        style.configure('TLabel', background=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])
        style.configure('TEntry', fieldbackground=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])
        style.configure('TButton', background=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])
        style.configure('TLabelframe', background=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])
        style.configure('TLabelframe.Label', background=self.app_settings['bg_color'], foreground=self.app_settings['text_color'])

        for widget in [self.headers_text, self.parameters_text, self.body_text, self.response_text]:
            widget.config(
                font=(self.app_settings['font_family'], self.app_settings['font_size']),
                background=self.app_settings['bg_color'],
                foreground=self.app_settings['text_color'],
                insertbackground=self.app_settings['text_color'],
                selectbackground=self.app_settings['text_color'],
                selectforeground=self.app_settings['bg_color']
            )

    def send_request_threaded(self):
        self.send_button.config(state='disabled')
        self.progress_var.set(0)
        self.progress_bar.start(10)
        
        threading.Thread(target=self.send_request, daemon=True).start()

    def send_request(self):
        try:
            method = self.method_var.get()
            url = self.url_entry.get()
            headers = self.parse_json(self.headers_text.get("1.0", tk.END))
            params = self.parse_json(self.parameters_text.get("1.0", tk.END))
            data = self.parse_json(self.body_text.get("1.0", tk.END))

            if not url:
                raise ValueError("Please enter a URL.")

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            self.display_response(response)
        except (requests.exceptions.RequestException, ValueError) as e:
            self.show_error(f"An error occurred: {e}")
        finally:
            self.send_button.config(state='normal')
            self.progress_bar.stop()
            self.progress_var.set(100)

    def parse_json(self, text):
        try:
            return json.loads(text) if text.strip() else None
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format.")

    def display_response(self, response):
        self.response_text.delete("1.0", tk.END)
        headers = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
        content = response.text

        try:
            content = json.dumps(response.json(), indent=2)
        except json.JSONDecodeError:
            pass

        display_text = (
            f"Status Code: {response.status_code}\n\n"
            f"Headers:\n{headers}\n\n"
            f"Content:\n{content}"
        )
        self.response_text.insert(tk.END, display_text)

    def show_error(self, message):
        messagebox.showerror("Error", message)
