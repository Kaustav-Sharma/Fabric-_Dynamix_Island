import gi
import re
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button

class NotificationServer:
    def __init__(self, on_new_notification):
        self.on_new_notification = on_new_notification
        self.current_id = 1
        
        xml = """
        <node>
            <interface name="org.freedesktop.Notifications">
                <method name="Notify">
                    <arg type="s" name="app_name" direction="in"/>
                    <arg type="u" name="replaces_id" direction="in"/>
                    <arg type="s" name="app_icon" direction="in"/>
                    <arg type="s" name="summary" direction="in"/>
                    <arg type="s" name="body" direction="in"/>
                    <arg type="as" name="actions" direction="in"/>
                    <arg type="a{sv}" name="hints" direction="in"/>
                    <arg type="i" name="expire_timeout" direction="in"/>
                    <arg type="u" name="id" direction="out"/>
                </method>
                <method name="GetCapabilities">
                    <arg type="as" name="caps" direction="out"/>
                </method>
                <method name="GetServerInformation">
                    <arg type="s" name="name" direction="out"/>
                    <arg type="s" name="vendor" direction="out"/>
                    <arg type="s" name="version" direction="out"/>
                    <arg type="s" name="spec_version" direction="out"/>
                </method>
                <signal name="ActionInvoked">
                    <arg type="u" name="id"/>
                    <arg type="s" name="action_key"/>
                </signal>
            </interface>
        </node>
        """
        self.node = Gio.DBusNodeInfo.new_for_xml(xml)
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.bus.register_object(
            "/org/freedesktop/Notifications",
            self.node.interfaces[0],
            self.handle_method_call,
            None, None
        )
        Gio.bus_own_name_on_connection(
            self.bus, "org.freedesktop.Notifications", 
            Gio.BusNameOwnerFlags.REPLACE, None, None
        )

    def invoke_action(self, notif_id, action_key):
        self.bus.emit_signal(
            None,
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "ActionInvoked",
            GLib.Variant("(us)", (notif_id, action_key))
        )

    def handle_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        if method_name == "GetCapabilities":
            invocation.return_value(GLib.Variant("(as)", (["body", "actions"],)))
        elif method_name == "GetServerInformation":
            invocation.return_value(GLib.Variant("(ssss)", ("FabricIsland", "Custom", "1.0", "1.2")))
        elif method_name == "Notify":
            params = parameters.unpack()
            app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout = params
            
            notif_id = replaces_id if replaces_id > 0 else self.current_id
            if replaces_id == 0:
                self.current_id += 1

            clean_body = re.sub('<[^<]+>', '', body)
            
            parsed_actions = []
            for i in range(0, len(actions), 2):
                if actions[i] != "default": 
                    parsed_actions.append({"key": actions[i], "label": actions[i+1]})
            
            notif = {
                "id": notif_id,
                "app": app_name, 
                "summary": summary, 
                "body": clean_body,
                "actions": parsed_actions
            }
            
            GLib.idle_add(self.on_new_notification, notif)
            invocation.return_value(GLib.Variant("(u)", (notif_id,)))

class NotificationPanel(Box):
    def __init__(self, on_action_click=None, **kwargs):
        super().__init__(
            name="notification-panel",
            orientation="v",
            spacing=14,
            **kwargs
        )
        self.on_action_click = on_action_click
        self.set_size_request(380, 400)
        
        self.header = Label(label="Notifications", name="panel-header", h_align="start")
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.get_style_context().add_class("notif-list")
        
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_min_content_height(340)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.add(self.list_box)

        self.add(self.header)
        self.add(self.scrolled_window)
        self.show_all()

    def add_notification(self, notif):
        row = Box(orientation="v", spacing=6, name="notif-row")
        
        summary_lbl = Label(label=notif["summary"][:40], name="notif-summary", h_align="start")
        body_lbl = Label(label=notif["body"][:100], name="notif-body", h_align="start")
        body_lbl.set_line_wrap(True)
        body_lbl.set_max_width_chars(45)

        row.add(summary_lbl)
        row.add(body_lbl)
        
        if notif.get("actions"):
            action_box = Box(orientation="h", spacing=8, name="notif-actions")
            for action in notif["actions"]:
                btn = Button(label=action["label"], name="notif-action-btn")
                if self.on_action_click:
                    btn.connect("clicked", lambda *_, n_id=notif["id"], a_key=action["key"]: self.on_action_click(n_id, a_key))
                action_box.add(btn)
            row.add(action_box)
        
        self.list_box.insert(row, 0)
        self.list_box.show_all()