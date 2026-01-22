'''
    PlatformIO Advanced Post-Build-Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=broad-except,E0602
# ------------------
# Importing Modules
# ------------------
import firmware_manager as fmw
from SCons.Script import Import #pylint: disable=C0415,W0611,E0401

# ------------------
# Callbacks
# ------------------
print( "\n", "-"*70, "\n\n", '\tpost_extra_script' )

try:
    if not fmw.pio_tools.has_cmd_line_target("idedata"):
        Import("env", "projenv")

        # Dump global construction environment (for debug purpose)
        with open("dump_env.ini"    ,"w",encoding="utf-8") as file:
            file.write( str( env.Dump() ) )
        with open("dump_projenv.ini","w",encoding="utf-8") as file:
            file.write( str( projenv.Dump() ) )

        fmw.post_extra_script_main(env, projenv)
except Exception as e:
    print(e)

print( "\n", "-"*70, "\n" )
