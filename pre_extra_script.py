'''
    PlatformIO Advanced Pre-Build-Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=superfluous-parens,broad-except,E0602
# ------------------
# Importing Modules
# ------------------
import firmware_manager as fmw
from SCons.Script import Import #pylint: disable=C0415,W0611,E0401

#TODO: Try to update the library
#git submodule update -f --remote

# ------------------
# Main Script
# ------------------
print( "\n", "-"*70, "\n\n", '\tpre_extra_script' )
try:
    Import("env")
    fmw.pre_extra_script_main(env)
except Exception as e:
    print(e)
print( "\n", "-"*70, "\n" )
