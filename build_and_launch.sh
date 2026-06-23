#!/bin/bash
clear

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Starting Build and Launch Process ---"

# Ensure we are in the workspace root
cd "$(dirname "$0")"
WORKSPACE_ROOT=$(pwd)

# Function to ensure all processes spawned by the launch file are killed
cleanup() {
    echo "Terminating all associated processes to ensure a clean exit..."
    pkill -f "gazebo.launch.py" || true
    pkill -x "rviz2" || true
    pkill -x "manus_ros2" || true
    pkill -f "gz sim" || true
    pkill -x "ruby" || true
}
# Trap exit signals to run the cleanup function
trap cleanup EXIT INT TERM


echo "Building the workspace packages..."
colcon build --base-paths src --symlink-install

echo "Sourcing local install space..."
source install/setup.bash

export MANUS_IP="192.168.1.100"

echo "Starting the unified project launch (Gazebo, RViz, and Go2 nodes)..."

# Classifier mode (options: 'lstm' or 'knn')
CLASSIFIER_MODE="lstm"

# Obstacle mode ('llm' or 'autonomous')
OBSTACLE_MODE="llm"
if [ "$1" == "--llm" ] || [ "$1" == "llm" ]; then
    OBSTACLE_MODE="llm"
    echo "Obstacle avoidance running in LLM mode"
else
    echo "Obstacle avoidance running in autonomous mode"
fi

# LLM mode ('simple' or 'code_as_policies')
LLM_MODE="simple"

# Fix CycloneDDS initialization error in WSL by forcing it to use loopback for local simulation
export CYCLONEDDS_URI="<CycloneDDS><Domain><General><NetworkInterfaceAddress>lo</NetworkInterfaceAddress><AllowMulticast>false</AllowMulticast></General></Domain></CycloneDDS>"

ros2 launch jazzy_go2_control gazebo.launch.py classifier_type:=$CLASSIFIER_MODE obstacle_mode:=$OBSTACLE_MODE llm_mode:=$LLM_MODE

