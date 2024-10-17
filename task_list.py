import tkinter as tk
from tkinter import messagebox
import json

class TaskList(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)  # Use master directly
        self.app_settings = app_settings

        self.tasks = []
        self.load_tasks()

        # Task Entry
        self.task_entry = tk.Entry(self)
        self.task_entry.pack(pady=10, padx=10, fill="x")

        # Add Task Button
        self.add_button = tk.Button(
            self, text="Add Task", command=self.add_task
        )
        self.add_button.pack(pady=5)

        # Task Listbox
        self.task_listbox = tk.Listbox(self)
        self.task_listbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.task_listbox.bind('<Double-Button-1>', self.toggle_task_completion)

        # Remove Task Button
        self.remove_button = tk.Button(
            self, text="Remove Task", command=self.remove_task
        )
        self.remove_button.pack(pady=5)

        # Save and Load Buttons
        self.save_button = tk.Button(
            self, text="Save Tasks", command=self.save_tasks
        )
        self.save_button.pack(pady=5)

        self.load_button = tk.Button(
            self, text="Load Tasks", command=self.load_tasks
        )
        self.load_button.pack(pady=5)

        self.pack(fill="both", expand=True)

        # Populate the listbox with existing tasks
        self.refresh_task_listbox()

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        # Apply settings to this panel
        widgets = self.winfo_children()
        for widget in widgets:
            self.apply_widget_settings(widget)
        # Update listbox items
        self.refresh_task_listbox()

    def apply_widget_settings(self, widget):
        widget_type = widget.winfo_class()
        if widget_type == 'Button':
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                activebackground=self.app_settings['bg_color'],
                activeforeground=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )
        elif widget_type == 'Label':
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )
        elif widget_type == 'Entry' or widget_type == 'Listbox':
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                selectbackground=self.app_settings['bg_color'],
                selectforeground=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            self.tasks.append({'text': task_text, 'completed': False})
            self.task_entry.delete(0, tk.END)
            self.refresh_task_listbox()
        else:
            messagebox.showwarning("Warning", "Please enter a task.")

    def remove_task(self):
        selected_indices = self.task_listbox.curselection()
        if selected_indices:
            for index in reversed(selected_indices):
                del self.tasks[index]
            self.refresh_task_listbox()
        else:
            messagebox.showwarning("Warning", "Please select a task to remove.")

    def toggle_task_completion(self, event):
        selected_index = self.task_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            self.tasks[index]['completed'] = not self.tasks[index]['completed']
            self.refresh_task_listbox()

    def refresh_task_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for i, task in enumerate(self.tasks):
            task_text = task['text']
            if task['completed']:
                task_text += " ✔"
            self.task_listbox.insert(tk.END, task_text)
            # Add a right-click menu to each task
            self.task_listbox.itemconfig(i, fg='green' if task['completed'] else 'black')
        self.apply_widget_settings(self.task_listbox)

    def save_tasks(self):
        try:
            with open("tasks.json", "w") as f:
                json.dump(self.tasks, f)
            messagebox.showinfo("Success", "Tasks saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                self.tasks = json.load(f)
            self.refresh_task_listbox()
        except FileNotFoundError:
            self.tasks = []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")
