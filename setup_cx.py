from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a console application).
base = None
# if sys.platform == "win32":
#    base = "Win32GUI"

setup(
    name = "Voice2Text",
    version = "0.1",
    description = "Voice to text application",
    executables = [Executable("main.py", base=base)]
)