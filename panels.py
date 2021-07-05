import bpy
from bpy.types import Panel
from .preferences import get_addon_prefs

class SWD_PT_SWD_panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tab Name"
    bl_label = "panel displayed name"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Wow')
        col.prop(context.scene.pgroup_name, 'str_prop')
        col.prop(context.scene.pgroup_name, 'bool_prop')
        col.prop(context.scene.pgroup_name, 'int_prop')

        row = col.row()
        row.prop(context.scene.pgroup_name, 'sauce')
        row.operator('catname.opsname', text='Turbo Ops', icon='SNAP_ON')


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
SWD_PT_SWD_panel,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.GPENCIL_MT_material_context_menu.append(palette_manager_menu)

def unregister():
    bpy.types.GPENCIL_MT_material_context_menu.remove(palette_manager_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)