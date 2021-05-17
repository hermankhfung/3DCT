# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['TDCT_main.py'],
             pathex=['C:\\fung\\3dct-master'],
             binaries=[],
             datas=[
               ('TDCT_main.ui','.'),
               ('TDCT_correlation.ui','.'),
               ('icons','./icons')
              ],
             hiddenimports=[
               'skimage.feature',
               'icons_rc',
               'imagecodecs'
              ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='3D Correlation Toolbox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon='icons\\3DCT_icon.ico')
