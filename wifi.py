import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label

def is_wifi_enabled():
    try:
        out = subprocess.check_output(["nmcli", "radio", "wifi"]).decode().strip()
        return out == "enabled"
    except Exception:
        return False

class WifiControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="wifi-control-panel", 
            orientation="h", 
            spacing=20, 
            h_align="center", 
            v_align="center",
            **kwargs
        )
        
        self.status_label = Label(label="Wi-Fi", name="wifi-status-text")
        self.toggle_btn = Button(label="󰖩  On", name="wifi-action-btn")
        self.toggle_btn.connect("clicked", self.on_toggle_clicked)
        
        self.children = [self.status_label, self.toggle_btn]
        self.sync_state()
        
        GLib.timeout_add_seconds(2, self.sync_state)

    def on_toggle_clicked(self, *args):
        next_state = "off" if is_wifi_enabled() else "on"
        try:
            subprocess.run(["nmcli", "radio", "wifi", next_state], check=False)
        except Exception:
            pass
        self.sync_state()

    def sync_state(self):
        enabled = is_wifi_enabled()
        if enabled:
            self.toggle_btn.set_label("󰖩  On")
            self.toggle_btn.add_style_class("active")
            try:
                cmd = "nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2"
                ssid = subprocess.check_output(cmd, shell=True).decode().strip()
                self.status_label.set_label(ssid if ssid else "Connected")
            except Exception:
                self.status_label.set_label("Connected")
        else:
            self.toggle_btn.set_label("󰖪  Off")
            self.toggle_btn.remove_style_class("active")
            self.status_label.set_label("Disabled")
        return True