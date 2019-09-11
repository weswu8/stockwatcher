set TCL_LIBRARY=C:\Python35\tcl\tcl8.6
set TK_LIBRARY=C:\Python35\tcl\tk8.6
python C:\Python35\Scripts\cxfreeze stockwatcher.py --base-name=C:\\Python35\\Lib\\site-packages\\cx_Freeze\\bases\\Win32GUI.exe --target-dir bin --icon sw-big.ico
copy C:\Python35\DLLs\tcl86t.dll bin
copy C:\Python35\DLLs\tk86t.dll bin
copy sw-small.ico bin
copy stockwatcher.conf bin
