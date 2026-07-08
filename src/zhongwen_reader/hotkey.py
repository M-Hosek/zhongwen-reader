"""Trigger-key state via Win32, no global hook needed."""

import ctypes


def is_key_held(vk_code: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
