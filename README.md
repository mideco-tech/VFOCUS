# VFOCUS

**F4HWN at heart. Clearer controls in focus.**

VFOCUS is an experimental firmware fork for the **Quansheng UV-K1 and UV-K5 V3**
(PY32F071), maintained by **MiDeCo** at [mideco-tech](https://github.com/mideco-tech).
The goal is to make everyday listening and scanning easier through memorable
controls, readable screens and consistent navigation.

VFOCUS is based on **[F4HWN by armel](https://github.com/armel/uv-k1-k5v3-firmware-custom)**.
The UV-K1 / UV-K5 V3 port is the joint work of **[armel](https://github.com/armel)**
and **[muzkr](https://github.com/muzkr)**. Their firmware is the foundation of this
project, and its authorship and acknowledgements remain part of VFOCUS.

## Project status

**[v0.1.0 Labs](https://github.com/mideco-tech/VFOCUS/releases/tag/v0.1.0)** is the
first experimental VFOCUS release, based on F4HWN v6.2.0. It adds configurable
**M Shrt / M Long** controls: short MENU switches A/B, long MENU opens settings,
and the assignment guard keeps at least one MENU action available.

See the [MENU controls guide](docs/MENU-KEYS.md) and [changelog](CHANGELOG.md).
The broader UX/UI redesign below remains planned work.

The existing files in [`archive/`](archive/) are inherited upstream artifacts,
including F4HWN and stock firmware. They are not VFOCUS release builds.
Inherited build presets retain the F4HWN names. The VFOCUS release script builds
Labs with its own artifact name and edition label.

## Where we are heading

- Shortcuts that are easy to remember, with consistent short- and long-press behavior.
- Clearer menu labels and navigation that make settings easier to understand.
- Readable screens for everyday listening, channel scanning and finding activity.
- Careful integration with the existing spectrum analyzer and other F4HWN tools.

These are design goals. Available functions depend on the firmware revision and
build preset. See the [F4HWN reference](docs/F4HWN.md) for the inherited feature set.

## Documentation

- [Documentation index](docs/README.md)
- [VFOCUS MENU controls and migration](docs/MENU-KEYS.md)
- [Detailed F4HWN reference](docs/F4HWN.md): features, editions, scanning and controls.
- [Build from source](docs/F4HWN.md#compiling-and-building-from-docker)
- [Flash a local build with UV Studio](docs/F4HWN.md#flashing-the-firmware-with-uv-studio)
- [Calibration backup and restore](docs/F4HWN.md#steps-to-dump-or-restore-calibration-data)
- [Upstream F4HWN Wiki](https://github.com/armel/uv-k1-k5v3-firmware-custom/wiki)

The upstream reference is retained in detail, with its original contributors and
technical guidance. VFOCUS-specific changes will be documented as they are introduced.

## Build

To build the VFOCUS Labs release, use Bash, CMake, Ninja, Python 3 and Arm GNU
Toolchain 13.3.Rel1 on `PATH`. Run from the repository root:

```bash
git clone https://github.com/mideco-tech/VFOCUS.git
cd VFOCUS
bash tools/build_vfocus.sh
```

The release outputs go to `build/VFOCUS-Labs/`. See the
[release build and tests](docs/MENU-KEYS.md#building-and-testing) for details.
The inherited Docker build remains available for other presets:

```bash
./compile-firmware.sh Fusion
```

The Docker build produces `.bin`, `.elf` and `.hex` files in `build/<Preset>/`.
See the [build reference](docs/F4HWN.md#compiling-and-building-from-docker) for other
presets and CMake options.

## Before flashing

This firmware targets the **UV-K1 and UV-K5 V3 with the PY32F071 MCU**.
The original UV-K5 V1 uses different hardware and is not supported by this port.
Use experimental firmware at your own risk and keep backups of your channels,
settings and device-specific calibration data.

[UV Studio by armel](https://armel.github.io/uvstudio/) provides flashing,
calibration backup, screen mirroring and remote keyboard control for compatible
builds. Load a local `.bin` file to install a VFOCUS build. Its catalog of official
F4HWN releases installs upstream F4HWN firmware.

For CHIRP, use a driver that matches the installed firmware. Drivers supplied with
[upstream F4HWN releases](https://github.com/armel/uv-k1-k5v3-firmware-custom/releases)
belong to those releases. They do not support the new MENU bindings and may
reset them when uploading settings. Configure MENU on the radio and check the
[CHIRP limitation](docs/MENU-KEYS.md#chirp-limitation) before using an upstream driver.

## Credits and license

VFOCUS carries forward the work of:

- **armel / F4HWN and muzkr**, for the [UV-K1 / UV-K5 V3 firmware](https://github.com/armel/uv-k1-k5v3-firmware-custom).
- **armel / F4HWN**, for the earlier [F4HWN firmware for UV-K5 V1](https://github.com/armel/uv-k5-firmware-custom).
- **Egzumer**, for [UV-K5 custom firmware](https://github.com/egzumer/uv-k5-firmware-custom).
- **Dual Tachyon**, for the original [open-source UV-K5 firmware](https://github.com/DualTachyon/uv-k5-firmware).
- **fagci, OneOfEleven and the other contributors** listed in the
  [full credits](docs/F4HWN.md#credits) and [NOTICE](NOTICE).

The main firmware is licensed under [Apache License 2.0](LICENSE).
Original copyright and attribution notices are preserved. Third-party components
retain their respective licenses, as recorded in [NOTICE](NOTICE).

README adapted for VFOCUS by MiDeCo. The detailed upstream documentation is preserved
in [`docs/F4HWN.md`](docs/F4HWN.md).
