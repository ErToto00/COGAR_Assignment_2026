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
# manus_ros2 is inside the workspace
MANUS_SDK_ROOT="$(realpath "$WORKSPACE_ROOT/manus_ros2")"

if [ -d "$MANUS_SDK_ROOT" ]; then
    # Link manus_ros2 into src/ so colcon can build it
    if [ ! -L src/manus_ros2 ] || [ "$(readlink -f src/manus_ros2)" != "$MANUS_SDK_ROOT" ]; then
        ln -sf "$MANUS_SDK_ROOT" src/manus_ros2
        echo "Linked manus_ros2 -> $MANUS_SDK_ROOT"
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

echo "Starting manus_ros2 node in background..."
export MANUS_IP="192.168.1.100"
ros2 run manus_ros2 manus_ros2 &
MANUS_PID=$!

echo "Waiting a few seconds for manus_ros2 to initialize..."
sleep 3

echo "Starting the unified project launch (Gazebo, RViz, and Go2 nodes)..."
ros2 launch jazzy_go2_control gazebo.launch.py

# Optional: Kill background processes when the launch file exits
trap "kill $MANUS_PID" EXIT
