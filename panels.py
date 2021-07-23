import bpy
from bpy.types import Panel
from .preferences import get_addon_prefs


class SWD_PT_SWD_GRAPH_ui(Panel):
    bl_label = "Display waveform"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Display"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        # row.operator('anim.timeline_draw_test', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.enable_draw', text='On', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.disable_draw', text='Off')

class SWD_PT_SWD_DOPE_ui(Panel):
    bl_label = "Display waveform"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Display"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        # row.operator('anim.timeline_draw_test', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.enable_draw', text='On', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.disable_draw', text='Off')

        row = layout.row()
        row.prop(context.scene.swd_settings, 'height_offset')



## function to append in a menu
def palette_manager_menu(self, context):
    """Palette menu to append in existing menu"""
    # GPENCIL_MT_material_context_menu
    layout = self.layout
    # {'EDIT_GPENCIL', 'PAINT_GPENCIL','SCULPT_GPENCIL','WEIGHT_GPENCIL', 'VERTEX_GPENCIL'}
    layout.separator()
    prefs = get_addon_prefs()

    layout.operator("", text='do stuff from material submenu', icon='MATERIAL')

#-# REGISTER

classes=(
SWD_PT_SWD_GRAPH_ui,
SWD_PT_SWD_DOPE_ui,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)