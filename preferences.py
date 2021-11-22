import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

def get_addon_prefs():
    '''
    function to read current addon preferences properties
    access with : get_addon_prefs().super_special_option
    '''
    import os 
    addon_name = os.path.splitext(__name__)[0]
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return (addon_prefs)


class SWD_OT_check_ffmpeg(bpy.types.Operator):
    """check if ffmpeg is in path"""
    bl_idname = "swd.check_ffmpeg"
    bl_label = "Check ffmpeg in system path"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        import  shutil
        self.ok = shutil.which('ffmpeg')
        return context.window_manager.invoke_props_dialog(self, width=250)
    
    def draw(self, context):
        layout = self.layout
        if self.ok:
            layout.label(text='Ok ! ffmpeg is in system PATH', icon='INFO')
        else:
            layout.label(text='ffmeg is not in system PATH', icon='CANCEL')

    def execute(self, context):
        return {'FINISHED'}

class SWD_sound_waveform_display_addonpref(bpy.types.AddonPreferences):
    bl_idname = __package__
    # bl_idname = __name__.split('.')[0] # or with: os.path.splitext(__name__)[0]

    path_to_ffmpeg : StringProperty(
        name="Path to ffmpeg binary",
        subtype='FILE_PATH')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.use_property_decorate = False
        box = layout.box()
        col = box.column()
        # col.label(text="This addon use ffmpeg to generate the waveform (need a recent version)")
        
        row = col.row()
        row.label(text="This functionallity need a recent ffmpeg binary")
        row.operator('wm.url_open', text='ffmpeg download page', icon='URL').url = 'https://www.ffmpeg.org/download.html'
        
        row = col.row()
        row.label(text="Leave field empty if ffmpeg is in system PATH")
        row.operator('swd.check_ffmpeg', text='Check if ffmpeg in PATH', icon='PLUGIN')
        
        # col.label(text="May not work if space are in path.")
        box.prop(self, "path_to_ffmpeg")

        ## Make an auto-install (at least for windows user), maybe store bin on a public repo...
        


### --- REGISTER ---

classes=(
SWD_OT_check_ffmpeg,
SWD_sound_waveform_display_addonpref,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)