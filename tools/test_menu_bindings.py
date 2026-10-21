#!/usr/bin/env python3
"""Exercise the firmware's actual MENU binding policy and byte encoding in C.

Compiles the production SETTINGS_* helpers rather than a Python policy model.
Run with Python 3 and native GCC/Clang, for example:
    python3 tools/test_menu_bindings.py
"""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

from test_menu_ab import ROOT, action_enum_source, function_source


SUPPORT = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static struct {
    uint8_t KEY_M_SHORT_PRESS_ACTION, KEY_M_LONG_PRESS_ACTION;
} gEeprom;
static uint8_t nv_state[0x100];
static unsigned writes, written_bytes;
static uint32_t write_addresses[2];
static unsigned write_sizes[2];
static void PY25Q16_WriteBuffer(uint32_t address, const void *data,
                                unsigned size, bool append) {
    assert(!append && writes < 2);
    assert(address >= 0xa000 && address + size <= 0xa100);
    write_addresses[writes] = address;
    write_sizes[writes++] = size;
    written_bytes += size;
    memcpy(nv_state + address - 0xa000, data, size);
}
'''


TESTS = r'''
static bool has_menu(void) {
    return gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_MENU ||
           gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU;
}

static void test_normalization_exhaustive(void) {
    for (unsigned short_action = 0; short_action < 256; ++short_action) {
        for (unsigned long_action = 0; long_action < 256; ++long_action) {
            gEeprom.KEY_M_SHORT_PRESS_ACTION = short_action;
            gEeprom.KEY_M_LONG_PRESS_ACTION = long_action;
            SETTINGS_NormalizeMenuActions();
            assert(gEeprom.KEY_M_SHORT_PRESS_ACTION < ACTION_OPT_LEN);
            assert(gEeprom.KEY_M_LONG_PRESS_ACTION < ACTION_OPT_LEN);
            assert(has_menu());
            if (short_action < ACTION_OPT_LEN && long_action < ACTION_OPT_LEN &&
                (short_action == ACTION_OPT_MENU || long_action == ACTION_OPT_MENU)) {
                assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == short_action);
                assert(gEeprom.KEY_M_LONG_PRESS_ACTION == long_action);
            }
            uint8_t saved_short = gEeprom.KEY_M_SHORT_PRESS_ACTION;
            uint8_t saved_long = gEeprom.KEY_M_LONG_PRESS_ACTION;
            SETTINGS_NormalizeMenuActions();
            assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == saved_short);
            assert(gEeprom.KEY_M_LONG_PRESS_ACTION == saved_long);
        }
    }
    puts("PASS all 65536 raw binding pairs normalize to a stable reachable menu");
}

static void test_assignment_exhaustive(void) {
    for (unsigned short_action = 0; short_action < ACTION_OPT_LEN; ++short_action) {
        for (unsigned long_action = 0; long_action < ACTION_OPT_LEN; ++long_action) {
            if (short_action != ACTION_OPT_MENU && long_action != ACTION_OPT_MENU)
                continue;
            for (unsigned is_long = 0; is_long < 2; ++is_long) {
                for (unsigned selected = 0; selected < ACTION_OPT_LEN; ++selected) {
                    gEeprom.KEY_M_SHORT_PRESS_ACTION = short_action;
                    gEeprom.KEY_M_LONG_PRESS_ACTION = long_action;
                    SETTINGS_SetMenuAction(is_long, selected);
                    uint8_t edited = is_long ? gEeprom.KEY_M_LONG_PRESS_ACTION :
                                               gEeprom.KEY_M_SHORT_PRESS_ACTION;
                    uint8_t other = is_long ? gEeprom.KEY_M_SHORT_PRESS_ACTION :
                                              gEeprom.KEY_M_LONG_PRESS_ACTION;
                    uint8_t previous_other = is_long ? short_action : long_action;
                    assert(edited == selected);
                    assert(has_menu());
                    if (selected == ACTION_OPT_MENU)
                        assert(other == previous_other);
                    else
                        assert(other == ACTION_OPT_MENU);
                }
            }
        }
    }
    for (unsigned invalid = ACTION_OPT_LEN; invalid < 256; ++invalid) {
        for (unsigned is_long = 0; is_long < 2; ++is_long) {
            gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_A_B;
            gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_MENU;
            SETTINGS_SetMenuAction(is_long, invalid);
            assert(has_menu());
            assert(gEeprom.KEY_M_SHORT_PRESS_ACTION < ACTION_OPT_LEN);
            assert(gEeprom.KEY_M_LONG_PRESS_ACTION < ACTION_OPT_LEN);
        }
    }
    puts("PASS assignment preserves the edited action and repairs the other binding");
}

