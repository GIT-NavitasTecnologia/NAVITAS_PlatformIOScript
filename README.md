This is a [PlatformIO Advanced-Script](https://docs.platformio.org/en/latest/scripting/actions.html "PlatformIO Advanced-Script") developed by Navitas Tecnologia, aimed to simplify common firmware problems, such as versioning.

**Table of Contents**

[TOC]

# Features

- Building auto generates a release .zip file with everything needed to manually program your board (Currently tested only with ESP32 and ESP8266);
- Firmware info built-in macros available to `src/` files;
- Firmware version increases once every build, but only once per commit, and only if there have been changes to code;

# How to use

## [VSCode PlatfomIO](https://docs.platformio.org/en/latest/integration/ide/vscode.html "VSCode PlatfomIO") project sub-module

1. Create your PlatformIO project;
1. Open the PlatformIO project folder with `git bash`;
1. Add this submodule to path: `scripts/versioning`:
`git submodule add https://github.com/GIT-NavitasTecnologia/NAVITAS_PlatformIOScript.git scripts/versioning`
1. Open your `platformio.ini` file and add the following lines:
```[ini]
extra_scripts =
	post:scripts/versioning/post_extra_script.py
	pre:scripts/versioning/pre_extra_script.py
```
1. Do **not** add these files to `.gitignore`:
 - `scripts/firmwareInfo.json`
 - `scripts/backup_firmwareInfo.json`

## Built-in Macros
### `NAVITAS_PROJECT_VERSION`
String containing the full firmware name, with information such as version number, board and last commit SHA1;
 - Example: `"2.6.7-esp32cam-72b2097"`

### `NAVITAS_PROJECT_VERSION_NUMBER`
Firmware version as a number.
 - Example: `267`

### `NAVITAS_PROJECT_BOARD_NAME`
String containing the board name.
 - Example: `"esp32cam"`

### `NAVITAS_PROJECT_COMMIT`
String containing the last commit SHA1;
 - Example: `"72b2097"`
 
 ### `NAVITAS_PROJECT_GMT_DATE`
String containing the date and time (GMT) information of the firmware build;
 - Example: `"19-Aug-2022-18:19"`

### `NAVITAS_PROJECT_EPOCH`
Unix timestamp relative to the time of the firmware build; 

### `NAVITAS_PROJECT_BOARD_x`
`x` in this case will be replace with actual board name, all capitalized.
Example:
```cpp
#if   defined(NAVITAS_PROJECT_BOARD_ESP32CAM)
#warning "Developing for ESP32CAM"

#elif defined(NAVITAS_PROJECT_BOARD_WT32_ETH01)
#warning "Developing for WT32-ETH01"

#else
#error "Board not yet compatible!"
#endif
```

 ### Example of usage
```cpp
printf("Version        = %s\r\n",NAVITAS_PROJECT_VERSION            );
printf("Version Number = %d\r\n",NAVITAS_PROJECT_VERSION_NUMBER     );
printf("Board Name     = %s\r\n",NAVITAS_PROJECT_BOARD_NAME         );
printf("Commit SHA1    = %s\r\n",NAVITAS_PROJECT_COMMIT             );
printf("Build GMT Date = %s\r\n",NAVITAS_PROJECT_GMT_DATE           );
printf("Build Epoch    = %u\r\n",NAVITAS_PROJECT_EPOCH              );
	```

## Release zip
After building your application with vscode, the `zip` file will be available inside the folder `.pio/release/`