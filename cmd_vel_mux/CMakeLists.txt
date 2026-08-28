cmake_minimum_required(VERSION 3.5...3.10)
project(cmd_vel_mux)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rcl_interfaces REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(rcpputils REQUIRED)
find_package(std_msgs REQUIRED)

include_directories(include)

# Nodelet library
add_library(${PROJECT_NAME} SHARED src/cmd_vel_mux.cpp)
# ament_target_dependencies() was removed in ROS 2 Lyrical; link the modern
# CMake targets exported by each dependency instead.
target_link_libraries(${PROJECT_NAME} PUBLIC
  geometry_msgs::geometry_msgs__rosidl_typesupport_cpp
  rcl_interfaces::rcl_interfaces__rosidl_typesupport_cpp
  rclcpp::rclcpp
  rclcpp_components::component
  rcpputils::rcpputils
  std_msgs::std_msgs__rosidl_typesupport_cpp
)

rclcpp_components_register_node(${PROJECT_NAME}
  PLUGIN "cmd_vel_mux::CmdVelMux"
  EXECUTABLE cmd_vel_mux_node)

install(TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION include/${PROJECT_NAME}
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ros_testing REQUIRED)

  add_ros_test(test/test_cmd_vel_mux.py
    TARGET test_cmd_vel_mux
    TIMEOUT 30
  )

  add_ros_test(test/test_cmd_vel_mux_updates.py
    TARGET test_cmd_vel_mux_updates
    TIMEOUT 30
  )
endif()

ament_package()
