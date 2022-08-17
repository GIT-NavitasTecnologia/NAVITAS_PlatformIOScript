# ------------------
# Importing Modules
# ------------------
import firmware_manager
from SCons.Script import COMMAND_LINE_TARGETS

#TODO: Try to update the library
#git submodule update --remote

# ------------------
# Main Script
# ------------------
print( "\n", "-"*70, "\n\n", "\tpre_script.py" )
Import("env")

if "idedata" in COMMAND_LINE_TARGETS: env.Exit(0)
firmware_manager.pre_extra_script_main(env)

print( "\n", "-"*70, "\n" )
