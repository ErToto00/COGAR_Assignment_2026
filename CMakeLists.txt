cmake_minimum_required(VERSION 3.5)
project(jazzy_go2_control)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

install(PROGRAMS
  src/go2_connection_node.py
  src/go2_walk_node.py
  src/llm_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
