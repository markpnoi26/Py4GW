from PackageTemplate.my_lib import *

from Py4GWCoreLib import *

MODULE_NAME = "widget template"

def configure():
    ConsoleLog(MODULE_NAME, "this is the configure function", Console.MessageType.Info)

def main():
    if PyImGui.begin("my library tester"):
        PyImGui.text(my_library_function())
    
    PyImGui.end()
    
if __name__ == "__main__":
    main()
