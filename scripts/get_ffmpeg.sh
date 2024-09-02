#!/bin/bash

echo PWD: $PWD

# Set variables
RELEASE_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/tag/latest"
FILE_NAME="ffmpeg-master-latest-linux64-gpl.tar.xz"
DOWNLOAD_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/${FILE_NAME}"
TEMP_DIR=$(mktemp -d)
BIN_DIR="./bin"

# Create the bin directory if it doesn't exist
mkdir -p "${BIN_DIR}"

# Download the file
echo "Downloading ${FILE_NAME} from ${DOWNLOAD_URL}..."
curl -L -o "${TEMP_DIR}/${FILE_NAME}" "${DOWNLOAD_URL}"

# Extract the file
echo "Extracting ${FILE_NAME}..."
tar -xJf "${TEMP_DIR}/${FILE_NAME}" -C "${TEMP_DIR}"

# Copy files to the bin directory
echo "Copying files to ${BIN_DIR}..."
cp -r "${TEMP_DIR}/ffmpeg-master-latest-linux64-gpl/bin/"* "${BIN_DIR}/"

# Clean up the temporary directory
rm -rf "${TEMP_DIR}"

echo "Done."