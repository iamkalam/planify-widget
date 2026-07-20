import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from database import update_task


class TaskRow(Gtk.Box):

    def __init__(self, task_id, content, checked, priority):

        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12
        )

        self.task_id = task_id

        self.checkbox = Gtk.CheckButton()
        self.checkbox.set_active(bool(checked))

        self.label = Gtk.Label(
            label=content,
            xalign=0
        )

        self.label.set_hexpand(True)

        self.append(self.checkbox)
        self.append(self.label)

        self.checkbox.connect(
            "toggled",
            self.on_toggled
        )

    def on_toggled(self, checkbox):

        update_task(
            self.task_id,
            checkbox.get_active()
        )