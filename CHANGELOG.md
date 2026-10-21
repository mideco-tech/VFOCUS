# Changelog

## v0.1.0 - 2026-10-21

First experimental VFOCUS release, based on F4HWN v6.2.0 by armel and
contributors. The published firmware edition is Labs for Quansheng UV-K1 and
UV-K5 V3 radios using the PY32F071 MCU.

### Added

- Configurable `M Shrt` and `M Long` settings in the Keys category.
- Short MENU defaults to A/B and long MENU defaults to opening settings.
- Automatic repair of the other binding when an assignment would remove the
  last MENU action. `MENU / MENU` is supported.
- Legacy-configuration migration to the default pair and validation of stored
  bindings, with the existing key-beep bit preserved.
- Native tests of production C handlers and settings helpers, including all
  65,536 raw binding pairs and both menu layouts.
- A portable Labs release build script and separate VFOCUS release numbering.
- English project documentation with the F4HWN reference and credits retained.

### Compatibility and limitations

- The protocol and configuration compatibility version remains `F4HWN v6.2.0`.
  The release edition is `VF0.1.0-Labs`.
- First boot with a legacy configuration replaces the old M Long binding with
  MENU and initializes M Short to A/B.
- MENU confirmation in settings and numeric input, contextual spectrum controls,
  keypad lock and menu lock retain their existing behavior.
- The upstream CHIRP driver does not support the new bindings and may reset them
  when uploading settings. No VFOCUS-specific driver is bundled.
- Only Labs is distributed as a VFOCUS v0.1.0 binary. Other inherited presets
  remain available in source.
- The broad UX/UI redesign is future work. This release focuses on MENU controls.
- The newly labeled release binary has not been tested on a radio. The original
  local implementation was tested on a UV-K1 before being ported into VFOCUS.

See the [MENU controls guide](docs/MENU-KEYS.md) for behavior, migration and tests.
