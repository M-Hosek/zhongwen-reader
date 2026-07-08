"""Generate the .ico for the packaged exe from the tray icon artwork."""

import sys

sys.path.insert(0, "src")

from zhongwen_reader.tray import _make_icon_image

_make_icon_image().save(
    "zhongwen_reader.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
)
print("wrote zhongwen_reader.ico")
