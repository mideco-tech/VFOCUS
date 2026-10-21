#!/usr/bin/env python3
"""Host event tests for MENU tap/hold, compiling the firmware's actual C bodies.

Run from any directory with Python 3 and a native GCC/Clang compiler:
    python3 tools/test_menu_ab.py

Only hardware/UI dependencies are faked. MAIN_Key_MENU, MAIN_ProcessKeys,
COMMON_SwitchVFOs, MENU_Key_MENU, MENU_IsEditingName, GUI_SelectNextDisplay,
ACTION_Handle, RXTX_LOG_IsEnabled, and the keypad-lock/PTT-release blocks
come directly from the checkout.
This is not a complete radio or spectrum emulator.
"""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def function_source(path, name):
    """Find a C function and balance braces, ignoring comments and literals."""
    source = (ROOT / path).read_text(encoding="utf-8")
    pattern = r"(?m)^(?:static\s+)?(?:void|bool)\s+" + re.escape(name) + r"\s*\([^;]*?\)\s*\{"
    match = re.search(pattern, source)
    if not match:
        raise RuntimeError(f"Cannot locate {name} in {path}")
    opening = source.index("{", match.start())
    tokens = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', re.S)
    depth = 0
    for token in tokens.finditer(source, opening):
        if token.group() == "{":
            depth += 1
        elif token.group() == "}":
            depth -= 1
            if depth == 0:
                line = source.count("\n", 0, match.start()) + 1
                return f'#line {line} "{path}"\n' + source[match.start():token.end()] + "\n"
    raise RuntimeError(f"Unbalanced function {name} in {path}")


def action_enum_source():
    source = (ROOT / "App/settings.h").read_text(encoding="utf-8")
    match = re.search(r"enum ACTION_OPT_t\s*\{.*?\};", source, re.S)
    if not match:
        raise RuntimeError("Cannot locate firmware action IDs")
    return match.group() + "\n"


def lock_guard_source():
    source = (ROOT / "App/app/app.c").read_text(encoding="utf-8")
    begin = source.index("#ifdef ENABLE_FEAT_F4HWN // Disable PTT if KEY_LOCK")
    end = source.index("    if (Key <= KEY_9 || Key == KEY_F)", begin)
    line = source.count("\n", 0, begin) + 1
    return f'#line {line} "App/app/app.c"\n' + source[begin:end]


def ptt_guard_source():
    source = (ROOT / "App/app/app.c").read_text(encoding="utf-8")
    process_key = source.index("static void ProcessKey(KEY_Code_t Key, bool bKeyPressed, bool bKeyHeld)\n{")
    begin = source.index("    bool bFlag = false;", process_key)
    end = source.index("    if (gCurrentFunction == FUNCTION_TRANSMIT)", begin)
    line = source.count("\n", 0, begin) + 1
    return f'#line {line} "App/app/app.c"\n' + source[begin:end]


SUPPORT = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "App/driver/keyboard.h"

#define ENABLE_FEAT_F4HWN
#define ENABLE_SCAN_RANGES
#define ENABLE_FEAT_F4HWN_FULL_WATCH
#define ENABLE_FEAT_F4HWN_RESCUE_OPS
#define ENABLE_VOICE
#define ENABLE_FEAT_F4HWN_MULTIBOOT
#define ENABLE_FEAT_F4HWN_MULTIBOOT_HOT_CFG
#define ENABLE_DTMF_CALLING
#ifndef TEST_FLAT_MENU
#define ENABLE_FEAT_F4HWN_MENU_CAT
#endif

enum { DISPLAY_INVALID = -1, DISPLAY_MAIN, DISPLAY_MENU };
enum { FUNCTION_FOREGROUND, FUNCTION_TRANSMIT };
enum { BEEP_NONE, BEEP_1KHZ_60MS_OPTIONAL, BEEP_500HZ_60MS_DOUBLE_BEEP_OPTIONAL };
enum { SCAN_OFF, SCAN_FORWARD };
enum { VFO_CONFIGURE_NONE, VFO_CONFIGURE };
enum { CROSS_BAND_OFF, CROSS_BAND_CHAN_A, CROSS_BAND_CHAN_B };
enum { DUAL_WATCH_OFF, DUAL_WATCH_CHAN_A, DUAL_WATCH_CHAN_B, DUAL_WATCH_FULL };
enum { MENU_LEVEL_CAT, MENU_LEVEL_ITEMS };
enum { SET_LCK_PTT = 1, SET_LCK_ACTIONS = 2 };
enum { VOICE_ID_INVALID = -1, VOICE_ID_MENU, VOICE_ID_CONFIRM, VOICE_ID_CANCEL,
       VOICE_ID_SCRAMBLER_OFF, VOICE_ID_SCRAMBLER_ON };
