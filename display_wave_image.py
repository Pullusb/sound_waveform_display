import bpy, os
from bpy.types import Operator
from pathlib import Path
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from time import time
from .preferences import get_addon_prefs
import subprocess

sw_coordlist = []
handle = None
image = None
sw_start = 0
sw_end = 100

def draw_callback_px(self, context):
    '''Draw callback use by modal to draw in viewport'''
    # if context.area.type != 'DOPESHEET_EDITOR':
    if context.area.type not in ('DOPESHEET_EDITOR', 'GRAPH_EDITOR'):
        return
    if context.area.type == 'DOPESHEET_EDITOR':
        # available_modes : 'TIMELINE', 'DOPESHEET', 'FCURVES','ACTION','GPENCIL','MASK','CACHEFILE'
        if context.space_data.mode not in ('DOPESHEET', 'FCURVES','ACTION','GPENCIL','MASK','CACHEFILE'):
            return

    margin = 12 * context.preferences.view.ui_scale
    # print('sw_coordlist: ', sw_coordlist)
    
    if context.region:
        coords = [\
            # (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1]*100)+margin)\
            (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1])+margin)\
            for co in sw_coordlist]

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
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

    shader.bind()
    shader.uniform_int("image", 0)
    batch.draw(shader)
    # self.batch_line.draw(shader)
    
    # restore opengl defaults
    # bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_BLEND)


class SWD_OT_enable_draw(Operator):
    bl_idname = "anim.enable_draw"
    bl_label = "Wave display On"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist
        global handle
        global image
        global sw_start
        global sw_end
        # bake the coords in a global variable ?
        # or custom prop
        # or types ?

        # disable handle if launched
        if handle:
            bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle, 'WINDOW')

        strip = context.scene.sequence_editor.active_strip
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
        print('sfp: ', sfp)
        sname = 'waveform.png' # sfp.stem + '_waveform'
        ifp = sfp.parent / sname

        # color : https://ffmpeg.org/ffmpeg-utils.html#Color
        # wave options : https://ffmpeg.org/ffmpeg-filters.html#showwaves
        # showwave pics : https://ffmpeg.org/ffmpeg-filters.html#showwavespic
        # exemples : https://www.zixi.org/archives/478.html
        # scale=lin <- defaut is Fine
        # filter=peak not working yet filter must be dealt differently

        # TODO Optional : separated left right to top-bottom of the area with 
        # split_channels=1 <- use defaut (do not split except if needed)
        
        ## color@0.1 <-- alpha a 10%
        # :draw=full (else scale) # seems to clear line border

        # TODO save in OS temp folder

        # COMPAND off :,compand=gain=-6 (less accurate wave but less flat... fo not seem worthy)
        # MONO out : [0:a]aformat=channel_layouts=mono

        if strip.frame_offset_start != 0 or strip.frame_offset_end != 0:
            print('cutted sound')
            # need to calculate the crop for command
            # Get sound full time
            # fulltime = strip.frame_duration * context.scene.render.fps
            timein = strip.frame_offset_start / context.scene.render.fps # -ss
            # duration = (strip.frame_duration - strip.frame_offset_end - strip.frame_offset_start) / context.scene.render.fps
            duration = strip.frame_final_duration / context.scene.render.fps # -t
            
            cmd = ['ffmpeg',
            '-ss', f'{timein:.2f}',
            '-t', f'{duration:.2f}',
            '-i', str(sfp), 
            '-filter_complex', 
            "[0:a]aformat=channel_layouts=mono,showwavespic=s=2000x400:colors=7FB3CE:draw=full,crop=iw:ih/2:0:0", 
            '-frames:v', '1', '-y', str(ifp)]

            print('timein: ', timein)
            print('duration: ', duration)
        else:
            print('plain sound')
            # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "showwavespic=s=1000x400:colors=blue", '-frames:v', '1', '-y', str(ifp)]
            # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
            # cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "[0:a]aformat=channel_layouts=mono,compand=gain=-6,showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
            cmd = ['ffmpeg', '-i', str(sfp), '-filter_complex', "[0:a]aformat=channel_layouts=mono,showwavespic=s=2000x800:colors=7FB3CE:draw=full", '-frames:v', '1', '-y', str(ifp)]
            cmd = ['ffmpeg', '-i', str(sfp), 
            '-filter_complex', 
            "[0:a]aformat=channel_layouts=mono,showwavespic=s=2000x400:colors=7FB3CE:draw=full,crop=iw:ih/2:0:0", 
            '-frames:v', '1', '-y', str(ifp)]
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
        handle = view_type.draw_handler_add(
                draw_callback_px, args, spacetype, 'POST_PIXEL')

        # store ??
        # bpy.types.ViewLayer.sw_viewtype = 'bpy.types.SpaceDopeSheetEditor'
        # bpy.types.ViewLayer.sw_spacetyper = 'WINDOW'
        # bpy.types.ViewLayer.sw_handle = handle
        # print(context.view_layer.sw_handle)
        return {'FINISHED'}


def disable_waveform_draw_handler():
    global handle
    if handle:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle, 'WINDOW')

class SWD_OT_disable_draw(Operator):
    bl_idname = "anim.disable_draw"
    bl_label = "Wave display off"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist
        global handle
        if handle:
            disable_waveform_draw_handler()
        else:
            self.report({'WARNING'}, 'Handler already disable')
        ## with normal handler
        # if 'name' in [hand.__name__ for hand in bpy.app.handlers.save_pre]:
        #     bpy.app.handlers.save_pre.remove(name)

        handle = None
        return {'FINISHED'}


classes=(
# SWD_OT_opsname,
# SWD_OT_timeline_draw_test,
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