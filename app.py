import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Gdk
import os

from ui.main_window import MainWindow

class PlanifyWidgetApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.planify.widget",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
        self.create_action("filter", self.on_filter, GLib.VariantType("s"))
    
    def do_activate(self):
        """Activate the application"""
        # Load CSS
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(__file__), "styles.css")
        
        # Check if CSS file exists
        if os.path.exists(css_path):
            css_provider.load_from_path(css_path)
        else:
            print(f"Warning: CSS file not found at {css_path}")
            # Load minimal CSS
            css_provider.load_from_data(b"")
        
        # In GTK4, use Gdk.Display to add CSS provider
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
        # Create and show window
        self.win = MainWindow(self)
        self.win.present()
    
    def create_action(self, name, callback, param_type=None):
        """Create an application action"""
        action = Gio.SimpleAction.new(name, param_type)
        action.connect("activate", callback)
        self.add_action(action)
    
    def on_filter(self, action, param):
        """Handle filter actions"""
        filter_type = param.get_string()
        if filter_type == "all":
            filter_type = None
        self.win.refresh_tasks(filter_type)

if __name__ == "__main__":
    app = PlanifyWidgetApp()
    app.run()