typedef int VOICE_ID_t;
typedef int GUI_DisplayType_t;
enum { MENU_SCR, MENU_UPCODE, MENU_DWCODE, MENU_ANI_ID, MENU_DEL_CH,
       MENU_MEM_NAME, MENU_RESET, MENU_MEM_CH, MENU_SET_CFG, MENU_S_LIST,
       MENU_OTHER };
enum { SCAN_LIST_MODE_MIX = 4, MB_OK = 0 };
/* ACTION_OPT_t is copied unchanged from App/settings.h before this support. */

static struct {
    int TX_VFO, CROSS_BAND_RX_TX, DUAL_WATCH;
    bool KEY_LOCK, MENU_LOCK;
    uint8_t KEY_1_SHORT_PRESS_ACTION, KEY_1_LONG_PRESS_ACTION;
    uint8_t KEY_2_SHORT_PRESS_ACTION, KEY_2_LONG_PRESS_ACTION;
    uint8_t KEY_M_SHORT_PRESS_ACTION, KEY_M_LONG_PRESS_ACTION;
} gEeprom;
static int gScreenToDisplay, gRequestDisplayScreen;
static int gCurrentFunction, gBeepToPlay, gKeyInputCountdown;
static int gScanStateDir, gVfoConfigureMode, gScanPauseDelayIn_10ms;
static unsigned gInputBoxIndex, gScanRangeStart, gNextMrChannel;
static unsigned lastFoundFrqOrChan, lastFoundFrqOrChanOld;
static int gMenuLevel, gMenuCatCursor, gMenuListCount, gMenuCursor, gMenuCategory;
static int gCatOrder[4], gCatLastPos[4];
static bool gDTMF_InputMode, gHasVfoBackup, gScanKeepResult;
bool gWasFKeyPressed;
static bool gUpdateStatus, gUpdateDisplay, gFlagRefreshSetting;
static bool gRequestSaveSettings, gFlagReconfigureVfos, gScheduleDualWatch;
static bool gFlagResetVfos, gScanMixEditorActive, gCssBackgroundScan;
static bool gIsInSubMenu, gFlagAcceptSetting, gConfigBankExitPending;
static uint32_t gScanMixEditorMask;
static int gScanMixEditorCursor, gAskForConfirmation, gSubMenuSelection;
static int gAnotherVoiceID, gSetting_set_lck, gKeypadLocked;
static bool gLowBatteryConfirmed;
static bool gPttWasPressed, gPttWasReleased, gAskToSave, gAskToDelete;
static int key_input_timeout_500ms = 20;
static char dtmf_input[17];
static int dtmf_length;
#define gDTMF_InputBox_Index dtmf_length
#define gDTMF_InputBox dtmf_input
static int edit_index, edit_last_key, edit_char_index;
static bool edit_is_uppercase;
static char edit[11], edit_original[11];
static struct { int voice_id; } MenuList[12];
static unsigned gMenuIndices[12];

/* Dependency fakes expose calls and ordering, not MENU decision logic. */
static int stop_calls, build_category_calls, build_view_calls, move_calls;
static int exclusion_writes, action_calls, scanner_stop_calls, routed;
static int next_sequence, stop_sequence, category_sequence;
static int current_menu_id, scan_saved_channel, channel_at_stop, last_action;
static bool source_input_consumed;
typedef struct { bool exclude; } ChannelAttributes_t;
static ChannelAttributes_t attributes;

