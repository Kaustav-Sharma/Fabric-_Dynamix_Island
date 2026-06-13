import gi
import subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from fabric.widgets.box import Box
from fabric.widgets.button import Button

class PowerProfiles(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="power-profiles",
            orientation="h",
            spacing=10,
            h_align="center",
            **kwargs
        )

        # Create the buttons (Using Nerd Font icons, change text if you prefer!)
        # Paste your old icons inside the quotes here!
        self.btn_saver = Button(name="profile-btn", label="")
        self.btn_balanced = Button(name="profile-btn", label="")
        self.btn_performance = Button(name="profile-btn", label="")

        # Wire the click events to the terminal commands
        self.btn_saver.connect("clicked", lambda *_: self.set_profile("power-saver"))
        self.btn_balanced.connect("clicked", lambda *_: self.set_profile("balanced"))
        self.btn_performance.connect("clicked", lambda *_: self.set_profile("performance"))

        # Add them to the layout
        self.add(self.btn_saver)
        self.add(self.btn_balanced)
        self.add(self.btn_performance)

        # Check which profile is currently active on boot
        self.sync_active_profile()
        self.show_all()

    def set_profile(self, profile_name):
        try:
            # This fires the command silently in the background
            subprocess.run(["powerprofilesctl", "set", profile_name], check=True)
            # Immediately update the UI to highlight the new active button
            self.sync_active_profile()
        except Exception as e:
            print(f"Failed to set power profile: {e}")

    def sync_active_profile(self):
        try:
            # Ask the system which profile is currently running
            active = subprocess.check_output(["powerprofilesctl", "get"]).decode().strip()

            # First, strip the 'active' highlight from all buttons
            self.btn_saver.remove_style_class("active")
            self.btn_balanced.remove_style_class("active")
            self.btn_performance.remove_style_class("active")

            # Apply the 'active' highlight to the correct button
            if active == "power-saver":
                self.btn_saver.add_style_class("active")
            elif active == "balanced":
                self.btn_balanced.add_style_class("active")
            elif active == "performance":
                self.btn_performance.add_style_class("active")
                
        except Exception as e:
            print(f"Could not read power profile: {e}")