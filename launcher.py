import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Gdk
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from fabric.widgets.entry import Entry

class AppLauncher(Box):
    def __init__(self, on_close=None, **kwargs):
        super().__init__(
            name="app-launcher-panel",
            orientation="v",
            spacing=14,
            **kwargs
        )
        self.on_close = on_close

        # Slightly taller to accommodate the larger 72px icons
        self.set_size_request(440, 420)

        # --- SEARCH BAR ---
        self.search_entry = Entry(
            name="launcher-search",
            placeholder="Search applications...",
            h_expand=True
        )
        self.search_entry.connect("changed", self.on_search_changed)
        self.search_entry.connect("activate", self.on_enter_pressed)
        self.search_entry.connect("key-press-event", self.on_key_pressed)

        # --- APP GRID ---
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        
        # FIX 1: Force the grid to stretch across the entire window (no dead space!)
        self.flowbox.set_halign(Gtk.Align.FILL)
        
        # FIX 2: Make all 4 columns identically wide
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_max_children_per_line(4) 
        self.flowbox.set_min_children_per_line(4) 
        
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_property("row-spacing", 8)
        self.flowbox.set_property("column-spacing", 8)
        self.flowbox.set_filter_func(self.filter_apps)

        # --- NATIVE SCROLLABLE WINDOW ---
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.get_style_context().add_class("launcher-scroll")
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_min_content_height(340)
        self.scrolled_window.set_min_content_width(420)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.add(self.flowbox)

        self.add(self.search_entry)
        self.add(self.scrolled_window)
        
        self.load_apps()
        self.show_all()

    def load_apps(self):
        app_infos = Gio.AppInfo.get_all()
        valid_apps = [app for app in app_infos if app.should_show()]
        valid_apps.sort(key=lambda a: a.get_display_name().lower())

        for app in valid_apps:
            btn = Button(name="app-btn")
            vbox = Box(orientation="v", spacing=6, v_align="center", h_align="center")

            btn._app_name = app.get_display_name().lower()
            btn._app_obj = app

            img = Image()
            
            # Fetch the icon
            icon = app.get_icon()
            if icon:
                try:
                    if isinstance(icon, Gio.ThemedIcon):
                        img.set_from_icon_name(icon.get_names()[0], Gtk.IconSize.DIALOG)
                    else:
                        img.set_from_gicon(icon, Gtk.IconSize.DIALOG)
                except Exception:
                    img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
            else:
                img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)

            # FIX 3: CRITICAL! This forcefully overrides the default GTK 48px cap to a massive 72px!
            img.set_pixel_size(72)

            name = app.get_display_name()
            # Allowed a bit more text length since the icons and grid are larger now
            display_name = name[:13] + "..." if len(name) > 13 else name
            lbl = Label(label=display_name, name="app-label")

            vbox.add(img)
            vbox.add(lbl)
            btn.add(vbox)

            btn.connect("clicked", lambda *_, a=app: self.launch_app(a))
            self.flowbox.add(btn)

    def filter_apps(self, child):
        query = self.search_entry.get_text().lower()
        if not query:
            return True 
            
        btn = child.get_child()
        if hasattr(btn, '_app_name'):
            return query in btn._app_name
        return False

    def on_search_changed(self, entry):
        self.flowbox.invalidate_filter()

    def on_enter_pressed(self, entry):
        for child in self.flowbox.get_children():
            if self.filter_apps(child):
                btn = child.get_child()
                self.launch_app(btn._app_obj)
                break

    def on_key_pressed(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.on_close:
                self.on_close()
            return True
        return False

    def launch_app(self, app):
        app.launch(None, None)
        if self.on_close:
            self.on_close()

    def focus_search(self):
        self.search_entry.set_text("")
        self.search_entry.grab_focus()
        self.flowbox.invalidate_filter()
        return False