void HideFKeyIcon(void) { gWasFKeyPressed = false; }
static void CHFRSCANNER_Stop(void) {
    ++stop_calls;
    stop_sequence = ++next_sequence;
    channel_at_stop = scan_saved_channel;
    gScanStateDir = SCAN_OFF;
}
static void UI_MENU_BuildCategoryScreen(void) {
    ++build_category_calls;
    category_sequence = ++next_sequence;
    gMenuListCount = 4;
}
static void UI_MENU_BuildView(void) { ++build_view_calls; gMenuListCount = 4; }
static void channelMoveSwitch(void) {
    ++move_calls;
    if (gInputBoxIndex) source_input_consumed = true;
}
static int UI_MENU_GetCurrentMenuId(void) { return current_menu_id; }
static bool RADIO_CheckValidChannel(int c, bool p, int list) {
    (void)c; (void)p; (void)list; return true;
}
static void SETTINGS_FetchChannelName(char *name, int channel) {
    (void)channel; strcpy(name, "Test");
}
static void MENU_OpenScanMixEditor(void) { gScanMixEditorActive = true; }
static void UI_DisplayMenu(void) {}
static void MENU_AcceptSetting(void) {}
static void NVIC_SystemReset(void) {}
static int MB_GetActiveBank(void) { return 0; }
static int MB_SetActiveBank(int bank) { (void)bank; return MB_OK; }
static void UI_MultibootShowConfigError(int err) { (void)err; }
static void MENU_ApplyConfigBank(int bank) { (void)bank; }
static void SCANNER_Stop(void) { ++scanner_stop_calls; }
static void AUDIO_SetVoiceID(int i, int voice) { (void)i; (void)voice; }
static void AUDIO_PlaySingleVoice(bool wait) { (void)wait; }
static void AUDIO_PlayBeep(int beep) { gBeepToPlay = beep; }
static char DTMF_GetCharacter(KEY_Code_t key) { return key == KEY_MENU ? 'A' : (char)0xFF; }
static void DTMF_Append(char value) { dtmf_input[dtmf_length++] = value; }
static void DTMF_clear_input_box(void) {
    dtmf_length = 0;
    dtmf_input[0] = 0;
    gDTMF_InputMode = false;
}
static void MAIN_Key_DIGITS(KEY_Code_t key, bool pressed, bool held) {
    (void)key; (void)pressed; (void)held;
}
static void MAIN_Key_UP_DOWN(bool pressed, bool held, int direction) {
    (void)pressed; (void)held; (void)direction;
}
static void MAIN_Key_EXIT(bool pressed, bool held) { (void)pressed; (void)held; }
static void MAIN_Key_STAR(bool pressed, bool held) { (void)pressed; (void)held; }
static void GENERIC_Key_F(bool pressed, bool held) { (void)pressed; (void)held; }
static void GENERIC_Key_PTT(bool pressed) { (void)pressed; }

/* Permit compiling the unchanged upstream body as a negative control too. */
static bool FUNCTION_IsRx(void) { return false; }
static bool CHFRSCANNER_ExcludeCurrentScanRange(void) { ++exclusion_writes; return true; }
static void UI_MAIN_NotifyScanProgressDataChanged(void) {}
static void CHFRSCANNER_ContinueScanning(void) {}
static ChannelAttributes_t *MR_GetChannelAttributes(unsigned channel) {
    (void)channel; return &attributes;
}
static void MR_SaveChannelAttributesToFlash(unsigned channel, ChannelAttributes_t *att) {
    (void)channel; (void)att; ++exclusion_writes;
}
void MAIN_OpenMenu(void);
void COMMON_SwitchVFOs(void);
static void ACTION_Execute(enum ACTION_OPT_t action) {
    last_action = action;
    if (action == ACTION_OPT_MENU) { MAIN_OpenMenu(); return; }
    if (action == ACTION_OPT_A_B) { COMMON_SwitchVFOs(); return; }
    if (action != ACTION_OPT_NONE) ++action_calls;
}
#define IS_MR_CHANNEL(channel) ((channel) < 1024)
'''


TESTS = r'''
#line 1 "menu_ab_host_tests"
static void reset(void) {
    memset(&gEeprom, 0, sizeof(gEeprom));
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_A_B;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_MENU;
    gScreenToDisplay = DISPLAY_MAIN;
    gRequestDisplayScreen = DISPLAY_INVALID;
    gCurrentFunction = FUNCTION_FOREGROUND;
    gBeepToPlay = BEEP_NONE;
    gKeyInputCountdown = 0;
    gScanStateDir = SCAN_OFF;
    gVfoConfigureMode = VFO_CONFIGURE_NONE;
    gInputBoxIndex = gScanRangeStart = 0;
    gDTMF_InputMode = gHasVfoBackup = gScanKeepResult = false;
    gWasFKeyPressed = false;
    gUpdateStatus = gUpdateDisplay = gFlagRefreshSetting = false;
    gRequestSaveSettings = gFlagReconfigureVfos = gScheduleDualWatch = false;
    gFlagResetVfos = gScanMixEditorActive = gCssBackgroundScan = false;
    gIsInSubMenu = gFlagAcceptSetting = gConfigBankExitPending = false;
    gMenuLevel = MENU_LEVEL_ITEMS;
    gMenuCatCursor = 2;
    gMenuListCount = 4;
    gMenuCursor = 1;
    for (int i = 0; i < 4; ++i) { gCatOrder[i] = i; gCatLastPos[i] = 0; }
    gScanMixEditorMask = 3;
    gScanMixEditorCursor = gAskForConfirmation = gSubMenuSelection = 0;
    gAnotherVoiceID = VOICE_ID_INVALID;
    gSetting_set_lck = 0;
    gKeypadLocked = 0;
    gLowBatteryConfirmed = false;
    gPttWasPressed = gPttWasReleased = gAskToSave = gAskToDelete = false;
    dtmf_length = 0;
    memset(dtmf_input, 0, sizeof(dtmf_input));
    edit_index = -1;
    stop_calls = build_category_calls = build_view_calls = move_calls = 0;
    exclusion_writes = action_calls = scanner_stop_calls = routed = 0;
    next_sequence = stop_sequence = category_sequence = 0;
    current_menu_id = MENU_OTHER;
    scan_saved_channel = 17;
    channel_at_stop = -1;
    last_action = ACTION_OPT_NONE;
    source_input_consumed = false;
}

