@echo off
echo Building WMS Application Executable...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "WMS_Application.exe" del "WMS_Application.exe"

echo Cleaning previous builds...

REM Build the executable using the spec file
echo Building executable with templates and static files...
pyinstaller --clean build_exe.spec

REM Copy the executable to the root directory for easy access
if exist "dist\WMS_Application.exe" (
    copy "dist\WMS_Application.exe" "WMS_Application.exe"
    echo.
    echo ✅ Build completed successfully!
    echo ✅ Executable: WMS_Application.exe
    echo.
    echo IMPORTANT NOTES:
    echo 1. Make sure your database is accessible from the target machine
    echo 2. Update credential.json path if needed (C:/tmp/sap_login/credential.json)
    echo 3. Templates and static files are now included in the executable
    echo 4. Run the executable from the same directory structure
    echo.
) else (
    echo ❌ Build failed! Check the error messages above.
)

pause