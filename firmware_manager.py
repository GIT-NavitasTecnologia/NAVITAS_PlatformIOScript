'''
    PlatformIO Advanced Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=broad-except
# ------------------
# Importing Modules
# ------------------
import os
import json
import datetime
import shutil
from hashlib import md5, sha256
import zipfile
import time
from pathlib import Path
import pio_tools
import git_tools

# ------------------
# Constants
# ------------------
CUR_FMW_INFO                 = "scripts/firmwareInfo.json"
OLD_FMW_INFO                 = "scripts/backup_firmwareInfo.json"
THIS_PATH                    = Path( os.path.realpath(__file__) ).parent
FIRMWARE_USB_UPDATE_ZIP_MAIN = os.path.realpath( THIS_PATH / "../usbUpdateInfo.zip" )
FIRMWARE_USB_UPDATE_ZIP_ALT  = os.path.realpath( THIS_PATH /  "./usbUpdateInfo.zip" )
RELEASE_OUTPUT_FOLDER        = ".pio/release/"
REM_PIO_UPLOAD_START         = "Rem begin pio upload command\n"
REM_PIO_UPLOAD_END           = "\nRem end pio upload command"

# ------------------
# Functions
# ------------------

def get_upload_script(env, p_path_to_copy_n_paste=''):
    ''' Prepare upload batch script '''
    out_str = r'''@echo off
Rem Terminal Setup
color F0
cls
title "Uploading Firmware"

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
	CALL :fun_echo_red "Folder \"bin\" not found!"
	pause
	exit
)

'''
    upload_cmd_str = pio_tools.get_from_env_recursive(env, env['UPLOADCMD'], p_path_to_copy_n_paste)
    upload_cmd_str = upload_cmd_str.replace('python.exe', r'%PYTHON_DIR%')
    upload_cmd_str = upload_cmd_str.replace('--port ', '')
    upload_cmd_str = upload_cmd_str.replace('$UPLOAD_PORT', '')
    upload_cmd_str = upload_cmd_str.replace('  ', ' ')

    out_str += REM_PIO_UPLOAD_START
    out_str += upload_cmd_str.strip()
    out_str += REM_PIO_UPLOAD_END

    fmw_path = pio_tools.get_default_firmware_path(env)
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



def filter_list_of_files_pending_commit(all_changed_files = None):
    ''' Filter invalid files from list '''
    if all_changed_files is None:
        all_changed_files = git_tools.get_files_pending_commit()
    filtered_changed_files = [x for x in all_changed_files if is_valid_changed_file(x)]
    return filtered_changed_files

def is_valid_changed_file( file_name:str ) -> bool:
    ''' Check if file changed in repository shall not be ignored '''
    if ".bin" in file_name:
        return False
    if CUR_FMW_INFO in file_name:
        return True
    if OLD_FMW_INFO in file_name:
        return False
    #if RELEASE_OUTPUT_FOLDER in fileName: return False
    #if FIRMWARE_USB_UPDATE_ZIP in fileName: return False
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

def delete_inside_folder( folder_name:str, list_to_ignore=None ):
    ''' Delete every file inside folder, except the files in list '''
    if list_to_ignore is None:
        list_to_ignore = []
    for filename in os.listdir( folder_name ):
        ignore_file = False
        for file_i in list_to_ignore:
            if file_i.lower().strip() == filename.lower().strip():
                ignore_file = True
                break
        if ignore_file:
            continue

        file_path = os.path.join( folder_name , filename )
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as excep:
            print(f'Failed to delete {file_path}. Reason: {excep}')

def save_new_json_version( new_info: dict ) -> dict:
    ''' Update firmware information to JSON '''
    if os.path.exists( OLD_FMW_INFO ):
        os.remove( OLD_FMW_INFO )
    if os.path.exists( CUR_FMW_INFO ):
        os.rename( CUR_FMW_INFO, OLD_FMW_INFO )
    with open( CUR_FMW_INFO , 'w', encoding='UTF-8') as file:
        file.write( json.dumps(new_info, indent=4, sort_keys=False) )
    return new_info

def get_custom_fmw_tag( info: dict ) -> str:
    ''' Get full name of firmware version '''
    fmw_version_name = info['Version']
    if( ('PIOENV' in info) and (len(info['PIOENV'].strip()) > 1) ):
        fmw_version_name += "-" + info['PIOENV'].strip()
    if len( info['Description'].strip() ) > 1:
        fmw_version_name += "-" + info['Description']
    if len( info['GIT_Commit'].strip() ) > 1:
        fmw_version_name += "-" + info['GIT_Commit'].replace("'","")
    return fmw_version_name

def get_fmw_number_version( info: dict ) -> int:
    ''' Get number equivalent to firmware version '''
    out = info['Version'].strip().split('.')
    out = sum(int(out[i]) * pow(10,len(out)-i-1) for i in range(len(out)))
    return out

def get_fmw_board_name( info: dict ) -> str:
    ''' Get board name '''
    return info['Board'].strip().replace("-","_")

def get_path_to_platform() -> str:
    ''' Get platform.io user's location '''
    path_to_platformio = os.path.join(
    os.getenv('PLATFORMIO_CORE_DIR', os.path.join(os.path.expanduser('~'), '.platformio')))
    return str(path_to_platformio).strip()

