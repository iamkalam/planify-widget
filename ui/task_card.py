import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GObject
from datetime import datetime, timedelta
import json

class TaskCard(Gtk.Box):
    """Enhanced task card with rich display"""
    
    __gsignals__ = {
        'task-toggled': (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
        'task-delete': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'task-edit': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, task):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.task = task
        
        # Extract values from task tuple with safe defaults
        self.task_id = str(task[0]) if task[0] is not None else ""
        self.content = str(task[1]) if len(task) > 1 and task[1] else ""
        self.description = str(task[2]) if len(task) > 2 and task[2] else ""
        self.due_raw = task[3] if len(task) > 3 else None
        self.priority = int(task[4]) if len(task) > 4 and task[4] else 1
        self.checked = bool(task[5]) if len(task) > 5 and task[5] else False
        self.labels = str(task[6]) if len(task) > 6 and task[6] else ""
        self.project_id = task[7] if len(task) > 7 else None
        self.pinned = bool(task[8]) if len(task) > 8 and task[8] else False
        self.project_name = str(task[9]) if len(task) > 9 and task[9] else None
        
        # Parse due date safely
        self.due_date = self.parse_due_date(self.due_raw)
        
        # Add CSS classes based on task state
        self.add_css_class("task-card")
        if self.checked:
            self.add_css_class("task-completed-card")
        if self.pinned:
            self.add_css_class("task-pinned")
        if self.is_overdue():
            self.add_css_class("task-overdue-card")
        
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        self.build_ui()
    
    def parse_due_date(self, due_raw):
        """Parse the due date from JSON format or plain string"""
        if not due_raw:
            return None
        
        # If it's already a datetime object
        if isinstance(due_raw, datetime):
            return due_raw
        
        # Convert to string if bytes
        if isinstance(due_raw, bytes):
            due_raw = due_raw.decode('utf-8', errors='ignore')
        
        if not isinstance(due_raw, str) or not due_raw.strip():
            return None
        
        due_raw = due_raw.strip()
        
        # Try JSON format first: {"date":"2026-07-20",...}
        if due_raw.startswith('{'):
            try:
                due_data = json.loads(due_raw)
                if isinstance(due_data, dict) and 'date' in due_data:
                    date_str = due_data['date']
                    if date_str and date_str.strip():
                        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
            except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                pass
        
        # Try plain date formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S", 
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(due_raw, fmt)
            except (ValueError, TypeError):
                continue
        
        # Try ISO format
        try:
            return datetime.fromisoformat(due_raw.replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            pass
        
        return None
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.checked or not self.due_date:
            return False
        try:
            return self.due_date < datetime.now()
        except:
            return False
    
    def get_relative_date(self):
        """Get human-readable relative date"""
        if not self.due_date:
            return None
        
        try:
            today = datetime.now().date()
            due_date = self.due_date.date()
            diff = due_date - today
            
            if diff.days == 0:
                return "Today"
            elif diff.days == 1:
                return "Tomorrow"
            elif diff.days == -1:
                return "Yesterday"
            elif diff.days < 0:
                return f"{abs(diff.days)} days ago"
            elif diff.days < 7:
                return f"In {diff.days} days"
            else:
                return self.due_date.strftime("%b %d")
        except:
            return self.due_date.strftime("%b %d") if self.due_date else None
    
    def build_ui(self):
        """Build the enhanced task card UI"""
        # Main card container
        card_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        card_box.set_margin_top(8)
        card_box.set_margin_bottom(8)
        card_box.set_margin_start(10)
        card_box.set_margin_end(10)
        
        # Checkbox
        self.checkbox = Gtk.CheckButton()
        self.checkbox.set_active(self.checked)
        self.checkbox.connect("toggled", self.on_toggled)
        self.checkbox.set_valign(Gtk.Align.START)
        self.checkbox.set_margin_top(2)
        
        # Main content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)
        
        # Top row: Pin + Title + Priority
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Pin indicator
        if self.pinned:
            pin_icon = Gtk.Image.new_from_icon_name("pin-symbolic")
            pin_icon.add_css_class("pin-icon")
            title_row.append(pin_icon)
        
        # Task title
        title_label = Gtk.Label(label=self.content)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_wrap(True)
        title_label.set_xalign(0)
        title_label.add_css_class("task-title")
        
        if self.checked:
            title_label.add_css_class("task-completed-text")
        
        title_row.append(title_label)
        
        # Priority badge
        if self.priority and self.priority > 0:
            priority_badge = self.create_priority_badge()
            title_row.append(priority_badge)
        
        content_box.append(title_row)
        
        # Description preview (if exists)
        if self.description and self.description.strip():
            desc_text = self.description.strip()[:100]
            if len(self.description.strip()) > 100:
                desc_text += "..."
            desc_label = Gtk.Label(label=desc_text)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_wrap(True)
            desc_label.set_xalign(0)
            desc_label.add_css_class("task-description")
            content_box.append(desc_label)
        
        # Bottom row: Due date + Labels + Project
        details_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Due date with relative format
        if self.due_date:
            try:
                date_text = self.get_relative_date()
                if date_text:
                    date_label = Gtk.Label(label=f"📅 {date_text}")
                    date_label.add_css_class("task-due-date")
                    
                    if self.is_overdue():
                        date_label.add_css_class("task-overdue")
                    elif date_text == "Today":
                        date_label.add_css_class("task-due-today")
                    elif date_text == "Tomorrow":
                        date_label.add_css_class("task-due-tomorrow")
                    
                    details_row.append(date_label)
            except Exception as e:
                print(f"Error formatting date: {e}")
        
        # Labels
        if self.labels and self.labels.strip():
            try:
                for label in self.labels.split(","):
                    label = label.strip()
                    if label:
                        label_widget = Gtk.Label(label=label)
                        label_widget.add_css_class("task-label")
                        details_row.append(label_widget)
            except:
                pass
        
        # Project name
        if self.project_name and self.project_name.strip():
            try:
                project_label = Gtk.Label(label=f"📁 {self.project_name}")
                project_label.add_css_class("task-project")
                details_row.append(project_label)
            except:
                pass
        
        content_box.append(details_row)
        
        # Action buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        actions_box.set_valign(Gtk.Align.START)
        
        # Edit button
        edit_button = Gtk.Button()
        edit_button.set_icon_name("document-edit-symbolic")
        edit_button.add_css_class("flat")
        edit_button.add_css_class("circular")
        edit_button.set_tooltip_text("Edit task")
        edit_button.connect("clicked", self.on_edit_clicked)
        
        # Delete button
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.add_css_class("flat")
        delete_button.add_css_class("circular")
        delete_button.add_css_class("destructive-action")
        delete_button.set_tooltip_text("Delete task")
        delete_button.connect("clicked", self.on_delete_clicked)
        
        actions_box.append(edit_button)
        actions_box.append(delete_button)
        
        # Assemble the card
        card_box.append(self.checkbox)
        card_box.append(content_box)
        card_box.append(actions_box)
        
        self.append(card_box)
    
    def create_priority_badge(self):
        """Create a colored priority badge"""
        badge = Gtk.Label()
        
        try:
            if self.priority == 3:
                badge.set_label("🔴")
                badge.set_tooltip_text("High Priority")
            elif self.priority == 2:
                badge.set_label("🟡")
                badge.set_tooltip_text("Medium Priority")
            else:
                badge.set_label("🟢")
                badge.set_tooltip_text("Low Priority")
        except:
            badge.set_label("⚪")
            badge.set_tooltip_text("Priority")
        
        badge.add_css_class("priority-badge")
        return badge
    
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