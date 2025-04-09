cmake_minimum_required(VERSION 3.5)
project(champ_gazebo)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
 
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
#find_package(gazebo REQUIRED)
#find_package(gazebo_dev REQUIRED)
#find_package(gazebo_msgs REQUIRED)
#find_package(gazebo_ros REQUIRED)

include_directories(
  include
  ${GAZEBO_INCLUDE_DIRS}) 

set(dependencies
  rclcpp
  rclpy
  std_msgs
  std_srvs
  tf2_ros
  geometry_msgs
#  gazebo
#  gazebo_dev
#  gazebo_msgs
#  gazebo_ros
)

add_executable(helper_publish_base_pose src/helper_publish_base_pose.cpp)
ament_target_dependencies(helper_publish_base_pose ${dependencies})

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.dsv.in")

install(TARGETS 
  helper_publish_base_pose
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  nodes/move_legs
  nodes/move_arm
  nodes/spot_walk
  nodes/republish_ground_truth
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY worlds models launch
  DESTINATION share/${PROJECT_NAME})
  
ament_package()
