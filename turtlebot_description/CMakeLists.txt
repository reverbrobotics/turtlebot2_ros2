cmake_minimum_required(VERSION 3.5...3.10)
project(turtlebot_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
