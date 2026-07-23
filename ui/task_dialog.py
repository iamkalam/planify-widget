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
        self.set_content_width(420)
        self.set_content_height(520)

        self.build_ui()

        if task:
            self.load_task_data()

    def make_section_label(self, text):
        """Small uppercase-style label used above each field group"""
        label = Gtk.Label(label=text)
        label.set_halign(Gtk.Align.START)
        label.add_css_class("dialog-section-label")
        return label

    def build_ui(self):
        """Build the dialog UI"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Task content (title) — the primary field, given the most emphasis
        main_box.append(self.make_section_label("Task Title"))

        self.content_entry = Gtk.Entry()
        self.content_entry.set_placeholder_text("What needs to be done?")
        self.content_entry.add_css_class("dialog-entry")
        self.content_entry.connect("changed", self.on_entry_changed)

        main_box.append(self.content_entry)

        # Description
        main_box.append(self.make_section_label("Description"))

        self.desc_entry = Gtk.Entry()
        self.desc_entry.set_placeholder_text("Add more detail (optional)...")
        self.desc_entry.add_css_class("dialog-entry")

        main_box.append(self.desc_entry)

        # Priority + Due date side by side to reduce vertical scroll
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.set_homogeneous(True)

        priority_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        priority_col.append(self.make_section_label("Priority"))

        self.priority_combo = Gtk.DropDown.new_from_strings([
            "Priority 1 (Low)",
            "Priority 2 (Medium)",
            "Priority 3 (High)"
        ])
        priority_col.append(self.priority_combo)
        row_box.append(priority_col)

        due_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        due_col.append(self.make_section_label("Due Date"))

        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        date_box.add_css_class("linked")

        self.due_entry = Gtk.Entry()
        self.due_entry.set_placeholder_text("YYYY-MM-DD")
        self.due_entry.set_hexpand(True)

        self.calendar_button = Gtk.Button()
        self.calendar_button.set_icon_name("x-office-calendar-symbolic")
        self.calendar_button.connect("clicked", self.show_calendar)

        date_box.append(self.due_entry)
        date_box.append(self.calendar_button)

        due_col.append(date_box)
        row_box.append(due_col)

        main_box.append(row_box)

        # Labels/Tags
        main_box.append(self.make_section_label("Labels"))

        self.labels_entry = Gtk.Entry()
        self.labels_entry.set_placeholder_text("work, personal, urgent...")
        self.labels_entry.add_css_class("dialog-entry")

        main_box.append(self.labels_entry)

        # Spacer pushes actions to the bottom for consistent placement
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)

        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(4)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel)
        cancel_button.add_css_class("flat")

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

        # Editing an existing task always has a valid title already
        self.save_button.set_sensitive(True)

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