def get_elf_file(env):
    ''' Get firmware.elf file path '''
    try:
        build_dir = Path( pio_tools.get_from_env_recursive(env, "$BUILD_DIR") )
        elf_file = build_dir / "firmware.elf"
        if os.path.isfile( elf_file ):
            return os.path.realpath( elf_file )
    except Exception as e:
        print(e)
    return None

def get_list_of_files_to_copy(env):
    ''' Get list of binary and essential files related to the firmware '''
    output = [CUR_FMW_INFO]
    if 'OBJCOPY' in env:
        output.append( env['OBJCOPY'] )
    # Include .elf file
    elf_file = get_elf_file(env)
    if elf_file is not None and elf_file not in output:
        output.append( elf_file )
    return output

def move_bin_files( env, p_out_folder ):
    ''' Move binary files related to the firmware to a release folder '''

    # First extract the zip folder
    zip_path = FIRMWARE_USB_UPDATE_ZIP_ALT
    if os.path.exists(FIRMWARE_USB_UPDATE_ZIP_MAIN):
        zip_path = FIRMWARE_USB_UPDATE_ZIP_MAIN
    with zipfile.ZipFile( zip_path, 'r' ) as zip_ref:
        zip_ref.extractall( p_out_folder )

    # Create a binary folder
    binary_folder = p_out_folder + "bin/"
    if not os.path.exists(binary_folder):
        os.makedirs( binary_folder )

    # Copy every file to the binary folder
    for dir_i in get_list_of_files_to_copy(env):
        if isinstance(dir_i, str):
            if not os.path.exists(dir_i):
                continue
            if os.path.isfile(dir_i):
                shutil.copy2(dir_i, binary_folder)
            else:
                shutil.copytree(dir_i, binary_folder)
        else:
            for file_j in dir_i:
                if not os.path.exists(dir_i):
                    continue
                if os.path.isfile(file_j):
                    shutil.copy2(file_j, binary_folder)
                else:
                    shutil.copytree(file_j, binary_folder)

    # Prepare Upload Script
    script_str = get_upload_script(env, binary_folder)
    script_str = fix_zip_file(env, script_str, p_out_folder)
    with open(p_out_folder + "fmw_upload.bat", 'w', encoding='UTF-8') as dir_i:
        dir_i.write(script_str)

