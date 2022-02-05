import bpy, os, sys, shutil
from bpy.types import Operator
from pathlib import Path
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from time import time
from .preferences import get_addon_prefs, open_addon_prefs
import subprocess
import tempfile

sw_coordlist = []
handle_dope = None
handle_graph = None
image = None
sw_start = 0
sw_end = 100

def show_message_box(_message = "", _title = "Message Box", _icon = 'INFO'):
    '''Show message box with element passed as string or list
    if _message if a list of lists:
        if sublist have 2 element:
            considered a label [text,icon]
        if sublist have 3 element:
            considered as an operator [ops_id_name, text, icon]
    '''

    def draw(self, context):
        for l in _message:
            if isinstance(l, str):
                self.layout.label(text=l)
            else:
                if len(l) == 2: # label with icon
                    self.layout.label(text=l[0], icon=l[1])
                elif len(l) == 3: # ops
                    self.layout.operator_context = "INVOKE_DEFAULT"
                    self.layout.operator(l[0], text=l[1], icon=l[2], emboss=False) # <- True highligh the entry
    
    if isinstance(_message, str):
        _message = [_message]
    bpy.context.window_manager.popup_menu(draw, title = _title, icon = _icon)

class SWD_OT_open_addon_prefs(Operator):
    bl_idname = "swd.open_addon_prefs"
    bl_label = "Open Addon Prefs"
    bl_description = "Open user preferences window in addon tab and prefill the search with addon name"
    bl_options = {"REGISTER"}

    def execute(self, context):
        open_addon_prefs()
        return {'FINISHED'}

def refresh():
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type in ('GRAPH_EDITOR',  'DOPESHEET_EDITOR'):
                area.tag_redraw()

def draw_callback_px(self, context):
    '''Draw callback use by modal to draw in viewport'''
    if context.area.type not in ('DOPESHEET_EDITOR', 'GRAPH_EDITOR'):
        return
    if context.area.type == 'DOPESHEET_EDITOR':
        # available modes : 'TIMELINE', 'DOPESHEET', 'FCURVES','ACTION','GPENCIL','MASK','CACHEFILE'
        if context.space_data.mode == 'TIMELINE':
            if not context.scene.swd_settings.use_time:
                return
        else:
            if not context.scene.swd_settings.use_dope:
                return
        # if context.space_data.mode not in ('DOPESHEET', 'FCURVES','ACTION','GPENCIL','MASK','CACHEFILE'):
        #     return
    if context.area.type == 'GRAPH_EDITOR' and not context.scene.swd_settings.use_graph:
        return

    margin = 12 * context.preferences.view.ui_scale
    # print('sw_coordlist: ', sw_coordlist)
    
    if not context.region:
        return
    coords = [\
        # (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1]*100)+margin)\
        # (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1])+margin)\
        [context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1])+margin]\
        for co in sw_coordlist]

    ## Absolute offset
    coords[2][1] += context.scene.swd_settings.height_offset
    coords[3][1] += context.scene.swd_settings.height_offset

    shader = gpu.shader.from_builtin('2D_IMAGE')
    batch = batch_for_shader(
        shader, 'TRI_FAN',
        {
            "pos": coords,
            "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
        },
    )
    
    if image.gl_load():
        raise Exception()

    # TODO : modulate opacity
    # TODO : adjust height with a interface linked slider


    bgl.glEnable(bgl.GL_BLEND) # bgl.GL_SRGB8_ALPHA8
    # bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

    ## TODO how to tweak transparency
    # bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, size, size, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, pixels)
    # bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, sx, sy, 0, bgl.GL_RGBA, bgl.GL_FLOAT, buf)

    # bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA) # looks like default...
    # bgl.glBlendFunc(bgl.GL_DST_COLOR, bgl.GL_ZERO) # alpha is black
    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE) # interesting : like an additive filter
    # bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

    shader.bind()

    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
    # shader.uniform_float("color", (0.8,0.1,0.1,0.5)) # how set color/transparency ?
    shader.uniform_int("image", 0)
    batch.draw(shader)
    # self.batch_line.draw(shader)
    
    # restore opengl defaults
    # bgl.glLineWidth(1)
    # bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_BLEND)


