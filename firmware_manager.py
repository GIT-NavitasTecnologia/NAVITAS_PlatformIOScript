'''
    PlatformIO Advanced Script for NavitasTecnologia
'''
# pylint: disable=superfluous-parens,broad-except
# ------------------
# Importing Modules
# ------------------
import os
import json
import datetime
import shutil
from hashlib import md5
import zipfile
import subprocess
import time

# ------------------
# Constants
# ------------------
FIRMWARE_FILE_NAME      = "scripts/firmwareInfo.json"
FIRMWARE_OLD_FILE_NAME  = "scripts/backup_firmwareInfo.json"
FIRMWARE_USB_UPDATE_ZIP = os.path.realpath(__file__).rsplit('\\',1)[0] + "\\usbUpdateInfo.zip" # Same folder
RELEASE_OUTPUT_FOLDER   = ".pio/release/"

# ------------------
# Functions
# ------------------

def get_default_firmware_path(env):
    ''' Find firmware file name '''
    fmw_path = get_from_env_recursive(env, '$PROG_PATH')
    bin_path = fmw_path.replace( fmw_path.split('.')[-1] , 'bin' )
    if( os.path.isfile( bin_path ) ):
        fmw_path = bin_path
    return fmw_path

def get_from_env_recursive(env, p_value, p_path_to_copy_n_paste = ''):
    ''' Find p_value from env '''
    if( isinstance(p_value, list) ):
        # List of values
        out_value = ""
        for p_value_i in p_value:
            p_value_i = p_value_i.replace('\'', '').replace('\"','').strip()
            out_value += get_from_env_recursive(env, p_value_i, p_path_to_copy_n_paste)
            if( p_value_i != p_value[-1] ):
                out_value += " "
        return out_value

    elif( isinstance(p_value, str) and p_value.count(' ')>1 ):
        # Space separated values
        tags = [ xi.replace('\'', '').replace('\"','').strip()
            for xi in p_value.split()
        ]
        tags_parsed = [get_from_env_recursive(env, t, p_path_to_copy_n_paste) for t in tags]
        parsed = p_value
        for i,tag_i in enumerate( p_value.split() ):
            parsed = parsed.replace(tag_i, tags_parsed[i])
        return parsed

    elif(str(p_value).count('$') > 1):
        # String with multiple tags
        tags = [ xi.replace('\\','').strip()
            for xi in p_value.split('$')
            if xi not in ['', '"', "'"]
        ]
        tags_parsed = [get_from_env_recursive(env, '$' + t, p_path_to_copy_n_paste) for t in tags]
        parsed      = p_value
        for i,tag_i in enumerate( tags ):
            parsed = parsed.replace(f'${tag_i}', tags_parsed[i])
        return parsed

    elif( ('${' in str(p_value) ) and ('}' in str(p_value) ) ):
        # Value is a function to be called
        fun_str   = p_value[2:].split('(')[0]
        param_str = p_value[p_value.index('(')+1:].split(')')[0].strip()
        if(param_str == '__env__'):
            return str(env[fun_str](env))
        return str(env[fun_str]())

    elif(str(p_value).count('$') == 1):
        # Value is another key
        key = p_value[1:].replace('\'', '').replace('\"','').strip()
        if( key in ['UPLOAD_PORT'] ):
            return '' # Ignore these values
        elif( key in env ):
            return get_from_env_recursive(env, env[key], p_path_to_copy_n_paste)
        else:
            if( key.upper() == "SOURCE" ):
                fmw_path = get_default_firmware_path(env)
                return get_from_env_recursive(env, fmw_path, p_path_to_copy_n_paste)
            if( key.upper() != "UPLOAD_PORT" ):
                print( f'"{key}" not found!' )
            return f"${key}"

    # Path to file
    if( os.path.isfile( str(p_value) ) ):
        # Copy File to folder
        if( ( p_path_to_copy_n_paste != '' ) and
            ( not "python" in p_value.lower() ) ):
            if( not os.path.exists(p_path_to_copy_n_paste) ):
                os.makedirs( p_path_to_copy_n_paste )
            shutil.copy2( p_value.replace("\\","/") , p_path_to_copy_n_paste )
        # Rename file
        p_value = p_value.split('\\')[-1]

    # Value
    return str(p_value)