def fix_zip_file_esptool(env, binary_folder, new_pio_upload):
    ''' Fix zip file when using esptool '''
    # Move whole 'tool-esptoolpy' folder to zip
    uploader_path = env['UPLOADER']
    if "tool-esptoolpy" in uploader_path.lower():
        folder_path = uploader_path[:uploader_path.rindex('\\')]
        shutil.copytree(folder_path, binary_folder + "tool-esptoolpy\\")
        os.remove( binary_folder + "esptool.py" )
        new_pio_upload = new_pio_upload.replace('esptool.py', '"tool-esptoolpy\\esptool.py"')
    return new_pio_upload

def fix_zip_file_openocd(env, binary_folder, new_pio_upload, p_out_folder):
    ''' Fix zip file when using openocd '''
    # Tested with 'stlink' in env['UPLOAD_PROTOCOL'].lower()

    def _add_double_quote(cmd, opt1, opt2):
        opt1 = f" {opt1} "
        opt2 = f" {opt2} "

        ref = cmd
        while True:
            has_opt1 = opt1 in ref
            has_opt2 = opt2 in ref
            if( has_opt1 or has_opt2 ):
                # Find where param starts
                index_start = -1
                if has_opt1:
                    index_start = ref.index(opt1) + len(opt1)
                else:
                    index_start = ref.index(opt2) + len(opt2)
                # Find where param ends
                index_end = -1
                aux = ''
                if not ' -' in ref[index_start:]:
                    aux = ref[ index_start : ]
                    ref = ''
                else:
                    index_end = index_start + ref[index_start:].index(' -')
                    aux = ref[ index_start : index_end ]
                    ref = ref[ index_end + 1: ]
                cmd = cmd.replace(
                    aux,
                    f'\"{aux}\"',
                    1
                )
            else:
                break
        return cmd

    env_paths     = env.get("ENV",'')["PATH"].split(';')
    uploader_path = env.get('UPLOADER','')
    for path_i in env_paths:
        if 'openocd' in path_i:
            uploader_path  = path_i
            folder_path    = uploader_path[ : uploader_path.rindex('\\') ]
            new_pio_upload = new_pio_upload.replace('openocd', '\"tool-openocd/bin/openocd\"',1)
            new_pio_upload = new_pio_upload.replace(folder_path, r'tool-openocd',1)
            shutil.copytree(folder_path, binary_folder + "tool-openocd\\")
            # Copy .elf too for STM32CubeProgrammer
            if 'PROGPATH' in env:
                elf_path = env.subst('$PROGPATH')
                if( os.path.isfile(elf_path) and '.elf' in elf_path ):
                    shutil.copy2(elf_path, p_out_folder)
                    # Use .elf instead of .bin
                    new_pio_upload = new_pio_upload.replace('firmware.bin', '../firmware.elf')

            # Add double quotes to openocd --command param
            new_pio_upload   = _add_double_quote(new_pio_upload  , "-c", "--command")
            # Add double quotes to openocd --file param
            new_pio_upload   = _add_double_quote(new_pio_upload  , "-f", "--file"   )
            # Add double quotes to openocd --search param
            new_pio_upload   = _add_double_quote(new_pio_upload  , "-s", "--search" )
            break
    return new_pio_upload

def fix_zip_file(env, script_str, p_out_folder) -> str:
    ''' Fix zip file for current platform and board '''
    binary_folder = p_out_folder + "bin/"

    pio_upload_start_index = script_str.index(REM_PIO_UPLOAD_START) + len(REM_PIO_UPLOAD_START)
    pio_upload_end_index   = script_str.index(REM_PIO_UPLOAD_END  )
    pio_upload             = script_str[pio_upload_start_index : pio_upload_end_index]
    new_pio_upload         = pio_upload

    if 'esptool' in env['UPLOAD_PROTOCOL'].lower():
        new_pio_upload = fix_zip_file_esptool(env, binary_folder, new_pio_upload)
    elif 'openocd' == env['UPLOADER'].lower():
        new_pio_upload = fix_zip_file_openocd(env, binary_folder, new_pio_upload, p_out_folder)

    script_str = script_str.replace(pio_upload, new_pio_upload, 1)
    return script_str

