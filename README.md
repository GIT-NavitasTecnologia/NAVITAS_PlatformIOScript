This is a [PlatformIO Advanced-Script](https://docs.platformio.org/en/latest/scripting/actions.html "PlatformIO Advanced-Script") developed by Navitas Tecnologia, aimed to simplify common firmware problems, such as versioning.

## Table of Contents
 - [Features](#Features)
 - [How to Use](#How_to_use)
  - [VSCode PlatformIO](#VSCode_PlatformIO)
  - [Built-in Macros](#Built_in_Macros)
    - [`NAVITAS_PROJECT_VERSION`](#NAVITAS_PROJECT_VERSION)
	- [`NAVITAS_PROJECT_VERSION_NUMBER`](#NAVITAS_PROJECT_VERSION_NUMBER)
	- [`NAVITAS_PROJECT_BOARD_NAME`](#NAVITAS_PROJECT_BOARD_NAME)
	- [`NAVITAS_PROJECT_COMMIT`](#NAVITAS_PROJECT_COMMIT)
	- [`NAVITAS_PROJECT_GMT_DATE`](#NAVITAS_PROJECT_GMT_DATE)
	- [`NAVITAS_PROJECT_EPOCH`](#NAVITAS_PROJECT_EPOCH)
	- [`NAVITAS_PROJECT_BOARD_x`](#NAVITAS_PROJECT_BOARD_x)
 - [Release zip](#Release_zip)

# Features

- Building auto generates a release .zip file with everything needed to manually program your board (Currently tested with ESP32, ESP8266, STM32);
- Firmware info built-in macros available to `src/` files;
- Firmware version increases once every build, but only once per commit, and only if there have been changes to code;

# How to use

## VSCode PlatformIO

1. Create your [VSCode PlatformIO](https://docs.platformio.org/en/latest/integration/ide/vscode.html) project;
2. Open the PlatformIO project folder with `git bash`;
3. Add this submodule to path: `scripts/versioning`: 
```[bash]
git submodule add https://github.com/GIT-NavitasTecnologia/NAVITAS_PlatformIOScript.git scripts/versioning
```
4. Open your `platformio.ini` file and add the following lines:
```[ini]
extra_scripts =
	post:scripts/versioning/post_extra_script.py
	pre:scripts/versioning/pre_extra_script.py
```
5. Do **not** add these files to `.gitignore`:
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

## Release zip

After building your application with vscode, the `zip` file will be available inside the folder `.pio/release/`
