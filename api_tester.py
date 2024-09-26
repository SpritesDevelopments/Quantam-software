import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json

class APITester(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)  # Use master directly
        self.app_settings = app_settings

        # Request Configuration
        config_frame = tk.Frame(self)
        config_frame.pack(pady=10, fill="x")

        # Method Selection
        self.method_label = tk.Label(config_frame, text="HTTP Method:")
        self.method_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.method_var = tk.StringVar(value="GET")
        self.method_menu = ttk.Combobox(
            config_frame,
            textvariable=self.method_var,
            values=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            state="readonly",
        )
        self.method_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # URL Entry
        self.url_label = tk.Label(config_frame, text="URL:")
        self.url_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.url_entry = tk.Entry(config_frame, width=50)
        self.url_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        # Headers and Parameters
        self.headers_label = tk.Label(config_frame, text="Headers (JSON):")
        self.headers_label.grid(row=2, column=0, padx=5, pady=5, sticky="nw")

        self.headers_text = tk.Text(config_frame, height=4)
        self.headers_text.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.params_label = tk.Label(config_frame, text="Parameters (JSON):")
        self.params_label.grid(row=3, column=0, padx=5, pady=5, sticky="nw")

        self.params_text = tk.Text(config_frame, height=4)
        self.params_text.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Request Body
        self.body_label = tk.Label(config_frame, text="Body (JSON):")
        self.body_label.grid(row=4, column=0, padx=5, pady=5, sticky="nw")

        self.body_text = tk.Text(config_frame, height=6)
        self.body_text.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Send Request Button
        self.send_button = tk.Button(
            self, text="Send Request", command=self.send_request
        )
        self.send_button.pack(pady=10)

        # Response Display
        self.response_text = tk.Text(self, height=15)
        self.response_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.pack(fill="both", expand=True)

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        # Apply settings to all widgets
        widgets = self.winfo_children()
        for widget in widgets:
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    self.apply_widget_settings(child)
            else:
                self.apply_widget_settings(widget)

    def apply_widget_settings(self, widget):
        from tkinter import ttk

        widget_type = widget.winfo_class()
        config_options = {
            'font': (self.app_settings['font_family'], self.app_settings['font_size']),
        }

        # Check if widget is not a ttk widget
        if not isinstance(widget, ttk.Widget):
            config_options['bg'] = self.app_settings['bg_color']
            config_options['fg'] = self.app_settings['text_color']

            # Apply insertbackground only to Entry and Text widgets
            if widget_type in ['Entry', 'Text']:
                config_options['insertbackground'] = self.app_settings['text_color']  # For cursor color

        widget.config(**config_options)

        if widget_type == 'Text':
            widget.config(
                selectbackground=self.app_settings['bg_color'],
                selectforeground=self.app_settings['text_color']
            )

    def send_request(self):
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = self.parse_json(self.headers_text.get("1.0", tk.END))
        params = self.parse_json(self.params_text.get("1.0", tk.END))
        data = self.parse_json(self.body_text.get("1.0", tk.END))

        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            self.display_response(response)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def parse_json(self, text):
        try:
            return json.loads(text) if text.strip() else None
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format.")
            return None

    def display_response(self, response):
        self.response_text.delete("1.0", tk.END)
        headers = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
        content = response.text

        display_text = (
            f"Status Code: {response.status_code}\n\n"
            f"Headers:\n{headers}\n\n"
            f"Content:\n{content}"
        )
        self.response_text.insert(tk.END, display_text)
