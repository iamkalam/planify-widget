import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw

from ui.main_window import MainWindow


class PlanifyWidget(Adw.Application):

    def __init__(self):
        super().__init__(
            application_id="com.planify.widget"
        )

    def do_activate(self):

        window = MainWindow(self)

        window.present()

    


app = PlanifyWidget()

app.run()