import bpy
import sys
import os
import subprocess
import shutil
import tempfile
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

def get_ffmpeg_version(ffpath='ffmpeg'):

    try:
        ret = subprocess.run(args=[ffpath, '-version'], text=True, capture_output=True)
    except Exception:
        print(f'impossible to check ffmpeg version at : {ffpath}')
        return 'Error checking version'

    if ret.stderr:
        ret = ret.stderr
    else:
        ret = ret.stdout

    if get_addon_prefs().debug:
        print()
        print(f'Path: {ffpath}')
        print('Version:')
        print(ret)

    line = ret.split('\n')[0]
    if not 'version' in line.lower():
        return 'Could not get version'
    return line.split(' Copyright')[0]

class SWD_OT_check_ffmpeg(bpy.types.Operator):
    """check if ffmpeg is in path"""
    bl_idname = "swd.check_ffmpeg"
    bl_label = "Check FFmpeg"
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        prefs = get_addon_prefs()
        import shutil
        self.sys_path_ok = shutil.which('ffmpeg')

        self.sys_path_version = None
        self.ffbin = None
        self.local_version = None

        self.ffmpeg_at_path = None
        self.ffmpeg_at_path_version = None

        if prefs.path_to_ffmpeg and Path(prefs.path_to_ffmpeg).exists():
            self.ffmpeg_at_path = prefs.path_to_ffmpeg
            self.ffmpeg_at_path_version = get_ffmpeg_version(prefs.path_to_ffmpeg)

        # check for executable
        self.local_ffmpeg = False
        if sys.platform.startswith('win'):
            self.ffbin = Path(__file__).parent / 'ffmpeg.exe'
            self.local_ffmpeg = self.ffbin.exists()
        else:
            # Mac / linux
            self.ffbin = Path(__file__).parent / 'ffmpeg'
            self.local_ffmpeg = self.ffbin.exists()
        
        if self.local_ffmpeg:
            self.ffbin = str(self.ffbin)
            self.local_version = get_ffmpeg_version(self.ffbin)

        if self.sys_path_ok:
            self.sys_path_version = get_ffmpeg_version()

        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout

        if self.ffmpeg_at_path:
            box = layout.box()
            col = box.column()
            col.label(text='This executable will be used', icon='INFO')
            col.label(text='ffmpeg at specified path', icon='CHECKMARK')
            col.label(text=self.ffmpeg_at_path, icon='FILE')
            col.label(text=self.ffmpeg_at_path_version)

        elif self.local_ffmpeg:
            box = layout.box()
            col = box.column()
            col.label(text='This executable will be used', icon='INFO')
            col.label(text='ffmpeg in addon folder', icon='CHECKMARK')
            col.label(text=self.ffbin, icon='PLUGIN')
            col.label(text=self.local_version)

        if self.sys_path_ok:
            box = layout.box()
            col = box.column()
            if not self.ffmpeg_at_path and not self.local_ffmpeg:
                col.label(text='This executable will be used', icon='INFO')
            col.label(text='ffmpeg in system PATH', icon='CHECKMARK')
            col.label(text=self.sys_path_ok, icon='SYSTEM')
            col.label(text=self.sys_path_version)

        else:
            layout.label(text='ffmpeg is not in system PATH', icon='X') # CANCEL

    def execute(self, context):
        return {'FINISHED'}