def get_upload_script(env, p_path_to_copy_n_paste=''):
    ''' Prepare upload batch script '''
    out_str = r'''@echo off
Rem Terminal Setup
color F0
cls
title "Programando via USB"

Rem Global Variables
set POWERSHELL_DIR="%Windir%\System32\WindowsPowerShell\v1.0\Powershell.exe"

Rem Finding Python
set PIO_PYTHON_DIR="%HOMEDRIVE%%HOMEPATH%\.platformio\penv\Scripts\python.exe"
set PYTHON_DIR=%PIO_PYTHON_DIR%
if not exist %PIO_PYTHON_DIR% (set PYTHON_DIR="python")

Rem Uploading Firmware
if exist "bin" (
	cd "bin"
) else (
	CALL :fun_echo_red "Pasta \"bin\" nao encontrada!"
	pause
	exit
)

'''

    upload_cmd_str = get_from_env_recursive(env, '$UPLOADCMD', p_path_to_copy_n_paste)
    upload_cmd_str = upload_cmd_str.replace('python.exe', r'%PYTHON_DIR%')
    upload_cmd_str = upload_cmd_str.replace('--port ', '')
    upload_cmd_str = upload_cmd_str.replace('$UPLOAD_PORT', '')
    upload_cmd_str = upload_cmd_str.replace('  ', ' ')
    out_str += upload_cmd_str.strip()

    fmw_path = get_default_firmware_path(env)
    md5_value = get_firmware_md5( fmw_path )
    with open( p_path_to_copy_n_paste + "firmware.md5", "w", encoding='UTF-8') as file:
        file.write( md5_value )

    out_str += r'''

Rem end of upload script
echo.
pause

Rem Function Print in Red
EXIT /B %ERRORLEVEL%
:fun_echo_red
	echo.
	if exist %POWERSHELL_DIR% (
		%POWERSHELL_DIR% write-host -foregroundcolor Red %1
	) else (
		echo %1
	)
	echo.
EXIT /B 0
'''
    return out_str

def show_git_info():
    ''' Print Repository Information '''
    print("Git information")
    print("\tProject     =", get_git_proj_name() )
    print("\tVersion     =", get_git_proj_version() )
    print("\tCommit      =", get_git_commit()  )
    print("\tBranch      =", get_git_branch()  )
    return

def get_branch_has_commits():
    ''' Check if current branch has commits '''
    try:
        looking_for = 'No commits yet'
        cmd = " git status -u no --no-renames --ignored no"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if( looking_for in out ):
            return 0
        return 1
    except Exception:
        pass
    return 0

def get_git_proj_name() -> str:
    ''' Get Git project name '''
    project = ''
    try:
        projcmd = "git rev-parse --show-toplevel"
        project = subprocess.check_output(projcmd, shell=True).decode().strip()
        project = project.split("/")
        project = project[-1]
    except Exception:
        pass
    return project

def get_git_proj_version() -> str:
    ''' Get 0.0.0 version from latest Git tag '''
    version = ''
    if( get_branch_has_commits() ):
        try:
            tagcmd = "git tag -l"
            values = subprocess.check_output(tagcmd, shell=True).decode().strip()
            if( len(values) > 1 ):
                tagcmd = "git describe --tags --abbrev=0"
                version = subprocess.check_output(tagcmd, shell=True).decode().strip()
        except Exception:
            pass
    return version

def get_git_commit() -> str:
    ''' Get latest commit short from Git '''
    commit = ''
    if( get_branch_has_commits() ):
        try:
            revcmd = "git log --pretty=format:'%h' -n 1"
            commit = subprocess.check_output(revcmd, shell=True).decode().strip().replace("'","")
        except Exception:
            pass
    return commit

