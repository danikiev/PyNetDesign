:: Windows script for building the PyNetDesign documentation.
:: Run: `build-docs.bat` from cmd
::      `build-docs.bat -i` to rebuild only what changed
::      `build-docs.bat -pdf` to also build the PDF into the HTML tree
:: Extra Sphinx options can be passed through the SPHINXOPTS variable, e.g.
::      set SPHINXOPTS=-D plot_gallery=0
:: Use `serve-docs.bat` to view the result in a browser.
:: Requires the docs extra: pip install -e ".[docs]"
:: The PDF additionally requires a LaTeX installation providing lualatex and latexmk.
:: D. Anikiev, 2026-09-11

@echo off
setlocal

set CLEAN=1
set BUILD_PDF=0
for %%i in (%*) do (
    if /i "%%i" == "-i" set CLEAN=0
    if /i "%%i" == "--incremental" set CLEAN=0
    if /i "%%i" == "-pdf" set BUILD_PDF=1
    if /i "%%i" == "--pdf" set BUILD_PDF=1
    if /i "%%i" == "-h" goto usage
    if /i "%%i" == "--help" goto usage
)
goto args_done

:usage
echo Usage: build-docs.bat [-i] [-pdf]
echo   -i, --incremental   skip the clean and rebuild only what changed
echo   -pdf, --pdf         also build the PDF into docs\build\html\_static
echo.
echo Pass extra Sphinx options through SPHINXOPTS.
exit /b 0

:args_done

set SOURCE_DIR=docs\source
set BUILD_DIR=docs\build
set PDF_NAME=pynetdesign.pdf
set TEX_NAME=pynetdesign.tex

if not exist %SOURCE_DIR%\conf.py (
    echo Sphinx configuration not found: %SOURCE_DIR%\conf.py
    echo Please run this script from the repository root.
    exit /b 1
)

call python -c "import sphinx" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Sphinx is not installed in the active environment.
    echo Install the documentation tools with: pip install -e ".[docs]"
    exit /b 2
)

if %BUILD_PDF% equ 1 (
    where lualatex >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo lualatex not found in PATH, which is required for the PDF build.
        echo Install a LaTeX distribution, or drop -pdf to build the HTML only.
        exit /b 2
    )
    where latexmk >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo latexmk not found in PATH, which is required for the PDF build.
        echo Install a LaTeX distribution, or drop -pdf to build the HTML only.
        exit /b 2
    )
)

if %CLEAN% equ 1 (
    echo ##################################################################
    echo Cleaning...
    call python -m sphinx -M clean %SOURCE_DIR% %BUILD_DIR%
    if %ERRORLEVEL% neq 0 (
        echo Error while cleaning!
        exit /b 1
    )
)

echo ##################################################################
echo Building HTML...
call python -m sphinx -M html %SOURCE_DIR% %BUILD_DIR% %SPHINXOPTS%
if %ERRORLEVEL% neq 0 (
    echo Error during HTML build process!
    exit /b 1
)

if %BUILD_PDF% equ 1 (
    echo ##################################################################
    echo Generating LaTeX...
    call python -m sphinx -M latex %SOURCE_DIR% %BUILD_DIR% %SPHINXOPTS%
    if %ERRORLEVEL% neq 0 (
        echo Error while generating LaTeX!
        exit /b 1
    )

    echo ##################################################################
    echo Building PDF...
    rem latexmk reads the latexmkrc that Sphinx writes next to the .tex, which binds the
    rem engine (lualatex) and the python.ist index style, so -pdf resolves to lualatex here.
    pushd %BUILD_DIR%\latex
    call latexmk -pdf -dvi- -ps- -interaction=nonstopmode -halt-on-error %TEX_NAME%
    if %ERRORLEVEL% neq 0 (
        echo Error during PDF build process!
        echo See %BUILD_DIR%\latex\pynetdesign.log for the LaTeX output.
        popd
        exit /b 1
    )
    popd

    if not exist %BUILD_DIR%\latex\%PDF_NAME% (
        echo PDF file not found after the build!
        exit /b 1
    )

    echo ##################################################################
    echo Copying the PDF into the HTML tree...
    if not exist %BUILD_DIR%\html\_static mkdir %BUILD_DIR%\html\_static
    copy /y %BUILD_DIR%\latex\%PDF_NAME% %BUILD_DIR%\html\_static\%PDF_NAME% >nul
    if %ERRORLEVEL% neq 0 (
        echo Error while copying the PDF!
        exit /b 2
    )
)

echo ##################################################################
echo Documentation built in docs\build\html
if %BUILD_PDF% equ 1 (
    echo PDF available at docs\build\html\_static\%PDF_NAME%
) else (
    echo The PDF was not built; pass -pdf to build it as well.
)
echo Open docs\build\html\index.html, or run serve-docs.bat to serve it.
