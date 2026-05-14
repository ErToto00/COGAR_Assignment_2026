import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Package name
    pkg_name = 'jazzy_go2_control'
    
    # Paths
    pkg_share = FindPackageShare(pkg_name)
    rviz_config_path = PathJoinSubstitution([pkg_share, 'config', 'hand_view.rviz'])
    
    # Declare launch arguments
    declared_arguments = []
    
    # Gazebo Sim: Include the Gazebo launch file
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # Bridge ROS topics and Gazebo topics for clock and joint states
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen'
    )

    # Manus ROS 2 Node
    manus_node = Node(
        package='manus_ros2',
        executable='manus_ros2',
        name='manus_ros2',
        output='screen'
    )

    # RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    # Static TFs to link hand frames to world
    tf_left = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '1', '0', '0', '0', 'world', 'manus_left']
    )
    tf_right = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '1', '0', '0', '0', 'world', 'manus_right']
    )

    # Assignment Nodes
    connection_node = Node(
        package=pkg_name,
        executable='go2_connection_node.py',
        name='go2_connection_node',
        output='screen'
    )
    walk_node = Node(
        package=pkg_name,
        executable='go2_walk_node.py',
        name='go2_walk_node',
        output='screen'
    )
    llm_node = Node(
        package=pkg_name,
        executable='llm_node.py',
        name='llm_node',
        output='screen'
    )

    nodes_to_start = [
        gazebo_launch,
        bridge,
        manus_node,
        rviz_node,
        tf_left,
        tf_right,
        connection_node,
        walk_node,
        llm_node,
    ]

    return LaunchDescription(declared_arguments + nodes_to_start)