def get_git_branch() -> str:
    ''' Get branch name from Git '''
    branch = ''
    if( get_branch_has_commits() ):
        try:
            branchcmd = "git rev-parse --abbrev-ref HEAD"
            branch = subprocess.check_output(branchcmd, shell=True).decode().strip()
        except Exception:
            pass
    return branch

def get_files_pending_commit():
    ''' Get list of files pending commit'''
    status = ''
    try:
        statuscmd = "git ls-files -m --others --exclude-standard"
        status = subprocess.check_output(statuscmd, shell=True).decode().strip()
    except Exception:
        pass
    all_changed_files = status.splitlines()
    return all_changed_files

def filter_list_of_files_pending_commit(all_changed_files = None):
    ''' Filter invalid files from list '''
    if(all_changed_files is None):
        all_changed_files = get_files_pending_commit()
    filtered_changed_files = [x for x in all_changed_files if is_valid_changed_file(x)]
    return filtered_changed_files

def is_valid_changed_file( file_name:str ) -> bool:
    ''' Check if file changed in repository shall not be ignored '''
    if( ".bin" in file_name ):
        return False
    if( FIRMWARE_FILE_NAME in file_name ):
        return True
    if( FIRMWARE_OLD_FILE_NAME in file_name ):
        return False
    #if( RELEASE_OUTPUT_FOLDER in fileName ): return False
    #if( FIRMWARE_USB_UPDATE_ZIP in fileName ): return False
    return True

def get_firmware_md5( p_file_path ):
    ''' Calculate firmware.bin MD5 checksum '''
    content = open(p_file_path, "rb").read()
    md5_hash = md5()
    md5_hash.update(content)
    digest = md5_hash.hexdigest()
    return str(digest).capitalize()

def zipdir( p_zip_name:str , p_folder_path:str ):
    ''' Zip a folder '''
    with zipfile.ZipFile( p_zip_name , 'w', zipfile.ZIP_DEFLATED ) as ziph:
        for root, _, files in os.walk( p_folder_path ):
            for file in files:
                file_path = os.path.join(root, file)
                ziph.write( file_path , file_path[len(p_folder_path):] )
    return #

def delete_inside_folder( folder_name:str, list_to_ignore=None ):
    ''' Delete every file inside folder, except the files in list '''
    if( list_to_ignore is None ):
        list_to_ignore = []
    for filename in os.listdir( folder_name ):
        ignore_file = False
        for file_i in list_to_ignore:
            if( file_i in filename ):
                ignore_file = True
                break
        if( ignore_file ):
            continue

        file_path = os.path.join( folder_name , filename )
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as excep:
            print(f'Failed to delete {file_path}. Reason: {excep}')
    return #

def save_new_json_version( new_info: dict ) -> dict:
    ''' Update firmware information to JSON '''
    if( os.path.exists( FIRMWARE_OLD_FILE_NAME ) ):
        os.remove( FIRMWARE_OLD_FILE_NAME )
    if( os.path.exists( FIRMWARE_FILE_NAME ) ):
        os.rename( FIRMWARE_FILE_NAME, FIRMWARE_OLD_FILE_NAME )
    with open( FIRMWARE_FILE_NAME , 'w', encoding='UTF-8') as file:
        file.write( json.dumps(new_info, indent=4, sort_keys=False) )
    return new_info

def get_custom_fmw_tag( info: dict ) -> str:
    ''' Get full name of firmware version '''
    fmw_version_name = info['Version']
    if( ('Board' in info) and (len(info['Board'].strip()) > 1) ):
        if( ('esp32dev' != info['Board'].strip() ) and
            ('esp-wrover-kit' != info['Board'].strip() ) ):
            fmw_version_name += "-" + info['Board'].strip()
    if( len( info['Description'].strip() ) > 1 ):
        fmw_version_name += "-" + info['Description']
    if( len( info['GIT_Commit'].strip() ) > 1 ):
        fmw_version_name += "-" + info['GIT_Commit'].replace("'","")
    return fmw_version_name