static void test_user_sequence(void) {
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_A_B;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_MENU;
    SETTINGS_SetMenuAction(true, ACTION_OPT_A_B);
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_MENU);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_A_B);
    SETTINGS_SetMenuAction(false, ACTION_OPT_SCAN);
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_SCAN);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU);
    SETTINGS_SetMenuAction(false, ACTION_OPT_MENU);
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_MENU);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU);
    SETTINGS_SetMenuAction(true, ACTION_OPT_NONE);
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_MENU);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_NONE);
    puts("PASS the requested long/short reassignment sequence always retains MENU");
}

static void encoded_state(uint8_t *packed_long, uint8_t *state) {
    memset(state, 0xa5, 8);
    *packed_long = 1;
    SETTINGS_EncodeMenuActions(packed_long, state);
}

static void test_byte_roundtrips(void) {
    for (unsigned short_action = 0; short_action < ACTION_OPT_LEN; ++short_action) {
        for (unsigned long_action = 0; long_action < ACTION_OPT_LEN; ++long_action) {
            if (short_action != ACTION_OPT_MENU && long_action != ACTION_OPT_MENU)
                continue;
            for (unsigned beep = 0; beep < 2; ++beep) {
                struct { uint8_t before, data[8], after; } guarded;
                memset(&guarded, 0xa5, sizeof(guarded));
                uint8_t packed_long = beep;
                gEeprom.KEY_M_SHORT_PRESS_ACTION = short_action;
                gEeprom.KEY_M_LONG_PRESS_ACTION = long_action;
                SETTINGS_EncodeMenuActions(&packed_long, guarded.data);
                assert(guarded.before == 0xa5 && guarded.after == 0xa5);
                for (unsigned i = 0; i < 5; ++i) assert(guarded.data[i] == 0xa5);
                assert((packed_long & 1) == beep);
                assert((packed_long >> 1) == long_action);
                assert(guarded.data[5] == short_action);
                uint8_t state_before[8];
                memcpy(state_before, guarded.data, sizeof(state_before));
                gEeprom.KEY_M_SHORT_PRESS_ACTION = 0xff;
                gEeprom.KEY_M_LONG_PRESS_ACTION = 0xff;
                assert(!SETTINGS_DecodeMenuActions(packed_long, guarded.data));
                assert(memcmp(state_before, guarded.data, sizeof(state_before)) == 0);
                assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == short_action);
                assert(gEeprom.KEY_M_LONG_PRESS_ACTION == long_action);
            }
        }
    }
    puts("PASS all valid pairs round-trip while beep, neighbors and input buffers survive");
}

static void test_migration_and_corruption(void) {
    uint8_t state[8], packed_long;
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_A_B;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_MENU;
    encoded_state(&packed_long, state);
    const uint8_t marker0 = state[6], marker1 = state[7];
    assert(marker0 == 0x4d && marker1 == 0x31);
    for (unsigned stale_long = 0; stale_long < 256; ++stale_long) {
        uint8_t legacy[8];
        memset(legacy, 0xff, sizeof(legacy));
        assert(SETTINGS_DecodeMenuActions(stale_long, legacy));
        assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_A_B);
        assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU);
    }
    for (unsigned which = 6; which < 8; ++which) {
        for (unsigned corrupted = 0; corrupted < 256; ++corrupted) {
            uint8_t damaged[8];
            memcpy(damaged, state, sizeof(damaged));
            if (corrupted == state[which]) continue;
            damaged[which] = corrupted;
            assert(SETTINGS_DecodeMenuActions(0, damaged));
            assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_A_B);
            assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU);
        }
    }
    /* A stock CHIRP save can replace the unknown MENU action by NONE. */
    state[5] = ACTION_OPT_A_B;
    assert(SETTINGS_DecodeMenuActions(ACTION_OPT_NONE << 1, state));
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_A_B);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_MENU);
    state[5] = ACTION_OPT_MENU;
    assert(!SETTINGS_DecodeMenuActions(ACTION_OPT_NONE << 1, state));
    assert(gEeprom.KEY_M_SHORT_PRESS_ACTION == ACTION_OPT_MENU);
    assert(gEeprom.KEY_M_LONG_PRESS_ACTION == ACTION_OPT_NONE);
    for (unsigned raw_short = 0; raw_short < 256; ++raw_short) {
        for (unsigned raw_long = 0; raw_long < 128; ++raw_long) {
            state[5] = raw_short;
            SETTINGS_DecodeMenuActions(raw_long << 1, state);
            assert(has_menu());
            assert(gEeprom.KEY_M_SHORT_PRESS_ACTION < ACTION_OPT_LEN);
            assert(gEeprom.KEY_M_LONG_PRESS_ACTION < ACTION_OPT_LEN);
        }
    }
    puts("PASS legacy, partial marker, corrupt and stock-CHIRP images cannot hide MENU");
}

