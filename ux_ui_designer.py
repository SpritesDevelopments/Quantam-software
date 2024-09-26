# ux_ui_designer.py

import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, simpledialog
import json
import uuid
import copy

class CanvasUI(tk.Frame):
    def __init__(self, master, app_settings):
        super().__init__(master)
        self.app_settings = app_settings
        self.components = {}  # Use a dictionary for easy access by ID

        # Create the main layout frames
        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(self, width=200)
        self.right_frame.pack(side="right", fill="y")

        # Create the canvas in the left frame
        self.canvas = tk.Canvas(self.left_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Properties panel in the right frame
        self.properties_panel = PropertiesPanel(self.right_frame, self)

        # Grid settings
        self.grid_size = 20  # Grid size in pixels
        self.show_grid = True
        self.draw_grid()

        # Bind events for component selection, dragging, and resizing
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)

        # Bind keyboard events
        self.canvas.focus_set()
        self.canvas.bind("<Delete>", self.delete_component)
        self.canvas.bind("<Control-c>", self.copy_component)
        self.canvas.bind("<Control-v>", self.paste_component)
        self.canvas.bind("<Control-z>", self.undo)
        self.canvas.bind("<Control-y>", self.redo)
        self.canvas.bind("<Control-a>", self.select_all)
        self.canvas.bind("<Escape>", self.deselect_component)

        self.selected_component = None
        self.selected_components = []  # For multiple selection
        self.dragging = False
        self.resizing = False
        self.resize_handle = None
        self.offset_x = 0
        self.offset_y = 0

        # Context Menu
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_component)
        self.context_menu.add_command(label="Edit Properties", command=self.edit_component)
        self.context_menu.add_command(label="Bring to Front", command=self.bring_to_front)
        self.context_menu.add_command(label="Send to Back", command=self.send_to_back)
        self.context_menu.add_command(label="Duplicate", command=self.duplicate_component)
        self.context_menu.add_command(label="Group", command=self.group_components)
        self.context_menu.add_command(label="Ungroup", command=self.ungroup_components)
        self.context_menu.add_command(label="Copy", command=self.copy_component)
        self.context_menu.add_command(label="Paste", command=self.paste_component)

        # Undo/Redo Stacks
        self.undo_stack = []
        self.redo_stack = []

        # Clipboard for copy/paste
        self.clipboard = None

        # Apply initial settings
        self.apply_settings()

        # For alignment guides
        self.guide_lines = []

        # For selection rectangle
        self.selection_rect = None

    def apply_settings(self):
        self.canvas.config(bg=self.app_settings['bg_color'])

    def draw_grid(self):
        self.canvas.delete("grid_line")
        if self.show_grid:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            # Vertical lines
            for i in range(0, w, self.grid_size):
                self.canvas.create_line([(i, 0), (i, h)], tag='grid_line', fill="#e0e0e0")
            # Horizontal lines
            for i in range(0, h, self.grid_size):
                self.canvas.create_line([(0, i), (w, i)], tag='grid_line', fill="#e0e0e0")

    def on_canvas_click(self, event):
        # Deselect if clicked on empty space
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items:
            self.deselect_component()
            self.start_selection(event)
        else:
            item = clicked_items[0]
            tags = self.canvas.gettags(item)
            if "resize_handle" in tags:
                self.selected_component = tags[1]  # Second tag is the component ID
                self.resizing = True
                self.start_x = event.x
                self.start_y = event.y
            elif "component" in tags:
                if event.state & 0x0004:  # Shift key is held
                    # Multi-selection
                    self.selected_components.append(tags[1])
                else:
                    self.deselect_component()
                    self.selected_components = [tags[1]]
                self.selected_component = tags[1]
                self.canvas.itemconfig(item, outline="blue")
                # For dragging
                self.dragging = True
                self.offset_x = event.x
                self.offset_y = event.y
                # Add resize handles
                self.add_resize_handles(self.components[self.selected_component])
                # Save the state for undo
                self.save_state()
                # Draw alignment guides
                self.show_alignment_guides()
                # Update properties panel
                self.properties_panel.update_properties(self.components[self.selected_component]['properties'])
        self.canvas.focus_set()

    def on_canvas_drag(self, event):
        if self.resizing and self.selected_component:
            component = self.components[self.selected_component]
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            self.resize_component(component, dx, dy)
            self.start_x = event.x
            self.start_y = event.y
            # Update properties panel
            self.properties_panel.update_properties(component['properties'])
        elif self.dragging and self.selected_components:
            dx = event.x - self.offset_x
            dy = event.y - self.offset_y
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                self.move_component(component, dx, dy)
            self.offset_x = event.x
            self.offset_y = event.y
            # Update alignment guides
            self.show_alignment_guides()
            # Update properties panel
            if self.selected_component:
                self.properties_panel.update_properties(self.components[self.selected_component]['properties'])
        elif self.selection_rect:
            self.update_selection_rect(event)

    def on_canvas_release(self, event):
        self.dragging = False
        self.resizing = False
        if self.selection_rect:
            self.finish_selection(event)
        # Remove alignment guides
        self.clear_alignment_guides()

    def on_right_click(self, event):
        clicked_items = self.canvas.find_withtag("current")
        if clicked_items:
            self.context_menu.post(event.x_root, event.y_root)

    def deselect_component(self, event=None):
        if self.selected_components:
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                for item in component['items']:
                    self.canvas.itemconfig(item, outline="")
                # Remove resize handles
                if 'resize_handles' in component:
                    for handle in component['resize_handles']:
                        self.canvas.delete(handle)
                    del component['resize_handles']
        self.selected_component = None
        self.selected_components = []
        # Clear properties panel
        self.properties_panel.clear_properties()

    def add_component(self, component_type):
        component_id = str(uuid.uuid4())
        if component_type == "Button":
            rect = self.canvas.create_rectangle(50, 50, 150, 80, fill="lightgrey", tags=("component", component_id))
            text = self.canvas.create_text(100, 65, text="Button", tags=("component", component_id))
            items = [rect, text]
            properties = {'type': 'Button', 'text': 'Button', 'fill': 'lightgrey', 'coords': [50, 50, 150, 80]}
        elif component_type == "Label":
            text = self.canvas.create_text(100, 100, text="Label", tags=("component", component_id))
            items = [text]
            bbox = self.canvas.bbox(text)
            properties = {'type': 'Label', 'text': 'Label', 'coords': bbox}
        elif component_type == "Entry":
            rect = self.canvas.create_rectangle(50, 100, 200, 130, fill="white", outline="black", tags=("component", component_id))
            items = [rect]
            properties = {'type': 'Entry', 'fill': 'white', 'coords': [50, 100, 200, 130]}
        elif component_type == "Checkbox":
            box = self.canvas.create_rectangle(50, 150, 70, 170, fill="white", outline="black", tags=("component", component_id))
            check_text = self.canvas.create_text(75, 160, text="Checkbox", anchor="w", tags=("component", component_id))
            items = [box, check_text]
            properties = {'type': 'Checkbox', 'text': 'Checkbox', 'fill': 'white', 'coords': [50, 150, 70, 170]}
        elif component_type == "Radiobutton":
            circle = self.canvas.create_oval(50, 200, 70, 220, fill="white", outline="black", tags=("component", component_id))
            radio_text = self.canvas.create_text(75, 210, text="Option", anchor="w", tags=("component", component_id))
            items = [circle, radio_text]
            properties = {'type': 'Radiobutton', 'text': 'Option', 'fill': 'white', 'coords': [50, 200, 70, 220]}
        elif component_type == "Image":
            image_path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", "*.png;*.jpg;*.gif")])
            if image_path:
                image = tk.PhotoImage(file=image_path)
                img = self.canvas.create_image(100, 100, image=image, anchor="center", tags=("component", component_id))
                self.canvas.image = image  # Keep a reference
                items = [img]
                properties = {'type': 'Image', 'image_path': image_path, 'coords': [100, 100]}
            else:
                return
        elif component_type == "Slider":
            line = self.canvas.create_line(50, 250, 200, 250, fill="gray", width=2, tags=("component", component_id))
            knob = self.canvas.create_oval(45, 245, 55, 255, fill="lightgrey", outline="black", tags=("component", component_id))
            items = [line, knob]
            properties = {'type': 'Slider', 'coords': [50, 250, 200, 250]}
        else:
            return

        self.components[component_id] = {'items': items, 'properties': properties}
        self.save_state()

    def move_component(self, component, dx, dy):
        if self.show_grid:
            dx = round(dx / self.grid_size) * self.grid_size
            dy = round(dy / self.grid_size) * self.grid_size
        for item in component['items']:
            self.canvas.move(item, dx, dy)
        # Move resize handles if present
        if 'resize_handles' in component:
            for handle in component['resize_handles']:
                self.canvas.move(handle, dx, dy)
        # Update coordinates
        properties = component['properties']
        coords = properties.get('coords', [])
        if coords:
            coords = [coord + delta for coord, delta in zip(coords, [dx, dy] * (len(coords) // 2))]
            properties['coords'] = coords

    def resize_component(self, component, dx, dy):
        # Assuming first item is the shape to resize
        item = component['items'][0]
        coords = self.canvas.coords(item)
        if self.show_grid:
            dx = round(dx / self.grid_size) * self.grid_size
            dy = round(dy / self.grid_size) * self.grid_size
        if self.canvas.type(item) in ['rectangle', 'oval']:
            coords[2] += dx
            coords[3] += dy
            self.canvas.coords(item, *coords)
            # Move associated text
            if len(component['items']) > 1:
                text_item = component['items'][1]
                text_coords = [(coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2]
                self.canvas.coords(text_item, *text_coords)
            # Update resize handles
            self.update_resize_handles(component)
            # Update properties
            component['properties']['coords'] = coords
        # Handle other types if needed

    def add_resize_handles(self, component):
        coords = self.canvas.coords(component['items'][0])
        x1, y1, x2, y2 = coords
        handle_size = 8
        handles = []
        # Bottom-right handle
        handle = self.canvas.create_rectangle(
            x2 - handle_size, y2 - handle_size, x2, y2,
            fill="black", tags=("resize_handle", component['items'][0]))
        handles.append(handle)
        component['resize_handles'] = handles

    def update_resize_handles(self, component):
        # Update position of resize handles
        coords = self.canvas.coords(component['items'][0])
        x1, y1, x2, y2 = coords
        handle_size = 8
        handle = component['resize_handles'][0]
        self.canvas.coords(
            handle,
            x2 - handle_size, y2 - handle_size, x2, y2
        )

    def delete_component(self, event=None):
        if self.selected_components:
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                for item in component['items']:
                    self.canvas.delete(item)
                # Delete resize handles
                if 'resize_handles' in component:
                    for handle in component['resize_handles']:
                        self.canvas.delete(handle)
                del self.components[comp_id]
            self.selected_components = []
            self.selected_component = None
            self.save_state()
            # Clear properties panel
            self.properties_panel.clear_properties()

    def duplicate_component(self, event=None):
        if self.selected_components:
            new_selection = []
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                new_comp_id = str(uuid.uuid4())
                new_items = []
                for item in component['items']:
                    item_type = self.canvas.type(item)
                    coords = self.canvas.coords(item)
                    tags = ("component", new_comp_id)
                    options = self.canvas.itemconfig(item)
                    if item_type == 'rectangle':
                        new_item = self.canvas.create_rectangle(*coords, tags=tags)
                    elif item_type == 'oval':
                        new_item = self.canvas.create_oval(*coords, tags=tags)
                    elif item_type == 'text':
                        new_item = self.canvas.create_text(*coords, text=self.canvas.itemcget(item, 'text'), tags=tags)
                    elif item_type == 'line':
                        new_item = self.canvas.create_line(*coords, tags=tags)
                    elif item_type == 'image':
                        # Handle image duplication
                        image_path = component['properties'].get('image_path')
                        if image_path:
                            image = tk.PhotoImage(file=image_path)
                            new_item = self.canvas.create_image(*coords, image=image, tags=tags)
                            self.canvas.image = image
                    else:
                        continue
                    # Apply options
                    for option in options:
                        if option not in ('tags', 'state'):
                            self.canvas.itemconfig(new_item, {option: options[option][-1]})
                    new_items.append(new_item)
                new_properties = copy.deepcopy(component['properties'])
                new_properties['coords'] = [coord + 10 for coord in new_properties['coords']]  # Offset duplicated items
                self.components[new_comp_id] = {'items': new_items, 'properties': new_properties}
                new_selection.append(new_comp_id)
            self.selected_components = new_selection
            self.save_state()

    def copy_component(self, event=None):
        if self.selected_components:
            self.clipboard = []
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                self.clipboard.append(copy.deepcopy(component))

    def paste_component(self, event=None):
        if self.clipboard:
            self.deselect_component()
            for component in self.clipboard:
                new_comp_id = str(uuid.uuid4())
                new_items = []
                for item in component['items']:
                    item_type = self.canvas.type(item)
                    coords = item['coords'] if isinstance(item, dict) else self.canvas.coords(item)
                    coords = [coord + 20 for coord in coords]  # Offset pasted items
                    tags = ("component", new_comp_id)
                    options = item['options'] if isinstance(item, dict) else self.canvas.itemconfig(item)
                    if item_type == 'rectangle':
                        new_item = self.canvas.create_rectangle(*coords, tags=tags)
                    elif item_type == 'oval':
                        new_item = self.canvas.create_oval(*coords, tags=tags)
                    elif item_type == 'text':
                        new_item = self.canvas.create_text(*coords, text=options.get('text', ''), tags=tags)
                    elif item_type == 'line':
                        new_item = self.canvas.create_line(*coords, tags=tags)
                    elif item_type == 'image':
                        # Handle image duplication
                        image_path = component['properties'].get('image_path')
                        if image_path:
                            image = tk.PhotoImage(file=image_path)
                            new_item = self.canvas.create_image(*coords, image=image, tags=tags)
                            self.canvas.image = image
                    else:
                        continue
                    # Apply options
                    for option in options:
                        if option not in ('tags', 'state'):
                            self.canvas.itemconfig(new_item, {option: options[option][-1]})
                    new_items.append(new_item)
                new_properties = copy.deepcopy(component['properties'])
                new_properties['coords'] = [coord + 20 for coord in new_properties['coords']]  # Offset pasted items
                self.components[new_comp_id] = {'items': new_items, 'properties': new_properties}
                self.selected_components.append(new_comp_id)
            self.save_state()

    def edit_component(self, event=None):
        if self.selected_component:
            component = self.components[self.selected_component]
            properties = component['properties']
            # Open a properties dialog
            prop_window = AdvancedPropertyEditor(self, properties)
            self.wait_window(prop_window)
            if prop_window.updated:
                # Update component properties
                self.update_component_properties(component, properties)
                self.save_state()
                # Update properties panel
                self.properties_panel.update_properties(properties)

    def update_component_properties(self, component, properties):
        # Update visual representation based on properties
        if properties['type'] in ['Button', 'Entry', 'Checkbox', 'Radiobutton']:
            # Update text
            if len(component['items']) > 1 and 'text' in properties:
                self.canvas.itemconfig(component['items'][1], text=properties.get('text', ''))
            # Update fill color
            if 'fill' in properties:
                self.canvas.itemconfig(component['items'][0], fill=properties.get('fill', 'white'))
            # Update coordinates
            coords = properties.get('coords')
            if coords:
                self.canvas.coords(component['items'][0], *coords)
                # Update text position
                if len(component['items']) > 1:
                    if properties['type'] in ['Checkbox', 'Radiobutton']:
                        text_coords = [coords[2] + 5, (coords[1] + coords[3]) / 2]
                        self.canvas.coords(component['items'][1], *text_coords)
                    else:
                        text_coords = [(coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2]
                        self.canvas.coords(component['items'][1], *text_coords)
        elif properties['type'] == 'Label':
            if 'text' in properties:
                self.canvas.itemconfig(component['items'][0], text=properties.get('text', ''))
            coords = properties.get('coords')
            if coords:
                self.canvas.coords(component['items'][0], *coords)
        # Update other component types accordingly
        # Update resize handles if necessary
        if 'resize_handles' in component:
            self.update_resize_handles(component)

    def bring_to_front(self, event=None):
        if self.selected_components:
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                for item in component['items']:
                    self.canvas.tag_raise(item)
            self.save_state()

    def send_to_back(self, event=None):
        if self.selected_components:
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                for item in component['items']:
                    self.canvas.tag_lower(item)
            self.save_state()

    def group_components(self):
        if len(self.selected_components) > 1:
            group_id = str(uuid.uuid4())
            group_items = []
            for comp_id in self.selected_components:
                component = self.components[comp_id]
                group_items.extend(component['items'])
                # Update tags
                for item in component['items']:
                    self.canvas.addtag_withtag(f"group_{group_id}", item)
                # Remove individual components
                del self.components[comp_id]
            # Create new group component
            self.components[group_id] = {'items': group_items, 'properties': {'type': 'Group'}}
            self.selected_components = [group_id]
            self.save_state()

    def ungroup_components(self):
        if self.selected_components:
            new_selection = []
            for comp_id in self.selected_components:
                component = self.components.get(comp_id)
                if component and component['properties']['type'] == 'Group':
                    # Remove group tag
                    for item in component['items']:
                        tags = list(self.canvas.gettags(item))
                        tags = [tag for tag in tags if not tag.startswith("group_")]
                        self.canvas.itemconfig(item, tags=tags)
                    # Recreate individual components
                    for item in component['items']:
                        new_comp_id = str(uuid.uuid4())
                        self.components[new_comp_id] = {'items': [item], 'properties': {'type': 'Component'}}
                        new_selection.append(new_comp_id)
                    del self.components[comp_id]
            self.selected_components = new_selection
            self.save_state()

    def select_all(self, event=None):
        self.selected_components = list(self.components.keys())
        for comp_id in self.selected_components:
            component = self.components[comp_id]
            for item in component['items']:
                self.canvas.itemconfig(item, outline="blue")

    def start_selection(self, event):
        self.selection_start = (event.x, event.y)
        self.selection_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, dash=(2, 2), fill='', outline='blue')

    def update_selection_rect(self, event):
        self.canvas.coords(self.selection_rect, self.selection_start[0], self.selection_start[1], event.x, event.y)

    def finish_selection(self, event):
        rect_coords = self.canvas.coords(self.selection_rect)
        self.canvas.delete(self.selection_rect)
        self.selection_rect = None
        self.selected_components = []
        items_in_rect = self.canvas.find_enclosed(*rect_coords)
        for item in items_in_rect:
            tags = self.canvas.gettags(item)
            if "component" in tags:
                comp_id = tags[1]
                if comp_id not in self.selected_components:
                    self.selected_components.append(comp_id)
                    component = self.components[comp_id]
                    for comp_item in component['items']:
                        self.canvas.itemconfig(comp_item, outline="blue")
        # Update properties panel if a single component is selected
        if len(self.selected_components) == 1:
            self.selected_component = self.selected_components[0]
            self.properties_panel.update_properties(self.components[self.selected_component]['properties'])
        else:
            self.selected_component = None
            self.properties_panel.clear_properties()

    def show_alignment_guides(self):
        # Clear existing guides
        self.clear_alignment_guides()
        if not self.selected_components:
            return
        selected_comp = self.components[self.selected_components[0]]
        selected_coords = self.canvas.coords(selected_comp['items'][0])
        selected_center = ((selected_coords[0] + selected_coords[2]) / 2, (selected_coords[1] + selected_coords[3]) / 2)
        for comp_id, component in self.components.items():
            if comp_id not in self.selected_components:
                coords = self.canvas.coords(component['items'][0])
                center = ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)
                # Check for alignment
                if abs(selected_center[0] - center[0]) <= 5:
                    line = self.canvas.create_line(center[0], 0, center[0], self.canvas.winfo_height(), fill='red', dash=(2, 2))
                    self.guide_lines.append(line)
                if abs(selected_center[1] - center[1]) <= 5:
                    line = self.canvas.create_line(0, center[1], self.canvas.winfo_width(), center[1], fill='red', dash=(2, 2))
                    self.guide_lines.append(line)

    def clear_alignment_guides(self):
        for line in self.guide_lines:
            self.canvas.delete(line)
        self.guide_lines.clear()

    def export_html(self):
        # Improved HTML/CSS export
        html = "<!DOCTYPE html>\n<html>\n<head>\n<style>\n"
        html += "body { position: relative; }\n"
        for component_id, component in self.components.items():
            style = ""
            properties = component['properties']
            coords = properties.get('coords', [])
            if properties['type'] == 'Button':
                left = coords[0]
                top = coords[1]
                width = coords[2] - coords[0]
                height = coords[3] - coords[1]
                style += f"#comp_{component_id} {{ position: absolute; left: {left}px; top: {top}px; width: {width}px; height: {height}px; background-color: {properties.get('fill', '#ccc')}; }}\n"
            # Handle other component types
            html += style
        html += "</style>\n</head>\n<body>\n"
        for component_id, component in self.components.items():
            properties = component['properties']
            if properties['type'] == 'Button':
                html += f'<button id="comp_{component_id}">{properties.get("text", "")}</button>\n'
            elif properties['type'] == 'Label':
                html += f'<div id="comp_{component_id}">{properties.get("text", "")}</div>\n'
            # Handle other component types
        html += "</body>\n</html>"
        return html

    def save_design(self):
        design = {'components': self.components}
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(design, f, default=str)
            messagebox.showinfo("Save Design", "Design saved successfully.")

    def load_design(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                design = json.load(f)
            # Clear current canvas
            self.canvas.delete("all")
            self.components.clear()
            # Redraw grid
            self.draw_grid()
            # Load components
            for component_id, component_data in design['components'].items():
                properties = component_data['properties']
                items = []
                if properties['type'] == 'Button':
                    coords = properties['coords']
                    rect = self.canvas.create_rectangle(*coords, fill=properties.get('fill', 'lightgrey'), tags=("component", component_id))
                    text_coords = [(coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2]
                    text = self.canvas.create_text(*text_coords, text=properties.get('text', ''), tags=("component", component_id))
                    items = [rect, text]
                elif properties['type'] == 'Label':
                    coords = properties['coords']
                    text = self.canvas.create_text(*coords, text=properties.get('text', ''), tags=("component", component_id))
                    items = [text]
                # Handle other component types
                self.components[component_id] = {'items': items, 'properties': properties}
            messagebox.showinfo("Load Design", "Design loaded successfully.")
            self.save_state()

    def save_state(self, event=None):
        # Save the current state for undo functionality
        state = json.dumps(self.components, default=str)
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self, event=None):
        if len(self.undo_stack) > 1:
            state = self.undo_stack.pop()
            self.redo_stack.append(state)
            self.restore_state(self.undo_stack[-1])

    def redo(self, event=None):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.restore_state(state)

    def restore_state(self, state):
        # Restore the canvas to a previous state
        self.canvas.delete("all")
        self.components = json.loads(state)
        # Redraw grid
        self.draw_grid()
        # Recreate components
        for component_id, component_data in self.components.items():
            properties = component_data['properties']
            items = []
            if properties['type'] == 'Button':
                coords = properties['coords']
                rect = self.canvas.create_rectangle(*coords, fill=properties.get('fill', 'lightgrey'), tags=("component", component_id))
                text_coords = [(coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2]
                text = self.canvas.create_text(*text_coords, text=properties.get('text', ''), tags=("component", component_id))
                items = [rect, text]
            elif properties['type'] == 'Label':
                coords = properties['coords']
                text = self.canvas.create_text(*coords, text=properties.get('text', ''), tags=("component", component_id))
                items = [text]
            # Handle other component types
            self.components[component_id]['items'] = items
        # Update properties panel if a component is selected
        if self.selected_component:
            self.properties_panel.update_properties(self.components[self.selected_component]['properties'])
        else:
            self.properties_panel.clear_properties()

class PropertiesPanel(tk.Frame):
    def __init__(self, master, canvas_ui):
        super().__init__(master)
        self.canvas_ui = canvas_ui
        self.pack(fill="y", padx=5, pady=5)
        self.create_widgets()

    def create_widgets(self):
        self.title_label = tk.Label(self, text="Properties", font=('Arial', 14, 'bold'))
        self.title_label.pack(pady=5)

        self.entries = {}
        self.vars = {}

    def update_properties(self, properties):
        self.clear_properties()
        for key, value in properties.items():
            if key == 'type':
                continue  # Skip type
            frame = tk.Frame(self)
            frame.pack(fill="x", pady=2)
            label = tk.Label(frame, text=key.capitalize() + ":")
            label.pack(side="left")
            var = tk.StringVar()
            if isinstance(value, list):
                var.set(','.join(map(str, value)))
            else:
                var.set(str(value))
            entry = tk.Entry(frame, textvariable=var)
            entry.pack(side="right", fill="x", expand=True)
            var.trace_add('write', lambda *args, key=key, var=var: self.on_property_change(key, var))
            self.entries[key] = entry
            self.vars[key] = var

    def on_property_change(self, key, var):
        value = var.get()
        properties = self.canvas_ui.components[self.canvas_ui.selected_component]['properties']
        if key == 'coords':
            try:
                coords = list(map(float, value.split(',')))
                properties[key] = coords
                self.canvas_ui.update_component_properties(self.canvas_ui.components[self.canvas_ui.selected_component], properties)
            except ValueError:
                pass  # Invalid coordinates, ignore
        else:
            properties[key] = value
            self.canvas_ui.update_component_properties(self.canvas_ui.components[self.canvas_ui.selected_component], properties)

    def clear_properties(self):
        for widget in self.winfo_children():
            if widget != self.title_label:
                widget.destroy()
        self.entries.clear()
        self.vars.clear()

class AdvancedPropertyEditor(tk.Toplevel):
    def __init__(self, master, properties):
        super().__init__(master)
        self.title("Edit Properties")
        self.properties = properties
        self.updated = False

        self.create_widgets()

    def create_widgets(self):
        row = 0
        self.entries = {}
        for key, value in self.properties.items():
            tk.Label(self, text=key.capitalize() + ":").grid(row=row, column=0, padx=5, pady=5, sticky="w")
            if isinstance(value, list):
                entry_text = ','.join(map(str, value))
            else:
                entry_text = str(value)
            entry = tk.Entry(self)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            entry.insert(0, entry_text)
            self.entries[key] = entry
            row += 1

        self.columnconfigure(1, weight=1)
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)

        save_btn = tk.Button(btn_frame, text="Save", command=self.save_properties)
        save_btn.pack(side="left", padx=5)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack(side="left", padx=5)

    def save_properties(self):
        for key, entry in self.entries.items():
            value = entry.get()
            if key == 'coords':
                try:
                    coords = list(map(float, value.split(',')))
                    self.properties[key] = coords
                except ValueError:
                    messagebox.showerror("Invalid Input", "Coordinates must be a comma-separated list of numbers.")
                    return
            else:
                self.properties[key] = value
        self.updated = True
        self.destroy()

    def cancel(self):
        self.destroy()

class ComponentLibrary(tk.Frame):
    def __init__(self, master, canvas_frame, app_settings):
        super().__init__(master)
        self.app_settings = app_settings
        self.canvas_frame = canvas_frame

        self.label = tk.Label(self, text="Components")
        self.label.pack(pady=10)

        self.button_component = tk.Button(self, text="Button", command=lambda: self.add_component("Button"))
        self.button_component.pack(pady=5)

        self.label_component = tk.Button(self, text="Label", command=lambda: self.add_component("Label"))
        self.label_component.pack(pady=5)

        self.entry_component = tk.Button(self, text="Entry", command=lambda: self.add_component("Entry"))
        self.entry_component.pack(pady=5)

        self.checkbox_component = tk.Button(self, text="Checkbox", command=lambda: self.add_component("Checkbox"))
        self.checkbox_component.pack(pady=5)

        self.radio_component = tk.Button(self, text="Radiobutton", command=lambda: self.add_component("Radiobutton"))
        self.radio_component.pack(pady=5)

        self.slider_component = tk.Button(self, text="Slider", command=lambda: self.add_component("Slider"))
        self.slider_component.pack(pady=5)

        self.image_component = tk.Button(self, text="Image", command=lambda: self.add_component("Image"))
        self.image_component.pack(pady=5)

        # Save and Load Buttons
        self.save_button = tk.Button(self, text="Save Design", command=self.canvas_frame.save_design)
        self.save_button.pack(pady=5)

        self.load_button = tk.Button(self, text="Load Design", command=self.canvas_frame.load_design)
        self.load_button.pack(pady=5)

        # Undo/Redo Buttons
        self.undo_button = tk.Button(self, text="Undo", command=self.canvas_frame.undo)
        self.undo_button.pack(pady=5)

        self.redo_button = tk.Button(self, text="Redo", command=self.canvas_frame.redo)
        self.redo_button.pack(pady=5)

        # Toggle Grid Button
        self.grid_button = tk.Button(self, text="Toggle Grid", command=self.toggle_grid)
        self.grid_button.pack(pady=5)

        # Apply initial settings
        self.apply_settings()

    def apply_settings(self):
        widgets = self.winfo_children()
        for widget in widgets:
            widget.config(
                bg=self.app_settings['bg_color'],
                fg=self.app_settings['text_color'],
                font=(self.app_settings['font_family'], self.app_settings['font_size'])
            )

    def add_component(self, component_type):
        self.canvas_frame.add_component(component_type)

    def toggle_grid(self):
        self.canvas_frame.show_grid = not self.canvas_frame.show_grid
        self.canvas_frame.draw_grid()