def get_fmw_number_version( info: dict ) -> int:
    ''' Get number equivalent to firmware version '''
    out = info['Version'].strip().split('.')
    out = sum([int(out[i]) * pow(10,len(out)-i-1) for i in range(len(out))])
    return out

def get_fmw_board_name( info: dict ) -> str:
    ''' Get board name '''
    return info['Board'].strip().replace("-","_")

def get_path_to_platform() -> str:
    ''' Get platform.io user's location '''
    path_to_platformio = os.path.join(
    os.getenv('PLATFORMIO_CORE_DIR', os.path.join(os.path.expanduser('~'), '.platformio')))
    return str(path_to_platformio).strip()

def get_list_of_files_to_copy(env):
    ''' Get list of binary and essential files related to the firmware '''
    output = [FIRMWARE_FILE_NAME]
    if('OBJCOPY' in env):
        output.append( env['OBJCOPY'] )
    return output

def move_bin_files( env, p_out_folder ):
    ''' Move binary files related to the firmware to a release folder '''
    with zipfile.ZipFile( FIRMWARE_USB_UPDATE_ZIP, 'r' ) as zip_ref:
        zip_ref.extractall( p_out_folder )
    binary_folder = p_out_folder + "bin/"
    if( not os.path.exists(binary_folder) ):
        os.makedirs( binary_folder )
    for dir_i in get_list_of_files_to_copy(env):
        if( isinstance(dir_i, str) ):
            if( not os.path.exists(dir_i) ):
                continue
            if( os.path.isfile(dir_i) ):
                shutil.copy2(dir_i, binary_folder)
            else:
                shutil.copytree(dir_i, binary_folder)
        else:
            for file_j in dir_i:
                if( not os.path.exists(dir_i) ):
                    continue
                if( os.path.isfile(file_j) ):
                    shutil.copy2(file_j, binary_folder)
                else:
                    shutil.copytree(file_j, binary_folder)
    # Prepare Upload Script
    script_str = get_upload_script(env, binary_folder)
    with open(p_out_folder + "uploadPorUSB.bat", 'w', encoding='UTF-8') as dir_i:
        dir_i.write(script_str)
    return #

def get_fmw_info( p_file_name, env )->dict:
    ''' Load Firmware Info JSON File '''
    data_out = json.loads(
'''
{
    "Version": "1.0.0",
    "Description": "",
    "Board": "",
    "Date": "",
    "GIT_Project": "",
    "GIT_Version": "",
    "GIT_Branch": "",
    "GIT_Commit": ""
}
''')
    data_out['Date'] = datetime.datetime.utcnow().strftime("%d-%b-%Y-%H:%M")
    data_out['GIT_Version'] = get_git_proj_version()
    if( os.path.exists( p_file_name ) ):
        data_out = json.loads( open( p_file_name , 'r', encoding='UTF-8' ).read() )
    # Override
    data_out['Board']       = env['BOARD']
    data_out['GIT_Project'] = get_git_proj_name()
    data_out['GIT_Branch']  = get_git_branch()
    data_out['GIT_Commit']  = get_git_commit()

    # Create or refresh json
    with open( FIRMWARE_FILE_NAME , 'w', encoding='UTF-8') as file:
        file.write( json.dumps(data_out, indent=4, sort_keys=False) )
    # Create backup if it does not exist
    if( not os.path.exists( FIRMWARE_OLD_FILE_NAME ) ):
        with open( FIRMWARE_OLD_FILE_NAME , 'w', encoding='UTF-8') as file:
            file.write( json.dumps(data_out, indent=4, sort_keys=False) )
    return data_out

