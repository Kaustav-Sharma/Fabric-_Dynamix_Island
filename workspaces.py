import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from fabric.widgets.box import Box

class WorkspaceSwitcher(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="workspaces",
            orientation="h",
            spacing=6,
            v_align="center",
            **kwargs
        )
        self.active_ws = 1
        self.dots = {}
        
        for i in range(1, 6):
            dot = Box(name="ws-dot")
            if i == self.active_ws:
                dot.add_style_class("active")
            self.dots[i] = dot
            
        self.children = list(self.dots.values())
        GLib.timeout_add(200, self.update_workspace)

    def update_workspace(self):
        try:
            out = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], stderr=subprocess.DEVNULL)
            ws_id = json.loads(out).get("id", 1)
        except Exception:
            ws_id = 1
            
        if ws_id > 5: ws_id = 5 
        if ws_id < 1: ws_id = 1

        if ws_id != self.active_ws:
            self.dots[self.active_ws].remove_style_class("active")
            self.active_ws = ws_id
            self.dots[self.active_ws].add_style_class("active")
            
        return True