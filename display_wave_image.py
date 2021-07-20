import bpy, os
from bpy.types import Operator
from pathlib import Path
import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from .preferences import get_addon_prefs
import subprocess

sw_coordlist = []
handle = None

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

    print('coords: ', coords)
    print(context.area.width, context.area.height)
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR') # initiate shader
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glLineWidth(2)
    
    batch_line = batch_for_shader(
        shader, 'LINE_STRIP', {"pos": coords})
    shader.bind()
    shader.uniform_float("color", (0.01, 0.64, 1.0, 0.7))
    batch_line.draw(shader)
    # self.batch_line.draw(shader)
    
    # restore opengl defaults
    bgl.glLineWidth(1)
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
        # bake the coords in a global variable ?
        # or custom prop
        # or types ?

        strip = context.scene.sequence_editor.active_strip
        if not strip:
            self.report({'ERROR'}, 'No active strip')
            return ({'CANCELLED'})
        if strip.type != 'SOUND':
            self.report({'ERROR'}, 'active VSE strip is not sound type')
            return ({'CANCELLED'})
        sframe = strip.frame_final_start
        sfp = os.path.abspath(bpy.path.abspath(strip.sound.filepath))
        
        sfp = Path(sfp)
        print('sfp: ', sfp)
        sname = 'waveform.png' # sfp.stem + '_waveform'
        # TODO save in OS temp folder

        cmd = ['ffmpeg', '-i', sfp, '-filter_complex', "showwavespic=s=720x180", '-frames:v', '1', str(sfp.parent / sname)]
        ret = subprocess.call(cmd)
        if ret != 0:
            print('--- problem generating sound wave image')

        sw_coordlist = [(10,10),(300,150),(400,500), (800, 100)]

        # TODO background mixdown of scene sound in temp

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


class SWD_OT_disable_draw(Operator):
    bl_idname = "anim.disable_draw"
    bl_label = "Wave display off"
    bl_description = "Active the display"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global sw_coordlist
        global handle
        if handle:
            # self.viewtype.draw_handler_remove(self._handle, self.spacetype)
            bpy.types.SpaceDopeSheetEditor.draw_handler_remove(handle, 'WINDOW')
            context.area.tag_redraw()
        else:
            self.report({'WARNING'}, 'Handler already disable')
        ## with normal handler
        # if 'name' in [hand.__name__ for hand in bpy.app.handlers.save_pre]:
        #     bpy.app.handlers.save_pre.remove(name)

        handle = None
        return {'FINISHED'}

