import bpy
from bpy.types import Operator

import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from .preferences import get_addon_prefs


def draw_callback_px(self, context):
    '''Draw callback use by modal to draw in viewport'''
    if context.area.type != 'DOPESHEET_EDITOR':
        return
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')  # initiate shader
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glLineWidth(1)
    
    batch_line = batch_for_shader(
        shader, 'LINE_STRIP', {"pos": self.coords})
    shader.bind()
    shader.uniform_float("color", (0.01, 0.64, 1.0, 0.8))
    batch_line.draw(shader)
    # self.batch_line.draw(shader)
    
    # restore opengl defaults
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_BLEND)


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
            # 
        
        # self.coords = [(10,10),(300,150),(400,500)]
        fcu = bpy.data.actions['CubeAction'].fcurves[0]
        point_coord = [p.co for p in fcu.keyframe_points]

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
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _exit_modal(self, context):
        self.viewtype.draw_handler_remove(self._handle, self.spacetype)
        context.area.tag_redraw()

    def modal(self, context, event):
        ## left_bar
        margin = 12 * context.preferences.view.ui_scale
        self.coords = [\
            (context.region.view2d.view_to_region(co[0], 0, clip=False)[0], (co[1]*100)+margin)\
            for co in self.org_coords]

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
            return {"RUNNING_MODAL"}
        
        # if event.type == 'LEFTMOUSE' and event.value=='PRESS':
        #     print('mouse_region', (event.mouse_region_x, event.mouse_region_y))
        #     self.coords.append((event.mouse_region_x, event.mouse_region_y))
        #     # return {"RUNNING_MODAL"}
        
        # if event.type == 'RIGHTMOUSE' and event.value=='PRESS':
        #     print('mouse', (event.mouse_x, event.mouse_y))
        #     print('mouse_region', (event.mouse_region_x, event.mouse_region_y))
        #     return {"RUNNING_MODAL"}

        context.area.tag_redraw()
        return {'PASS_THROUGH'}
        # return {"RUNNING_MODAL"}

classes=(
# SWD_OT_opsname,
SWD_OT_timeline_draw_test,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)