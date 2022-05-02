import bpy
import tempfile
from pathlib import Path
from time import time

## context manager
class attr_set():
    '''Receive a list of tuple [(data_path, "attribute" [, wanted value)] ]
    entering with-statement : Store existing values, assign wanted value (if any)
    exiting with-statement: Restore values to their old values
    '''

    def __init__(self, attrib_list):
        self.store = []
        # item = (prop, attr, [new_val])
        for item in attrib_list:
            prop, attr = item[:2]
            self.store.append( (prop, attr, getattr(prop, attr)) )
            if len(item) >= 3:
                setattr(prop, attr, item[2])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for prop, attr, old_val in self.store:
            setattr(prop, attr, old_val)


## -- Mixdown ops reference
# bpy.ops.sound.mixdown(
# mixdown()
# bpy.ops.sound.mixdown(filepath="", check_existing=True,
# filemode=9, relative_path=True,
# accuracy=1024,
# container='FLAC', # ('AC3', 'FLAC', 'MATROSKA', 'MP2', 'MP3', 'OGG', 'WAV')
# codec='FLAC', # ('AAC', 'AC3', 'FLAC', 'MP2', 'MP3', 'PCM', 'VORBIS')
# format='S16', # ('U8', 'S16', 'S24', 'S32', 'F32', 'F64')
# bitrate=192,
# split_channels=False)

def get_sound_strip_in_scene_range(vse=None):
    vse = vse or bpy.context.scene.sequence_editor
    scn = bpy.context.scene
    strips =  [s for s in vse.sequences if s.type == 'SOUND' \
        and not s.mute \
        and not (s.final_frame_end <= scn.frame_start or s.final_frame_start >= scn.frame_end)]
    
    return strips

def get_start_end(strip_list):
    start = min([s.frame_final_start for s in strip_list])
    end = max([s.frame_final_end for s in strip_list])
    return start, end

def mixdown(filepath, mode='SELECT'):
    '''mode in (SELECT, UNMUTED, SCENE)'''

    scn = bpy.context.scene
    vse = scn.sequence_editor
    if mode == 'SCENE':
        temp_changes = []

        # Optimise by reducing range to first/las audible strips
        strips = get_sound_strip_in_scene_range(vse)
        start, end = get_start_end(strips)
        if start > scn.frame_start:
            temp_changes.append((scn, 'frame_start', start))
        if end > scn.frame_end:
            temp_changes.append((scn, 'frame_end', end),)

    elif mode == 'UNMUTED':
        # unmuted range (no need to render the whole )
        unmuted = [s for s in vse.sequences if s.type == 'SOUND' and not s.mute]
        start, end = get_start_end(unmuted)

        temp_changes = [
            (scn, 'frame_start', start),
            (scn, 'frame_end', end),
            ]

    else: # SELECT
        selected_strips = [s for s in vse.sequences if s.type == 'SOUND' and s.select]
        unselected_strips = [s for s in vse.sequences if s.type == 'SOUND' and not s.select]
        
        # get range
        start, end = get_start_end(selected_strips)

        temp_changes = [
            # (scn, 'use_preview_range', False) # not affected by preview range
            (scn, 'frame_start', start),
            (scn, 'frame_end', end),
            ]

        # mute non selected strips
        temp_changes += [(s, 'mute', True) for s in unselected_strips]
        # unmute selected strips (can be counter-logic to some...)
        temp_changes += [(s, 'mute', False) for s in selected_strips]

    with attr_set(temp_changes):
        t0 = time()

        ## fastest container to write seem to be wav... need further testing

        ret = bpy.ops.sound.mixdown(filepath=str(filepath), check_existing=False, relative_path=False,
        accuracy=1024,
        
        container='WAV', # ('AC3', 'FLAC', 'MATROSKA', 'MP2', 'MP3', 'OGG', 'WAV') # 0.310
        codec='PCM', # ('AAC', 'AC3', 'FLAC', 'MP2', 'MP3', 'PCM', 'VORBIS')
        
        # container='FLAC', # ('AC3', 'FLAC', 'MATROSKA', 'MP2', 'MP3', 'OGG', 'WAV') # 0.450
        # codec='FLAC', # ('AAC', 'AC3', 'FLAC', 'MP2', 'MP3', 'PCM', 'VORBIS')
        
        # container='OGG', # ('AC3', 'FLAC', 'MATROSKA', 'MP2', 'MP3', 'OGG', 'WAV') # 1.114 ~ 1.313
        # codec='VORBIS', # ('AAC', 'AC3', 'FLAC', 'MP2', 'MP3', 'PCM', 'VORBIS')

        # container='MP3', # ('AC3', 'FLAC', 'MATROSKA', 'MP2', 'MP3', 'OGG', 'WAV') # 0.8
        # codec='MP3', # ('AAC', 'AC3', 'FLAC', 'MP2', 'MP3', 'PCM', 'VORBIS')
                
        format='S16', # ('U8', 'S16', 'S24', 'S32', 'F32', 'F64')
        bitrate=128, # default 192 [32, 512]
        split_channels=False)

        print(f'Mixdown time: {time() - t0:.3f}s')

    if ret != {'FINISHED'}:
        print(ret)
        return None, None
        
    return start, end