class SWD_OT_remove_ffmpeg(bpy.types.Operator):
    """remove local ffmpeg in folder"""
    bl_idname = "swd.remove_ffmpeg"
    bl_label = "Remove ffmpeg"
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        # check for executable
        self.local_ffmpeg = False
        if sys.platform.startswith('win'):
            self.ffbin = Path(__file__).parent / 'ffmpeg.exe'
            self.local_ffmpeg = self.ffbin.exists()
        else:
            # Mac / linux
            self.ffbin = Path(__file__).parent / 'ffmpeg'
            self.local_ffmpeg = self.ffbin.exists()
        
        if self.local_ffmpeg:
            try:
                os.remove(self.ffbin)
                self.mess = f'Local ffmpeg removed from addon folder'
            except Exception as e:
                print(e)
                self.mess = f'Error: Could not remove local ffmpeg file'
        else:
            self.mess = 'No ffmpeg file found in addon folder'

        return context.window_manager.invoke_props_dialog(self, width=700)

    def draw(self, context):
        layout = self.layout
        layout.label(text='Executable path:')
        layout.label(text=str(self.ffbin))
        layout.label(text=self.mess)

        if self.mess.startswith('Error'):
            layout.label(text='Try removing ffmpeg executable manually')
            layout.operator('wm.path_open', text='Open addon folder', icon='FILE_FOLDER').filepath = str(Path(__file__).parent)

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
    """Download if ffmpeg is not in path"""
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
            ('RELATIVE', 'Relative', 'Waveform size is relative and adapt to editor height', 0),
            ('ABSOLUTE', 'Absolute', 'Waveform size is absolute and do not change according to editor size', 1),
            ))

    debug : BoolProperty(
        name="Debug Mode",
        description="Enable prints in console to follow script behavior\
            \nkeep mixdown audio in temp folder for inspection",
        default=False, options={'HIDDEN'})

    show_help : BoolProperty(
        name="Help for manual ffmpeg install",
        description="This addon need ffmpeg, This quick help show the step for manual installation",
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

        if self.debug:
            dbox = box.box()
            # dbox.label(text='Debug mode add prints in console', icon='INFO')
            col = dbox.column()
            col.label(text='Debug tools:')
            col.label(text='Audio mix and Waveform image are generated in operating system "temp" folder')
            col.label(text='- Waveform image file is named ".tmp_scene_waveform.png"')
            col.label(text='- Sound Mixdown file is named "tmp_scene_mixdown.wav"')
            # col.label(text='While debug is enabled, audio file will not be removed from temp folder')
            col.operator('wm.path_open', text='Open Temp Folder', icon='FILE_FOLDER').filepath = str(Path(tempfile.gettempdir()))
            
            col.separator()
            col.label(text='When using ffmpeg auto-install below, ffmpeg executable is placed in addon folder')
            col.label(text='If no waveform are generated you can try removing ffmpeg executable')
            col.label(text='or point to another using below path')
            col.operator('wm.path_open', text='Open addon folder', icon='FILE_FOLDER').filepath = str(Path(__file__).parent)
            

        box = layout.box()
        box.label(text='FFmpeg check and auto-installation:')
        
        col = box.column()
        # col.label(text="This addon use ffmpeg to generate the waveform (need a recent version)")

        col.label(text="This addon need an ffmpeg binary (Need to be installed if not in PATH)")
        row = col.row()
        row.operator('swd.check_ffmpeg', text='Check if FFmpeg is ready', icon='PLUGIN')
        # row = col.row()
        row = col.row(align=True)
        row.operator('swd.download_ffmpeg', text='Auto-install FFmpeg', icon='IMPORT')
        row.operator('swd.remove_ffmpeg', text='Remove auto-installed', icon='X')

        # row.operator("wm.call_menu", text="Ffmpeg Manual Install Help", icon='HELP').name = "SWD_MT_help_ffmpeg_install"
        # row.operator('wm.url_open', text='FFmpeg Download Page', icon='URL').url = 'https://www.ffmpeg.org/download.html'

        col.separator()
        col.label(text="Alternatively, you can point to ffmpeg executable:")
        col.label(text="(Can leave field empty if ffmpeg is in system PATH or executable is in addon folder)")
        col.prop(self, "path_to_ffmpeg")
        

        ## Manual install helper (big button)
        box = layout.box()
        title_row = box.row()
        title_row.use_property_split = False
        title_row.scale_y = 2
        title_row.prop(self, 'show_help', icon='HELP')

        if self.show_help:
            help_infos(box)


def help_infos(layout):

    col = layout.column()
    col.label(text='FFmpeg Manual Installation')
    col.separator()
    col.label(text='If the auto-install fails, here are steps for manual installation')
    
    ## Direct download links
    if sys.platform.startswith('win'):
        user_os = 'Windows'
        release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/windows/ffmpeg.exe'
    elif sys.platform.startswith(('linux','freebsd')):
        user_os = 'Linux'
        release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/linux/ffmpeg'
    else: # Mac
        user_os = 'Mac'
        release_url = 'https://github.com/Pullusb/static_bin/raw/main/ffmpeg/mac/ffmpeg'
    
    col.label(text='Step 1: Download ffmpeg', icon='IMPORT')

    col.label(text="Direct download link (From dedicated Pullusb repository):")
    col.operator('wm.url_open', text=f'Direct Download FFmpeg for {user_os}', icon='URL').url = release_url
    if user_os == 'Mac':
        col.label(text='/!\ Note for Mac user: This ffmpeg bin is not compatible with Mac M1!')
    
    col.separator()
    col.label(text='Alternative Step 1: Download ffmpeg yourself from ffmpeg website:', icon='IMPORT')
    col.operator('wm.url_open', text='FFmpeg Download Page', icon='URL').url = 'https://www.ffmpeg.org/download.html'

    col.separator()
    col.separator()
    col.label(text='Step 2: Move it into addon', icon='PASTEDOWN')
    col.label(text="Copy ffmpeg file into addon folder")
    col.operator('wm.path_open', text='Click here to open addon folder', icon='FILE_FOLDER').filepath = str(Path(__file__).parent)
    
    col.separator()
    col.label(text='Alternative Step 2: Enter ffmpeg path', icon='PASTEDOWN')
    col.label(text="Tell the addon which file to execute if not placed in addon folder")
    col.prop(get_addon_prefs(), 'path_to_ffmpeg')


# class SWD_MT_help_ffmpeg_install(bpy.types.Menu):
#     bl_label = "Help FFmpeg Install"
#     def draw(self, context):
#         layout = self.layout

#         help_infos(layout)


### --- REGISTER ---

classes=(
SWD_OT_open_addon_prefs,
SWD_OT_check_ffmpeg,
SWD_OT_remove_ffmpeg,
SWD_OT_download_ffmpeg,
# SWD_MT_help_ffmpeg_install,
SWD_sound_waveform_display_addonpref,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)