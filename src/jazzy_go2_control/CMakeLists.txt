cmake_minimum_required(VERSION 3.5)
project(jazzy_go2_control)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

install(PROGRAMS
  scripts/connection_node.py
  scripts/movement_node.py
  scripts/llm_node.py
  scripts/gesture_classifier_node.py
  scripts/obstacle_avoidance_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
