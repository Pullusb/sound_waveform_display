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

def mixdown(filepath, mode='SELECT'):
    '''mode in (SELECT, UNMUTED, SCENE)'''

    vse = bpy.context.scene.sequence_editor
    if mode == 'SCENE':
        temp_changes = []
        # TODO: optimize by placing getting leftmost and righmost uncuted strip range

    elif mode == 'UNMUTED':
        # unmuted range (no need to render the whole )
        unmuted = [s for s in vse.sequences if s.type == 'SOUND' and not s.mute]
        start = min([s.frame_final_start for s in unmuted])
        end = max([s.frame_final_end for s in unmuted])
        temp_changes = [
            (bpy.context.scene, 'frame_start', start),
            (bpy.context.scene, 'frame_end', end),
            ]

    else: # SELECT
        selected_strips = [s for s in vse.sequences if s.type == 'SOUND' and s.select]
        unselected_strips = [s for s in vse.sequences if s.type == 'SOUND' and not s.select]
        
        # get range
        start = min([s.frame_final_start for s in selected_strips])
        end = max([s.frame_final_end for s in selected_strips])

        temp_changes = [
            # (bpy.context.scene, 'use_preview_range', False) # not affected by preview range
            (bpy.context.scene, 'frame_start', start),
            (bpy.context.scene, 'frame_end', end),
            ]

        temp_changes += [(s, 'mute', True) for s in unselected_strips]
        
        ## unmute selected strips (disable ? cana be counter-logic for some...)
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