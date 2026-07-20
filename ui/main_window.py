import gi
from database import get_tasks, update_task
from ui.task_row import TaskRow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("Planify Widget")
        self.set_default_size(420, 600)

        header = Adw.HeaderBar()

        title = Gtk.Label(label="📋 Planify Widget")
        header.set_title_widget(title)

        self.set_content(self.build_ui())

    def build_ui(self):

        scroll = Gtk.ScrolledWindow()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=15,
            margin_bottom=15,
            margin_start=15,
            margin_end=15,
        )

        tasks = get_tasks()

        for task in tasks:

            row = TaskRow(*task)

            box.append(row)

        scroll.set_child(box)

        return scroll
