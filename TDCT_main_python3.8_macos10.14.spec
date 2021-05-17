# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['TDCT_main.py'],
             pathex=['/Users/kf656/Desktop/Scripts/correlativeFIB/repo_3DCT'],
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

a.binaries = a.binaries - TOC([('libpng16.16.dylib',None,None)])  # avoid bundling X11 libpng (too old)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options = [ ('W ignore', None, 'OPTION') ],
          name='3D Correlation Toolbox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon='icons/3DCT_icon.icns')

app = BUNDLE(exe,
             name='3D Correlation Toolbox.app',
             icon='icons/3DCT_icon.icns',
             bundle_identifier=None,
             info_plist={
                'NSHighResolutionCapable': 'True',
                'CFBundleShortVersionString': '3.0.0',
                'CFBundleVersion': '3.0.0'
                })
