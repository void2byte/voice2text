#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from window_binder.utils.window_identifier import WindowIdentificationService

def test_detection_modes():
    """Тест различных режимов обнаружения окон"""
    service = WindowIdentificationService()
    
    # Проверяем доступность WIN32
    from window_binder.utils.window_identifier import WIN32_AVAILABLE
    print(f"WIN32_AVAILABLE: {WIN32_AVAILABLE}")
    
    print("Testing detection modes:")
    print("Mode 0: Filtered (only user windows)")
    print("Mode 1: Visible windows")
    print("Mode 2: Basic extended (+ some hidden)")
    print("Mode 3: Full extended (all windows)")
    print()
    
    for mode in range(4):
        try:
            print(f"Testing mode {mode}...")
            windows = service.get_all_windows_with_details(mode)
            print(f"Mode {mode}: {len(windows)} windows")
            
            # Показываем первые несколько окон для каждого режима
            if windows:
                print(f"  First few windows in mode {mode}:")
                for i, window in enumerate(windows[:5]):
                    print(f"    {i+1}. {window.get('title', 'No title')}")
            print()
        except Exception as e:
            print(f"Error in mode {mode}: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    test_detection_modes()