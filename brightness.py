import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from fabric.widgets.box import Box
from fabric.widgets.label import Label

def get_brightness():
    try:
        # Get current brightness percentage
        actual = float(subprocess.check_output(["brightnessctl", "g"]).decode().strip())
        max_br = float(subprocess.check_output(["brightnessctl", "m"]).decode().strip())
        return int((actual / max_br) * 100)
    except Exception:
        return 0

class BrightnessControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="brightness-control-panel", 
            orientation="h", 
            spacing=16, 
            h_align="center", 
            v_align="center",
            **kwargs
        )
        
        self.status_label = Label(label="Brightness", name="slider-status-text")
        
        current_br = get_brightness()
        self.adjustment = Gtk.Adjustment(value=current_br, lower=0, upper=100, step_increment=2, page_increment=10, page_size=0)
        self.slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment)
        self.slider.set_hexpand(True)
        self.slider.set_draw_value(False)
        self.slider.set_size_request(160, -1)
        
        self.slider.get_style_context().add_class("slider-bar")
        self.slider.connect("value-changed", self.on_slider_changed)
        
        self.add(self.status_label)
        self.add(self.slider)
        
        GLib.timeout_add_seconds(1, self.sync_brightness)

    def on_slider_changed(self, scale):
        val = int(scale.get_value())
        try:
            subprocess.run(["brightnessctl", "s", f"{val}%"], check=False)
        except Exception:
            pass

    def sync_brightness(self):
        current_br = get_brightness()
        self.slider.handler_block_by_func(self.on_slider_changed)
        self.slider.set_value(current_br)
        self.slider.handler_unblock_by_func(self.on_slider_changed)
        
        self.status_label.set_label(f"Brightness {current_br}%")
        return True