static void tap(void) {
    MAIN_Key_MENU(true, false);
    MAIN_Key_MENU(false, false);
}

static void hold(void) {
    MAIN_Key_MENU(true, false);
    MAIN_Key_MENU(true, true);
}

static void test_tap_switches_once(void) {
    reset();
    gWasFKeyPressed = true;
    gScanRangeStart = 14400000;
    MAIN_Key_MENU(true, false);
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen == DISPLAY_INVALID);
    assert(gBeepToPlay == BEEP_1KHZ_60MS_OPTIONAL);
    MAIN_Key_MENU(false, false);
    assert(gEeprom.TX_VFO == 1 && !gWasFKeyPressed);
    assert(gRequestDisplayScreen == DISPLAY_MAIN);
    assert(gRequestSaveSettings && gFlagReconfigureVfos && gScheduleDualWatch);
    assert(gVfoConfigureMode == VFO_CONFIGURE && gScanRangeStart == 0);
    assert(build_category_calls == 0 && action_calls == 0);
    tap();
    assert(gEeprom.TX_VFO == 0);
    puts("PASS tap switches A/B on release, once per tap");
}

static void test_hold_and_release(void) {
    reset();
    gWasFKeyPressed = true;
    gInputBoxIndex = 2;
    gHasVfoBackup = true;
    hold();
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen == DISPLAY_MENU);
    assert(gFlagRefreshSetting && !gScanMixEditorActive && !gWasFKeyPressed);
    assert(gInputBoxIndex == 0 && action_calls == 0);
    assert(gAnotherVoiceID == VOICE_ID_MENU);
#ifdef ENABLE_FEAT_F4HWN_MENU_CAT
    assert(gMenuLevel == MENU_LEVEL_CAT && gMenuCursor == 2);
    assert(build_category_calls == 1);
#else
    assert(build_category_calls == 0);
#endif
    /* Exercise the real destination handler after GUI_SelectNextDisplay. */
    gIsInSubMenu = true;
    gAskForConfirmation = 1;
    GUI_SelectNextDisplay(gRequestDisplayScreen);
    gRequestDisplayScreen = DISPLAY_INVALID;
    assert(!gIsInSubMenu && !gAskForConfirmation);
    MENU_Key_MENU(false, true);
    assert(gRequestDisplayScreen == DISPLAY_INVALID && !gIsInSubMenu);
    assert(gEeprom.TX_VFO == 0 && build_view_calls == 0);
    puts("PASS hold opens menu; held release cannot confirm or switch A/B");
}

static void test_hold_release_on_main(void) {
    reset();
    MAIN_Key_MENU(false, true);
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen == DISPLAY_INVALID);
    assert(stop_calls == 0 && action_calls == 0);
    puts("PASS held release is inert if the screen has not changed");
}

