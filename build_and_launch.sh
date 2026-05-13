#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting build process..."
# Ensure Manus ROS2 packages are linked in src/
mkdir -p src
if [ ! -L src/manus_ros2 ]; then
    echo "Linking manus_ros2..."
    ln -s ../ManusSDK_v3.1.1/ROS2/manus_ros2 src/manus_ros2
fi
if [ ! -L src/manus_ros2_msgs ]; then
    echo "Linking manus_ros2_msgs..."
    ln -s ../ManusSDK_v3.1.1/ROS2/manus_ros2_msgs src/manus_ros2_msgs
fi

echo "Building the workspace packages..."
colcon build

echo "Sourcing local install space..."
source install/setup.bash

echo "Starting Gazebo simulation in a new terminal..."
gnome-terminal -- bash -c "source /opt/ros/jazzy/setup.bash; source install/setup.bash; ros2 launch jazzy_go2_control gazebo.launch.py; exec bash"

echo "Starting go2_connection_node in the background..."
ros2 run jazzy_go2_control go2_connection_node &
CONNECTION_PID=$!

echo "Starting go2_walk_node in the background..."
ros2 run jazzy_go2_control go2_walk_node &
WALK_PID=$!

echo "Starting llm_node in the background..."
ros2 run jazzy_go2_control llm_node &
LLM_PID=$!

# Ensure the background processes are killed when the script exits
trap "echo 'Cleaning up...'; kill $CONNECTION_PID $WALK_PID $LLM_PID 2>/dev/null || true" EXIT

echo "All processes started."
echo "Press Ctrl+C in this window to stop the background nodes."
wait $CONNECTION_PID $WALK_PID $LLM_PID
