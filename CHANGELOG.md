# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- ## [Unreleased] -->

## [0.6.2] - 2022-05-11 18:04:30

### Added

- Quick prefs: pref button open a popover to adjust wave color/detail or fully open the addon prefs (previously opened addon prefs directly)

## [0.6.1] - 2022-05-08

### Added

- Sound list: Select a sound strip directly in panel, no need to open sequencer editor

### Changed

- Active strip is also considered selected

### Fixed

- Audio mixdown works even if playback muted

## [0.5.0] - 2022-05-04

### Added

- Color customization in addon preferences (note: on some darker color, generated hex is invalid -> wave turns full white)
- button to pop-open preferences in UI

### Fixed

- Sequencer mode ignore speaker properly

## [0.4.0] - 2022-05-04

### Added

- support for object speaker
- filter to use object sequencer only, speaker or both (default: sequencer-selected)
### Fixed

- bug with mixdown disabled

### Changed

- Force mixdown enabled by default

## [0.3.1] - 2022-05-03

### Added

- Option to force mixdown in every case
- range optimisations

## [0.3.0] - 2022-05-02

### Added

- Can display mutiple selected strip
- Target choice `Selected Strips` (default), `Unmuted Strips` or `Scene Range`
### Changed

- Always mixdown the sound to a temp file for result consistency

## [0.2.3] - 2022-02-05

### Fixed

- Error always trying to get ffmpeg from addon folder

## [0.2.2] - 2021-11-28

### Added

- If ffmpeg is not found, pop-up a shortcut to addon-preferences

## [0.2.1] - 2021-11-23

### Added

- Automatic download of a compatible ffmpeg executable from github (windows platform only) ~90Mo. and autoset `path_to_ffmpeg` 

## [0.2.0] - 2021-11-22

### Added

- manual ffmpeg bin path in preferences when not in Path
- ffmpeg in PATH checker button in prefs

## [0.1.9] - 2021-09-02

### Fixed

- refresh draw when toggling on off

## [0.1.8] - 2021-07-26

### Added

- display also in graph editor and timeline
- 3 toggles to choose where to display
- automatically get audio strip if there if only 1 available in VSE
- Error handling in case sound filepath is bad or is packed.
- warning if used strip is muted
- info on strip used
- wave is now transparent with a bgl fusion mode (needs more testing)

## [0.1.7] - 2021-07-26

### Added

- neat clipped border when zoomed on waveform
- Silent ffmpeg running in console
- generate the image file in temp dir

## [0.1.6] - 2021-07-24

### Added

- propertie group and intProp exposed in panel to manually  control height offset

## [0.1.5] - 2021-07-23

### Added

- only upper half waveform generated and displayed (image size divided by 2)
- crop and align image if strip handles have some offset
- avoid potential error on unregister
## [0.1.4] - 2021-07-22

### Changed

- First working prototype with draw image mode. Using ffmpeg generated image

## [0.1.3] - 2021-07-21

### Changed

- handler without modal ops running.
- Start on ffmpeg generated image base model

## [0.1.2] - 2021-07-16

### Changed

- Tryed to implement bake from curve but too unpredictable and random

## [0.1.1] - 2021-07-05

### Fixed

- Draw regions (discard timeline editor for now)
## [0.1.0] - 2021-07-05

### Added

- initial commit


<!--
Added: for new features.
Changed: for changes in existing functionality.
Deprecated: for soon-to-be removed features.
Removed: for now removed features.
Fixed: for any bug fixes.
Security: in case of vulnerabilities.
-->