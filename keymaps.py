import bpy

addon_keymaps = []

def register():
    addon = bpy.context.window_manager.keyconfigs.addon
    # km = addon.keymaps.new(name = "Window", space_type = "EMPTY")# from everywhere
    
    km = addon.keymaps.new(name = "3D View", space_type = "VIEW_3D")

    ## detailed
    # kmi = km.keymap_items.new(
    #     name="name",
    #     idname="catname.opsname",
    #     type="F",
    #     value="PRESS",
    #     shift=True,
    #     ctrl=True,
    #     alt = False,
    #     oskey=False
    #     )

    kmi = km.keymap_items.new('catname.opsname', type='F5', value='PRESS')

    # km = addon.keymaps.new(name = "Grease Pencil Stroke Sculpt Mode", space_type = "EMPTY", region_type='WINDOW')
    # kmi = km.keymap_items.new('wm.context_toggle', type='THREE', value='PRESS')
    # kmi.properties.data_path='scene.tool_settings.use_gpencil_select_mask_segment'
    # addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    
    addon_keymaps.clear()