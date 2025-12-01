# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Sound Waveform Display",
    "description": "Display selected sound waveform in timeline/dopesheet/graph",
    "author": "Samuel Bernou",
    "version": (2, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/sound_waveform_display",
    "tracker_url": "https://github.com/Pullusb/sound_waveform_display/issues",
    "category": "Animation" }

from . import properties
from . import preferences
from . import display_wave_image
from . import panels

import bpy

def register():
    if bpy.app.background:
        return

    properties.register()
    preferences.register()
    display_wave_image.register()
    panels.register()

def unregister():
    if bpy.app.background:
        return
    panels.unregister()
    display_wave_image.unregister()
    preferences.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
