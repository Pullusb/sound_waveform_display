import bpy
from bpy.types import Panel
from .preferences import get_addon_prefs

class SWD_PT_quick_pref_ui(Panel):
    bl_label = "Sound waveform quick prefs"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Display"
    bl_options = {'INSTANCED'}
    # bl_context = "Display"

    def draw(self, context):
        prefs = get_addon_prefs()
        layout = self.layout
        # layout.use_property_split = True
        layout.prop(prefs, 'wave_color', text='Color')
        layout.prop(prefs, 'wave_detail', text='Detail')
        # layout.prop(prefs, 'force_mixdown')
        layout.operator("swd.open_addon_prefs", text='Open All Prefs', icon='PREFERENCES')


def side_menu(self, context):
        layout = self.layout
        scn = context.scene
        row = layout.row()
        # row.operator('anim.timeline_draw_test', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.enable_draw', text='On', icon = 'NORMALIZE_FCURVES')
        row.operator('anim.disable_draw', text='Off')

        row = layout.row()
        row.prop(scn.swd_settings, 'height_offset')

        row = layout.row()
        row.prop(scn.swd_settings, 'use_dope')
        row.prop(scn.swd_settings, 'use_graph')
        row = layout.row()
        row.prop(scn.swd_settings, 'use_time')
        ## Direct prefs
        # row.operator("swd.open_addon_prefs", text='Prefs', icon='PREFERENCES')
        ## quick prefs
        row.popover('SWD_PT_quick_pref_ui', text='Prefs', icon='PREFERENCES')

        layout.prop(scn.swd_settings, 'source')
        if scn.swd_settings.source == 'SEQUENCER':
            vse = scn.sequence_editor
            if not vse:
                layout.label(text='No sequencer active in scene')
                return
            layout.prop(scn.swd_settings, 'vse_target')
            if scn.swd_settings.vse_target == 'LIST':
                layout.template_list("SWD_UL_sound_list", "", vse, "sequences", \
                    scn.swd_settings, "seq_idx", rows=3)

        # elif scn.swd_settings.source == 'SPEAKERS':
        #     layout.prop(scn.swd_settings, 'spk_target')
        
        # row = layout.row()
        # row.prop(scn.swd_settings, 'color')

def header_layout(self, context):
    layout = self.layout
    row = layout.row()
    row.alignment = 'RIGHT'
    row.operator("swd.open_addon_prefs", text='', icon='PREFERENCES')

class SWD_PT_SWD_GRAPH_ui(Panel):
    bl_label = "Display waveform"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Display"

    # def draw_header(self, context):
    #     header_layout(self, context)

    def draw(self, context):
        side_menu(self, context)
        # layout = self.layout

        # row = layout.row()
        # # row.operator('anim.timeline_draw_test', icon = 'NORMALIZE_FCURVES')
        # row.operator('anim.enable_draw', text='On', icon = 'NORMALIZE_FCURVES')
        # row.operator('anim.disable_draw', text='Off')

class SWD_PT_SWD_DOPE_ui(Panel):
    bl_label = "Display waveform"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Display"

    # def draw_header(self, context):
    #     header_layout(self, context)

    def draw(self, context):
        side_menu(self, context)

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
SWD_PT_quick_pref_ui,
SWD_PT_SWD_GRAPH_ui,
SWD_PT_SWD_DOPE_ui,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)