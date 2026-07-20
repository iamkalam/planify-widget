import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GObject
from datetime import datetime
import json

class TaskCard(Gtk.Box):
    """Enhanced task card with more features"""
    
    __gsignals__ = {
        'task-toggled': (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
        'task-delete': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'task-edit': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, task):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.task = task
        
        # Extract values from task tuple
        self.task_id = task[0] if task[0] is not None else ""
        self.content = task[1] if len(task) > 1 else ""
        self.description = task[2] if len(task) > 2 else ""
        self.due_raw = task[3] if len(task) > 3 else None
        self.priority = task[4] if len(task) > 4 else 1
        self.checked = bool(task[5]) if len(task) > 5 else False
        self.labels = task[6] if len(task) > 6 else ""
        self.project_id = task[7] if len(task) > 7 else None
        self.pinned = task[8] if len(task) > 8 else 0
        
        # Parse due date
        self.due_date = self.parse_due_date(self.due_raw)
        
        self.add_css_class("task-card")
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        self.build_ui()
    
    def parse_due_date(self, due_raw):
        """Parse the due date from JSON format"""
        if not due_raw:
            return None
        
        try:
            # Try to parse as JSON
            due_data = json.loads(due_raw)
            if isinstance(due_data, dict) and 'date' in due_data:
                date_str = due_data['date']
                if date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d")
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        
        # Try as direct ISO format
        try:
            if isinstance(due_raw, str):
                return datetime.fromisoformat(due_raw.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def build_ui(self):
        """Build the task card UI"""
        # Checkbox
        self.checkbox = Gtk.CheckButton()
        self.checkbox.set_active(self.checked)
        self.checkbox.connect("toggled", self.on_toggled)
        
        # Main content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)
        
        # Task title
        title_label = Gtk.Label(label=self.content)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_wrap(True)
        title_label.add_css_class("task-title")
        
        if self.checked:
            title_label.add_css_class("task-completed")
        
        content_box.append(title_label)
        
        # Task details row
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Priority indicator
        if self.priority and self.priority > 0:
            priority_label = Gtk.Label()
            stars = "⭐" * self.priority
            priority_label.set_label(stars)
            priority_label.add_css_class("task-priority")
            details_box.append(priority_label)
        
        # Due date
        if self.due_date:
            date_str = self.due_date.strftime("%b %d")
            date_label = Gtk.Label(label=date_str)
            date_label.add_css_class("task-due-date")
            
            # Check if overdue
            if self.due_date < datetime.now() and not self.checked:
                date_label.add_css_class("task-overdue")
            
            details_box.append(date_label)
        
        # Labels
        if self.labels:
            for label in self.labels.split(","):
                label = label.strip()
                if label:
                    label_widget = Gtk.Label(label=label)
                    label_widget.add_css_class("task-label")
                    details_box.append(label_widget)
        
        content_box.append(details_box)
        
        # Action buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        # Edit button
        edit_button = Gtk.Button()
        edit_button.set_icon_name("document-edit-symbolic")
        edit_button.add_css_class("flat")
        edit_button.connect("clicked", self.on_edit_clicked)
        
        # Delete button
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.add_css_class("flat")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self.on_delete_clicked)
        
        actions_box.append(edit_button)
        actions_box.append(delete_button)
        
        # Assemble the card
        self.append(self.checkbox)
        self.append(content_box)
        self.append(actions_box)
    
    def on_toggled(self, checkbox):
        """Handle checkbox toggle"""
        checked_state = bool(checkbox.get_active())
        self.emit("task-toggled", self.task_id, checked_state)
    
    def on_edit_clicked(self, button):
        """Handle edit button click"""
        self.emit("task-edit", self.task_id)
    
    def on_delete_clicked(self, button):
        """Handle delete button click"""
        self.emit("task-delete", self.task_id)