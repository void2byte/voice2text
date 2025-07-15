#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    import win32gui
    import win32process
    import psutil
    print("WIN32 modules imported successfully")
    
    def test_enum_windows():
        windows = []
        
        def enum_callback(hwnd, windows_list):
            try:
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    windows_list.append(title)
            except Exception as e:
                print(f"Error getting window title: {e}")
            return True
        
        win32gui.EnumWindows(enum_callback, windows)
        print(f"Found {len(windows)} windows with titles")
        
        if windows:
            print("First 5 windows:")
            for i, title in enumerate(windows[:5]):
                print(f"  {i+1}. {title}")
    
    test_enum_windows()
    
except ImportError as e:
    print(f"WIN32 import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()