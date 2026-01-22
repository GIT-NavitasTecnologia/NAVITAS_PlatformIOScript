'''
    PlatformIO Advanced Script for NavitasTecnologia
    See: https://docs.platformio.org/en/latest/scripting/actions.html
'''
# pylint: disable=broad-except
# ------------------
# Importing Modules
# ------------------
import subprocess

def show_git_info():
    ''' Print Repository Information '''
    print("Git information")
    print("\tProject     =", get_git_proj_name() )
    print("\tVersion     =", get_git_proj_version() )
    print("\tCommit      =", get_git_commit()  )
    print("\tBranch      =", get_git_branch()  )

def get_branch_has_commits():
    ''' Check if current branch has commits '''
    try:
        looking_for = 'No commits yet'
        cmd = " git status -u no --no-renames --ignored no"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if looking_for in out:
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
    if get_branch_has_commits():
        try:
            tagcmd = "git tag -l"
            values = subprocess.check_output(tagcmd, shell=True).decode().strip()
            if len(values) > 1:
                tagcmd = "git describe --tags --abbrev=0"
                version = subprocess.check_output(tagcmd, shell=True).decode().strip()
        except Exception:
            pass
    return version

def get_git_commit() -> str:
    ''' Get latest commit short from Git '''
    commit = ''
    if get_branch_has_commits():
        try:
            revcmd = "git log --pretty=format:'%h' -n 1"
            commit = subprocess.check_output(revcmd, shell=True).decode().strip().replace("'","")
        except Exception:
            pass
    return commit

def get_git_branch() -> str:
    ''' Get branch name from Git '''
    branch = ''
    if get_branch_has_commits():
        try:
            branchcmd = "git rev-parse --abbrev-ref HEAD"
            branch = subprocess.check_output(branchcmd, shell=True).decode().strip()
        except Exception:
            pass
    return branch

def get_git_origin() -> str:
    ''' Get git origin url '''
    origin = ''
    if get_branch_has_commits():
        try:
            cmd = "git config --get remote.origin.url"
            origin = subprocess.check_output(cmd, shell=True).decode().strip()
        except Exception:
            pass
    return origin

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
