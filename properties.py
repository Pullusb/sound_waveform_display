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

    range : EnumProperty(
        name="Show", description="Define what should be displayed", 
        default='SELECTION', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('SELECTION', 'Selected Strips', 'Waveform of selected strips in VSE (even muted ones)', 0),
            ('UNMUTED', 'Unmuted Strips', 'Display all audible strips in VSE', 1),
            ('SCENE', 'Scene Range', 'Display VSE audio of scene range (not preview range)', 2),
            # ('ALL', 'All Strip', '', '', 2),
            ))
    


    ## property with update on change
    # edit_lines_opacity : FloatProperty(
    #     name="edit lines Opacity", description="Change edit lines opacity for all grease pencils", 
    #     default=0.5, min=0.0, max=1.0, step=3, precision=2)



# classes=(
# SWD_PGT_settings,
# )

def register(): 
    # for cls in classes:
    #     bpy.utils.register_class(cls)
    bpy.utils.register_class(SWD_PGT_settings)
    bpy.types.Scene.swd_settings = bpy.props.PointerProperty(type = SWD_PGT_settings)
    

def unregister():
    # for cls in reversed(classes):
    #     bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(SWD_PGT_settings)
    del bpy.types.Scene.swd_settings