# VFOCUS MENU controls

[Back to VFOCUS](../README.md) | [Documentation index](README.md)

VFOCUS v0.1.0 introduces configurable MENU short- and long-press actions on top
of the F4HWN v6.2.0 implementation by armel and contributors.

## Default controls

Open the settings menu and select the **Keys** category:

| Setting on the radio | Press | Default action |
| --- | --- | --- |
| `M Shrt` | Short MENU press | Switch between VFO A and VFO B |
| `M Long` | Hold MENU | `MENU`: open the settings menu |

On the main screen, a short action runs once when the key is released. A long
action runs once when the hold threshold is reached. Releasing after a long
press does not also trigger the short action.

Inside the settings menu, a short MENU press continues to select, edit and
confirm. During frequency or channel-number entry, it continues to confirm the
input. Specialized screens, including the spectrum analyzer, keep their own
context-dependent controls. Keypad and menu locks still apply.

## Keeping the settings menu reachable

At least one of the two MENU bindings must open the settings menu. When you save
an assignment, the selected action is kept. If neither binding would then open
the menu, the other binding automatically becomes `MENU`. Both are saved together.

| Before: Short / Long | Assignment | After: Short / Long |
| --- | --- | --- |
| A/B / MENU | Set `M Long` to A/B | MENU / A/B |
| MENU / A/B | Set `M Shrt` to A/B | A/B / MENU |
| A/B / MENU | Set `M Shrt` to MENU | MENU / MENU |
| MENU / MENU | Set `M Long` to A/B | MENU / A/B |

Assigning `MENU` to both presses is allowed. An existing reachable menu binding
is left alone unless repairing it is necessary. This guard protects against
losing the menu through these two assignments. An explicitly enabled menu or
keypad lock remains a separate setting.

## Upgrading from F4HWN

On first loading an older configuration without the MENU binding marker,
VFOCUS initializes **Short = A/B, Long = MENU**. This deliberately replaces the
previous M Long assignment. Configurations already carrying the MENU-Keys marker
retain their valid bindings. Invalid bindings are repaired to keep a menu action.

The firmware retains **`F4HWN v6.2.0`** as its protocol identity and configuration
compatibility version. The release build uses **`VF0.1.0-Labs`** as its edition
name so the fork version can be identified without changing that compatibility
field. Channel storage, calibration layout and the overlay-app API are unchanged
by this modification. Keep your own backups before flashing.

### CHIRP limitation

No VFOCUS-specific CHIRP driver is bundled with v0.1.0. The upstream F4HWN v6.2.0
driver does not expose M Short or recognize the new MENU action. Uploading
settings with it may reset MENU assignments. Configure these bindings on the
radio and check them after using an upstream programming tool. Do not treat the
upstream driver as providing full support for the new settings.

### Storage reference

These details are provided for developers and readback tools:

| Logical address | Content |
| --- | --- |
| `0xA0A8`, bits 1..7 | Existing M Long action |
| `0xA0A8`, bit 0 | Existing key-beep flag, preserved |
| `0xA0C5` | New M Short action |
| `0xA0C6..0xA0C7` | Format marker `4D 31`, ASCII `M1` |

Existing action IDs `0..24` retain their meanings. A/B remains `9` and the new
`ACTION_OPT_MENU` is `25`.

## Building and testing

The release build requires Bash, CMake 3.24 or later, Ninja, Python 3 and an Arm
GNU Toolchain on `PATH`. The v0.1.0 artifact is built with Arm GNU Toolchain
13.3.Rel1. From the repository root:

```bash
python3 tools/test_menu_bindings.py
python3 tools/test_menu_ab.py
bash tools/build_vfocus.sh
```

The host tests need a native GCC or Clang compiler, including AddressSanitizer
and UndefinedBehaviorSanitizer support. They compile the production C handlers
and policy helpers. The tests cover 65,536 raw binding pairs, assignments,
encoding, legacy migration and MENU events in both categorized and flat menus.

If the cross-compiler is outside `PATH`, pass its `bin` directory:

```bash
bash tools/build_vfocus.sh /path/to/arm-toolchain/bin
```

The script reads the release number from [`VERSION`](../VERSION), uses the Labs
preset and writes `vfocus.labs.v0.1.0.bin`, `.elf`, `.hex` and `.map` in
`build/VFOCUS-Labs/`. It takes `SOURCE_DATE_EPOCH` from the current Git commit
unless the environment supplies one. It leaves the configuration version at
`v6.2.0` and prints the binary SHA-256.

GitHub source archives do not contain Git history. When building from an archive,
set `SOURCE_DATE_EPOCH` to the value in the release's `manifest.json` before
running the build script.

Host tests and a successful cross-build do not prove operation of a particular
binary on hardware. The original local MENU-Keys implementation passed remote
key/LCD and spectrum tests on a UV-K1 before this release. The newly labeled
v0.1.0 release binary has not been flashed or tested on a radio as part of this
release process.
