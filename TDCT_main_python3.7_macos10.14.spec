# -*- mode: python ; coding: utf-8 -*-

import os

spec_root = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None

a = Analysis(['TDCT_main.py'],
             pathex=[
                spec_root,
                os.path.join(spec_root,'venv_python3.7_macos10.14/lib/python3.7/site-packages')
                ],
             binaries=[],
             datas=[
                (os.path.join(spec_root,'TDCT_main.ui'),'.'),
                (os.path.join(spec_root,'TDCT_correlation.ui'),'.'),
                (os.path.join(spec_root,'icons'),'./icons')
             ],
             hiddenimports=[
                'PyQt5',
                'numpy',
                'scipy',
                'matplotlib',
                'opencv-python-headless',
                'tifffile',
                'qimage2ndarray',
                'colorama',
                'tools3dct',
                'pkg_resources.py2_warn',
                'icons_rc'
                ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
# avoid bundling X11 libpng (too old)
a.binaries = a.binaries - TOC([('libpng16.16.dylib',None,None)])
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          options = [ ('W ignore', None, 'OPTION') ],
          exclude_binaries=True,
          name='3D Correlation Toolbox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon=os.path.join(spec_root,'icons/3DCT_icon.icns'))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='TDCT_main')
app = BUNDLE(coll,
             name='3D Correlation Toolbox.app',
             icon=os.path.join(spec_root,'icons/3DCT_icon.icns'),
             bundle_identifier=None,
             info_plist={
                'NSHighResolutionCapable': 'True',
                'CFBundleShortVersionString': '3.0.0',
                'CFBundleVersion': '3.0.0'
                })
