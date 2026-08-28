cmake_minimum_required(VERSION 3.5)
project(kobuki_keyop)

find_package(ament_cmake_ros REQUIRED)
find_package(ecl_build REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(kobuki_ros_interfaces REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)

ecl_enable_cxx14_compiler()
ecl_enable_cxx_warnings()

include_directories(include)

add_library(kobuki_keyop SHARED src/keyop.cpp)
# ament_target_dependencies() was removed in ROS 2 Lyrical; link the modern
# CMake targets exported by each dependency instead.
target_link_libraries(kobuki_keyop PUBLIC
  geometry_msgs::geometry_msgs__rosidl_typesupport_cpp
  kobuki_ros_interfaces::kobuki_ros_interfaces__rosidl_typesupport_cpp
  rclcpp::rclcpp
  rclcpp_components::component
)

rclcpp_components_register_node(kobuki_keyop
  PLUGIN "kobuki_keyop::KeyOp"
  EXECUTABLE kobuki_keyop_node)

install(TARGETS kobuki_keyop
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION include/${PROJECT_NAME}
)
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
