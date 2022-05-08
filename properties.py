import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        FloatVectorProperty,
                        PointerProperty)

## update on prop change
def change_edit_lines_opacity(self, context):
    for gp in bpy.data.grease_pencils:
        if not gp.is_annotation:
            gp.edit_line_color[3]=self.edit_lines_opacity

class SWD_UL_sound_list(bpy.types.UIList):
    #   index is index of the current item in the collection.
    #   flt_flag is the result of the filtering process for this item.
    #   Note: as index and flt_flag are optional arguments, you do not have to use/declare them here if you don't
    #         need them.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        strip = item
        ## showing the prop make strip name editable by double click!
        # layout.prop(strip, "name", text="", emboss=False) # , icon_value=icon
        ## non editable name
        layout.label(text=strip.name)
   
    def draw_filter(self, context, layout):
        row = layout.row()
        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="") # Only show items matching this name (use ‘*’ as wildcard)
        ## reverse order filter (not really needed)
        # icon = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
        # subrow.prop(self, "use_filter_sort_reverse", text="", icon=icon) # built-in reverse

    def filter_items(self, context, data, propname):
        collec = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        # note : self.bitflag_filter_item == 1073741824 (reserved to filter)

        flt_type = 'SOUND'
        flt_flags = []
        flt_neworder = []
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, collec, "name",
                                                          reverse=self.use_filter_sort_reverse)#self.use_filter_name_reverse)
            # combine search result and type filter result
            flt_flags = [flt_flags[i] & self.bitflag_filter_item if strip.type == flt_type else 0 for i, strip in enumerate(collec)]
        else:
            flt_flags = [self.bitflag_filter_item if strip.type == flt_type else 0 for strip in collec]
        return flt_flags, flt_neworder

class SWD_PGT_settings(bpy.types.PropertyGroup):
    ## HIDDEN to hide the animatable dot thing
    # stringprop : StringProperty(
    #     name="str prop",
    #     description="",
    #     default="")# update=None, get=None, set=None
    
    use_graph : BoolProperty(
        name="Graph",
        description="Enable display in graph editor",
        default=True, options={'HIDDEN'})
    
    use_dope : BoolProperty(
        name="Dopesheet",
        description="Enable display in dopesheet editor",
        default=True, options={'HIDDEN'})
    
    use_time : BoolProperty(
        name="Timeline",
        description="Enable display in timeline editor",
        default=True, options={'HIDDEN'})

    height_offset : IntProperty(
        name="Height Offset", description="Adjust the height of the waveform", 
        default=0, min=-10000, max=10000, soft_min=-5000, soft_max=5000, step=1, options={'HIDDEN'})#, subtype='PIXEL'
    

    color : FloatVectorProperty(
        name="Color", description="Get wanted color (need relaunch)", default=(0.0368, 0.1714, 0.3371),
        step=3, precision=2,
        subtype='COLOR', # COLOR_GAMMA
        size=3, options={'HIDDEN'})

    source : EnumProperty(
        name="Source", description="Define audio source to display, sequencer strips, speakers or both", 
        default='SEQUENCER', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('ALL', 'All', 'Sounds from sequencer sound strip AND speaker objects in the scene range', 0),
            ('SEQUENCER', 'Sequencer', 'Only sounds from video sequencer strips with filters and optimisation', 1),
            ('SPEAKERS', 'Speaker Objects', 'Only sounds from speaker objects', 2),
            # ('ALL', 'All Strip', '', '', 2),
            ))

    vse_target : EnumProperty(
        name="Show", description="Define what should be displayed", 
        default='SELECTED', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('SELECTED', 'Selected Strips', 'Display only selected strips in sequencer (even muted ones)', 0),
            ('LIST', 'Sound In List', 'Display only sound from listed sequencer strip (list even muted ones)', 1),
            ('UNMUTED', 'Audible Strips', 'Display all audible strips in sequencer', 2),
            ('SCENE', 'Scene Range', 'Display sequencer audio of scene range (not preview range)', 3),
            ))

    seq_idx : IntProperty(default=-1)

    # spk_target : EnumProperty(
    #     name="Show", description="Define what should be displayed", 
    #     default='UNMUTED', options={'HIDDEN', 'SKIP_SAVE'},
    #     items=(
    #         ('UNMUTED', 'Audible Speakers', 'Display all audible speaker objects', 0),
    #         ('SELECTED', 'Selected Speakers', 'Display only selected speaker objects', 1),
    #         ))


classes = (
    SWD_PGT_settings,
    SWD_UL_sound_list,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_class(SWD_PGT_settings)
    bpy.types.Scene.swd_settings = bpy.props.PointerProperty(type = SWD_PGT_settings)
    # bpy.utils.register_class(SWD_UL_sound_list)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # bpy.utils.unregister_class(SWD_UL_sound_list)
    del bpy.types.Scene.swd_settings
    # bpy.utils.unregister_class(SWD_PGT_settings)