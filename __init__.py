bl_info = {
    "name": "Sound Waveform Display",
    "description": "Display waveform in dopesheet",
    "author": "Samuel Bernou",
    "version": (0, 1, 7),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "WIP",
    "doc_url": "",
    "category": "Animation" }

from . import properties
from . import preferences
from . import ops_display
from . import display_wave_image
from . import panels
# from . import keymaps

import bpy


def register():
    if bpy.app.background:
        return

    properties.register()
    # preferences.register()
    # ops_display.register()
    display_wave_image.register()
    panels.register()
    # keymaps.register()

def unregister():
    if bpy.app.background:
        return
    # keymaps.unregister()
    panels.unregister()
    display_wave_image.unregister()
    # ops_display.unregister()
    # preferences.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