static void test_numeric_and_dtmf_input(void) {
    reset();
    gInputBoxIndex = 2;
    tap();
    assert(source_input_consumed && move_calls == 1 && gInputBoxIndex == 0);
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen == DISPLAY_MAIN);
    assert(!gRequestSaveSettings && build_category_calls == 0);
    reset();
    gDTMF_InputMode = true;
    tap();
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen == DISPLAY_INVALID);
    assert(move_calls == 0 && stop_calls == 0);
    puts("PASS tap confirms partial numeric input and leaves DTMF entry alone");
}

static void test_scan_interactions(void) {
    reset();
    gScanStateDir = SCAN_FORWARD;
    gScanKeepResult = true;
    gScanPauseDelayIn_10ms = 50;
    hold();
    assert(stop_calls == 1 && channel_at_stop == 17 && gScanKeepResult);
    assert(gRequestDisplayScreen == DISPLAY_MENU && gEeprom.TX_VFO == 0);
    assert(exclusion_writes == 0 && action_calls == 0);
#ifdef ENABLE_FEAT_F4HWN_MENU_CAT
    assert(stop_sequence > 0 && category_sequence > stop_sequence);
#endif
    reset();
    gScanStateDir = SCAN_FORWARD;
    gScanKeepResult = true;
    tap();
    assert(stop_calls == 1 && gScanStateDir == SCAN_OFF);
    assert(gEeprom.TX_VFO == 1 && gRequestDisplayScreen == DISPLAY_MAIN);
    assert(exclusion_writes == 0 && action_calls == 0);
    puts("PASS scan stops before menu/A-B action and MENU never excludes channels");
}

static void test_vfo_modes(void) {
    reset();
    gEeprom.CROSS_BAND_RX_TX = CROSS_BAND_CHAN_A;
    gEeprom.DUAL_WATCH = DUAL_WATCH_CHAN_A;
    tap();
    assert(gEeprom.CROSS_BAND_RX_TX == CROSS_BAND_CHAN_B);
    assert(gEeprom.DUAL_WATCH == DUAL_WATCH_CHAN_B);
    tap();
    assert(gEeprom.CROSS_BAND_RX_TX == CROSS_BAND_CHAN_A);
    assert(gEeprom.DUAL_WATCH == DUAL_WATCH_CHAN_A);
    reset();
    gEeprom.DUAL_WATCH = DUAL_WATCH_FULL;
    tap();
    assert(gEeprom.DUAL_WATCH == DUAL_WATCH_FULL);
    puts("PASS A/B uses existing cross-band and dual/full-watch behavior");
}

static void test_menu_confirmation(void) {
    reset();
    gScreenToDisplay = DISPLAY_MENU;
#ifdef ENABLE_FEAT_F4HWN_MENU_CAT
    gMenuLevel = MENU_LEVEL_CAT;
    MENU_Key_MENU(true, false);
    assert(gMenuLevel == MENU_LEVEL_ITEMS && build_view_calls == 1);
    assert(!gIsInSubMenu);
#endif
    MENU_Key_MENU(true, false);
    assert(gIsInSubMenu && !gFlagAcceptSetting);
    MENU_Key_MENU(false, false);
    assert(gIsInSubMenu && !gFlagAcceptSetting);
    MENU_Key_MENU(true, false);
    assert(!gIsInSubMenu && gFlagAcceptSetting);
    assert(gEeprom.TX_VFO == 0);
    puts("PASS MENU inside settings retains category, edit, and confirm behavior");
}

