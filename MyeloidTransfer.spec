# -*- mode: python -*-

block_cipher = None


a = Analysis(['MyeloidTransfer.py'],
             pathex=['C:\\Users\\ben\\Documents\\Work\\python_myeloid_coverage'],
             binaries=[],
             datas=[],
             hiddenimports=['tkinter', 'xlsxwriter'],
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
          name='Myeloid_transfer_and_coverage',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True , icon='dna.ico')

		  
import shutil
shutil.copyfile('transfer.config', '{0}/transfer.config'.format(DISTPATH))
