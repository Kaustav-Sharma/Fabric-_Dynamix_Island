import fabric
import os
import gi
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

from fabric import Application
from fabric.widgets.datetime import DateTime
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.revealer import Revealer
from fabric.widgets.eventbox import EventBox
from fabric.widgets.label import Label

from workspaces import WorkspaceSwitcher
from stats import SystemStats
from power import PowerProfiles
from wifi import WifiControl
from control_center import ControlCenter
from launcher import AppLauncher
from notifications import NotificationPanel, NotificationServer
from media import MediaPlayer

class StatusBar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="top",
            margin="2px 0px 0px 0px",
            exclusivity="none", 
            keyboard_mode="on-demand",
            **kwargs
        )

        GtkLayerShell.set_exclusive_zone(self, 39)

        # --- 1. THE TOP BAR COMPONENTS ---
        self.workspaces = WorkspaceSwitcher()
        self.stats = SystemStats(
            on_bat_click=self.toggle_power_menu,
            on_wifi_click=self.toggle_wifi_menu
        )

        self.time_label = DateTime(format="%H:%M", name="time-label")
        self.date_label = DateTime(format="%A, %d %B", name="date-label")
        self.date_revealer = Revealer(
            transition_type="slide-down",
            transition_duration=300, 
            child=self.date_label
        )
        
        self.time_box = Box(
            name="time-box",
            orientation="v",
            spacing=0,
            v_align="center",
            children=[self.time_label, self.date_revealer]
        )

        # --- THE TOP MEDIA PILL ---
        self.top_media_icon = Label(label="󰎆", name="icon-label")
        self.top_media_text = Label(label="", name="stat-label")
        self.top_media_text.set_max_width_chars(15)
        self.top_media_text.set_ellipsize(3) 
        
        self.top_media_box = Box(orientation="h", spacing=6, children=[self.top_media_icon, self.top_media_text])
        self.top_media_btn = EventBox(events="button-press-mask", child=self.top_media_box)
        self.top_media_btn.connect("button-press-event", lambda *_: self.toggle_media_menu())

        self.media_revealer = Revealer(
            transition_type="slide-right",
            transition_duration=400,
            child=self.top_media_btn
        )

        # --- THE TOP STACK ---
        self.default_top = Box(
            name="top-island-inner",
            orientation="h",
            spacing=12,
            h_align="center"
        )
        self.default_top.pack_start(self.workspaces, False, False, 0)
        self.default_top.pack_start(self.media_revealer, False, False, 0)
        self.default_top.pack_start(self.time_box, False, False, 0)
        self.default_top.pack_start(self.stats, False, False, 0)

        self.notif_top = Box(name="notif-top", orientation="h", spacing=10, h_align="center", v_align="center")
        self.notif_icon = Label(label="💬", name="icon-label")
        self.notif_summary = Label(label="", name="top-notif-summary", h_align="start")
        self.notif_body = Label(label="", name="top-notif-body", h_align="start")
        self.notif_text_box = Box(orientation="v", spacing=2)
        self.notif_text_box.add(self.notif_summary)
        self.notif_text_box.add(self.notif_body)
        self.notif_top.pack_start(self.notif_icon, False, False, 0)
        self.notif_top.pack_start(self.notif_text_box, False, False, 0)

        self.top_stack = Gtk.Stack()
        self.top_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.top_stack.set_transition_duration(300)
        self.top_stack.add_named(self.default_top, "default")
        self.top_stack.add_named(self.notif_top, "notification")
        self.top_stack.set_visible_child_name("default")

        # --- 2. THE MORPHING BOTTOM STACK ---
        self.power_menu = PowerProfiles()
        self.wifi_menu = WifiControl()
        self.control_center = ControlCenter()
        self.launcher_menu = AppLauncher(on_close=self.close_all_menus)
        self.notif_panel = NotificationPanel(on_action_click=self.handle_notif_action)
        self.media_panel = MediaPlayer(on_track_change=self.handle_track_change)

        self.bottom_stack = Gtk.Stack()
        self.bottom_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.bottom_stack.set_transition_duration(300)
        self.bottom_stack.set_interpolate_size(True)
        self.bottom_stack.set_homogeneous(False)

        self.empty_state = Box()
        self.empty_state.show()

        self.bottom_stack.add_named(self.empty_state, "empty")
        self.bottom_stack.add_named(self.power_menu, "power")
        self.bottom_stack.add_named(self.wifi_menu, "wifi")
        self.bottom_stack.add_named(self.control_center, "sliders")
        self.bottom_stack.add_named(self.launcher_menu, "launcher")
        self.bottom_stack.add_named(self.notif_panel, "notifications")
        self.bottom_stack.add_named(self.media_panel, "media")

        self.bottom_stack.show_all()
        self.bottom_stack.set_visible_child_name("empty")

        # --- 3. THE WRAPPER ---
        self.island_wrapper = Box(
            name="dynamic-island",
            orientation="v",
            h_align="center", 
            v_align="start",  
            children=[self.top_stack, self.bottom_stack]
        )

        self.event_box = EventBox(
            events="enter-notify-mask | leave-notify-mask",
            child=self.island_wrapper
        )
        self.event_box.connect("enter-notify-event", self.on_hover_enter)
        self.event_box.connect("leave-notify-event", self.on_hover_leave)
        
        self.add(self.event_box)
        self.show_all()
        
        self.auto_hide_timeout_id = None

        # --- DAEMONS & SIGNALS ---
        self.notif_server = NotificationServer(self.handle_new_notification)
        self.notif_timer = None

        signal.signal(signal.SIGUSR1, self.on_launcher_signal)
        signal.signal(signal.SIGUSR2, self.on_sliders_signal)
        signal.signal(signal.SIGALRM, self.on_notif_panel_signal)

    # --- ACTION HOOKS ---
    def handle_track_change(self, is_playing, title):
        if is_playing or title != "":
            self.top_media_text.set_label(title)
            self.media_revealer.set_reveal_child(True)
            
            # --- THE VISUALIZER HOOK ---
            if is_playing:
                self.workspaces.add_style_class("visualizer-active")
            else:
                self.workspaces.remove_style_class("visualizer-active")
        else:
            self.media_revealer.set_reveal_child(False)
            self.workspaces.remove_style_class("visualizer-active")

    def toggle_media_menu(self):
        if self.bottom_stack.get_visible_child_name() == "media":
            self.close_all_menus()
        else:
            self.bottom_stack.set_visible_child_name("media")
            self.island_wrapper.add_style_class("menu-expanded")

    def handle_notif_action(self, notif_id, action_key):
        self.notif_server.invoke_action(notif_id, action_key)

    def on_notif_panel_signal(self, signum, frame):
        GLib.idle_add(self.toggle_notif_panel)

    def toggle_notif_panel(self):
        if self.bottom_stack.get_visible_child_name() == "notifications":
            self.close_all_menus()
        else:
            self.bottom_stack.set_visible_child_name("notifications")
            self.island_wrapper.add_style_class("menu-expanded")
        return False

    def handle_new_notification(self, notif):
        self.notif_panel.add_notification(notif)
        self.notif_summary.set_label(notif["summary"][:35])
        self.notif_body.set_label(notif["body"][:40]) 
        self.top_stack.set_visible_child_name("notification")
        self.island_wrapper.add_style_class("expanded")
        
        if self.notif_timer is not None:
            GLib.source_remove(self.notif_timer)
        self.notif_timer = GLib.timeout_add_seconds(4, self.hide_notification_banner)

    def hide_notification_banner(self):
        self.top_stack.set_visible_child_name("default")
        self.island_wrapper.remove_style_class("expanded")
        self.notif_timer = None
        return False

    def on_launcher_signal(self, signum, frame):
        GLib.idle_add(self.toggle_launcher)

    def on_sliders_signal(self, signum, frame):
        GLib.idle_add(self.open_sliders_via_hardware)

    def close_all_menus(self):
        self.cancel_auto_hide_timer()
        self.bottom_stack.set_visible_child_name("empty")
        self.island_wrapper.remove_style_class("menu-expanded")
        self.island_wrapper.remove_style_class("launcher-expanded")

    def toggle_launcher(self):
        if self.bottom_stack.get_visible_child_name() == "launcher":
            self.close_all_menus()
        else:
            self.bottom_stack.set_visible_child_name("launcher")
            self.island_wrapper.add_style_class("launcher-expanded")
            GLib.timeout_add(150, self.launcher_menu.focus_search)
        return False

    def open_sliders_via_hardware(self):
        self.control_center.update_all()
        self.bottom_stack.set_visible_child_name("sliders")
        self.island_wrapper.add_style_class("menu-expanded")
        
        self.cancel_auto_hide_timer()
        self.auto_hide_timeout_id = GLib.timeout_add_seconds(2, self.auto_hide_sliders)
        return False

    def auto_hide_sliders(self):
        if self.bottom_stack.get_visible_child_name() == "sliders" and not self.island_wrapper.has_style_class("expanded"):
            self.close_all_menus()
        self.auto_hide_timeout_id = None
        return False

    def cancel_auto_hide_timer(self):
        if self.auto_hide_timeout_id is not None:
            GLib.source_remove(self.auto_hide_timeout_id)
            self.auto_hide_timeout_id = None

    def toggle_power_menu(self):
        if self.bottom_stack.get_visible_child_name() == "power":
            self.close_all_menus()
        else:
            self.bottom_stack.set_visible_child_name("power")
            self.island_wrapper.add_style_class("menu-expanded")

    def toggle_wifi_menu(self):
        if self.bottom_stack.get_visible_child_name() == "wifi":
            self.close_all_menus()
        else:
            self.bottom_stack.set_visible_child_name("wifi")
            self.island_wrapper.add_style_class("menu-expanded")

    def on_hover_enter(self, widget, event):
        if event.detail == Gdk.NotifyType.INFERIOR: return False
        self.cancel_auto_hide_timer()
        self.date_revealer.set_reveal_child(True)
        self.stats.battery_revealer.set_reveal_child(True)
        self.stats.wifi_revealer.set_reveal_child(True)
        self.island_wrapper.add_style_class("expanded")

    def on_hover_leave(self, widget, event):
        if event.detail == Gdk.NotifyType.INFERIOR: return False
        if self.bottom_stack.get_visible_child_name() == "launcher": return False 
        
        self.date_revealer.set_reveal_child(False)
        self.stats.battery_revealer.set_reveal_child(False)
        self.stats.wifi_revealer.set_reveal_child(False)
        self.island_wrapper.remove_style_class("expanded")
        self.close_all_menus()

if __name__ == "__main__":
    settings = Gtk.Settings.get_default()
    if settings is not None:
        settings.set_property("gtk-application-prefer-dark-theme", True)

    current_dir = os.path.dirname(os.path.realpath(__file__))
    css_file = os.path.join(current_dir, "style.css")

    bar = StatusBar()
    app = Application("bar-example", bar)
    app.set_stylesheet_from_file(css_file)
    app.run()