import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio


def themed_icon(names, pixel_size=16, css_class=None):
    """Build a Gtk.Image that tries each icon name in order until one
    resolves in the current icon theme, instead of silently falling
    back to a broken 'missing icon' placeholder.

    `names` can be a single icon name string or a list of candidate
    names ordered from most to least specific — GTK will use the
    first one it can actually find.
    """
    if isinstance(names, str):
        names = [names]

    icon = Gtk.Image.new_from_gicon(Gio.ThemedIcon.new_from_names(list(names)))
    icon.set_pixel_size(pixel_size)
    if css_class:
        icon.add_css_class(css_class)
    return icon


def icon_button(names, pixel_size=16, css_classes=None, tooltip=None):
    """A Gtk.Button whose icon uses the same theme-name fallback chain
    as themed_icon(). Gtk.Button.set_icon_name() only accepts a single
    name with no fallback, so we build the icon ourselves and set it
    as the button's child instead."""
    button = Gtk.Button()
    button.set_child(themed_icon(names, pixel_size))
    for cls in (css_classes or []):
        button.add_css_class(cls)
    if tooltip:
        button.set_tooltip_text(tooltip)
    return button
