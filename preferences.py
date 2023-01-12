import bpy
import sys
import shutil
import zipfile
from pathlib import Path
import urllib.request
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        FloatVectorProperty)

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

def open_addon_prefs():
    '''Open addon prefs windows with focus on current addon'''
    from .__init__ import bl_info
    wm = bpy.context.window_manager
    wm.addon_filter = 'All'
    if not 'COMMUNITY' in  wm.addon_support: # reactivate community
        wm.addon_support = set([i for i in wm.addon_support] + ['COMMUNITY'])
    wm.addon_search = bl_info['name']
    bpy.context.preferences.active_section = 'ADDONS'
    bpy.ops.preferences.addon_expand(module=__package__)
    bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

class SWD_OT_open_addon_prefs(bpy.types.Operator):
    bl_idname = "swd.open_addon_prefs"
    bl_label = "Open Addon Prefs"
    bl_description = "Open user preferences window in addon tab and prefill the search with addon name"
    bl_options = {"REGISTER"}

    def execute(self, context):
        open_addon_prefs()
        return {'FINISHED'}

class SWD_OT_check_ffmpeg(bpy.types.Operator):
    """check if ffmpeg is in path"""
    bl_idname = "swd.check_ffmpeg"
    bl_label = "Check ffmpeg in system path"
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        import  shutil
        self.sys_path_ok = shutil.which('ffmpeg')

        # check for executable
        self.local_ffmpeg = False

        is_windows_os = sys.platform.startswith('win')
        if is_windows_os:
            ffbin = Path(__file__).parent / 'ffmpeg.exe'
            self.local_ffmpeg = ffbin.exists()
        else:
            # Mac / linux
            ffbin = Path(__file__).parent / 'ffmpeg'
            self.local_ffmpeg = ffbin.exists()

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        if self.local_ffmpeg:
            layout.label(text='ffmpeg found in addon folder (this binary will be used)', icon='CHECKMARK')

        if self.sys_path_ok:
            layout.label(text='ffmpeg is in system PATH', icon='CHECKMARK')
        else:
            layout.label(text='ffmpeg is not in system PATH', icon='X') # CANCEL

    def execute(self, context):
        return {'FINISHED'}

## download ffmpeg

def dl_url(url, dest):
    '''download passed url to dest file (include filename)'''
    import urllib.request
    import time
    start_time = time.time()
    with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    print(f"Download time {time.time() - start_time:.2f}s",)

def simple_dl_url(url, dest, fallback_url=None):
    ## need to import urllib.request or linux module does not found 'request' using urllib directly
    ## need to create an SSl context or linux fail returning unverified ssl

    if sys.platform.startswith(('linux','freebsd')):
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context

    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print('Error trying to download\n', e)
        if fallback_url:
            print('\nDownload page for manual install:', fallback_url)
        return e

def unzip(zip_path, extract_dir_path):
    '''Get a zip path and a directory path to extract to'''
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir_path)

class SWD_OT_download_ffmpeg(bpy.types.Operator):
    """Download if ffmpeg is in path"""
    bl_idname = "swd.download_ffmpeg"
    bl_label = "Download ffmpeg"
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        if sys.platform.startswith('win'):
            self.release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/windows/ffmpeg.exe'
        elif sys.platform.startswith(('linux','freebsd')):
            self.release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/linux/ffmpeg'
        else: # Mac
            self.release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/mac/ffmpeg'

        # Check if an ffmpeg version is already in addon path
        addon_loc = Path(__file__).parent
        self.ffbin = addon_loc / Path(self.release_url).name
        self.exists = self.ffbin.exists()
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if self.exists:
            col.label(text='ffmpeg is already in addon folder, delete and re-download ? (80~100 Mo)', icon='INFO')
        else:
            col.label(text='This will download ffmpeg static release in addon folder (80~100 Mo)', icon='INFO')
            col.label(text='Would you like to continue ?')

    def execute(self, context):
        if self.exists:
            self.ffbin.unlink()

        ## Get ffmpeg static ffmpeg bin
        # dl_url(self.release_url, str(self.ffbin))
        simple_dl_url(self.release_url, str(self.ffbin), fallback_url='https://www.ffmpeg.org/download.html')

        if self.ffbin.exists():
            prefs = get_addon_prefs()
            prefs.path_to_ffmpeg = str(self.ffbin.resolve())

        self.report({'INFO'}, f'Installed: {self.ffbin.resolve()}')
        return {'FINISHED'}


class SWD_sound_waveform_display_addonpref(bpy.types.AddonPreferences):
    bl_idname = __name__.split('.')[0]

    path_to_ffmpeg : StringProperty(
        name="Path to ffmpeg binary",
        description='Set the path to ffmpeg or leave empty if ffmpeg is in your path',
        subtype='FILE_PATH')

    wave_color: FloatVectorProperty(
        name="Waveform Color",
        subtype='COLOR_GAMMA', # 'COLOR'
        size=3,
        default=(0.2392, 0.5098, 0.6941),
        min=0.0, max=1.0,
        description="Color of the waveform")

    wave_detail : EnumProperty(
        name="Waveform Details", description="Precision (by increasing resolution) of the sound waveform", 
        default='4000x1000', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            # ('2000x500', 'Low', 'Resolution of the generated wave image', 0),
            ('4000x1000', 'Medium', 'Resolution of the generated wave image', 0),
            ('8000x2000', 'High', 'Resolution of the generated wave image', 1),
            ('12000x3000', 'Very High', 'Resolution of the generated wave image', 2), # too high
            ))

    height_mode : EnumProperty(
        name="Waveform Height", description="How waveform size adapt to editor height", 
        default='RELATIVE', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('RELATIVE', 'Relative', 'Waveform size is relative and adapt to editor hieght', 0),
            ('ABSOLUTE', 'Absolute', 'Waveform size is absolute and do not change according to editor size', 1),
            ))

    debug : BoolProperty(
        name="Verbose Mode",
        description="Verbose/Debug mode. Enable prints in console to follow script behavior",
        default=False, options={'HIDDEN'})


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.use_property_decorate = False

        box = layout.box()
        box.label(text='Waveform Options:')
        box.prop(self, "wave_color")
        box.prop(self, "wave_detail")
        box.prop(self, "height_mode")
        box.prop(self, "debug")

        box = layout.box()
        box.label(text='FFmpeg check and installation:')
        col = box.column()
        # col.label(text="This addon use ffmpeg to generate the waveform (need a recent version)")

        col.label(text="This addon need an ffmpeg binary")
        row = col.row()
        row.operator('swd.check_ffmpeg', text='Check If FFmpeg In PATH', icon='PLUGIN')
        row.label(text="(Need to be installed if not in PATH)")


        row = col.row()
        row.operator('swd.download_ffmpeg', text='Auto-install FFmpeg', icon='IMPORT')
        row.operator('wm.url_open', text='FFmpeg Download Page', icon='URL').url = 'https://www.ffmpeg.org/download.html'
        # if sys.platform.startswith('win'):
        #     col.operator('swd.download_ffmpeg', text='Auto-install FFmpeg (windows)', icon='IMPORT')

        col.separator()
        col.label(text="Alternatively, you can point to ffmpeg executable:")
        col.label(text="(Leave field empty if ffmpeg is in system PATH)")
        col.prop(self, "path_to_ffmpeg")


### --- REGISTER ---

classes=(
SWD_OT_open_addon_prefs,
SWD_OT_check_ffmpeg,
SWD_OT_download_ffmpeg,
SWD_sound_waveform_display_addonpref,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)