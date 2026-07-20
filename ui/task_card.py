import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, GObject


class TaskCard(Gtk.Frame):

    __gsignals__ = {
        "task-toggled": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (int, bool),
        )
    }

    def __init__(self, task_id, content, checked, priority):

        super().__init__()

        self.task_id = task_id

        outer = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=10,
            margin_bottom=10,
            margin_start=10,
            margin_end=10
        )

        # -------------------------
        # Top Row
        # -------------------------

        top = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12
        )

        self.checkbox = Gtk.CheckButton()
        self.checkbox.set_active(bool(checked))

        title = Gtk.Label(
            label=content,
            xalign=0
        )

        title.set_hexpand(True)

        top.append(self.checkbox)
        top.append(title)

        outer.append(top)

        # -------------------------
        # Bottom Row
        # -------------------------

        bottom = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8
        )

        priority_label = Gtk.Label(
            label=f"⭐ Priority {priority}"
        )

        priority_label.set_xalign(0)

        bottom.append(priority_label)

        outer.append(bottom)

        self.set_child(outer)

        self.checkbox.connect(
            "toggled",
            self.on_toggled
        )

    def on_toggled(self, checkbox):

        self.emit(
            "task-toggled",
            self.task_id,
            checkbox.get_active()
        )