def get_fmw_info( p_file_name, env )->dict:
    ''' Load Firmware Info JSON File '''
    data_out = json.loads(
'''
{
    "Version": "1.0.0",
    "Description": "",
    "Board": "",
    "PIOENV": "",
    "Date": "",
    "GIT_Project": "",
    "GIT_Version": "",
    "GIT_Branch": "",
    "GIT_Commit": "",
    "GIT_Origin": ""
}
''')
    data_out['Date'] = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%b-%Y-%H:%M")
    data_out['GIT_Version'] = git_tools.get_git_proj_version()
    if os.path.exists( p_file_name ):
        with open( p_file_name, 'r', encoding='UTF-8' ) as file:
            data_out = json.loads( file.read() )
    # Override
    data_out['Board']       = env.get('BOARD',"")
    data_out['PIOENV']      = env.get('PIOENV',"").replace("-","_").upper()
    data_out['GIT_Project'] = git_tools.get_git_proj_name()
    data_out['GIT_Branch']  = git_tools.get_git_branch()
    data_out['GIT_Commit']  = git_tools.get_git_commit()
    data_out['GIT_Origin']  = git_tools.get_git_origin()

    # Create or refresh json
    with open( CUR_FMW_INFO , 'w', encoding='UTF-8') as file:
        file.write( json.dumps(data_out, indent=4, sort_keys=False) )
    # Create backup if it does not exist
    if not os.path.exists( OLD_FMW_INFO ):
        with open( OLD_FMW_INFO , 'w', encoding='UTF-8') as file:
            file.write( json.dumps(data_out, indent=4, sort_keys=False) )
    return data_out

def get_new_fmw_info( p_old_info, env ) -> dict:
    ''' Increase version from old firmware information '''
    data_out    = p_old_info
    old_version = p_old_info['Version'].strip().split('.')
    temp = [ int(old_version[0]), int(old_version[1]), int(old_version[2])+1 ]
    for i in range(2,0,-1):
        if temp[i] > 9:
            temp[i] = 0
            temp[i-1] += 1
    data_out['Version'] = f'{temp[0]}.{temp[1]}.{temp[2]}'
    data_out['Date'] = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%b-%Y-%H:%M")
    data_out['GIT_Project'] = git_tools.get_git_proj_name()
    data_out['GIT_Version'] = git_tools.get_git_proj_version()
    data_out['GIT_Branch']  = git_tools.get_git_branch()
    data_out['GIT_Commit']  = git_tools.get_git_commit()
    data_out['GIT_Origin']  = git_tools.get_git_origin()
    data_out['Board']       = env.get('BOARD',"")
    data_out['PIOENV']      = env.get('PIOENV',"").replace("-","_").upper()
    return data_out


