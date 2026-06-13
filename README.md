# Fabric Dynamic Island for Hyprland

A custom, reactive Dynamic Island built for Hyprland using the Fabric Python framework. It features real-time system monitoring, notification interception, media controls, and hardware OSD overlays.

## Features
- **Reactive UI:** Morphing island state based on active events.
- **Notification Server:** Intercepts system notifications via DBus and displays them in a custom panel.
- **Media Visualizer:** Uses MPRIS to sync with active media and creates a real-time waveform effect on your workspace dots.
- **Hardware OSD:** Custom overlays for Volume and Brightness, replacing default pop-ups.

## Dependencies
- `python`
- `fabric`
- `playerctl`
- `brightnessctl`

## Installation
1. Clone this repository into `~/.config/fabric`.
2. Ensure you have the `fabric` framework installed.
3. Configure your Hyprland binds to call the script.
