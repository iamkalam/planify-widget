import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from datetime import datetime

class TaskDialog(Adw.Dialog):
    """Dialog for adding or editing tasks"""
    
    def __init__(self, parent, controller, task=None):
        super().__init__()
        
        self.controller = controller
        self.task = task
        self.parent = parent
        
        self.set_title("New Task" if not task else "Edit Task")
        self.set_content_width(400)
        self.set_content_height(500)
        
        self.build_ui()
        
        if task:
            self.load_task_data()
    
    def build_ui(self):
        """Build the dialog UI"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Task content (title)
        content_label = Gtk.Label(label="Task Title")
        content_label.set_halign(Gtk.Align.START)
        content_label.add_css_class("heading")
        
        self.content_entry = Gtk.Entry()
        self.content_entry.set_placeholder_text("Enter task title...")
        self.content_entry.connect("changed", self.on_entry_changed)
        
        main_box.append(content_label)
        main_box.append(self.content_entry)
        
        # Description
        desc_label = Gtk.Label(label="Description")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("heading")
        
        self.desc_entry = Gtk.Entry()
        self.desc_entry.set_placeholder_text("Add description...")
        
        main_box.append(desc_label)
        main_box.append(self.desc_entry)
        
        # Priority
        priority_label = Gtk.Label(label="Priority")
        priority_label.set_halign(Gtk.Align.START)
        priority_label.add_css_class("heading")
        
        self.priority_combo = Gtk.DropDown.new_from_strings([
            "Priority 1 (Low)",
            "Priority 2 (Medium)", 
            "Priority 3 (High)"
        ])
        
        main_box.append(priority_label)
        main_box.append(self.priority_combo)
        
        # Due Date
        due_label = Gtk.Label(label="Due Date")
        due_label.set_halign(Gtk.Align.START)
        due_label.add_css_class("heading")
        
        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.due_entry = Gtk.Entry()
        self.due_entry.set_placeholder_text("YYYY-MM-DD")
        
        self.calendar_button = Gtk.Button()
        self.calendar_button.set_icon_name("x-office-calendar-symbolic")
        self.calendar_button.connect("clicked", self.show_calendar)
        
        date_box.append(self.due_entry)
        date_box.append(self.calendar_button)
        
        main_box.append(due_label)
        main_box.append(date_box)
        
        # Labels/Tags
        labels_label = Gtk.Label(label="Labels")
        labels_label.set_halign(Gtk.Align.START)
        labels_label.add_css_class("heading")
        
        self.labels_entry = Gtk.Entry()
        self.labels_entry.set_placeholder_text("work, personal, urgent...")
        
        main_box.append(labels_label)
        main_box.append(self.labels_entry)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel)
        cancel_button.add_css_class("destructive-action")
        
        self.save_button = Gtk.Button(label="Save")
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self.on_save)
        self.save_button.set_sensitive(False)
        
        button_box.append(cancel_button)
        button_box.append(self.save_button)
        
        main_box.append(button_box)
        
        # Set the content
        self.set_child(main_box)
    
    def load_task_data(self):
        """Load existing task data for editing"""
        if not self.task:
            return
        
        task_id, content, description, due, priority, checked, labels, project_id, pinned = self.task
        
        self.content_entry.set_text(content)
        self.desc_entry.set_text(description or "")
        self.priority_combo.set_selected(priority - 1 if priority > 0 else 0)
        
        # Parse due date from JSON format
        if due:
            import json
            try:
                due_data = json.loads(due)
                if isinstance(due_data, dict) and 'date' in due_data and due_data['date']:
                    self.due_entry.set_text(due_data['date'])
            except (json.JSONDecodeError, ValueError):
                try:
                    # Try as direct date string
                    due_date = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    self.due_entry.set_text(due_date.strftime("%Y-%m-%d"))
                except:
                    pass
        
        if labels:
            self.labels_entry.set_text(labels)
    
    def on_entry_changed(self, entry):
        """Enable/disable save button based on content"""
        self.save_button.set_sensitive(len(entry.get_text().strip()) > 0)
    
    def show_calendar(self, button):
        """Show calendar popover for date selection"""
        popover = Gtk.Popover()
        calendar = Gtk.Calendar()
        
        # Set current date if exists
        current_text = self.due_entry.get_text()
        if current_text:
            try:
                date = datetime.strptime(current_text, "%Y-%m-%d")
                calendar.select_day(GLib.DateTime.new_local(
                    date.year, date.month, date.day, 0, 0, 0
                ))
            except:
                pass
        
        calendar.connect("day-selected", self.on_date_selected, popover)
        popover.set_child(calendar)
        popover.set_parent(button)
        popover.popup()
    
    def on_date_selected(self, calendar, popover):
        """Handle date selection from calendar"""
        date = calendar.get_date()
        self.due_entry.set_text(date.format("%Y-%m-%d"))
        popover.popdown()
    
    def on_save(self, button):
        """Save the task"""
        content = self.content_entry.get_text().strip()
        if not content:
            return
        
        description = self.desc_entry.get_text().strip()
        priority = self.priority_combo.get_selected() + 1
        due_date = self.due_entry.get_text().strip() or None
        labels = self.labels_entry.get_text().strip()
        
        try:
            if self.task:
                # Edit existing task
                task_id = self.task[0]
                self.controller.update_task(
                    task_id,
                    content=content,
                    description=description,
                    priority=priority,
                    due_date=due_date,
                    labels=labels
                )
            else:
                # Add new task
                self.controller.add_task(
                    content=content,
                    description=description,
                    priority=priority,
                    due_date=due_date,
                    labels=labels
                )
            
            # Refresh the parent window
            self.parent.refresh_tasks()
            self.close()
            
        except Exception as e:
            self.show_error(f"Failed to save task: {str(e)}")
    
    def on_cancel(self, button):
        """Cancel the dialog"""
        self.close()
    
    def show_error(self, message):
        """Show error message"""
        dialog = Adw.MessageDialog(
            transient_for=self.parent,
            heading="Error",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()