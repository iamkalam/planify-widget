import gi
import os 
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio  # Gio must be imported
from controllers.task_controller import TaskController
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.controller = TaskController()
        self._last_stats = None
        self._refresh_pending = False
        
        self.set_title("Planify Widget")
        self.set_default_size(400, 600)
        
        self.build_ui()
        self.refresh_tasks()
        
        # Start file monitoring for live sync
        self.start_file_monitor()
    
    def build_ui(self):
        """Build the main window UI"""
        # Main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header with sync status
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        # Sync status indicator
        self.sync_label = Gtk.Label()
        self.sync_label.set_tooltip_text("Synced with Planify")
        self.sync_label.add_css_class("sync-status")
        header.pack_start(self.sync_label)
        
        # Filter button
        filter_button = Gtk.MenuButton()
        filter_button.set_icon_name("view-list-symbolic")
        
        filter_menu = Gio.Menu()
        filter_menu.append("All Tasks", "app.filter::all")
        filter_menu.append("Today", "app.filter::today")
        filter_menu.append("Upcoming", "app.filter::upcoming")
        filter_menu.append("Overdue", "app.filter::overdue")
        filter_menu.append("Completed", "app.filter::completed")
        filter_menu.append("High Priority", "app.filter::high_priority")
        
        filter_button.set_menu_model(filter_menu)
        header.pack_end(filter_button)
        
        self.main_box.append(header)
        
        # Statistics section
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        stats_box.set_margin_top(12)
        stats_box.set_margin_bottom(12)
        stats_box.set_margin_start(24)
        stats_box.set_margin_end(24)
        
        self.stats_label = Gtk.Label()
        self.stats_label.add_css_class("title-4")
        self.stats_label.set_halign(Gtk.Align.CENTER)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.add_css_class("osd")
        
        stats_box.append(self.stats_label)
        stats_box.append(self.progress_bar)
        
        self.main_box.append(stats_box)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.append(separator)
        
        # Tasks list
        self.task_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.task_list.set_margin_top(12)
        self.task_list.set_margin_start(12)
        self.task_list.set_margin_end(12)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_child(self.task_list)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.main_box.append(scrolled_window)
        
        # Add task button
        add_button = Gtk.Button(label="+ Add Task")
        add_button.add_css_class("suggested-action")
        add_button.set_margin_top(12)
        add_button.set_margin_bottom(12)
        add_button.set_margin_start(24)
        add_button.set_margin_end(24)
        add_button.connect("clicked", self.on_add_task)
        
        self.main_box.append(add_button)
        
        self.set_content(self.main_box)
    
    def start_file_monitor(self):
        """Watch the Planify database file for changes"""
        from config import DATABASE
        db_path = str(DATABASE)
        
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}")
            self.sync_label.set_text("⚠️")
            return
        
        try:
            # Create a file monitor
            gfile = Gio.File.new_for_path(db_path)
            self.db_monitor = gfile.monitor_file(
                Gio.FileMonitorFlags.WATCH_MOVES,
                None  # Cancellable
            )
            
            if self.db_monitor:
                self.db_monitor.connect("changed", self.on_database_changed)
                self.sync_label.set_text("🔄")
                print("File monitor started successfully")
            else:
                print("Failed to create file monitor")
                self.sync_label.set_text("⚠️")
                
        except Exception as e:
            print(f"Error setting up file monitor: {e}")
            self.sync_label.set_text("⚠️")
    
    def on_database_changed(self, monitor, file, other_file, event_type):
        """Handle database file changes from Planify"""
        # Map event types to readable names
        event_names = {
            Gio.FileMonitorEvent.CHANGED: "CHANGED",
            Gio.FileMonitorEvent.CHANGES_DONE_HINT: "CHANGES_DONE",
            Gio.FileMonitorEvent.DELETED: "DELETED",
            Gio.FileMonitorEvent.CREATED: "CREATED",
            Gio.FileMonitorEvent.ATTRIBUTE_CHANGED: "ATTR_CHANGED",
            Gio.FileMonitorEvent.PRE_UNMOUNT: "PRE_UNMOUNT",
            Gio.FileMonitorEvent.UNMOUNTED: "UNMOUNTED",
            Gio.FileMonitorEvent.MOVED: "MOVED",
            Gio.FileMonitorEvent.RENAMED: "RENAMED",
            Gio.FileMonitorEvent.MOVED_IN: "MOVED_IN",
            Gio.FileMonitorEvent.MOVED_OUT: "MOVED_OUT",
        }
        
        event_name = event_names.get(event_type, f"UNKNOWN({event_type})")
        print(f"Database event: {event_name}")
        
        # React to relevant events
        if event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            # Planify finished writing changes - perfect time to refresh
            self.schedule_refresh()
        elif event_type == Gio.FileMonitorEvent.CHANGED:
            # Database was modified - schedule a refresh with debounce
            self.schedule_refresh()
        elif event_type == Gio.FileMonitorEvent.DELETED:
            # Database was deleted - show warning
            self.sync_label.set_text("❌")
            print("Database file was deleted!")
        elif event_type == Gio.FileMonitorEvent.CREATED:
            # Database was recreated - refresh and restart monitor
            self.sync_label.set_text("🔄")
            self.schedule_refresh()
    
    def schedule_refresh(self):
        """Schedule a UI refresh with debouncing to avoid excessive updates"""
        # Remove any pending refresh
        if self._refresh_pending:
            GLib.source_remove(self._refresh_timeout_id)
        
        # Schedule new refresh with 500ms delay to batch changes
        self._refresh_timeout_id = GLib.timeout_add(500, self._do_refresh)
        self._refresh_pending = True
    
    def _do_refresh(self):
        """Perform the actual refresh"""
        self._refresh_pending = False
        
        # Update sync indicator
        self.sync_label.set_text("🔄")
        GLib.timeout_add(1000, lambda: self.sync_label.set_text("✅"))
        
        # Refresh the task list
        self.refresh_tasks()
        
        return False  # Don't repeat
    
    def refresh_tasks(self, filter_type=None):
        """Refresh the task list and statistics"""
        # Clear existing task cards
        while True:
            child = self.task_list.get_first_child()
            if child is None:
                break
            self.task_list.remove(child)
        
        try:
            # Get tasks and statistics
            tasks = self.controller.get_tasks(filter_type)
            stats = self.controller.get_statistics()
            
            # Update statistics
            self.update_statistics(stats)
            
            # Create task cards
            for task in tasks:
                task_card = TaskCard(task)
                task_card.connect("task-toggled", self.on_task_toggled)
                task_card.connect("task-edit", self.on_task_edit)
                task_card.connect("task-delete", self.on_task_delete)
                self.task_list.append(task_card)
                
        except Exception as e:
            print(f"Error refreshing tasks: {e}")
    
    def update_statistics(self, stats):
        """Update statistics display"""
        completed = stats['completed']
        total = stats['total']
        
        self.stats_label.set_text(f"{completed} / {total} Tasks Completed")
        
        if total > 0:
            fraction = completed / total
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{int(fraction * 100)}%")
        else:
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("0%")
    
    def on_task_toggled(self, task_card, task_id, checked):
        """Handle task completion toggle"""
        try:
            self.controller.toggle_task(task_id, checked)
            # Update statistics immediately
            stats = self.controller.get_statistics()
            self.update_statistics(stats)
            # Update sync indicator
            self.sync_label.set_text("✅")
        except Exception as e:
            print(f"Error toggling task: {e}")
    
    def on_add_task(self, button):
        """Open add task dialog"""
        dialog = TaskDialog(self, self.controller)
        dialog.present(self)
    
    def on_task_edit(self, task_card, task_id):
        """Open edit task dialog"""
        try:
            # Find the task data
            tasks = self.controller.get_tasks()
            task = next((t for t in tasks if t[0] == task_id), None)
            
            if task:
                dialog = TaskDialog(self, self.controller, task)
                dialog.present(self)
        except Exception as e:
            print(f"Error editing task: {e}")
    
    def on_task_delete(self, task_card, task_id):
        """Delete a task with confirmation"""
        try:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Delete Task",
                body="Are you sure you want to delete this task?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("delete", "Delete")
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            
            def on_response(dialog, response):
                if response == "delete":
                    try:
                        self.controller.delete_task(task_id)
                        self.refresh_tasks()
                        self.sync_label.set_text("✅")
                    except Exception as e:
                        print(f"Error deleting task: {e}")
                dialog.close()
            
            dialog.connect("response", on_response)
            dialog.present()
            
        except Exception as e:
            print(f"Error showing delete dialog: {e}")
    
    def on_destroy(self):
        """Clean up when window is destroyed"""
        # Cancel file monitor
        if hasattr(self, 'db_monitor') and self.db_monitor:
            self.db_monitor.cancel()
        
        # Remove any pending refresh
        if self._refresh_pending:
            GLib.source_remove(self._refresh_timeout_id)
            
            
    def start_file_monitor(self):
        """Watch database file for changes"""
        from config import DATABASE
        db_path = str(DATABASE)
        
        file = Gio.File.new_for_path(db_path)
        self.monitor = file.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect("changed", self.on_database_changed)
        print("File monitor started - watching for Planify changes")
    
    def on_database_changed(self, monitor, file, other_file, event_type):
        """Handle database file changes"""
        if event_type in (Gio.FileMonitorEvent.CHANGED, 
                           Gio.FileMonitorEvent.CREATED,
                           Gio.FileMonitorEvent.DELETED):
            print("Planify modified the database, refreshing...")
            self.refresh_tasks()