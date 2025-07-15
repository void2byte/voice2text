#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from window_binder.utils.window_identifier import WindowIdentificationService

service = WindowIdentificationService()

print("Testing detection modes:")
for mode in range(4):
    try:
        windows = service.get_all_windows_with_details(mode)
        print(f"Mode {mode}: {len(windows)} windows")
        if windows:
            print(f"  First window: {windows[0]['title']}")
    except Exception as e:
        print(f"Mode {mode}: Error - {e}")
        import traceback
        traceback.print_exc()
    print()