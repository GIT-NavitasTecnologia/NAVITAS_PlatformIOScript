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