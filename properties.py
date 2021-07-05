import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

## update on prop change
def change_edit_lines_opacity(self, context):
    for gp in bpy.data.grease_pencils:
        if not gp.is_annotation:
            gp.edit_line_color[3]=self.edit_lines_opacity
    
class SWD_PGT_settings(bpy.types.PropertyGroup) :
    ## HIDDEN to hide the animatable dot thing
    stringprop : StringProperty(
        name="str prop",
        description="",
        default="")# update=None, get=None, set=None
    
    boolprop : BoolProperty(
        name="bool prop",
        description="",
        default=False, options={'HIDDEN'}) # options={'ANIMATABLE'},subtype='NONE', update=None, get=None, set=None

    IntProperty : IntProperty(
        name="int prop", description="", default=25, min=1, max=2**31-1, soft_min=1, soft_max=2**31-1, step=1, options={'HIDDEN'})#, subtype='PIXEL'

    ## property with update on change
    edit_lines_opacity : FloatProperty(
        name="edit lines Opacity", description="Change edit lines opacity for all grease pencils", 
        default=0.5, min=0.0, max=1.0, step=3, precision=2, update=change_edit_lines_opacity)

    ## enum (with Icon)
    keyframe_type : EnumProperty(
        name="Keyframe Filter", description="Only jump to defined keyframe type", 
        default='ALL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('ALL', 'All', '', 0), # 'KEYFRAME'
            ('KEYFRAME', 'Keyframe', '', 'KEYTYPE_KEYFRAME_VEC', 1),
            ('BREAKDOWN', 'Breakdown', '', 'KEYTYPE_BREAKDOWN_VEC', 2),
            ('MOVING_HOLD', 'Moving Hold', '', 'KEYTYPE_MOVING_HOLD_VEC', 3),
            ('EXTREME', 'Extreme', '', 'KEYTYPE_EXTREME_VEC', 4),
            ('JITTER', 'Jitter', '', 'KEYTYPE_JITTER_VEC', 5),
            ))


# classes=(
# SWD_PGT_settings,
# )

def register(): 
    # for cls in classes:
    #     bpy.utils.register_class(cls)
    bpy.utils.register_class(SWD_PGT_settings)
    bpy.types.Scene.pgroup_name = bpy.props.PointerProperty(type = SWD_PGT_settings)
    

def unregister():
    # for cls in reversed(classes):
    #     bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(SWD_PGT_settings)
    del bpy.types.Scene.pgroup_name