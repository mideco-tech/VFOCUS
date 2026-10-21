# VFOCUS documentation

[Back to the project README](../README.md)

VFOCUS builds on [F4HWN by armel](https://github.com/armel/uv-k1-k5v3-firmware-custom).
The [detailed F4HWN reference](F4HWN.md) preserves the inherited documentation and
credits. It describes the upstream feature set, with availability depending on the
build preset. The first VFOCUS-specific change is documented in the
[MENU controls guide](MENU-KEYS.md).

## Using the firmware

- [VFOCUS M Shrt / M Long controls](MENU-KEYS.md)
- [Editions and features](F4HWN.md#main-features-and-improvements-from-f4hwn)
- [Spectrum analyzer](F4HWN.md#spectrum-analyzer)
- [Scanning and scan lists](F4HWN.md#scanning)
- [Display and user interface](F4HWN.md#user-interface)
- [Settings and controls](F4HWN.md#settings-and-controls)
- [Keyboard shortcuts and assignable actions](F4HWN.md#keyboard-shortcuts-and-assignable-actions)
- [Overlay applications and APRS](F4HWN.md#overlay-applications-and-aprs)
- [Upstream F4HWN Wiki](https://github.com/armel/uv-k1-k5v3-firmware-custom/wiki)

## Building and maintenance

- [Build and test the VFOCUS Labs release](MENU-KEYS.md#building-and-testing)
- [Build with Docker](F4HWN.md#compiling-and-building-from-docker)
- [Flash firmware with UV Studio](F4HWN.md#flashing-the-firmware-with-uv-studio)
- [Back up or restore calibration](F4HWN.md#steps-to-dump-or-restore-calibration-data)
- [Receiver limitations](F4HWN.md#radio-performance)
- [Application documentation](../App/apps/), where available in each app's README

Build commands are run from the repository root. The VFOCUS release uses its own
artifact name and edition label, retaining the F4HWN v6.2.0 configuration identity.
Other inherited build presets retain their F4HWN names.
The binaries in [`archive/`](../archive/) are inherited artifacts, not VFOCUS releases.

## Authors and sources

- [F4HWN reference credits](F4HWN.md#credits)
- [Attribution and third-party notices](../NOTICE)
- [Apache License 2.0](../LICENSE)
- [UV Studio by armel](https://armel.github.io/uvstudio/)
- [UV-K1 teardown by armel](https://github.com/armel/k1-teardown)

Maintained for VFOCUS by MiDeCo, with the original F4HWN authorship retained.
