:: Windows installer script for PyNetDesign
:: This script creates the Conda environment from "environment.yml" and installs the package.
:: environment.yml pins only the interpreter; the dependencies come from pyproject.toml,
:: as runtime requirements plus the optional "dev" and "docs" groups.
:: Run: install.bat from cmd
:: D. Anikiev, 2025-04-01

@echo off
:: Note: do not name any variable PIP_something. pip reads PIP_<OPTION> from the
:: environment, so e.g. PIP_TARGET would silently become pip's --target option.

set ENV_NAME=pnd
set ENV_YAML=environment.yml
set PACKAGE_NAME=pynetdesign

:: Ask whether the development tools should be installed as well
echo PyNetDesign will be installed into the Conda environment "%ENV_NAME%".
echo.
echo The development tools add pytest, a Jupyter stack and the Sphinx
echo toolchain for building the documentation locally.
set /p DEV_CHOICE="Install the development tools as well? (y/n): "

if /i "%DEV_CHOICE%" == "y" (
    set INSTALL_SPEC=".[dev,docs]"
    echo Installing with the development tools.
) else (
    set INSTALL_SPEC=.
    echo Installing the runtime dependencies only.
)

:: Check for Conda Installation
where conda >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Conda is not installed or not found in the system PATH.
    echo Please install Conda and make sure it's added to the system PATH.
    pause
    exit /b 2
)

:: Check for environment file
if not exist %ENV_YAML% (
    echo %ENV_YAML% not found in the current directory
    echo Please check and try again.
    pause
    exit /b 3
)

echo Creating Conda environment %ENV_NAME% from %ENV_YAML%...
call conda env create -f %ENV_YAML% -n %ENV_NAME%
:: Check if environment creation was successful
if %ERRORLEVEL% equ 0 (
    echo Conda environment %ENV_NAME% created successfully.
) else (
    echo Failed to create Conda environment %ENV_NAME%. Please check the error messages above.
    pause
    exit /b 4
)

:: List conda environments
call conda env list

:: Activate environment
echo Activating Conda environment %ENV_NAME%...
call conda activate %ENV_NAME%
:: Check if environment activation was successful
if %ERRORLEVEL% equ 0 (
    echo Conda environment %ENV_NAME% activated successfully.
) else (
    echo Failed to activate Conda environment %ENV_NAME%. Please check the error messages above.
    pause
    exit /b 5
)

echo Installing %PACKAGE_NAME%...
call pip install -e %INSTALL_SPEC%
if %ERRORLEVEL% equ 0 (
    echo Successfully installed %PACKAGE_NAME%.
) else (
    echo Failed to install %PACKAGE_NAME%. Please check the error messages above.
    pause
    exit /b 6
)

echo Python version:
call python --version

echo Python path:
:: Pick only first output
for /f "tokens=* usebackq" %%f in (`where python`) do (set "pythonpath=%%f" & goto :next)
:next

echo %pythonpath%

echo Done!

pause