class SWD_OT_timeline_draw_test(Operator):
    bl_idname = "anim.timeline_draw_test"
    bl_label = "Wave display test"
    bl_description = "Run test"
    bl_options = {"REGISTER"} # INTERNAL , "UNDO"

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):

        #### Prepare batchs to draw static parts
        # shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')  # initiate shader
        # self.batch_line = batch_for_shader(
        #     shader, 'LINE_STRIP', {"pos": [(10,10),(300,150),(400,500)]})

        args = (self, context)
        # self.viewtype = None
        # self.spacetype = 'WINDOW'  # is PREVIEW for VSE, needed for handler remove

        # if context.space_data.type == 'VIEW_3D':
        #     self.viewtype = bpy.types.SpaceView3D
        #     self._handle = bpy.types.SpaceView3D.draw_handler_add(
        #         draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        # elif context.space_data.type == 'SEQUENCE_EDITOR':
        #     self.viewtype = bpy.types.SpaceSequenceEditor
        #     self.spacetype = 'PREVIEW'
        #     self._handle = bpy.types.SpaceSequenceEditor.draw_handler_add(
        #         draw_callback_px, args, 'PREVIEW', 'POST_PIXEL')

        # elif context.space_data.type == 'CLIP_EDITOR':
        #     self.viewtype = bpy.types.SpaceClipEditor
        #     self._handle = bpy.types.SpaceClipEditor.draw_handler_add(
        #         draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        
        ## BAKING
        bpy.types.Scene.wd_bake_prop = bpy.props.FloatProperty()
        org_frame = context.scene.frame_current

        strip = context.scene.sequence_editor.active_strip
        if not strip:
            self.report({'ERROR'}, 'No active strip')
            return ({'CANCELLED'})
        if strip.type != 'SOUND':
            self.report({'ERROR'}, 'active VSE strip is not sound type')
            return ({'CANCELLED'})

        # store
        sframe = strip.frame_final_start
        print('startframe: ', sframe)
        sfp = os.path.abspath(bpy.path.abspath(strip.sound.filepath))
        fps = context.scene.render.fps
        context.scene.frame_current = sframe

        ## 1 create an fcurve, 2 make it show up, 3 select only this one before bake
        context.scene.keyframe_insert('wd_bake_prop')
        fcufilter = context.space_data.dopesheet.filter_fcurve_name
        context.space_data.dopesheet.filter_fcurve_name = 'wd_bake_prop'

        act = None
        for action in bpy.data.actions:
            if not action.name.startswith('SceneAction'):
                continue
            if action.fcurves.find('wd_bake_prop'):
                act = action
                break
        
        if not act:
            self.report({'ERROR'}, 'Action containing wd_bake_prop not found')
            return ({'CANCELLED'})
        
        print('act: ', act.name)

        fcu = act.fcurves.find('wd_bake_prop')
        if not fcu:
            self.report({'ERROR'}, 'baking prop wd_bake_prop not found')
            return ({'CANCELLED'})

        fcu.select = True

        # Bakes a sound wave to selected F-Curves
        print(1, fcu.data_path, len(fcu.keyframe_points))
        bpy.ops.graph.sound_bake(filepath=sfp, 
        show_multiview=False, use_multiview=False, display_type='DEFAULT', sort_method='DEFAULT', 
        low=0,
        high=100000,
        attack=0.005,
        release=0.2,
        threshold=0,
        use_accumulate=False,
        use_additive=False,
        use_square=False,
        sthreshold=0.1)
        fcu.update()
        print(2, fcu.data_path, len(fcu.keyframe_points))
        point_coord = [p.co for p in fcu.sampled_points] # from sampled points
        # print('point_coord: ', len(point_coord))

        ### Dosn't work... Need to directly sample from ffmpeg...

        # bpy.ops.graph.unbake() # convert to real points (can access sampled points but needed to clean/smooth)
        # fcu.update()

        # print(3, fcu.data_path, len(fcu.keyframe_points))
        # bpy.ops.graph.clean(threshold=0.001, channels=False) # avoid flats
        # fcu.update()

        # print(4, fcu.data_path, len(fcu.keyframe_points))
        # bpy.ops.graph.smooth()
        # fcu.update()


        # print(fcu.data_path, len(fcu.keyframe_points))
        # point_coord = [p.co for p in fcu.keyframe_points]
        # print('point_coord: ', point_coord[:15])
        

        # restore
        context.scene.frame_current = org_frame
        context.scene.render.fps = fps
        context.space_data.dopesheet.filter_fcurve_name = fcufilter

        ## PREPARE DRAWING
        # self.coords = [(10,10),(300,150),(400,500)]
        # fcu = bpy.data.actions['CubeAction'].fcurves[0]
        # delete fcurve and aciton if needed
        act.fcurves.remove(fcu)
        if not len(act.fcurves):
            bpy.data.actions.remove(act)

        ## get max height to normalize (else use 1)
        max_level = max(point_coord,  key=lambda x: x[1])
        print('max_level: ', max_level)
        # self.ui_scale = context.preferences.view.ui_scale
        # 10 pixel bottom margin * user ui scale (gutter)
        self.org_coords = self.coords = point_coord
        ## DOPESHEET_EDITOR
        self.viewtype = bpy.types.SpaceDopeSheetEditor
        self.spacetype = 'WINDOW' # 'PREVIEW'
        self._handle = self.viewtype.draw_handler_add(
                draw_callback_px, args, self.spacetype, 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        # context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _exit_modal(self, context):
        self.viewtype.draw_handler_remove(self._handle, self.spacetype)
        # context.area.tag_redraw()

    def modal(self, context, event):
        ## left_bar

        margin = 12 * context.preferences.view.ui_scale
        if context.region:
            self.coords = [\
                (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1]*100)+margin)\
                for co in self.org_coords]
        
        # print('self.coords: ', self.coords[0])

        if event.type == 'ESC':
            print('Stop Modal')
            # context.scene.frame_current = self.cancel_frame
            self._exit_modal(context)
            return {'CANCELLED'}
        
        if event.type == 'I':
            print('infos')
            for i in dir(context.space_data):
                if i.startswith('__'):
                    continue
                print(i)
            print()
            return {"RUNNING_MODAL"}
        if event.type == 'T' and event.value=='PRESS':
            print(context.space_data.mode)
            return {"RUNNING_MODAL"}
        if event.type == 'Y' and event.value=='PRESS':
            print(context.space_data.type)
            return {"RUNNING_MODAL"}
        if event.type == 'Q' and event.value=='PRESS':
            print(context.space_data.type)
            return {"RUNNING_MODAL"}
        if event.type == 'R' and event.value=='PRESS':
            rd = context.region_data
            print('region_data: ', rd)
            r = context.region
            print(f'{r.width}x{r.height}')

            ## View_to_region seems good !!
            active_strip = context.scene.sequence_editor.active_strip
            if active_strip:
                active_strip.frame_final_start
                print('active_strip.frame_final_start: ', active_strip.frame_final_start)
                x, y = r.view2d.view_to_region(active_strip.frame_final_start, 0, clip=False)
            else:
                x, y = r.view2d.view_to_region(0, 0)

            # r.view2d.view_to_region(active_strip.frame_final_start, 0)

            # context
            # x, y = r.view2d.view_to_region(0, 0)
            # x, y = r.view2d.region_to_view(0, 0)
            print('view_to_region x, y: ', x, y)
            lb = context.area.regions[1].width
            print('left_bar',context.area.regions[1].type , lb)
            # x, y = x-lb, y
            # print('x, y: ', x, y)

            ## convert to view
            # x, y = r.view2d.region_to_view(x, y)
            # print('region_to_view x, y: ', x, y)
            self.coords.append((x, event.mouse_region_y))
            print('x: ', x)
            print('y: ', y)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        
        # if event.type == 'LEFTMOUSE' and event.value=='PRESS':
        #     print('mouse_region', (event.mouse_region_x, event.mouse_region_y))
        #     self.coords.append((event.mouse_region_x, event.mouse_region_y))
        #     # return {"RUNNING_MODAL"}
        
        # if event.type == 'RIGHTMOUSE' and event.value=='PRESS':
        #     print('mouse', (event.mouse_x, event.mouse_y))
        #     print('mouse_region', (event.mouse_region_x, event.mouse_region_y))
        #     return {"RUNNING_MODAL"}

        # context.area.tag_redraw()
        return {'PASS_THROUGH'}
        # return {"RUNNING_MODAL"}



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
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)