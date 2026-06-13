import gi
gi.require_version('Gtk', '3.0')
from fabric.widgets.box import Box
from volume import VolumeControl
from brightness import BrightnessControl

class ControlCenter(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-center-panel",
            orientation="v",
            spacing=10,
            **kwargs
        )
        
        self.volume_row = VolumeControl()
        self.brightness_row = BrightnessControl()
        
        self.children = [self.volume_row, self.brightness_row]
        
        # FIX 1: Force GTK to render the sliders so the height is > 0px
        self.show_all()

    def update_all(self):
        # FIX 2: Manually trigger the sync functions instantly, bypassing the 1-second timer delay
        self.volume_row.sync_volume()
        self.brightness_row.sync_brightness()