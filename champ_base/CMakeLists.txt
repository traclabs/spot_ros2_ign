cmake_minimum_required(VERSION 3.10)
project(champ_base)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Expose the distro to the sources (e.g. ROS_DISTRO_JAZZY) for API differences between distros
string(TOUPPER "$ENV{ROS_DISTRO}" ros_distro_upper)
add_compile_definitions("ROS_DISTRO_${ros_distro_upper}=1")

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(angles REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(champ_msgs REQUIRED)
find_package(champ REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(message_filters REQUIRED)
find_package(urdf REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)


include_directories(
  include
  ${champ_INCLUDE_DIRS}
  ${champ_INCLUDE_DIRS}/champ/
  ${champ_INCLUDE_DIRS}/champ/champ/ 
)

install(DIRECTORY  
  DESTINATION share/${PROJECT_NAME}
)

foreach(target message_relay quadruped_controller state_estimation)
  add_executable(${target} src/${target}.cpp)
  target_link_libraries(${target} PUBLIC
    ${champ_msgs_TARGETS}
    ${geometry_msgs_TARGETS}
    ${nav_msgs_TARGETS}
    ${sensor_msgs_TARGETS}
    ${trajectory_msgs_TARGETS}
    ${visualization_msgs_TARGETS}
    rclcpp::rclcpp
    sensor_msgs::sensor_msgs_library
    tf2::tf2
    tf2_geometry_msgs::tf2_geometry_msgs
    tf2_ros::static_transform_broadcaster_node
    tf2_ros::tf2_ros
    urdf::urdf
  )
endforeach()

install(TARGETS 
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(TARGETS quadruped_controller
                message_relay
                state_estimation
  RUNTIME DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY include/
  DESTINATION include/)

install(
  DIRECTORY 
  DESTINATION share/${PROJECT_NAME})

ament_package()