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

VFOCUS is in early development. This repository currently contains the inherited
F4HWN implementation. The UX/UI redesign described below is planned work, and
there are no published VFOCUS firmware releases yet.

The existing files in [`archive/`](archive/) are inherited upstream artifacts,
including F4HWN and stock firmware. They are not VFOCUS release builds.
Build presets and output filenames currently retain the F4HWN names.

## Where we are heading

- Shortcuts that are easy to remember, with consistent short- and long-press behavior.
- Clearer menu labels and navigation that make settings easier to understand.
- Readable screens for everyday listening, channel scanning and finding activity.
- Careful integration with the existing spectrum analyzer and other F4HWN tools.

These are design goals. Available functions depend on the firmware revision and
build preset. See the [F4HWN reference](docs/F4HWN.md) for the inherited feature set.

## Documentation

- [Documentation index](docs/README.md)
- [Detailed F4HWN reference](docs/F4HWN.md): features, editions, scanning and controls.
- [Build from source](docs/F4HWN.md#compiling-and-building-from-docker)
- [Flash a local build with UV Studio](docs/F4HWN.md#flashing-the-firmware-with-uv-studio)
- [Calibration backup and restore](docs/F4HWN.md#steps-to-dump-or-restore-calibration-data)
- [Upstream F4HWN Wiki](https://github.com/armel/uv-k1-k5v3-firmware-custom/wiki)

The upstream reference is retained in detail, with its original contributors and
technical guidance. VFOCUS-specific changes will be documented as they are introduced.

## Build

With Docker running and a Bash shell available, clone the repository and build
from its root directory:

```bash
git clone https://github.com/mideco-tech/VFOCUS.git
cd VFOCUS
./compile-firmware.sh Fusion
```

`Fusion` is the default general-purpose preset. To build the experimental Labs edition:

```bash
./compile-firmware.sh Labs
```

The build produces `.bin`, `.elf` and `.hex` files in `build/<Preset>/`.
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
belong to those releases. Check compatibility before using one with a VFOCUS build.

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