static void test_actual_startup_write_block(void) {
    for (unsigned old_beep = 0; old_beep < 2; ++old_beep) {
        memset(nv_state, 0xa5, sizeof(nv_state));
        memset(nv_state + 0xc5, 0xff, 3);
        nv_state[0xa8] = (ACTION_OPT_MONITOR << 1) | old_beep;
        uint8_t before[sizeof(nv_state)];
        memcpy(before, nv_state, sizeof(before));
        writes = written_bytes = 0;
        uint8_t loaded_state[8];
        memcpy(loaded_state, nv_state + 0xc0, 8);
        startup_menu_block(nv_state[0xa8], loaded_state);
        assert(writes == 2 && written_bytes == 4);
        assert(write_addresses[0] == 0xa0a8 && write_sizes[0] == 1);
        assert(write_addresses[1] == 0xa0c5 && write_sizes[1] == 3);
        assert(nv_state[0xa8] == ((ACTION_OPT_MENU << 1) | old_beep));
        assert(nv_state[0xc5] == ACTION_OPT_A_B);
        assert(nv_state[0xc6] == 0x4d && nv_state[0xc7] == 0x31);
        for (unsigned i = 0; i < sizeof(nv_state); ++i) {
            if (i != 0xa8 && (i < 0xc5 || i > 0xc7))
                assert(nv_state[i] == before[i]);
        }
        writes = written_bytes = 0;
        memcpy(loaded_state, nv_state + 0xc0, 8);
        startup_menu_block(nv_state[0xa8], loaded_state);
        assert(writes == 0 && written_bytes == 0);
        /* A stock CHIRP write removes MENU but keeps the custom marker. */
        nv_state[0xa8] = old_beep;
        memcpy(loaded_state, nv_state + 0xc0, 8);
        startup_menu_block(nv_state[0xa8], loaded_state);
        assert(writes == 2 && written_bytes == 4);
        assert(nv_state[0xa8] == ((ACTION_OPT_MENU << 1) | old_beep));
        assert(has_menu());
    }
    puts("PASS production boot migration writes only four bytes and stable boot writes none");
}

int main(void) {
    assert(ACTION_OPT_A_B == 9 && ACTION_OPT_MENU == 25 && ACTION_OPT_LEN == 26);
    test_normalization_exhaustive();
    test_assignment_exhaustive();
    test_user_sequence();
    test_byte_roundtrips();
    test_migration_and_corruption();
    test_actual_startup_write_block();
    puts("All 6 MENU binding policy groups passed.");
    return 0;
}
'''


def constants_source():
    """Copy settings' object-like constants used by the extracted helpers."""
    result = []
    for relative in ("App/settings.h", "App/settings.c"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        for line in source.splitlines():
            if re.match(r"\s*#define\s+SETTINGS_\w+\s+", line):
                if line.rstrip().endswith("\\"):
                    raise RuntimeError(f"Unsupported multiline settings constant: {line}")
                result.append(line)
    return "\n".join(result)


def startup_block_source():
    """Copy exactly the production decode/repair block from EEPROM loading."""
    source = (ROOT / "App/settings.c").read_text(encoding="utf-8")
    begin = source.index("    if (SETTINGS_DecodeMenuActions(packedMenuLong, Data)) {")
    end = source.index("\n    // 0ED0..0ED7", begin)
    line = source.count("\n", 0, begin) + 1
    return ("static void startup_menu_block(uint8_t packedMenuLong, uint8_t *Data) {\n"
            + f'#line {line} "App/settings.c"\n' + source[begin:end] + "\n}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--no-sanitize", action="store_true")
    args = parser.parse_args()
    pieces = [SUPPORT, action_enum_source(), constants_source()]
    for name in ("SETTINGS_NormalizeMenuActions", "SETTINGS_SetMenuAction",
                 "SETTINGS_DecodeMenuActions", "SETTINGS_EncodeMenuActions"):
        pieces.append(function_source("App/settings.c", name))
    pieces.append(startup_block_source())
    pieces.append(TESTS)
    with tempfile.TemporaryDirectory(prefix="f4hwn-menu-bindings-") as temporary:
        source = Path(temporary) / "menu_bindings_test.c"
        executable = Path(temporary) / "menu_bindings_test"
        source.write_text("\n".join(pieces), encoding="utf-8")
        command = shlex.split(args.cc) + [
            "-std=c11", "-O1", "-g", "-funsigned-char", "-Wall", "-Wextra",
            "-Werror", "-fno-omit-frame-pointer", str(source), "-o", str(executable),
        ]
        if not args.no_sanitize:
            command += ["-fsanitize=address,undefined"]
        print(f"Compiling actual firmware MENU policy with {args.cc}", flush=True)
        subprocess.run(command, check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
