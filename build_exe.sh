#!/bin/bash
echo "Building WMS Application Executable..."
echo

# Install PyInstaller if not already installed
pip install pyinstaller

# Clean previous builds
if [ -d "build" ]; then
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi
if [ -f "WMS_Application" ]; then
    rm WMS_Application
fi

echo "Cleaning previous builds..."

# Build the executable using the spec file
echo "Building executable with templates and static files..."
pyinstaller --clean build_exe.spec

# Copy the executable to the root directory for easy access
if [ -f "dist/WMS_Application" ]; then
    cp "dist/WMS_Application" "WMS_Application"
    chmod +x "WMS_Application"
    echo
    echo "✅ Build completed successfully!"
    echo "✅ Executable: WMS_Application"
    echo
    echo "IMPORTANT NOTES:"
    echo "1. Make sure your database is accessible from the target machine"
    echo "2. Update credential.json path if needed (/tmp/sap_login/credential.json)"
    echo "3. Templates and static files are now included in the executable"
    echo "4. Run the executable from the same directory structure"
    echo
else
    echo "❌ Build failed! Check the error messages above."
fi