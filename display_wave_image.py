import bpy, os, sys, shutil
import subprocess
import tempfile
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from bpy.types import Operator
from pathlib import Path
from time import time
from .preferences import get_addon_prefs
from . import fn
from bpy.app.handlers import persistent

sw_coordlist = []
handle_dope = None
handle_graph = None
image = None

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

    if not context.region:
        return
    coords = [\
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

    bgl.glEnable(bgl.GL_BLEND) # bgl.GL_SRGB8_ALPHA8
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

    # bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, size, size, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, pixels)
    # bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, sx, sy, 0, bgl.GL_RGBA, bgl.GL_FLOAT, buf)

    # bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA) # same as default ?
    # bgl.glBlendFunc(bgl.GL_DST_COLOR, bgl.GL_ZERO) # alpha is black
    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE) # overlay with a kind of additive filter
    # bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)

    shader.bind()

    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

    shader.uniform_int("image", 0)
    batch.draw(shader)

    ## restore opengl defaults
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

        prefs = get_addon_prefs()
        dbg = prefs.debug
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

        ## disable handle_dope if launched
        try:
            if handle_dope:
                bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle_dope, 'WINDOW')
            if handle_graph:
                bpy.types.SpaceGraphEditor.draw_handler_remove(handle_graph, 'WINDOW')
        except:
            print('Handler was already removed')
            pass

        ## initialize
        source = context.scene.swd_settings.source
        vse_tgt = context.scene.swd_settings.vse_target
        # spk_tgt = context.scene.swd_settings.spk_target


        temp_dir = Path(tempfile.gettempdir())
        sname = 'tmp_scene_waveform.png'
        tmp_sound_name = 'tmp_scene_mixdown.wav'
        ifp = temp_dir / sname # temp files
        mixdown_path = temp_dir / tmp_sound_name


        vse = context.scene.sequence_editor
        all_sound_strips = [s for s in vse.sequences if s.type == 'SOUND']
        speakers = [o for o in context.scene.objects if o.type == 'SPEAKER' and not o.data.muted and not o.hide_viewport]
        
        if source == 'ALL' and not all_sound_strips and not speakers:
            self.report({'ERROR'}, 'No sound strip in sequencer and no speaker in scene!')
            return {'CANCELLED'}
        
        if source == 'SEQUENCER' and not all_sound_strips:
            self.report({'ERROR'}, 'No sound strip in sequencer!')
            return {'CANCELLED'}
        
        if source == 'SPEAKERS' and not speakers:
            self.report({'ERROR'}, 'No unmuted speaker in scene!')
            return {'CANCELLED'}

        if dbg: print('--- Display Sound Waveform')

        sfp = mixdown_path

        if source == 'ALL' and not speakers:
            # Use VSE range optimisation
            source = 'SEQUENCER'
            vse_tgt = 'SCENE'

        if source == 'ALL':
            sw_start, sw_end = fn.mixdown(filepath=mixdown_path, source=source)

        elif source == 'SPEAKERS':
            sw_start, sw_end = fn.mixdown(filepath=mixdown_path, source=source)

        elif source == 'SEQUENCER':
            strips = []
            if vse_tgt == 'SELECTED':
                strips = [s for s in all_sound_strips if s.select or (s == vse.active_strip)]
                if not strips:
                    self.report({'ERROR'}, 'No selected sound strip!')
                    return {'CANCELLED'}
            
            if vse_tgt == 'LIST':
                if context.scene.swd_settings.seq_idx < 0:
                    self.report({'ERROR'}, 'Must select a sound in list')
                    return {'CANCELLED'}
                the_strip = vse.sequences[context.scene.swd_settings.seq_idx]
                if the_strip.type != 'SOUND':
                    self.report({'ERROR'}, 'Must select a sound in list (active index is not a sound)')
                    return {'CANCELLED'}
                strips = [the_strip]

            elif vse_tgt == 'UNMUTED':
                strips = [s for s in all_sound_strips if not s.mute]
                if not strips:
                    self.report({'ERROR'}, 'No unmuted sound strip!')
                    return {'CANCELLED'}

            elif vse_tgt == 'SCENE':
                strips = fn.get_sound_strip_in_scene_range(vse)
                if not strips:
                    self.report({'ERROR'}, 'No sound strip within scene range!')
                    return {'CANCELLED'}


            sw_start, sw_end = fn.mixdown(filepath=mixdown_path, source=source, vse_tgt=vse_tgt)


        if sw_start is None:
                self.report({'ERROR'}, sw_end)
                return {'CANCELLED'}

        if dbg: print('sound path: ', sfp)

        # color : https://ffmpeg.org/ffmpeg-utils.html#Color
        # wave options : https://ffmpeg.org/ffmpeg-filters.html#showwaves
        # showwave pics : https://ffmpeg.org/ffmpeg-filters.html#showwavespic
        # exemples : https://www.zixi.org/archives/478.html
        # scale=lin <- defaut is Fine
        # filter=peak not working yet, filter must be dealt differently

        # split_channels=1 <- use defaut (do not split except if needed)

        ## color@0.1 <-- alpha a 10%
        # :draw=full (else scale) # seems to clear line border

        # COMPAND off :,compand=gain=-6 (less accurate wave but less flat... do not seem worthy)
        # MONO out : [0:a]aformat=channel_layouts=mono

        hex_colo = fn.rgb_to_hex(prefs.wave_color)

        img_res = prefs.wave_detail

        cmd += ['-i', str(sfp), 
        '-hide_banner', 
        '-loglevel', 'error',
        '-filter_complex', 
        f"[0:a]aformat=channel_layouts=mono,showwavespic=s={img_res}:colors={hex_colo}:draw=full,crop=iw:ih/2:0:0",
        '-frames:v', '1', 
        '-y', str(ifp)]
        # "[0:a]aformat=channel_layouts=mono,showwavespic=s=4000x1000:colors=3D82B1", # Static filter line
        
        if dbg: print('cmd:', ' '.join(list(map(str, cmd)))) # print final cmd

        t0 = time()
        ret = subprocess.call(cmd)
        if ret != 0:
            self.report({'ERROR'}, '--- problem generating sound wave image')
            return {'CANCELLED'}

        if dbg: print(f'Generated sound waveform: {time() - t0:.3f}s')
        if not ifp.exists():
            self.report({'ERROR'}, f'Waveform not generated at : {ifp}')
            return {'CANCELLED'}

        image = bpy.data.images.get(sname)
        if image:
            bpy.data.images.remove(image)

        image = bpy.data.images.load(str(ifp), check_existing=False)

        sw_frames = sw_end - sw_start
        height = (sw_frames * image.size[1]) // image.size[0]
        if dbg: print(f'image generated at {ifp}')

        ## show full image
        sw_coordlist = ((sw_start, 0),
                        (sw_end, 0),
                        (sw_end, height),
                        (sw_start, height))

        ## show at half-height position
        # half = height // 2
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

        ## Ensure to delete mixdown sound after generating waveform
        if sfp.exists() and sfp.name == tmp_sound_name:
            try:
                sfp.unlink()
            except Exception as e:
                print(f'! impossible to remove: {sfp}\n\n{e}')
        return {'FINISHED'}


def disable_waveform_draw_handler():
    global handle_dope
    global handle_graph
    stopped = []
    if handle_dope:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle_dope, 'WINDOW')
        handle_dope = None
        stopped.append('Dopesheet display')
    if handle_graph:
        bpy.types.SpaceGraphEditor.draw_handler_remove(handle_graph, 'WINDOW')
        handle_graph = None
        stopped.append('Graph display')
    refresh()
    return stopped

class SWD_OT_disable_draw(Operator):
    bl_idname = "anim.disable_draw"
    bl_label = "Wave display off"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist

        stopped = disable_waveform_draw_handler()
        if not stopped:
            self.report({'WARNING'}, 'Already disabled')

        return {'FINISHED'}

classes=(
SWD_OT_enable_draw,
SWD_OT_disable_draw,
)

@persistent
def disable_wave_on_load(dummy):
    disable_waveform_draw_handler()

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_pre.append(disable_wave_on_load)

def unregister():
    disable_waveform_draw_handler()
    if 'disable_wave_on_load' in [hand.__name__ for hand in bpy.app.handlers.load_pre]:
        bpy.app.handlers.load_pre.remove(disable_wave_on_load)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)