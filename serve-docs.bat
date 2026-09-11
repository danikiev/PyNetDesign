:: Windows script for serving the PyNetDesign documentation locally.
:: Rebuilds first, incrementally, so only the pages that changed are regenerated.
:: Run: `serve-docs.bat` from cmd
::      `serve-docs.bat -p 8080` to serve on another port
::      `serve-docs.bat -n` to serve what is already built
::      `serve-docs.bat -pdf` to also build the PDF, so its download link works
:: Extra Sphinx options can be passed through the SPHINXOPTS variable.
:: D. Anikiev, 2026-09-11

@echo off
setlocal

set PORT=8000
set DO_BUILD=1
set BUILD_PDF=0
set HTML_DIR=docs\build\html

:: Parse arguments
:parse_args
if "%~1" == "" goto args_done
if /i "%~1" == "-n" (
    set DO_BUILD=0
    shift
    goto parse_args
)
if /i "%~1" == "--no-build" (
    set DO_BUILD=0
    shift
    goto parse_args
)
if /i "%~1" == "-pdf" (
    set BUILD_PDF=1
    shift
    goto parse_args
)
if /i "%~1" == "--pdf" (
    set BUILD_PDF=1
    shift
    goto parse_args
)
if /i "%~1" == "-p" goto set_port
if /i "%~1" == "--port" goto set_port
if /i "%~1" == "-h" goto usage
if /i "%~1" == "--help" goto usage
echo Unknown option: %~1
echo Try serve-docs.bat --help
exit /b 1

:set_port
if "%~2" == "" (
    echo Missing value for %~1
    exit /b 1
)
set PORT=%~2
shift
shift
goto parse_args

:usage
echo Usage: serve-docs.bat [-p PORT] [-n] [-pdf]
echo   -p, --port PORT   port to serve on (default 8000)
echo   -n, --no-build    skip the rebuild and serve what is already there
echo   -pdf, --pdf       also build the PDF, so its download link works
echo.
echo Pass extra Sphinx options through SPHINXOPTS.
exit /b 0

:args_done

:: Build when asked, and also when there is nothing to serve yet
if %DO_BUILD% equ 1 goto do_build
if not exist %HTML_DIR%\index.html (
    echo No existing build found, building anyway...
    goto do_build
)
goto serve

:do_build
:: Delegate to build-docs so the build logic lives in one place
if %BUILD_PDF% equ 1 (
    call build-docs.bat -i -pdf
) else (
    call build-docs.bat -i
)
if %ERRORLEVEL% neq 0 (
    echo Build failed, not serving.
    exit /b 1
)

:serve
if not exist %HTML_DIR%\index.html (
    echo Documentation was not built: %HTML_DIR%\index.html is missing.
    exit /b 3
)

echo ##################################################################
echo Serving documentation at http://localhost:%PORT%
echo Press Ctrl+C to stop.
pushd %HTML_DIR%
call python -m http.server %PORT%
popd
