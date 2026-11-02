cmake_minimum_required(VERSION 3.5...3.10)
project(turtlebot_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
