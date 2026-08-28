cmake_minimum_required(VERSION 3.5...3.10)

project(kobuki_bumper2pc)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake_ros REQUIRED)
find_package(kobuki_ros_interfaces REQUIRED)
find_package(rcl_interfaces REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)

add_library(kobuki_bumper2pc src/kobuki_bumper2pc.cpp)
target_include_directories(kobuki_bumper2pc PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>"
)
# ament_target_dependencies() was removed in ROS 2 Lyrical; link the modern
# CMake targets exported by each dependency instead.
target_link_libraries(kobuki_bumper2pc PUBLIC
  kobuki_ros_interfaces::kobuki_ros_interfaces__rosidl_typesupport_cpp
  rcl_interfaces::rcl_interfaces__rosidl_typesupport_cpp
  rclcpp::rclcpp
  rclcpp_components::component
  sensor_msgs::sensor_msgs__rosidl_typesupport_cpp
)

rclcpp_components_register_node(kobuki_bumper2pc
  PLUGIN "kobuki_bumper2pc::Bumper2PcNode"
  EXECUTABLE kobuki_bumper2pc_node)

install(TARGETS kobuki_bumper2pc
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION include/${PROJECT_NAME}
)
# config/ holds kobuki_bumper2pc_params.yaml, which the launch file reads from
# the install space - it has to be installed alongside launch/.
install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
