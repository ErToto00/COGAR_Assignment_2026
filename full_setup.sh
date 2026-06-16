#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Starting Full Environment Setup for COGAR Assignment ---"

# 1. Install Python Dependencies from Source
echo "Installing Unitree SDK from source..."
if [ ! -d "unitree_sdk2_python" ]; then
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
fi
# Install dependencies and the package itself
pip install cyclonedds --user --break-system-packages
cd unitree_sdk2_python
pip install . --user --break-system-packages
cd ..

# 2. Setup Manus SDK Links
echo "Linking Manus ROS2 packages..."
mkdir -p src
# Check if manus_ros2 exists in the parent directory
if [ -d "../manus_ros2" ]; then
    if [ ! -L src/manus_ros2 ]; then
        ln -s ../../manus_ros2 src/manus_ros2
        echo "Linked manus_ros2"
    fi
    if [ ! -L src/manus_ros2_msgs ]; then
        ln -s ../../manus_ros2/ext/ManusSDK_v3.1.1/ROS2/manus_ros2_msgs src/manus_ros2_msgs
        echo "Linked manus_ros2_msgs"
    fi
elif [ -d "ManusSDK_v3.1.1" ]; then
    if [ ! -L src/manus_ros2 ]; then
        ln -s ../ManusSDK_v3.1.1/ROS2/manus_ros2 src/manus_ros2
        echo "Linked manus_ros2"
    fi
    if [ ! -L src/manus_ros2_msgs ]; then
        ln -s ../ManusSDK_v3.1.1/ROS2/manus_ros2_msgs src/manus_ros2_msgs
        echo "Linked manus_ros2_msgs"
    fi
else
    echo "Warning: Manus SDK directory not found. Skipping Manus links."
fi

# 3. Setup Go2 Robot Description (URDF)
echo "Setting up Go2 URDF and Description..."
cd src
# Official Unitree ROS
if [ ! -d "unitree_ros" ]; then
    git clone https://github.com/unitreerobotics/unitree_ros.git
fi

# Community Go2 ROS 2 Description
if [ ! -d "go2_description_ros2" ]; then
    git clone https://github.com/anujjain-dev/go2_description.git go2_description_ros2
fi
cd ..

# 4. Build the Workspace
echo "Building the workspace packages..."
colcon build --symlink-install

# 5. Final Sourcing
echo "Sourcing the workspace..."
source install/setup.bash

echo "--- Setup Complete! ---"
echo "You can now run your project using ./build_and_launch.sh"
