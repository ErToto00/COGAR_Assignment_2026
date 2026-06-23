#!/bin/bash
clear

# Exit immediately if a command exits with a non-zero status
set -e
echo "--- Starting Full Environment Setup for COGAR Assignment ---"


# 0. System Setup and ROS 2 Repository Setup
echo "--- System Setup and Prerequisites ---"
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install software-properties-common curl -y
sudo add-apt-repository universe -y

# Detect ROS distro based on Ubuntu version or use environment variable
UBUNTU_CODENAME=$(lsb_release -sc)
if [ "$UBUNTU_CODENAME" == "jammy" ]; then
    ROS_VER=${ROS_DISTRO:-humble}
elif [ "$UBUNTU_CODENAME" == "noble" ]; then
    ROS_VER=${ROS_DISTRO:-jazzy}
else
    ROS_VER=${ROS_DISTRO:-jazzy}
fi

echo "--- Setting Up ROS 2 Repository ---"
if [ ! -d "/opt/ros/${ROS_VER}" ]; then
    sudo mkdir -p /usr/share/keyrings
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

    echo "Installing system dependencies via APT (requires sudo)..."
    sudo apt update
    sudo apt upgrade -y

    # Install ROS 2 Desktop and Gazebo Harmonic
    echo "--- Installing ROS 2 ${ROS_VER} and Gazebo ---"
    sudo apt install ros-${ROS_VER}-desktop ros-${ROS_VER}-ros-gz -y
else
    echo "ROS 2 ${ROS_VER} is already installed in /opt/ros/${ROS_VER}. Skipping ROS 2 base installation."
    sudo apt update
fi

# Install extra dependencies
sudo apt install -y python3-pip python3-dev python3-colcon-common-extensions python3-rosdep dos2unix \
    ros-${ROS_VER}-cyclonedds ros-${ROS_VER}-rmw-cyclonedds-cpp \
    ros-${ROS_VER}-moveit libfmt-dev \
    ros-${ROS_VER}-ros2-control ros-${ROS_VER}-ros2-controllers ros-${ROS_VER}-gz-ros2-control \
    ros-${ROS_VER}-robot-localization ros-${ROS_VER}-xacro ros-${ROS_VER}-velodyne ros-${ROS_VER}-velodyne-description \
    ros-${ROS_VER}-pointcloud-to-laserscan \
    libprotobuf-dev libgrpc++-dev protobuf-compiler-grpc

# Environment Configuration
source /opt/ros/${ROS_VER}/setup.bash
if ! grep -q "source /opt/ros/${ROS_VER}/setup.bash" ~/.bashrc; then
    echo "source /opt/ros/${ROS_VER}/setup.bash" >> ~/.bashrc
fi

sudo rosdep init || true
rosdep update

echo "Installing Python ML libraries via pip..."
pip3 install pandas numpy scikit-learn joblib requests --user --break-system-packages
pip3 install torch --index-url https://download.pytorch.org/whl/cpu --user --break-system-packages



# 1. Install Unitree SDK and CycloneDDS Python binding
echo "Installing Unitree SDK from source..."
if [ ! -d "unitree_sdk2_python" ]; then
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
fi
# Export CYCLONEDDS_HOME to point to ROS 2 installation where the C library resides
export CYCLONEDDS_HOME="/opt/ros/${ROS_DISTRO:-jazzy}"
# Install dependencies and the package itself
pip3 install cyclonedds --user --break-system-packages
# Copy the SDK to a native Linux folder (/tmp) to avoid NTFS permission issues during build
cp -r unitree_sdk2_python /tmp/unitree_sdk2_python_build
cd /tmp/unitree_sdk2_python_build
# Rimuoviamo il vincolo stretto su cyclonedds==0.10.2 per usare il wheel precompilato 11.0.1 ed evitare crash di compilazione
sed -i 's/cyclonedds==0.10.2/cyclonedds>=0.10.2/g' setup.py
pip3 install . --user --break-system-packages
cd - > /dev/null
rm -rf /tmp/unitree_sdk2_python_build


# 2. Setup Manus SDK Links
echo "Manus ROS2 package is already cloned into src/manus_ros2."
echo "Assuming ManusSDK is placed in the project root..."


# 3. Setup Go2 Robot Description (URDF)
echo "Setting up Go2 URDF and Description..."
cd src
# Official Unitree ROS
if [ ! -d "unitree_ros" ]; then
    git clone https://github.com/unitreerobotics/unitree_ros.git
fi



cd ..


# 3.5 Fix Python Script Line Endings and Permissions
echo "Fixing line endings and permissions for Python scripts..."
dos2unix src/jazzy_go2_control/scripts/*.py || true
chmod +x src/jazzy_go2_control/scripts/*.py || true


# 4. Build the Workspace
echo "Building the workspace packages..."
source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
colcon build --base-paths src --symlink-install


# 5. Final Sourcing
echo "Sourcing the workspace..."
source install/setup.bash


echo "--- Setup Complete! ---"
echo "You can now run your project using ./build_and_launch.sh"
