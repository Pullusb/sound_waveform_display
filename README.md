# Display Sound Waveform

Display sound waveform in animation editors

**[Get it on Gumroad](https://pullusb.gumroad.com/l/sound_waveform_display)**

**[Download latest](https://github.com/Pullusb/sound_waveform_display/archive/refs/heads/main.zip)**

<!-- ### [Demo Youtube]() -->

> Note: This addon needs ffmpeg in your path to work (on windows a button in addon pref allows an auto install)

---

![sound waveform display basic use demo](https://raw.githubusercontent.com/Pullusb/images_repo/master/SWD_sound_wave_display_demo_01.gif)


## Important

This addon use ffmpeg, if not already accessible on your machine, an auto-install is available in addon preferences

## Description

Display scene audio sound in editor using following interface:

`On` : Enable or refresh

`Off` : Disable

`Height offset` : Allow to manually tweak the peak heights (sometimes it might display too small or too high)

There are several options to select sounds show waveform.

Source:

- `All`
- `Sequencer only` (default).
- `Speaker only`

If `sequencer` source is used, more options are available:

- `Selected Strips` : Display only selected strips in sequencer (even muted ones)
- `Sound In List` : Display only sound from listed sequencer strip within panel (list even muted ones)
- `Audible Strips` : Display all audible strips in sequencer
- `Scene Range` : Display sequencer audio only on scene range (not preview range)

## Preferences

In the preferences you have come customizable settings:

`Waveform color` : Customize color as you like (note: too dark values might fail and use white instead)

`Waveform details` : Details (as resolution) of the generated wave image  
choose between Blocky, Very Low, Low, Medium (default), High  
The waveform aspect will be more detailed, as you go up but will take more time to generate and take more memory.

`Verbose` : prints status and commands in console for debugging purposes.

### Where ?

Dopesheet/ Graph editor / Timeline sidebar (`N` bar) > `Display` tab > `Display Waveform` panel

<!-- ## How

The addon use ffmpeg to generate a waveform from the sound then load it and display in editors background.
For speaker sound or for multiple sequencer strips, audio is mixdowned into a temporary audio file -->
