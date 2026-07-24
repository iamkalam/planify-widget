import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from ui.icon_utils import themed_icon
import cairo
import math


class CircularProgress(Gtk.Box):
    """A small Apple-widget-style circular progress ring: a thin arc
    with an icon centered inside it, and a value/caption below.

    Usage:
        ring = CircularProgress(icon_names=["emblem-ok-symbolic", "object-select-symbolic"], size=64)
        ring.set_fraction(0.77)      # fills the arc, clamped to [0, 1]
        ring.set_value_text("77%")   # bold text under the ring
        ring.set_caption("Completed")  # small muted text under that
    """

    def __init__(self, icon_names="emblem-ok-symbolic", size=60, line_width=6):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_halign(Gtk.Align.CENTER)
        self.add_css_class("circular-progress")

        self._fraction = 0.0
        self._line_width = line_width

        overlay = Gtk.Overlay()
        overlay.set_size_request(size, size)

        self._drawing_area = Gtk.DrawingArea()
        self._drawing_area.set_content_width(size)
        self._drawing_area.set_content_height(size)
        self._drawing_area.set_draw_func(self._on_draw, None)
        overlay.set_child(self._drawing_area)

        icon = themed_icon(icon_names, pixel_size=max(14, int(size * 0.32)), css_class="ring-icon")
        icon.set_halign(Gtk.Align.CENTER)
        icon.set_valign(Gtk.Align.CENTER)
        overlay.add_overlay(icon)

        self.append(overlay)

        self._value_label = Gtk.Label(label="")
        self._value_label.add_css_class("ring-value-label")
        self.append(self._value_label)

        self._caption_label = Gtk.Label(label="")
        self._caption_label.add_css_class("ring-caption-label")
        self.append(self._caption_label)

    def set_fraction(self, fraction):
        """Set how much of the ring is filled, clamped to [0, 1]."""
        try:
            fraction = float(fraction)
        except (TypeError, ValueError):
            fraction = 0.0
        self._fraction = max(0.0, min(1.0, fraction))
        self._drawing_area.queue_draw()

    def set_value_text(self, text):
        self._value_label.set_text(text)

    def set_caption(self, text):
        self._caption_label.set_text(text)

    def _on_draw(self, area, cr, width, height, data):
        cx = width / 2
        cy = height / 2
        radius = (min(width, height) / 2) - (self._line_width / 2) - 1

        cr.set_line_width(self._line_width)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)

        # Background track — always a full circle
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.set_source_rgba(1, 1, 1, 0.28)
        cr.stroke()

        # Filled progress arc, starting at 12 o'clock and going clockwise
        if self._fraction > 0:
            start_angle = -math.pi / 2
            end_angle = start_angle + (self._fraction * 2 * math.pi)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.set_source_rgba(1, 1, 1, 0.95)
            cr.stroke()
