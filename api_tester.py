import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import datetime
import webbrowser
from pathlib import Path
import base64
import xml.dom.minidom
import urllib.parse
import ssl
import sqlite3

class RequestCollection:
    def __init__(self, name):
        self.name = name
        self.requests = []

class SavedRequest:
    def __init__(self, name, method, url, headers, body):
        self.name = name
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.created = datetime.datetime.now()

class APITester(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.collections = []
        self.request_history = []
        self.environments = {}
        self.current_env = None
        self.setup_database()
        self.create_widgets()
        self.load_saved_data()

    def create_widgets(self):
        # Create main paned window
        self.main_pane = ttk.PanedWindow(self, orient='horizontal')
        self.main_pane.pack(fill='both', expand=True)

        # Left sidebar for collections and history
        self.create_sidebar()

        # Main content area
        self.content_pane = ttk.PanedWindow(self.main_pane, orient='vertical')
        self.main_pane.add(self.content_pane, weight=3)

        # Create request area
        self.create_request_area()
        
        # Create response area
        self.create_response_area()

    def create_sidebar(self):
        sidebar = ttk.Frame(self.main_pane)
        self.main_pane.add(sidebar, weight=1)

        # Environment selector
        env_frame = ttk.LabelFrame(sidebar, text="Environment", padding=5)
        env_frame.pack(fill='x', padx=5, pady=5)
        
        self.env_var = tk.StringVar(value="No Environment")
        env_menu = ttk.OptionMenu(env_frame, self.env_var, "No Environment")
        env_menu.pack(fill='x')
        
        ttk.Button(env_frame, text="Manage Environments", 
                  command=self.show_env_manager).pack(fill='x', pady=2)

        # Collections
        collections_frame = ttk.LabelFrame(sidebar, text="Collections", padding=5)
        collections_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.collections_tree = ttk.Treeview(collections_frame, show='tree')
        self.collections_tree.pack(fill='both', expand=True)
        self.collections_tree.bind('<Double-1>', self.load_saved_request)

        btn_frame = ttk.Frame(collections_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="New Collection", 
                  command=self.new_collection).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Import", 
                  command=self.import_collection).pack(side='left', padx=2)

        # History
        history_frame = ttk.LabelFrame(sidebar, text="History", padding=5)
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.history_tree = ttk.Treeview(history_frame, 
                                       columns=('method', 'url'),
                                       show='headings',
                                       height=10)
        self.history_tree.heading('method', text='Method')
        self.history_tree.heading('url', text='URL')
        self.history_tree.pack(fill='both', expand=True)
        self.history_tree.bind('<Double-1>', self.load_history_request)

    def create_request_area(self):
        request_frame = ttk.LabelFrame(self.content_pane, text="Request", padding=5)
        self.content_pane.add(request_frame, weight=1)

        # URL and method bar
        url_frame = ttk.Frame(request_frame)
        url_frame.pack(fill='x', pady=5)

        # Method selector with all HTTP methods
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", 
                  "OPTIONS", "TRACE", "CONNECT"]
        self.method_var = tk.StringVar(value="GET")
        method_menu = ttk.OptionMenu(url_frame, self.method_var, "GET", *methods)
        method_menu.pack(side='left')

        # URL with environment variable support
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Request options notebook
        self.request_notebook = ttk.Notebook(request_frame)
        self.request_notebook.pack(fill='both', expand=True)

        # Parameters tab
        params_frame = ttk.Frame(self.request_notebook)
        self.create_params_table(params_frame)
        self.request_notebook.add(params_frame, text='Params')

        # Headers tab
        headers_frame = ttk.Frame(self.request_notebook)
        self.create_headers_table(headers_frame)
        self.request_notebook.add(headers_frame, text='Headers')

        # Authentication tab
        auth_frame = ttk.Frame(self.request_notebook)
        self.create_auth_frame(auth_frame)
        self.request_notebook.add(auth_frame, text='Auth')

        # Body tab
        body_frame = ttk.Frame(self.request_notebook)
        self.create_body_frame(body_frame)
        self.request_notebook.add(body_frame, text='Body')

        # Pre-request Script tab
        script_frame = ttk.Frame(self.request_notebook)
        self.create_script_frame(script_frame)
        self.request_notebook.add(script_frame, text='Pre-request Script')

        # Tests tab
        tests_frame = ttk.Frame(self.request_notebook)
        self.create_tests_frame(tests_frame)
        self.request_notebook.add(tests_frame, text='Tests')

        # Request actions
        actions_frame = ttk.Frame(request_frame)
        actions_frame.pack(fill='x', pady=5)
        
        ttk.Button(actions_frame, text="Send", 
                  command=self.send_request).pack(side='left', padx=2)
        ttk.Button(actions_frame, text="Save", 
                  command=self.save_request).pack(side='left', padx=2)
        ttk.Button(actions_frame, text="Generate Code", 
                  command=self.generate_code).pack(side='left', padx=2)

    def create_response_area(self):
        response_frame = ttk.LabelFrame(self.content_pane, text="Response", padding=5)
        self.content_pane.add(response_frame, weight=1)

        # Response info bar
        info_frame = ttk.Frame(response_frame)
        info_frame.pack(fill='x')
        
        self.status_label = ttk.Label(info_frame, text="Status: ")
        self.status_label.pack(side='left')
        
        self.time_label = ttk.Label(info_frame, text="Time: ")
        self.time_label.pack(side='left', padx=10)
        
        self.size_label = ttk.Label(info_frame, text="Size: ")
        self.size_label.pack(side='left', padx=10)

        # Response notebook
        self.response_notebook = ttk.Notebook(response_frame)
        self.response_notebook.pack(fill='both', expand=True)

        # Body tab with format options
        body_frame = ttk.Frame(self.response_notebook)
        self.create_response_body(body_frame)
        self.response_notebook.add(body_frame, text='Body')

        # Headers tab
        headers_frame = ttk.Frame(self.response_notebook)
        self.create_response_headers(headers_frame)
        self.response_notebook.add(headers_frame, text='Headers')

        # Cookies tab
        cookies_frame = ttk.Frame(self.response_notebook)
        self.create_response_cookies(cookies_frame)
        self.response_notebook.add(cookies_frame, text='Cookies')

        # Test Results tab
        test_results_frame = ttk.Frame(self.response_notebook)
        self.create_test_results(test_results_frame)
        self.response_notebook.add(test_results_frame, text='Test Results')

    def setup_database(self):
        """Setup the SQLite database for storing requests and collections"""
        self.conn = sqlite3.connect('api_tester.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY,
                collection_id INTEGER,
                name TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                body TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id) REFERENCES collections (id)
            )
        ''')
        self.conn.commit()

    def load_saved_data(self):
        """Load saved collections and requests from the database"""
        self.cursor.execute('SELECT * FROM collections')
        collections = self.cursor.fetchall()
        for collection in collections:
            collection_obj = RequestCollection(collection[1])
            self.collections.append(collection_obj)
            self.cursor.execute('SELECT * FROM requests WHERE collection_id = ?', (collection[0],))
            requests = self.cursor.fetchall()
            for req in requests:
                request_obj = SavedRequest(req[2], req[3], req[4], json.loads(req[5]), req[6])
                collection_obj.requests.append(request_obj)
        self.populate_collections_tree()

    def populate_collections_tree(self):
        """Populate the collections tree with saved collections and requests"""
        for collection in self.collections:
            collection_node = self.collections_tree.insert('', 'end', text=collection.name)
            for request in collection.requests:
                self.collections_tree.insert(collection_node, 'end', text=request.name)

    def save_request(self):
        """Save the current request to the database"""
        name = self.url_entry.get()
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = json.dumps(self.get_headers())
        body = self.get_body()

        collection_id = self.get_selected_collection_id()
        if collection_id is None:
            messagebox.showerror("Error", "Please select a collection to save the request")
            return

        self.cursor.execute('''
            INSERT INTO requests (collection_id, name, method, url, headers, body)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (collection_id, name, method, url, headers, body))
        self.conn.commit()
        messagebox.showinfo("Success", "Request saved successfully!")

    def get_selected_collection_id(self):
        """Get the ID of the selected collection"""
        selected_item = self.collections_tree.selection()
        if selected_item:
            collection_name = self.collections_tree.item(selected_item[0], 'text')
            self.cursor.execute('SELECT id FROM collections WHERE name = ?', (collection_name,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
        return None

    def get_headers(self):
        """Get headers from the headers table"""
        headers = {}
        for child in self.headers_table.get_children():
            key, value = self.headers_table.item(child, 'values')
            headers[key] = value
        return headers

    def get_body(self):
        """Get the request body"""
        return self.body_text.get('1.0', tk.END).strip()

    def new_collection(self):
        """Create a new collection"""
        dialog = tk.Toplevel(self)
        dialog.title("New Collection")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="Collection Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)

        def create_collection():
            name = name_entry.get()
            if name:
                self.cursor.execute('INSERT INTO collections (name) VALUES (?)', (name,))
                self.conn.commit()
                collection = RequestCollection(name)
                self.collections.append(collection)
                self.populate_collections_tree()
                dialog.destroy()
                messagebox.showinfo("Success", "Collection created successfully!")
            else:
                messagebox.showerror("Error", "Collection name cannot be empty")

        ttk.Button(dialog, text="Create", command=create_collection).pack(pady=5)

    def import_collection(self):
        """Import a collection from a JSON file"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                collection_name = data.get('name')
                requests = data.get('requests', [])
                if collection_name:
                    self.cursor.execute('INSERT INTO collections (name) VALUES (?)', (collection_name,))
                    collection_id = self.cursor.lastrowid
                    for req in requests:
                        self.cursor.execute('''
                            INSERT INTO requests (collection_id, name, method, url, headers, body)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (collection_id, req['name'], req['method'], req['url'], json.dumps(req['headers']), req['body']))
                    self.conn.commit()
                    collection = RequestCollection(collection_name)
                    for req in requests:
                        request_obj = SavedRequest(req['name'], req['method'], req['url'], req['headers'], req['body'])
                        collection.requests.append(request_obj)
                    self.collections.append(collection)
                    self.populate_collections_tree()
                    messagebox.showinfo("Success", "Collection imported successfully!")
                else:
                    messagebox.showerror("Error", "Invalid collection format")

    def load_saved_request(self, event):
        """Load a saved request into the request area"""
        selected_item = self.collections_tree.selection()
        if selected_item:
            request_name = self.collections_tree.item(selected_item[0], 'text')
            for collection in self.collections:
                for request in collection.requests:
                    if request.name == request_name:
                        self.method_var.set(request.method)
                        self.url_entry.delete(0, tk.END)
                        self.url_entry.insert(0, request.url)
                        self.set_headers(request.headers)
                        self.body_text.delete('1.0', tk.END)
                        self.body_text.insert('1.0', request.body)
                        return

    def load_history_request(self, event):
        """Load a request from the history into the request area"""
        selected_item = self.history_tree.selection()
        if selected_item:
            method, url = self.history_tree.item(selected_item[0], 'values')
            self.method_var.set(method)
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            # Load headers and body from history if needed

    def set_headers(self, headers):
        """Set headers in the headers table"""
        self.headers_table.delete(*self.headers_table.get_children())
        for key, value in headers.items():
            self.headers_table.insert('', 'end', values=(key, value))

    def show_env_manager(self):
        """Show the environment manager dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Manage Environments")
        dialog.geometry("400x300")

        # Environment list
        env_list_frame = ttk.Frame(dialog)
        env_list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.env_listbox = tk.Listbox(env_list_frame)
        self.env_listbox.pack(side='left', fill='both', expand=True)
        self.env_listbox.bind('<<ListboxSelect>>', self.load_environment)

        env_scrollbar = ttk.Scrollbar(env_list_frame, orient='vertical', command=self.env_listbox.yview)
        env_scrollbar.pack(side='right', fill='y')
        self.env_listbox.config(yscrollcommand=env_scrollbar.set)

        # Environment details
        details_frame = ttk.Frame(dialog)
        details_frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(details_frame, text="Environment Name:").pack(anchor='w')
        self.env_name_entry = ttk.Entry(details_frame)
        self.env_name_entry.pack(fill='x', pady=5)

        ttk.Label(details_frame, text="Variables (key=value):").pack(anchor='w')
        self.env_vars_text = tk.Text(details_frame, height=10)
        self.env_vars_text.pack(fill='both', expand=True, pady=5)

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="Save", command=self.save_environment).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_environment).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="New", command=self.new_environment).pack(side='right', padx=5)

        self.load_environments()

    def load_environments(self):
        """Load environments into the listbox"""
        self.env_listbox.delete(0, tk.END)
        for env_name in self.environments.keys():
            self.env_listbox.insert(tk.END, env_name)

    def load_environment(self, event):
        """Load selected environment details"""
        selected = self.env_listbox.curselection()
        if selected:
            env_name = self.env_listbox.get(selected[0])
            self.env_name_entry.delete(0, tk.END)
            self.env_name_entry.insert(0, env_name)
            env_vars = self.environments[env_name]
            self.env_vars_text.delete('1.0', tk.END)
            for key, value in env_vars.items():
                self.env_vars_text.insert(tk.END, f"{key}={value}\n")

    def save_environment(self):
        """Save the current environment"""
        env_name = self.env_name_entry.get()
        env_vars = self.env_vars_text.get('1.0', tk.END).strip().split('\n')
        env_vars_dict = {}
        for var in env_vars:
            if '=' in var:
                key, value = var.split('=', 1)
                env_vars_dict[key.strip()] = value.strip()
        self.environments[env_name] = env_vars_dict
        self.load_environments()
        messagebox.showinfo("Success", "Environment saved successfully!")

    def delete_environment(self):
        """Delete the selected environment"""
        selected = self.env_listbox.curselection()
        if selected:
            env_name = self.env_listbox.get(selected[0])
            del self.environments[env_name]
            self.load_environments()
            self.env_name_entry.delete(0, tk.END)
            self.env_vars_text.delete('1.0', tk.END)
            messagebox.showinfo("Success", "Environment deleted successfully!")

    def new_environment(self):
        """Create a new environment"""
        self.env_name_entry.delete(0, tk.END)
        self.env_vars_text.delete('1.0', tk.END)
        self.env_name_entry.focus()

    def create_params_table(self, parent):
        """Create parameters table"""
        self.params_table = ttk.Treeview(parent, columns=('key', 'value'), show='headings')
        self.params_table.heading('key', text='Key')
        self.params_table.heading('value', text='Value')
        self.params_table.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_param).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_param).pack(side='left', padx=2)

    def create_headers_table(self, parent):
        """Create headers table"""
        self.headers_table = ttk.Treeview(parent, columns=('key', 'value'), show='headings')
        self.headers_table.heading('key', text='Key')
        self.headers_table.heading('value', text='Value')
        self.headers_table.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_header).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_header).pack(side='left', padx=2)

    def create_auth_frame(self, parent):
        """Create authentication frame"""
        auth_frame = ttk.Frame(parent)
        auth_frame.pack(fill='both', expand=True)

        ttk.Label(auth_frame, text="Authentication Type:").pack(anchor='w')
        self.auth_type = tk.StringVar(value="None")
        auth_types = ["None", "Basic Auth", "Bearer Token", "OAuth 2.0"]
        for auth_type in auth_types:
            ttk.Radiobutton(auth_frame, text=auth_type, value=auth_type, variable=self.auth_type).pack(anchor='w')

        self.auth_details_frame = ttk.Frame(auth_frame)
        self.auth_details_frame.pack(fill='both', expand=True)

        self.auth_type.trace('w', self.update_auth_details)

    def create_body_frame(self, parent):
        """Create body frame"""
        body_frame = ttk.Frame(parent)
        body_frame.pack(fill='both', expand=True)

        ttk.Label(body_frame, text="Body Type:").pack(anchor='w')
        self.body_type = tk.StringVar(value="None")
        body_types = ["None", "Form Data", "JSON", "Raw"]
        for body_type in body_types:
            ttk.Radiobutton(body_frame, text=body_type, value=body_type, variable=self.body_type).pack(anchor='w')

        self.body_text = tk.Text(body_frame, height=10)
        self.body_text.pack(fill='both', expand=True, pady=5)

    def create_script_frame(self, parent):
        """Create pre-request script frame"""
        script_frame = ttk.Frame(parent)
        script_frame.pack(fill='both', expand=True)

        self.script_text = tk.Text(script_frame, height=10)
        self.script_text.pack(fill='both', expand=True, pady=5)

    def create_tests_frame(self, parent):
        """Create tests frame"""
        tests_frame = ttk.Frame(parent)
        tests_frame.pack(fill='both', expand=True)

        self.tests_text = tk.Text(tests_frame, height=10)
        self.tests_text.pack(fill='both', expand=True, pady=5)

    def add_param(self):
        """Add a new parameter"""
        self.params_table.insert('', 'end', values=('', ''))

    def remove_param(self):
        """Remove selected parameter"""
        selected_item = self.params_table.selection()
        if selected_item:
            self.params_table.delete(selected_item)

    def add_header(self):
        """Add a new header"""
        self.headers_table.insert('', 'end', values=('', ''))

    def remove_header(self):
        """Remove selected header"""
        selected_item = self.headers_table.selection()
        if selected_item:
            self.headers_table.delete(selected_item)

    def update_auth_details(self, *args):
        """Update authentication details based on selected type"""
        for widget in self.auth_details_frame.winfo_children():
            widget.destroy()

        auth_type = self.auth_type.get()
        if auth_type == "Basic Auth":
            ttk.Label(self.auth_details_frame, text="Username:").pack(anchor='w')
            self.auth_username = ttk.Entry(self.auth_details_frame)
            self.auth_username.pack(fill='x', pady=2)

            ttk.Label(self.auth_details_frame, text="Password:").pack(anchor='w')
            self.auth_password = ttk.Entry(self.auth_details_frame, show='*')
            self.auth_password.pack(fill='x', pady=2)

        elif auth_type == "Bearer Token":
            ttk.Label(self.auth_details_frame, text="Token:").pack(anchor='w')
            self.auth_token = ttk.Entry(self.auth_details_frame)
            self.auth_token.pack(fill='x', pady=2)

        elif auth_type == "OAuth 2.0":
            ttk.Label(self.auth_details_frame, text="Client ID:").pack(anchor='w')
            self.auth_client_id = ttk.Entry(self.auth_details_frame)
            self.auth_client_id.pack(fill='x', pady=2)

            ttk.Label(self.auth_details_frame, text="Client Secret:").pack(anchor='w')
            self.auth_client_secret = ttk.Entry(self.auth_details_frame, show='*')
            self.auth_client_secret.pack(fill='x', pady=2)

            ttk.Label(self.auth_details_frame, text="Access Token URL:").pack(anchor='w')
            self.auth_token_url = ttk.Entry(self.auth_details_frame)
            self.auth_token_url.pack(fill='x', pady=2)

    def send_request(self):
        """Send the HTTP request and display the response"""
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = self.get_headers()
        body = self.get_body()

        try:
            # Send the request
            response = requests.request(method, url, headers=headers, data=body)
            
            # Display response details
            self.status_label.config(text=f"Status: {response.status_code}")
            self.time_label.config(text=f"Time: {response.elapsed.total_seconds()}s")
            self.size_label.config(text=f"Size: {len(response.content)} bytes")
            
            # Display response body
            self.display_response_body(response)
            
            # Display response headers
            self.display_response_headers(response)
            
            # Display response cookies
            self.display_response_cookies(response)
            
            # Run tests
            self.run_tests(response)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send request: {str(e)}")

    def display_response_body(self, response):
        """Display the response body in the response tab"""
        self.response_body_text.delete('1.0', tk.END)
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            try:
                json_content = json.dumps(response.json(), indent=2)
                self.response_body_text.insert('1.0', json_content)
            except json.JSONDecodeError:
                self.response_body_text.insert('1.0', response.text)
        elif 'text/xml' in content_type or 'application/xml' in content_type:
            try:
                xml_content = xml.dom.minidom.parseString(response.text).toprettyxml()
                self.response_body_text.insert('1.0', xml_content)
            except Exception:
                self.response_body_text.insert('1.0', response.text)
        else:
            self.response_body_text.insert('1.0', response.text)

    def display_response_headers(self, response):
        """Display the response headers in the response tab"""
        self.response_headers_text.delete('1.0', tk.END)
        for key, value in response.headers.items():
            self.response_headers_text.insert('1.0', f"{key}: {value}\n")

    def display_response_cookies(self, response):
        """Display the response cookies in the response tab"""
        self.response_cookies_text.delete('1.0', tk.END)
        for key, value in response.cookies.items():
            self.response_cookies_text.insert('1.0', f"{key}: {value}\n")

    def run_tests(self, response):
        """Run tests on the response"""
        self.test_results_text.delete('1.0', tk.END)
        tests = self.tests_text.get('1.0', tk.END).strip()
        
        if tests:
            try:
                exec(tests, {'response': response, 'print': self.print_test_result})
            except Exception as e:
                self.print_test_result(f"Test execution error: {str(e)}")

    def print_test_result(self, result):
        """Print test result to the test results text area"""
        self.test_results_text.insert('end', f"{result}\n")

    def create_response_body(self, parent):
        """Create response body tab"""
        self.response_body_text = tk.Text(parent, wrap='none')
        self.response_body_text.pack(fill='both', expand=True)

    def create_response_headers(self, parent):
        """Create response headers tab"""
        self.response_headers_text = tk.Text(parent, wrap='none')
        self.response_headers_text.pack(fill='both', expand=True)

    def create_response_cookies(self, parent):
        """Create response cookies tab"""
        self.response_cookies_text = tk.Text(parent, wrap='none')
        self.response_cookies_text.pack(fill='both', expand=True)

    def create_test_results(self, parent):
        """Create test results tab"""
        self.test_results_text = tk.Text(parent, wrap='none')
        self.test_results_text.pack(fill='both', expand=True)

    def generate_code(self):
        """Generate code snippet for the current request"""
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = self.get_headers()
        body = self.get_body()

        code_snippet = f"""import requests

url = "{url}"
headers = {json.dumps(headers, indent=4)}
data = {json.dumps(body)}

response = requests.request("{method}", url, headers=headers, data=data)
print(response.text)
"""

        # Display the generated code in a new window
        dialog = tk.Toplevel(self)
        dialog.title("Generated Code")
        dialog.geometry("600x400")

        code_text = tk.Text(dialog, wrap='none')
        code_text.pack(fill='both', expand=True)
        code_text.insert('1.0', code_snippet)
        code_text.config(state='disabled')

        ttk.Button(dialog, text="Copy to Clipboard", command=lambda: self.copy_to_clipboard(code_snippet)).pack(pady=5)

    def copy_to_clipboard(self, text):
        """Copy the given text to the clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Success", "Code copied to clipboard!")

    # ...rest of existing methods...
