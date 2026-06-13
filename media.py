import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Playerctl', '2.0')
from gi.repository import Gtk, GLib, Playerctl
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button

class MediaPlayer(Box):
    def __init__(self, on_track_change=None, **kwargs):
        super().__init__(name="media-panel", orientation="v", spacing=12, **kwargs)
        self.on_track_change = on_track_change
        self.current_player = None

        # --- UI Elements ---
        self.lbl_title = Label(label="Not Playing", name="media-title", h_align="center")
        self.lbl_artist = Label(label="Open Spotify or a Browser", name="media-artist", h_align="center")
        
        self.lbl_title.set_max_width_chars(25)
        self.lbl_title.set_line_wrap(True)
        self.lbl_artist.set_max_width_chars(30)
        self.lbl_artist.set_ellipsize(3) 

        self.btn_prev = Button(label="󰒮", name="media-btn")
        self.btn_play = Button(label="󰐊", name="media-btn-play")
        self.btn_next = Button(label="󰒭", name="media-btn")

        self.btn_prev.connect("clicked", self.do_prev)
        self.btn_play.connect("clicked", self.do_play_pause)
        self.btn_next.connect("clicked", self.do_next)

        controls = Box(orientation="h", spacing=16, h_align="center")
        controls.add(self.btn_prev)
        controls.add(self.btn_play)
        controls.add(self.btn_next)

        self.add(self.lbl_title)
        self.add(self.lbl_artist)
        self.add(controls)

        # --- Playerctl Backend Setup ---
        self.manager = Playerctl.PlayerManager()
        self.manager.connect('name-appeared', self.on_player_appeared)
        self.manager.connect('player-vanished', self.on_player_vanished)

        for name in self.manager.props.player_names:
            self.init_player(name)

        self.show_all()

    def init_player(self, name):
        player = Playerctl.Player.new_from_name(name)
        player.connect('playback-status::playing', self.on_playback_status, player)
        player.connect('playback-status::paused', self.on_playback_status, player)
        player.connect('metadata', self.on_metadata, player)
        self.manager.manage_player(player)

    def on_player_appeared(self, manager, name):
        self.init_player(name)

    def on_player_vanished(self, manager, player):
        if self.current_player == player:
            self.current_player = None
            self.lbl_title.set_label("Not Playing")
            self.lbl_artist.set_label("")
            self.btn_play.set_label("󰐊")
            if self.on_track_change:
                self.on_track_change(False, "")

    def on_playback_status(self, player, status, _):
        self.current_player = player
        is_playing = status == Playerctl.PlaybackStatus.PLAYING
        self.btn_play.set_label("󰏤" if is_playing else "󰐊")
        self.update_ui(player)

    def on_metadata(self, player, metadata, _):
        self.current_player = player
        self.update_ui(player)

    def update_ui(self, player):
        try:
            title = player.get_title() or "Unknown Track"
            artist = player.get_artist() or ""
            status = player.props.playback_status
            is_playing = status == Playerctl.PlaybackStatus.PLAYING

            self.lbl_title.set_label(title)
            self.lbl_artist.set_label(artist)
            self.btn_play.set_label("󰏤" if is_playing else "󰐊")

            # Dim buttons if the app doesn't support skipping
            self.btn_next.set_sensitive(player.props.can_go_next)
            self.btn_prev.set_sensitive(player.props.can_go_previous)

            if self.on_track_change:
                self.on_track_change(is_playing, title)
        except Exception:
            pass

    def do_play_pause(self, *args):
        if self.current_player:
            try:
                self.current_player.play_pause()
            except Exception:
                pass

    def do_prev(self, *args):
        if self.current_player and self.current_player.props.can_go_previous:
            try:
                self.current_player.previous()
            except Exception:
                pass

    def do_next(self, *args):
        if self.current_player and self.current_player.props.can_go_next:
            try:
                self.current_player.next()
            except Exception:
                pass