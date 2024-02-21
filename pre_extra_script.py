'''
    PlatformIO Advanced Pre-Build-Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=superfluous-parens,broad-except,E0602
# ------------------
# Importing Modules
# ------------------
from SCons.Script import COMMAND_LINE_TARGETS #pylint: disable=W0611,E0401
import firmware_manager

#TODO: Try to update the library
#git submodule update -f --remote

# ------------------
# Main Script
# ------------------
print( "\n", "-"*70, "\n\n", "\tpre_script.py" )
Import("env")

if "idedata" in COMMAND_LINE_TARGETS:
    env.Exit(0)
firmware_manager.pre_extra_script_main(env)

print( "\n", "-"*70, "\n" )

# Dump global construction environment (for debug purpose)
#with open("dump_env.ini"    ,"w",encoding="utf-8") as file: file.write( str( env.Dump ) )