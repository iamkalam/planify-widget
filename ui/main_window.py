import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from controllers.task_controller import TaskController
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog
import os

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.controller = TaskController()
        self._last_stats = None
        self._refresh_pending = False
        self.active_filter = "all"
        self.filter_buttons = {}
        
        self.set_title("Planify Widget")
        self.set_default_size(420, 650)
        
        self.build_ui()
        self.refresh_tasks()
        
        # Start file monitoring for live sync
        self.start_file_monitor()
    
    def build_ui(self):
        """Build the main window UI"""
        # Main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        # Sync status indicator
        self.sync_label = Gtk.Label()
        self.sync_label.set_tooltip_text("Synced with Planify")
        self.sync_label.add_css_class("sync-status")
        header.pack_start(self.sync_label)
        
        # Project filter button
        self.project_button = Gtk.MenuButton()
        self.project_button.set_icon_name("folder-symbolic")
        self.project_button.set_tooltip_text("Filter by project")
        header.pack_end(self.project_button)
        
        self.main_box.append(header)
        
        # Search bar
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(8)
        search_box.set_margin_bottom(2)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search tasks...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_entry.set_hexpand(True)
        self.search_entry.set_size_request(-1, 32)  # Make search bar shorter
        
        # Clear search button
        clear_button = Gtk.Button()
        clear_button.set_icon_name("edit-clear-symbolic")
        clear_button.add_css_class("flat")
        clear_button.set_tooltip_text("Clear search")
        clear_button.connect("clicked", self.on_clear_search)
        
        search_box.append(self.search_entry)
        search_box.append(clear_button)
        
        self.main_box.append(search_box)
        
        # Filter chips in a FlowBox for wrapping
        filter_frame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        filter_frame.set_margin_start(8)
        filter_frame.set_margin_end(8)
        filter_frame.set_margin_top(2)
        filter_frame.set_margin_bottom(2)
        
        self.filter_flowbox = Gtk.FlowBox()
        self.filter_flowbox.set_homogeneous(False)
        self.filter_flowbox.set_row_spacing(4)
        self.filter_flowbox.set_column_spacing(4)
        self.filter_flowbox.set_max_children_per_line(10)
        self.filter_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.filter_flowbox.set_hexpand(True)
        
        # Create filter chips
        filters = [
            ("all", "All", "view-list-symbolic"),
            ("active", "Active", "task-due-symbolic"),
            ("today", "Today", "starred-symbolic"),
            ("upcoming", "Upcoming", "go-up-symbolic"),
            ("overdue", "Overdue", "dialog-warning-symbolic"),
            ("completed", "Done", "emblem-ok-symbolic"),
            ("high_priority", "Priority", "important-symbolic"),
        ]
        
        for filter_id, label, icon in filters:
            chip = self.create_filter_chip(filter_id, label, icon)
            self.filter_buttons[filter_id] = chip
            self.filter_flowbox.append(chip)
        
        # Set "All" as active by default
        if "all" in self.filter_buttons:
            self.filter_buttons["all"].add_css_class("filter-chip-active")
        
        filter_frame.append(self.filter_flowbox)
        self.main_box.append(filter_frame)
        
        # Statistics section
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        stats_box.set_margin_top(2)
        stats_box.set_margin_bottom(4)
        stats_box.set_margin_start(24)
        stats_box.set_margin_end(24)
        
        self.stats_label = Gtk.Label()
        self.stats_label.add_css_class("stats-label")
        self.stats_label.set_halign(Gtk.Align.CENTER)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.add_css_class("osd")
        self.progress_bar.set_size_request(-1, 6)  # Thinner progress bar
        
        stats_box.append(self.stats_label)
        stats_box.append(self.progress_bar)
        
        self.main_box.append(stats_box)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(2)
        separator.set_margin_bottom(2)
        self.main_box.append(separator)
        
        # Results count
        self.results_label = Gtk.Label()
        self.results_label.set_halign(Gtk.Align.CENTER)
        self.results_label.add_css_class("results-count")
        self.results_label.set_margin_top(2)
        self.results_label.set_margin_bottom(2)
        self.main_box.append(self.results_label)
        
        # Tasks list
        self.task_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.task_list.set_margin_top(2)
        self.task_list.set_margin_start(6)
        self.task_list.set_margin_end(6)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_child(self.task_list)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.main_box.append(scrolled_window)
        
        # Empty state
        self.empty_label = Gtk.Label(label="No tasks found")
        self.empty_label.set_halign(Gtk.Align.CENTER)
        self.empty_label.set_valign(Gtk.Align.CENTER)
        self.empty_label.add_css_class("empty-state")
        self.empty_label.set_vexpand(True)
        self.empty_label.set_visible(False)
        self.main_box.append(self.empty_label)
        
        # Add task button
        add_button = Gtk.Button(label="+ Add Task")
        add_button.add_css_class("suggested-action")
        add_button.set_margin_top(6)
        add_button.set_margin_bottom(8)
        add_button.set_margin_start(24)
        add_button.set_margin_end(24)
        add_button.connect("clicked", self.on_add_task)
        
        self.main_box.append(add_button)
        
        self.set_content(self.main_box)
    
    def create_filter_chip(self, filter_id, label, icon_name):
        """Create a compact filter chip button"""
        button = Gtk.Button()
        
        # Create chip content
        chip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        if icon_name:
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(14)  # Smaller icons
            icon.add_css_class("filter-icon")
            chip_box.append(icon)
        
        label_widget = Gtk.Label(label=label)
        label_widget.add_css_class("filter-label")
        chip_box.append(label_widget)
        
        button.set_child(chip_box)
        button.add_css_class("filter-chip")
        button.set_tooltip_text(f"Show {label.lower()} tasks")
        button.connect("clicked", self.on_filter_changed, filter_id)
        
        return button
    
    def on_filter_changed(self, button, filter_id):
        """Handle filter chip click"""
        self.active_filter = filter_id
        
        # Update chip styles
        for fid, chip in self.filter_buttons.items():
            if fid == filter_id:
                chip.add_css_class("filter-chip-active")
            else:
                chip.remove_css_class("filter-chip-active")
        
        # Refresh tasks with filter
        filter_type = None if filter_id == "all" else filter_id
        search_query = self.search_entry.get_text().strip() or None
        self.refresh_tasks(filter_type, search_query)
    
    def on_search_changed(self, search_entry):
        """Handle search entry changes"""
        search_query = search_entry.get_text().strip() or None
        filter_type = None if self.active_filter == "all" else self.active_filter
        self.refresh_tasks(filter_type, search_query)
    
    def on_clear_search(self, button):
        """Clear search entry"""
        self.search_entry.set_text("")
    
    def start_file_monitor(self):
        """Watch the Planify database file for changes"""
        from config import DATABASE
        db_path = str(DATABASE)
        
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}")
            self.sync_label.set_text("⚠️")
            return
        
        try:
            gfile = Gio.File.new_for_path(db_path)
            self.db_monitor = gfile.monitor_file(
                Gio.FileMonitorFlags.WATCH_MOVES,
                None
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
        if event_type in (Gio.FileMonitorEvent.CHANGES_DONE_HINT, 
                          Gio.FileMonitorEvent.CHANGED,
                          Gio.FileMonitorEvent.CREATED):
            self.schedule_refresh()
    
    def schedule_refresh(self):
        """Schedule a UI refresh with debouncing"""
        if self._refresh_pending:
            GLib.source_remove(self._refresh_timeout_id)
        
        self._refresh_timeout_id = GLib.timeout_add(500, self._do_refresh)
        self._refresh_pending = True
    
    def _do_refresh(self):
        """Perform the actual refresh"""
        self._refresh_pending = False
        
        self.sync_label.set_text("🔄")
        GLib.timeout_add(1000, lambda: self.sync_label.set_text("✅"))
        
        filter_type = None if self.active_filter == "all" else self.active_filter
        search_query = self.search_entry.get_text().strip() or None
        self.refresh_tasks(filter_type, search_query)
        
        return False
    
    def refresh_tasks(self, filter_type=None, search_query=None):
        """Refresh the task list and statistics"""
        # Clear existing task cards
        while True:
            child = self.task_list.get_first_child()
            if child is None:
                break
            self.task_list.remove(child)
        
        try:
            # Get tasks and statistics
            tasks = self.controller.get_tasks(filter_type, search_query)
            stats = self.controller.get_statistics()
            
            # Update statistics
            self.update_statistics(stats)
            
            # Update results count
            task_count = len(tasks)
            if search_query:
                self.results_label.set_text(f"{task_count} task{'s' if task_count != 1 else ''} found")
                self.results_label.set_visible(True)
            else:
                self.results_label.set_visible(False)
            
            # Show empty state if no tasks
            if task_count == 0:
                self.empty_label.set_visible(True)
                if search_query:
                    self.empty_label.set_label(f"No tasks matching '{search_query}'")
                else:
                    self.empty_label.set_label("No tasks found")
            else:
                self.empty_label.set_visible(False)
                
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
        overdue = stats.get('overdue', 0)
        today = stats.get('today', 0)
        
        stats_text = f"{completed} / {total} Completed"
        if overdue > 0:
            stats_text += f"  •  {overdue} Overdue"
        if today > 0:
            stats_text += f"  •  {today} Today"
        
        self.stats_label.set_text(stats_text)
        
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
            filter_type = None if self.active_filter == "all" else self.active_filter
            search_query = self.search_entry.get_text().strip() or None
            self.refresh_tasks(filter_type, search_query)
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
                        filter_type = None if self.active_filter == "all" else self.active_filter
                        search_query = self.search_entry.get_text().strip() or None
                        self.refresh_tasks(filter_type, search_query)
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
        if hasattr(self, 'db_monitor') and self.db_monitor:
            self.db_monitor.cancel()
        
        if self._refresh_pending:
            GLib.source_remove(self._refresh_timeout_id)