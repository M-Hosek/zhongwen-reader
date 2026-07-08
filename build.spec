# PyInstaller spec: onefile windowed build of Zhongwen Reader.
# Build with:  .venv\Scripts\pyinstaller build.spec --noconfirm

a = Analysis(
    ["run_app.py"],
    pathex=["src"],
    datas=[("data/cedict_ts.u8", "data")],
    hiddenimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="ZhongwenReader",
    icon="zhongwen_reader.ico",
    console=False,
    upx=False,
)