def pre_build_action(source, target, env):
    # pylint: disable=unused-argument
    ''' Pre Build PlatformIO Action '''
    print("\tUpdate firmware info? [y/n]")
    if not input().lower().strip().startswith('y'):
        return
    old_info = get_fmw_info( CUR_FMW_INFO, env )
    new_info = old_info

    # Handle Pending Changes
    files_pending_commit = git_tools.get_files_pending_commit()
    filtered_list_pending_commit = filter_list_of_files_pending_commit( files_pending_commit )
    if len(filtered_list_pending_commit) > 0:
        if OLD_FMW_INFO in files_pending_commit:
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

    board_name = get_fmw_board_name(new_info)

    # Round epoch time
    build_time = int(time.time())
    #build_time -= build_time % (30 * 60)

    macro_values = {
        'NAVITAS_PROJECT_VERSION':                     f'\"{get_custom_fmw_tag(new_info)}\"',
        'NAVITAS_PROJECT_VERSION_NUMBER':              f'{get_fmw_number_version(new_info)}',
        'NAVITAS_PROJECT_GMT_DATE':                    f"\"{new_info['Date']}\"",
        'NAVITAS_PROJECT_EPOCH':                       f'{build_time}UL',
        'NAVITAS_PROJECT_COMMIT':                      f"\"{new_info['GIT_Commit']}\"",
        'NAVITAS_PROJECT_BOARD_NAME':                  f'\"{board_name}\"',
        f'NAVITAS_PROJECT_BOARD_{board_name.upper()}': True,
    }

    #for key,val in macro_values.items(): env['SRC_BUILD_FLAGS'].append(f"'-D {key} = {val}'")
    lib_folder = Path( os.path.realpath("lib/firmware_info/") )
    os.makedirs(lib_folder.absolute(), exist_ok=True)
    lib_c_txt = '''#include "firmware_info.h"


'''
    lib_h_txt = '''///
/// @file firmware_info.h
/// @author wrgallo@hotmail.com
/// @brief Firmware Info
///
#pragma once

#ifdef __cplusplus 
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

'''
    max_len = max(len(i) for i in macro_values) + 1
    for key,val in macro_values.items():
        #lib_h_txt += f'#define {key:<{max_len}} {val}\n'
        key = f'k{key}'
        if isinstance(val, str) and val.startswith('\"'):
            key += '[]'
            lib_h_txt += f'extern const char     {key};\n'
            lib_c_txt += f'const char     {key:<{max_len}} = {val};\n'
        elif isinstance(val, bool):
            lib_h_txt += f'extern const bool     {key};\n'
            lib_c_txt += f'const bool     {key:<{max_len}} = {int(val)};\n'
        else:
            lib_h_txt += f'extern const uint32_t {key};\n'
            lib_c_txt += f'const uint32_t {key:<{max_len}} = {val};\n'
    lib_h_txt += '''

#ifdef __cplusplus
}
#endif
    '''
    with open(lib_folder / "firmware_info.h", 'w', encoding='utf-8') as file:
        file.write(lib_h_txt)
    with open(lib_folder / "firmware_info.c", 'w', encoding='utf-8') as file:
        file.write(lib_c_txt)

def post_build_action(source, target, env):
    # pylint: disable=unused-argument
    ''' PlatformIO PostBuildProgram Callback '''
    print( "\n", "-"*70, "\n\n", "\tPost Build Action Script")

    print("\t>> Getting Firmware Info")
    new_info = get_fmw_info( CUR_FMW_INFO, env )
    elf_file = get_elf_file(env)
    if elf_file is not None:
        with open(elf_file, 'rb') as file:
            elf_data = file.read()
            elf_sha256 = sha256(elf_data).hexdigest()
            new_info['elf_sha256'] = elf_sha256
            save_new_json_version( new_info )

    print("\t>> Moving Files to Release Folder")
    output_folder = RELEASE_OUTPUT_FOLDER + "v" + get_custom_fmw_tag( new_info ) + "/"
    move_bin_files( env, output_folder )

    print("\t>> Zipping everything together")
    zip_name   = new_info['GIT_Project'] + "_v" + get_custom_fmw_tag( new_info ) + '.zip'
    zip_folder = RELEASE_OUTPUT_FOLDER + env.get('PIOENV',"unknown") + "/"
    os.makedirs( zip_folder, exist_ok=True )
    zipdir( zip_folder + zip_name , output_folder )
    shutil.rmtree( output_folder )
    delete_inside_folder( zip_folder, [zip_name] )

    print( "\n", "-"*70, "\n" )

def pre_extra_script_main(env):
    ''' Script to be executed in pre_extra_script '''
    if env.GetOption('clean'):
        return
    if pio_tools.has_cmd_line_target(["idedata", "debug"]):
        return
    #env.AddPreAction("buildprog", pre_build_action)
    pre_build_action(None, None, env)

def post_extra_script_main(env, projenv):
    # pylint: disable=unused-argument
    ''' Script to be executed in post_extra_script '''
    #env.AddPreAction("buildprog", pre_build_action)
    env.AddPostAction("buildprog", post_build_action)
    env.AddPostAction("upload", post_build_action)

if __name__ == "__main__":
    git_tools.show_git_info()
    input("Enter to continue...")
