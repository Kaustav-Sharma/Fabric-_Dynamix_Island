import os
import subprocess
import threading
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.revealer import Revealer
from fabric.widgets.eventbox import EventBox

def get_battery():
    try:
        power_dir = "/sys/class/power_supply/"
        if os.path.exists(power_dir):
            supplies = os.listdir(power_dir)
            bat_folder = next((d for d in supplies if d.startswith("BAT")), None)
            
            if bat_folder:
                with open(os.path.join(power_dir, bat_folder, "capacity"), "r") as f:
                    return f"{f.read().strip()}%"
        return "100%"
    except Exception:
        return "100%"

def get_wifi_info():
    # This is the slow function that we will now run in the background!
    try:
        radio = subprocess.check_output(["nmcli", "radio", "wifi"]).decode().strip()
        if radio != "enabled":
            return "󰖪", "Off"
        cmd = "nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2"
        ssid = subprocess.check_output(cmd, shell=True).decode().strip()
        return " ", (ssid if ssid else "Connected")
    except Exception:
        return "󰖪", "Offline"

class SystemStats(Box):
    def __init__(self, on_bat_click=None, on_wifi_click=None, **kwargs):
        super().__init__(orientation="h", spacing=12, v_align="center", **kwargs)
        self.on_bat_click = on_bat_click
        self.on_wifi_click = on_wifi_click

        # --- BATTERY ---
        self.battery_icon = Label(label="󰁹", name="icon-label")
        self.battery_btn = EventBox(events="button-press-mask", child=self.battery_icon, name="clickable-icon")
        self.battery_btn.connect("button-press-event", lambda *_: self.on_bat_click() if self.on_bat_click else None)
        
        # Initialize text with a placeholder, it will update immediately
        self.battery_text = Label(label="...", name="stat-label")
        self.battery_revealer = Revealer(transition_type="slide-left", transition_duration=400, child=self.battery_text)
        self.bat_box = Box(orientation="h", spacing=4, children=[self.battery_btn, self.battery_revealer])

        # --- WIFI ---
        self.wifi_icon = Label(label=" ", name="icon-label")
        self.wifi_btn = EventBox(events="button-press-mask", child=self.wifi_icon, name="clickable-icon")
        self.wifi_btn.connect("button-press-event", lambda *_: self.on_wifi_click() if self.on_wifi_click else None)
        
        self.wifi_text = Label(label="...", name="stat-label")
        self.wifi_revealer = Revealer(transition_type="slide-left", transition_duration=400, child=self.wifi_text)
        self.wifi_box = Box(orientation="h", spacing=4, children=[self.wifi_btn, self.wifi_revealer])

        self.children = [self.bat_box, self.wifi_box]
        
        # Trigger an immediate update, then start the 2-second loop
        self.update_stats()
        GLib.timeout_add_seconds(2, self.update_stats)

    def update_stats(self):
        # Battery reading from a file is extremely fast, safe to do on the main thread
        self.battery_text.set_label(get_battery())
        
        # Send the slow Wi-Fi check to a background thread so the UI never freezes
        threading.Thread(target=self._fetch_wifi_async, daemon=True).start()
        
        return True # Keep the timeout loop running

    def _fetch_wifi_async(self):
        # This runs in the background. It can take 2 seconds, and the UI won't care!
        w_icon, w_text = get_wifi_info()
        
        # GLib.idle_add safely hands the results back to the main UI thread to update the labels
        GLib.idle_add(self._update_wifi_ui, w_icon, w_text)

    def _update_wifi_ui(self, icon, text):
        self.wifi_icon.set_label(icon)
        self.wifi_text.set_label(text)
        return False