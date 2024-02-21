'''
    PlatformIO Advanced Post-Build-Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=superfluous-parens,broad-except,E0602
# ------------------
# Importing Modules
# ------------------
import firmware_manager

# ------------------
# Callbacks
# ------------------
print( "\n", "-"*70, "\n\n", "\tpost_script.py" )
Import("env", "projenv")

firmware_manager.post_extra_script_main(env, projenv)

print( "\n", "-"*70, "\n" )

# Dump global construction environment (for debug purpose)
#with open("dump_env.ini"    ,"w",encoding="utf-8") as file: file.write( str( env.Dump ) )
#with open("dump_projenv.ini","w",encoding="utf-8") as file: file.write( str( projenv.Dump) )