import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from controllers.task_controller import TaskController
from ui.task_card import TaskCard


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("Planify Widget")
        self.set_default_size(420, 600)

        # Controller
        self.controller = TaskController()

        self.set_content(self.build_ui())

    def build_ui(self):

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=15,
            margin_bottom=15,
            margin_start=15,
            margin_end=15,
        )

        # -------------------------
        # Title
        # -------------------------

        title = Gtk.Label()
        title.set_markup(
            "<span size='18000'><b>📋 Planify Widget</b></span>"
        )
        title.set_xalign(0)

        root.append(title)

        # -------------------------
        # Statistics
        # -------------------------

        self.info = Gtk.Label()
        self.info.set_xalign(0)

        root.append(self.info)

        # -------------------------
        # Progress Bar
        # -------------------------

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)

        root.append(self.progress)

        # -------------------------
        # Scroll Area
        # -------------------------

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        self.task_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8
        )

        scroll.set_child(self.task_box)

        root.append(scroll)

        # -------------------------
        # Footer Button
        # -------------------------

        add_button = Gtk.Button(
            label="+ Add Task"
        )

        root.append(add_button)

        # Initial Load

        self.refresh_ui()

        return root

    # =====================================
    # Statistics
    # =====================================

    def refresh_statistics(self):

        completed, total = self.controller.get_statistics()

        self.info.set_text(
            f"{completed} / {total} Tasks Completed"
        )

        fraction = completed / total if total else 0

        self.progress.set_fraction(fraction)
        self.progress.set_text(f"{fraction:.0%}")

    # =====================================
    # Tasks
    # =====================================

    def refresh_tasks(self):

        while True:

            child = self.task_box.get_first_child()

            if child is None:
                break

            self.task_box.remove(child)

        tasks = self.controller.get_tasks()

        for task in tasks:

            card = TaskCard(*task)

            card.connect(
                "task-toggled",
                self.on_task_toggled
            )

            self.task_box.append(card)

    # =====================================
    # Refresh Everything
    # =====================================

    def refresh_ui(self):

        self.refresh_statistics()
        self.refresh_tasks()

    # =====================================
    # Checkbox Changed
    # =====================================

    def on_task_toggled(
        self,
        card,
        task_id,
        checked
    ):

        self.controller.toggle_task(
            task_id,
            checked
        )

        self.refresh_statistics()