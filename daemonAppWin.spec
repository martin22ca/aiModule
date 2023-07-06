# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
         ( 'src/models/dlib_face_recognition_resnet_model_v1.dat', 'models/' ),
         ( 'src/models/knnPickleFile.pickle', 'models/' ),
         ( 'src/models/namesFile.pickle', 'models/' ),
         ( 'src/models/shape_predictor_5_face_landmarks.dat', 'models/' ),
         ( '.venv/Lib/site-packages/mediapipe/modules', 'mediapipe/modules'),
         ( 'src/config.ini', '.')
         ]


a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='daemonApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='daemonApp',
)