static void test_menu_lock(void) {
    reset();
    gEeprom.MENU_LOCK = true;
    gScanStateDir = SCAN_FORWARD;
    hold();
    assert(gRequestDisplayScreen != DISPLAY_MENU && stop_calls == 0);
    assert(gEeprom.TX_VFO == 0);
    MAIN_Key_MENU(false, true);
    assert(gEeprom.TX_VFO == 0);
    /* Rescue menu lock blocks configuration, not an ordinary A/B tap. */
    tap();
    assert(gEeprom.TX_VFO == 1);
    puts("PASS rescue MENU_LOCK still blocks entering settings");
}
'''


GUARD_TESTS = r'''
#line 1 "menu_ab_lock_tests"
static void test_keypad_lock(void) {
    const bool events[][2] = {{true, false}, {true, true}, {false, true}, {false, false}};
    for (int actions = 0; actions <= SET_LCK_ACTIONS; actions += SET_LCK_ACTIONS) {
        for (unsigned i = 0; i < sizeof(events) / sizeof(events[0]); ++i) {
            reset();
            gEeprom.KEY_LOCK = true;
            gSetting_set_lck = actions;
            guarded_dispatch(KEY_MENU, events[i][0], events[i][1], false);
            assert(!routed && gEeprom.TX_VFO == 0);
            assert(gRequestDisplayScreen != DISPLAY_MENU);
        }
    }
    reset();
    gEeprom.KEY_LOCK = true;
    guarded_dispatch(KEY_SIDE1, true, true, false);
    assert(routed);
    reset();
    gEeprom.KEY_LOCK = true;
    gSetting_set_lck = SET_LCK_ACTIONS;
    guarded_dispatch(KEY_SIDE1, true, true, false);
    assert(!routed);
    reset();
    guarded_dispatch(KEY_MENU, true, true, true);
    assert(!routed && gRequestDisplayScreen != DISPLAY_MENU);
    reset();
    guarded_dispatch(KEY_EXIT, true, false, true);
    assert(gLowBatteryConfirmed && !routed);
    puts("PASS actual dispatcher lock block blocks MENU tap/hold and preserves side actions");
}

static void test_dtmf_event_chain(void) {
    reset();
    gDTMF_InputMode = true;
    guarded_dispatch(KEY_MENU, true, false, false);
    assert(dtmf_length == 1 && dtmf_input[0] == 'A' && gPttWasReleased);
    guarded_dispatch(KEY_MENU, true, true, false);
    assert(dtmf_length == 1 && gDTMF_InputMode);
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen != DISPLAY_MENU);
    guarded_dispatch(KEY_MENU, false, true, false);
    assert(dtmf_length == 1 && gDTMF_InputMode && !gPttWasReleased);
    assert(gEeprom.TX_VFO == 0 && gRequestDisplayScreen != DISPLAY_MENU);
    puts("PASS actual MAIN DTMF entry and PTT-release guard consume held MENU sequence");
}

static void test_menu_and_side_assignments(void) {
    reset();
    assert(!RXTX_LOG_IsEnabled());
    uint8_t *actions[] = {
        &gEeprom.KEY_1_SHORT_PRESS_ACTION, &gEeprom.KEY_1_LONG_PRESS_ACTION,
        &gEeprom.KEY_2_SHORT_PRESS_ACTION, &gEeprom.KEY_2_LONG_PRESS_ACTION,
        &gEeprom.KEY_M_SHORT_PRESS_ACTION, &gEeprom.KEY_M_LONG_PRESS_ACTION,
    };
    const KEY_Code_t keys[] = {KEY_SIDE1, KEY_SIDE1, KEY_SIDE2, KEY_SIDE2, KEY_MENU, KEY_MENU};
    for (unsigned i = 0; i < 6; ++i) {
        *actions[i] = ACTION_OPT_RXTX_LOG;
        assert(RXTX_LOG_IsEnabled());
        const bool held = i % 2 != 0;
        ACTION_Handle(keys[i], !held, held);
        assert(action_calls == (int)i);
        ACTION_Handle(keys[i], held, held);
        assert(action_calls == (int)i + 1 && last_action == ACTION_OPT_RXTX_LOG);
        *actions[i] = ACTION_OPT_NONE;
        assert(!RXTX_LOG_IsEnabled());
    }
    puts("PASS all six short/long assignments execute once and activate RF log");
}

static void test_reversed_assignments(void) {
    reset();
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_MENU;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_A_B;
    MAIN_Key_MENU(true, false);
    assert(gRequestDisplayScreen == DISPLAY_INVALID && gEeprom.TX_VFO == 0);
    MAIN_Key_MENU(false, false);
    assert(gRequestDisplayScreen == DISPLAY_MENU && gEeprom.TX_VFO == 0);
    GUI_SelectNextDisplay(DISPLAY_MENU);
    gRequestDisplayScreen = DISPLAY_INVALID;
    MENU_Key_MENU(false, false);
    assert(!gIsInSubMenu && gRequestDisplayScreen == DISPLAY_INVALID);
    reset();
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_MENU;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_A_B;
    hold();
    assert(gEeprom.TX_VFO == 1 && gRequestDisplayScreen == DISPLAY_MAIN);
    MAIN_Key_MENU(false, true);
    assert(gEeprom.TX_VFO == 1 && gRequestDisplayScreen == DISPLAY_MAIN);
    assert(build_category_calls == 0);
    reset();
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_MENU;
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_A_B;
    gEeprom.MENU_LOCK = true;
    tap();
    assert(gRequestDisplayScreen != DISPLAY_MENU);
    hold();
    assert(gEeprom.TX_VFO == 1);
    puts("PASS reversed MENU/A-B binding opens on tap and switches once on hold");
}

