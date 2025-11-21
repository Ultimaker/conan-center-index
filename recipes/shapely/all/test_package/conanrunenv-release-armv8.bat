@echo off
chcp 65001 > nul
setlocal
echo @echo off > "%~dp0/deactivate_conanrunenv-release-armv8.bat"
echo echo Restoring environment >> "%~dp0/deactivate_conanrunenv-release-armv8.bat"
for %%v in (SHAPELY_WHEEL PATH) do (
    set foundenvvar=
    for /f "delims== tokens=1,2" %%a in ('set') do (
        if /I "%%a" == "%%v" (
            echo set "%%a=%%b">> "%~dp0/deactivate_conanrunenv-release-armv8.bat"
            set foundenvvar=1
        )
    )
    if not defined foundenvvar (
        echo set %%v=>> "%~dp0/deactivate_conanrunenv-release-armv8.bat"
    )
)
endlocal


set "SHAPELY_WHEEL=C:\Users\alire\.conan2\p\b\shapee8cbb20a216b2\p\dist\shapely-2.0.6-cp312-cp312-win_arm64.whl"
set "PATH=C:\Users\alire\.conan2\p\b\geos3c78aab2b309a\p\bin;%PATH%"