class SWD_OT_enable_draw(Operator):
    bl_idname = "anim.enable_draw"
    bl_label = "Wave display On"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist
        global handle_dope
        global handle_graph
        global image
        global sw_start
        global sw_end
        # bake the coords in a global variable ?
        # or custom prop
        # or types ?


        prefs = get_addon_prefs()
        ffbin = Path(__file__).parent / 'ffmpeg.exe'
            
        cmd = ['ffmpeg',]
        
        if prefs.path_to_ffmpeg:
            ffpath = Path(prefs.path_to_ffmpeg)
            if ffpath.exists() and ffpath.is_file():
                cmd = [prefs.path_to_ffmpeg] # replace ffmpeg bin
            else:
                self.report({'ERROR'}, "Invalid path to ffmpeg in the addon preference")
                return {'CANCELLED'}      
        
        elif ffbin.exists():
            cmd = [str(ffbin)]
        
        else:
            if not shutil.which('ffmpeg'):
                show_message_box(_title = "No ffmpeg found", _icon = 'INFO',
                    _message =[
                            "ffmpeg is needed to display wave, see addon prefs",
                            ["swd.open_addon_prefs", "Click here to open addon prefs", "PREFERENCES"] # TOOL_SETTINGS
                        ])
                return {'CANCELLED'}

        ## auto-override ffmpeg bin if one in folder ?
        # else:
        #     if sys.platform.startswith('win'):
        #         winbin_path = Path(__file__).paremt / 'ffmpeg.exe'
        #         if winbin_path.exists():
        #             cmd = [str(winbin_path)] # replace ffmpeg bin

        # disable handle_dope if launched
        if handle_dope:
            bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle_dope, 'WINDOW')
        if handle_graph:
            bpy.types.SpaceGraphEditor.draw_handler_remove(handle_graph, 'WINDOW')

        
        strip = context.scene.sequence_editor.active_strip
        all_sound_strips = [s for s in context.scene.sequence_editor.sequences if s.type == 'SOUND']
        if len(all_sound_strips) == 1:
            strip = all_sound_strips[0]
        if not strip:
            self.report({'ERROR'}, 'No active strip')
            return ({'CANCELLED'})
        if strip.type != 'SOUND':
            self.report({'ERROR'}, 'active VSE strip is not sound type')
            return ({'CANCELLED'})
        

        sw_start = strip.frame_final_start
        sw_end = strip.frame_final_end
        sfp = os.path.abspath(bpy.path.abspath(strip.sound.filepath))
        
        sfp = Path(sfp)

        if not sfp.exists():
            if strip.sound.packed_file:
                # TODO need to support auto-export/unpack
                self.report({'ERROR'}, 'Sound strip must be unpacked to be used')
                return ({'CANCELLED'})
            else:
                self.report({'ERROR'}, f'Sound not found at: {sfp}')
                return ({'CANCELLED'})

        if strip.mute:
            self.report({'WARNING'}, f'Used sound strip is muted : {strip.name}')
        else:
            self.report({'INFO'}, f'Wave from: {strip.name}')

        print('sfp: ', sfp)
        sname = 'waveform.png' # sfp.stem + '_waveform'
        
        # ifp = sfp.parent / sname # same folder as the source video
        ifp = Path(tempfile.gettempdir()) / sname # temp files

        # color : https://ffmpeg.org/ffmpeg-utils.html#Color
        # wave options : https://ffmpeg.org/ffmpeg-filters.html#showwaves
        # showwave pics : https://ffmpeg.org/ffmpeg-filters.html#showwavespic
        # exemples : https://www.zixi.org/archives/478.html
        # scale=lin <- defaut is Fine
        # filter=peak not working yet filter must be dealt differently

        # split_channels=1 <- use defaut (do not split except if needed)
        
        ## color@0.1 <-- alpha a 10%
        # :draw=full (else scale) # seems to clear line border

        # COMPAND off :,compand=gain=-6 (less accurate wave but less flat... fo not seem worthy)
        # MONO out : [0:a]aformat=channel_layouts=mono

        if strip.frame_offset_start != 0 or strip.frame_offset_end != 0:
            print('Trimmed sound')
            # need to calculate the crop for command
            # Get sound full time
            fulltime = strip.frame_duration * context.scene.render.fps

            timein = strip.frame_offset_start / context.scene.render.fps # -ss

            # duration = (strip.frame_duration - strip.frame_offset_end - strip.frame_offset_start) / context.scene.render.fps
            duration = strip.frame_final_duration / context.scene.render.fps # -t

            if timein != 0:
                cmd += ['-ss', f'{timein:.2f}']
                print(f'Cutted start at {timein:.2f}')
            if duration != fulltime:
                cmd += ['-t', f'{duration:.2f}']
                print(f'reduced duration to {duration:.2f}')

        # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "showwavespic=s=1000x400:colors=blue", '-frames:v', '1', '-y', str(ifp)]
        # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
        # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "[0:a]aformat=channel_layouts=mono,compand=gain=-6,showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
        # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "[0:a]aformat=channel_layouts=mono,showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
        print('sfp: ', sfp)
        cmd += ['-i', str(sfp), 
        '-hide_banner', '-loglevel', 'error',
        '-filter_complex', 
        "[0:a]aformat=channel_layouts=mono,showwavespic=s=8192x2048:colors=3D82B1:draw=full,crop=iw:ih/2:0:0", 
        '-frames:v', '1', '-y', str(ifp)]

        # blue clear 7FB3CE
        # 3D82B1
        # 30668B
        # 244D69
        # 1A374B        
        # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "showwavespic=s=4000x1600", '-frames:v', '1', '-y', str(ifp)]
        print('\ncmd:', ' '.join(list(map(str, cmd)))) # print final cmd
        
        t0 = time()
        ret = subprocess.call(cmd)
        if ret != 0:
            self.report({'ERROR'}, '--- problem generating sound wave image')
            return ({'CANCELLED'})

        print(f'Generated sound waveform: {time() - t0:.2f}s')
        if not ifp.exists():
            self.report({'ERROR'}, f'Waveform not generated at : {ifp}')
            return ({'CANCELLED'})
        
        image = bpy.data.images.get(sname)
        if image:
            bpy.data.images.remove(image)

        image = bpy.data.images.load(str(ifp), check_existing=False)
        # TODO background mixdown of scene sound in temp

        
        height = ((sw_end - sw_start) * image.size[1]) // image.size[0]
        half = height // 2
        # print(f'image generated at {ifp}')
        # sw_coordlist = ((100, 100), (600, 100), (600, 200), (100, 200)) # test

        ## full image
        sw_coordlist = ((sw_start, 0),
                        (sw_end, 0),
                        (sw_end, height),
                        (sw_start, height))
        
        ## half height position (if not cutted)
        # sw_coordlist = ((sw_start, -half),
        #                 (sw_end, -half),
        #                 (sw_end, half),
        #                 (sw_start, half))
        
        ## enable handler
        view_type = bpy.types.SpaceDopeSheetEditor
        spacetype = 'WINDOW' # 'PREVIEW'
        args = (self, context)
        handle_dope = view_type.draw_handler_add(
                draw_callback_px, args, spacetype, 'POST_PIXEL')
        
        handle_graph = bpy.types.SpaceGraphEditor.draw_handler_add(
                draw_callback_px, args, spacetype, 'POST_PIXEL')

        refresh()
        # store ??
        # bpy.types.ViewLayer.sw_viewtype = 'bpy.types.SpaceDopeSheetEditor'
        # bpy.types.ViewLayer.sw_spacetyper = 'WINDOW'
        # bpy.types.ViewLayer.sw_handle = handle
        # print(context.view_layer.sw_handle)
        return {'FINISHED'}


def disable_waveform_draw_handler():
    global handle_dope
    global handle_graph
    stopped = []
    if handle_dope:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle_dope, 'WINDOW')
        handle_dope = None
        stopped.append('dopesheet display')
    if handle_graph:
        bpy.types.SpaceGraphEditor.draw_handler_remove(handle_graph, 'WINDOW')
        handle_graph = None
        stopped.append('graph display')
    refresh()
    return stopped

class SWD_OT_disable_draw(Operator):
    bl_idname = "anim.disable_draw"
    bl_label = "Wave display off"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist
        # global handle_dope
        # global handle_dope
        stopped = disable_waveform_draw_handler()
        if not stopped:
            self.report({'WARNING'}, 'Handler already disable')
        ## with normal handler
        # if 'name' in [hand.__name__ for hand in bpy.app.handlers.save_pre]:
        #     bpy.app.handle_dopers.save_pre.remove(name)

        return {'FINISHED'}


classes=(
# SWD_OT_opsname,
# SWD_OT_timeline_draw_test,
SWD_OT_open_addon_prefs,
SWD_OT_enable_draw,
SWD_OT_disable_draw,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    disable_waveform_draw_handler()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)