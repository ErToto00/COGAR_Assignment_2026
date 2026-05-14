#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Starting Build and Launch Process ---"

# Ensure we are in the workspace root
cd "$(dirname "$0")"
WORKSPACE_ROOT=$(pwd)

echo "Linking Manus ROS2 packages with absolute paths..."
mkdir -p src

# Define absolute paths for Manus SDK
# Assuming manus_ros2 is in the same parent directory as this repository
MANUS_SDK_ROOT="$(realpath "$WORKSPACE_ROOT/../manus_ros2")"

if [ -d "$MANUS_SDK_ROOT" ]; then
    # Link manus_ros2
    if [ ! -L src/manus_ros2 ] || [ "$(readlink -f src/manus_ros2)" != "$MANUS_SDK_ROOT" ]; then
        ln -sf "$MANUS_SDK_ROOT" src/manus_ros2
        echo "Linked manus_ros2 -> $MANUS_SDK_ROOT"
    fi
    
    # Link manus_ros2_msgs
    MSGS_PATH="$MANUS_SDK_ROOT/ext/ManusSDK_v3.1.1/ROS2/manus_ros2_msgs"
    if [ -d "$MSGS_PATH" ]; then
        if [ ! -L src/manus_ros2_msgs ] || [ "$(readlink -f src/manus_ros2_msgs)" != "$MSGS_PATH" ]; then
            ln -sf "$MSGS_PATH" src/manus_ros2_msgs
            echo "Linked manus_ros2_msgs -> $MSGS_PATH"
        fi
    else
        echo "Warning: manus_ros2_msgs not found at $MSGS_PATH"
    fi
else
    echo "Error: Manus SDK directory not found at $MANUS_SDK_ROOT"
    exit 1
fi

echo "Building the workspace packages..."
# colcon build should now find both jazzy_go2_control (in src/) and manus_ros2 (in src/)
colcon build --symlink-install

echo "Sourcing local install space..."
source install/setup.bash

echo "Starting the unified project launch (Gazebo, RViz, Manus, and Go2 nodes)..."
ros2 launch jazzy_go2_control gazebo.launch.py
