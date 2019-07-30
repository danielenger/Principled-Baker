import os
import filecmp

file_names = ["__init__.py",
              "pbaker_bake.py",
              "pbaker_functions.py",
              "pbaker_list.py",
              "pbaker_panel.py",
              "pbaker_prefs.py",
              "pbaker_preset.py",
              "pbaker_settings.py",
              "pbaker_panel_279.py",]

path_28 = os.path.abspath("D:\\blender\_projects\Addon_Principled Baker_for_2-8")
path_27 = os.path.abspath("D:\\blender\_projects\Addon_Principled Baker_for_2-79")


print(path_28)
print(os.path.join(path_28, "__init__.py"))

for name in file_names:
    if not filecmp.cmp(os.path.join(path_28, name), os.path.join(path_27, name)):
        print("NOT EQUAL {}".format(name))

        file_28 = open(os.path.join(path_28, name), 'r')
        file_27 = open(os.path.join(path_27, name), 'w')

        text = file_28.read()

        if name == "__init__.py":
            text = text.replace("(2, 80, 0)", "(2, 79, 0)")

        if name == "pbaker_settings.py":
            text = text.replace(": ", "= ")

        if name == "pbaker_prefs.py":
            text = text.replace(": ", "= ")

        if name == "pbaker_list.py":
            text = text.replace("suffix: ", "suffix= ")
            text = text.replace("do_bake: ", "do_bake= ")

        file_27.write(text)
    else:
        print("EQUAL     {}".format(name))