static void test_non_menu_scan_action(void) {
    reset();
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_SCAN;
    gScanStateDir = SCAN_FORWARD;
    tap();
    assert(stop_calls == 0 && gScanStateDir == SCAN_FORWARD);
    assert(last_action == ACTION_OPT_SCAN && action_calls == 1);
    reset();
    gEeprom.KEY_M_LONG_PRESS_ACTION = ACTION_OPT_SCAN;
    gEeprom.KEY_M_SHORT_PRESS_ACTION = ACTION_OPT_MENU;
    gScanStateDir = SCAN_FORWARD;
    hold();
    MAIN_Key_MENU(false, true);
    assert(stop_calls == 0 && gScanStateDir == SCAN_FORWARD);
    assert(last_action == ACTION_OPT_SCAN && action_calls == 1);
    puts("PASS assigned SCAN reaches its action without a premature scanner stop");
}

int main(void) {
    test_tap_switches_once();
    test_hold_and_release();
    test_hold_release_on_main();
    test_numeric_and_dtmf_input();
    test_scan_interactions();
    test_vfo_modes();
    test_menu_confirmation();
    test_menu_lock();
    test_keypad_lock();
    test_dtmf_event_chain();
    test_menu_and_side_assignments();
    test_reversed_assignments();
    test_non_menu_scan_action();
#ifdef TEST_FLAT_MENU
    puts("All 13 MENU event groups passed (flat menu).");
#else
    puts("All 13 MENU event groups passed (category menu).");
#endif
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"), help="Native C compiler command")
    parser.add_argument("--no-sanitize", action="store_true", help="Disable address/undefined sanitizers")
    args = parser.parse_args()
    pieces = [action_enum_source(), SUPPORT]
    pieces.append(function_source("App/app/action.c", "ACTION_Handle"))
    pieces.append(function_source("App/app/rxtx_log.c", "RXTX_LOG_IsEnabled"))
    pieces.append(function_source("App/app/common.c", "COMMON_SwitchVFOs"))
    pieces.append(function_source("App/app/main.c", "MAIN_OpenMenu"))
    pieces.append(function_source("App/app/main.c", "MAIN_Key_MENU"))
    pieces.append(function_source("App/app/main.c", "MAIN_ProcessKeys"))
    pieces.append(function_source("App/app/menu.c", "MENU_IsEditingName"))
    pieces.append(function_source("App/app/menu.c", "MENU_Key_MENU"))
    pieces.append(function_source("App/ui/ui.c", "GUI_SelectNextDisplay"))
    pieces.append(TESTS)
    pieces.append("\nstatic void guarded_dispatch(KEY_Code_t Key, bool bKeyPressed, bool bKeyHeld, bool lowBatPopup) {\n")
    pieces.append(lock_guard_source())
    pieces.append(ptt_guard_source())
    pieces.append("\n    routed = 1;\n    MAIN_ProcessKeys(Key, bKeyPressed, bKeyHeld);\nSkip:;\n}\n")
    pieces.append(GUARD_TESTS)
    with tempfile.TemporaryDirectory(prefix="f4hwn-menu-host-") as temporary:
        source = Path(temporary) / "menu_ab_test.c"
        source.write_text("\n".join(pieces), encoding="utf-8")
        for mode in ("categories", "flat"):
            executable = Path(temporary) / f"menu_ab_{mode}"
            command = shlex.split(args.cc) + [
                "-std=c11", "-O1", "-g", "-funsigned-char", "-Wall", "-Wextra",
                "-Wno-unused-function", "-Wno-unused-variable", "-Werror=implicit-function-declaration",
                "-fno-omit-frame-pointer", "-I", str(ROOT), str(source), "-o", str(executable),
            ]
            if not args.no_sanitize:
                command += ["-fsanitize=address,undefined"]
            if mode == "flat":
                command += ["-DTEST_FLAT_MENU"]
            print(f"Compiling actual firmware MENU handlers ({mode}) with {args.cc}", flush=True)
            subprocess.run(command, check=True)
            subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
