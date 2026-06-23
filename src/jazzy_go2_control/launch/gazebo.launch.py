import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Package name
    pkg_name = 'jazzy_go2_control'
    
    # Paths
    pkg_share = FindPackageShare(pkg_name)
    rviz_config_path = PathJoinSubstitution([pkg_share, 'config', 'hand_view.rviz'])
    
    # Set GZ_SIM_RESOURCE_PATH so Gazebo Harmonic can find the meshes
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=PathJoinSubstitution([FindPackageShare('unitree_go2_description'), '..'])
    )
    
    # Declare launch arguments
    declared_arguments = []
    
    classifier_type_arg = DeclareLaunchArgument(
        'classifier_type',
        default_value='lstm',
        description='Type of classifier to use: knn or lstm'
    )
    obstacle_mode_arg = DeclareLaunchArgument(
        'obstacle_mode',
        default_value='autonomous',
        description='Mode for obstacle avoidance: autonomous or llm'
    )
    llm_mode_arg = DeclareLaunchArgument(
        'llm_mode',
        default_value='simple',
        description='Mode for LLM prompt generation: simple or code_as_policies'
    )
    declared_arguments.append(classifier_type_arg)
    declared_arguments.append(obstacle_mode_arg)
    declared_arguments.append(llm_mode_arg)

    # Unitree Go2 Integration (CHAMP, Gazebo, Robot State Publisher)
    unitree_go2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('unitree_go2_sim'), 'launch', 'unitree_go2_launch.py'])
        ),
        launch_arguments={'rviz': 'false'}.items(), # We use our own RViz
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
    # The new stack links map -> odom -> base_link. Link world -> map to align the hands.
    tf_world_to_map = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'map']
    )

    # Convert 3D PointCloud to 2D LaserScan for obstacle avoidance
    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        remappings=[
            ('cloud_in', '/unitree_lidar/points'),
            ('scan', '/scan')
        ],
        parameters=[{
            'target_frame': 'base_link',
            'min_height': -0.1,
            'max_height': 0.5,
            'angle_min': -3.1415,
            'angle_max': 3.1415,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.1,
            'range_max': 20.0,
            'use_inf': True,
        }],
        output='screen'
    )

    # Assignment Nodes
    connection_node = Node(
        package=pkg_name,
        executable='connection_node.py',
        name='connection_node',
        output='screen'
    )
    walk_node = Node(
        package=pkg_name,
        executable='movement_node.py',
        name='movement_node',
        output='screen'
    )
    llm_node = Node(
        package=pkg_name,
        executable='llm_node.py',
        name='llm_node',
        output='screen',
        parameters=[{
            'llm_mode': LaunchConfiguration('llm_mode'),
            'classifier_type': LaunchConfiguration('classifier_type')
        }]
    )
    gesture_node = Node(
        package=pkg_name,
        executable='gesture_classifier_node.py',
        name='gesture_classifier_node',
        output='screen',
        parameters=[{'classifier_type': LaunchConfiguration('classifier_type')}]
    )
    obstacle_node = Node(
        package=pkg_name,
        executable='obstacle_avoidance_node.py',
        name='obstacle_avoidance_node',
        output='screen',
        parameters=[{'mode': LaunchConfiguration('obstacle_mode')}]
    )

    nodes_to_start = [
        gz_resource_path,
        unitree_go2_launch,
        manus_node,
        rviz_node,
        tf_left,
        tf_right,
        tf_world_to_map,
        pointcloud_to_laserscan_node,
        connection_node,
        walk_node,
        llm_node,
        gesture_node,
        obstacle_node,
    ]

    return LaunchDescription(declared_arguments + nodes_to_start)