def get_new_fmw_info( p_old_info, env ) -> dict:
    ''' Increase version from old firmware information '''
    data_out    = p_old_info
    old_version = p_old_info['Version'].strip().split('.')
    temp = [ int(old_version[0]), int(old_version[1]), int(old_version[2])+1 ]
    for i in range(2,0,-1):
        if( temp[i] > 9 ):
            temp[i] = 0
            temp[i-1] += 1
    data_out['Version'] = f'{temp[0]}.{temp[1]}.{temp[2]}'
    data_out['Date'] = datetime.datetime.utcnow().strftime("%d-%b-%Y-%H:%M")
    data_out['GIT_Project'] = get_git_proj_name()
    data_out['GIT_Version'] = get_git_proj_version()
    data_out['GIT_Branch']  = get_git_branch()
    data_out['GIT_Commit']  = get_git_commit()
    data_out['Board']       = env['BOARD']
    return data_out


def pre_build_action(source, target, env):
    # pylint: disable=unused-argument
    ''' Pre Build PlatformIO Action '''
    old_info = get_fmw_info( FIRMWARE_FILE_NAME, env )
    new_info = old_info
    # Handle Pending Changes
    files_pending_commit = get_files_pending_commit()
    filtered_list_pending_commit = filter_list_of_files_pending_commit( files_pending_commit )
    if( len(filtered_list_pending_commit) > 0 ):
        if( FIRMWARE_OLD_FILE_NAME in files_pending_commit ):
            print("\tFirmware info has already been updated!")
        else:
            print("\tPending changes to commit.\n\tFirmware info is going to be updated!")
            for i,file_i in enumerate( filtered_list_pending_commit ):
                print(f"\t\tChanged file[%02d]: {file_i}" % (i+1))
            new_info = get_new_fmw_info( old_info, env )
    else:
        print("\tNO pending changes to commit.\n\tFirmware info is NOT going to be updated!")
    save_new_json_version( new_info )
    print()
    print("\tFirmware Version          =", new_info['Version']      )
    print("\tFirmware Description      =", new_info['Description']  )
    print("\tFirmware Compilation Date =", new_info['Date']         )
    print("\tFirmware Version-Name     =", get_custom_fmw_tag(new_info) )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_VERSION = \"{get_custom_fmw_tag(new_info)}\"'"
    )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_VERSION_NUMBER = {get_fmw_number_version(new_info)}'"
    )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_BOARD = {get_fmw_board_name(new_info)}'"
    )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_GMT_DATE = \"{new_info['Date']}\"'"
    )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_EPOCH = {int(time.time())}U'"
    )
    env['SRC_BUILD_FLAGS'].append(
        f"'-D NAVITAS_PROJECT_COMMIT = \"{new_info['GIT_Commit']}\"'"
    )
    return

def post_build_action(source, target, env):
    # pylint: disable=unused-argument
    ''' PlatformIO PostBuildProgram Callback '''
    print( "\n", "-"*70, "\n\n", "\tPost Build Action Script")

    print("\t>> Getting Firmware Info")
    new_info = get_fmw_info( FIRMWARE_FILE_NAME, env )

    print("\t>> Moving Files to Release Folder")
    output_folder = RELEASE_OUTPUT_FOLDER + "v" + get_custom_fmw_tag( new_info ) + "/"
    move_bin_files( env, output_folder )

    print("\t>> Zipping everything together")
    zip_name = "v" + get_custom_fmw_tag( new_info ) + '.zip'
    zipdir( RELEASE_OUTPUT_FOLDER + zip_name , output_folder )
    shutil.rmtree( output_folder )
    delete_inside_folder( RELEASE_OUTPUT_FOLDER, [zip_name] )

    print( "\n", "-"*70, "\n" )
    return #

def pre_extra_script_main(env):
    ''' Script to be executed in pre_extra_script '''
    #env.AddPreAction( "buildProg", preBuildAction )
    pre_build_action(None, None, env)
    return #

def post_extra_script_main(env, projenv):
    # pylint: disable=unused-argument
    ''' Script to be executed in post_extra_script '''
    env.AddPostAction("buildprog", post_build_action)
    env.AddPostAction("upload", post_build_action)
    return #

if __name__ == "__main__":
    show_git_info()
