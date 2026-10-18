# Qt / PySide6 / Shiboken6

The native interface uses unmodified PySide6 Essentials, Shiboken6 and Qt 6.8.3 shared libraries under the LGPL version 3 option. LGPL-3.0 and GPL-3.0 license texts accompany this package. No QtWebEngine or embedded browser is used.

Corresponding upstream sources for these exact releases:

- https://github.com/pyside/pyside-setup/tree/v6.8.3
- https://github.com/qt/qtbase/tree/v6.8.3
- https://github.com/qt/qtwayland/tree/v6.8.3

The Python bindings and Qt shared libraries remain separate files, without a signature lock or anti-replacement mechanism. Compatible replacements may be placed in runtime/windows/Lib/site-packages on Windows or _internal on Linux. Application source and build scripts are provided in the repository. Rebuilding the application is permitted; firmware compatibility checks are not restrictions on replacing the Qt libraries.

Official unmodified binary distributions: PyPI PySide6-Essentials 6.8.3 and shiboken6 6.8.3. Runtime component hashes and dependency information are recorded in the package manifest. Python and UEFIExtract have their own accompanying notices. The Linux launcher uses PyInstaller 6.16.0 with its bootloader exception; see PyInstaller-COPYING.txt.
