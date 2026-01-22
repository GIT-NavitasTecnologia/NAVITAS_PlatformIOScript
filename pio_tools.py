'''
    PlatformIO Advanced Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=broad-except
# ------------------
# Importing Modules
# ------------------
import os
import shutil

def get_default_firmware_path(env):
    ''' Find firmware file name '''
    fmw_path = get_from_env_recursive(env, '$PROG_PATH')
    bin_path = fmw_path.replace( fmw_path.split('.')[-1] , 'bin' )
    if os.path.isfile( bin_path ):
        fmw_path = bin_path
    return fmw_path

def get_from_env_recursive(env, p_value, p_path_to_copy_n_paste = ''):
    ''' Find p_value from env '''
    # TODO use env.get( p_value, p_value ), env.subst( p_value )

    if isinstance(p_value, list):
        # List of values
        out_value = ""
        for i, p_value_i in enumerate(p_value):
            p_value_i = p_value_i.replace('\'', '').replace('\"','').strip()
            out_value += get_from_env_recursive(env, p_value_i, p_path_to_copy_n_paste)
            if i != ( len(p_value) - 1 ):
                out_value += " "
        return out_value

    elif ( isinstance(p_value, str) and p_value.count(' ') > 1 ):
        # Space separated values
        tags = [
            xi.replace('\'', '').replace('\"','').strip()
            for xi in p_value.split()
        ]
        tags_parsed = [get_from_env_recursive(env, t, p_path_to_copy_n_paste) for t in tags]
        return ' '.join(tags_parsed)

    elif str(p_value).count('$') > 1:
        # String with multiple tags
        tags = [ xi.replace('\\','').strip()
            for xi in p_value.split('$')
            if xi not in ['', '"', "'"]
        ]
        tags_parsed = [get_from_env_recursive(env, '$' + t, p_path_to_copy_n_paste) for t in tags]
        parsed      = p_value
        #return ' '.join(tags_parsed)
        for i,tag_i in enumerate( tags ):
            parsed = parsed.replace(f'${tag_i}', tags_parsed[i], 1)
        return parsed

    elif( ('${' in str(p_value) ) and ('}' in str(p_value) ) ):
        # Value is a function to be called
        fun_str  = p_value[2:].split('(')[0]
        params   = p_value[p_value.index('(')+1:].split(')')[0].strip().split(',')
        if len(params) == 0:
            return str(env[fun_str]())
        if( len(params)==1 and ( params[0] == '__env__') ):
            return str(env[fun_str](env))
        return env.subst( p_value )

    elif str(p_value).count('$') == 1:
        #/ Value is another key
        add_bracets = ( (p_value[0] == '{') and (p_value[-1] == '}') )
        key         = p_value[ p_value.index('$') + 1: ].replace('\'', '').replace('\"','').strip()
        if add_bracets:
            key = key[:-1]
        out_param   = ''
        if key in ['UPLOAD_PORT']:
            # Ignore these values
            out_param = ''
        elif key in env:
            # Get value from env
            out_param = get_from_env_recursive(env, env[key], p_path_to_copy_n_paste)
        elif key.upper() == "SOURCE":
            # Get firmware file
            fmw_path = get_default_firmware_path(env)
            out_param = get_from_env_recursive(env, fmw_path, p_path_to_copy_n_paste)
        else:
            # Not found
            print( f'"{key}" not found!' )
            return f"${key}"
        return '{%s}' % out_param if add_bracets else out_param

    # Path to file
    if os.path.isfile( str(p_value) ):
        # Copy File to folder
        if( ( p_path_to_copy_n_paste != '' ) and
            ( not "python" in p_value.lower() ) ):
            if not os.path.exists(p_path_to_copy_n_paste):
                os.makedirs( p_path_to_copy_n_paste )
            shutil.copy2( p_value.replace("\\","/") , p_path_to_copy_n_paste )
        # Rename file
        p_value = p_value.split('\\')[-1]

    # Value
    return str(p_value)

def has_cmd_line_target( cmd, targets=None, dump_targets=False ):
    ''' Check if there is a command with that name in targets '''
    # Get default targets from SCons
    if targets is None:
        from SCons.Script import COMMAND_LINE_TARGETS #pylint: disable=W0611,E0401,C0415
        targets = COMMAND_LINE_TARGETS
    # Debug dump targets
    if dump_targets:
        with open("dump_targets.txt", "w", encoding="utf-8") as file:
            file.write( str(targets) )
    # Check for each item inside a list
    if isinstance(cmd, list):
        for cmd_i in cmd:
            if len([c for c in targets if cmd_i in c]) > 0:
                return True
        return False
    # Check for a single item
    return len([c for c in targets if cmd in c]) > 0
