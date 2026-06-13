import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from fabric.widgets.box import Box
from fabric.widgets.label import Label

def get_volume():
    try:
        out = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]).decode().strip()
        parts = out.split()
        if len(parts) >= 2:
            vol = float(parts[1]) * 100
            return int(vol), "[MUTED]" in out
    except Exception:
        pass
    return 0, False

class VolumeControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="volume-control-panel", 
            orientation="h", 
            spacing=16, 
            h_align="center", 
            v_align="center",
            **kwargs
        )
        
        self.status_label = Label(label="Volume", name="slider-status-text")
        
        vol, muted = get_volume()
        self.adjustment = Gtk.Adjustment(value=vol, lower=0, upper=100, step_increment=2, page_increment=10, page_size=0)
        self.slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment)
        self.slider.set_hexpand(True)
        self.slider.set_draw_value(False)
        self.slider.set_size_request(160, -1)
        
        self.slider.get_style_context().add_class("slider-bar")
        self.slider.connect("value-changed", self.on_slider_changed)
        
        self.add(self.status_label)
        self.add(self.slider)
        
        GLib.timeout_add_seconds(1, self.sync_volume)

    def on_slider_changed(self, scale):
        val = int(scale.get_value())
        try:
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val/100:.2f}"], check=False)
        except Exception:
            pass

    def sync_volume(self):
        vol, muted = get_volume()
        self.slider.handler_block_by_func(self.on_slider_changed)
        self.slider.set_value(vol)
        self.slider.handler_unblock_by_func(self.on_slider_changed)
        
        if muted:
            self.status_label.set_label("Muted")
        else:
            self.status_label.set_label(f"Volume {vol}%")
        return True