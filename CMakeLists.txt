cmake_minimum_required(VERSION 3.5)
project(jazzy_ur5e_control)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(ur_description REQUIRED)

add_executable(jazzy_ur5e_control_node src/jazzy_ur5e_control_node.py)

ament_target_dependencies(jazzy_ur5e_control_node
  rclpy
  ur_description
)

install(TARGETS
  jazzy_ur5e_control_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
