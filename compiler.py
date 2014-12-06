import py_compile, zipfile, os

WOTVersion = "0.9.4"

if os.path.exists("autoaim_indicator-"+WOTVersion+".zip"):
    os.remove("autoaim_indicator-"+WOTVersion+".zip")

py_compile.compile("src/__init__.py")
py_compile.compile("src/CameraNode.py")
py_compile.compile("src/autoaim_indicator.py")

fZip = zipfile.ZipFile("autoaim_indicator-"+WOTVersion+".zip", "w")
fZip.write("src/__init__.pyc", WOTVersion+"/scripts/client/mods/__init__.pyc")
fZip.write("src/CameraNode.pyc", WOTVersion+"/scripts/client/CameraNode.pyc")
fZip.write("src/autoaim_indicator.pyc", WOTVersion+"/scripts/client/mods/autoaim_indicator.pyc")
fZip.write("data/autoaim_indicator.dds", WOTVersion+"/scripts/client/mods/autoaim_indicator.dds")
fZip.write("data/autoaim_indicator.json", WOTVersion+"/scripts/client/mods/autoaim_indicator.json")
fZip.close()
