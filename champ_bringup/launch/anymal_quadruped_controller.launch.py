# Copyright (c) 2021 Fetullah Atas, Norwegian University of Life Sciences
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, SetParameter
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.actions import RegisterEventHandler
from launch.actions import IncludeLaunchDescription
from launch.actions import ExecuteProcess
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch.substitutions import PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

from os import environ
import os
import xacro

def generate_launch_description():

  # Get here directories of packages
  champ_bringup_share_dir = get_package_share_directory(
      'champ_bringup')
  champ_description_share_dir = get_package_share_directory(
      'champ_description')

  launch_args = [

    DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='If true, use simulated clock'),
    DeclareLaunchArgument(
        'champ_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'champ_params_anymal.yaml'),
        description='path to locks params.'),
    DeclareLaunchArgument(
        'localization_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'robot_localization_params.yaml'),
        description='Path to the vox_nav parameters file.')
  ]
  
  use_simulator = LaunchConfiguration('use_simulator')
  use_sim_time = LaunchConfiguration('use_sim_time', default=True)
  champ_params = LaunchConfiguration('champ_params')  

  # ros2 topic pub /vox_nav/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
  quadruped_controller_node = Node(
        package='champ_base',
        executable='quadruped_controller',
        name='quadruped_controller',
        output='screen',
        # namespace='',
        arguments=['--ros-args', '--log-level', 'INFO'],
        # prefix=['xterm -e gdb -ex run --args'],
        parameters=[
            {"use_sim_time": use_sim_time},
            champ_params],
        remappings=[('cmd_vel', 'vox_nav/cmd_vel')]
        )
    
  return LaunchDescription(
    launch_args + 
    [
      quadruped_controller_node,
      #declare_state_estimation_node,
      #declare_rviz_launch_include,
      #declare_localization_params,
      #footprint_to_odom_ekf,
      #base_to_footprint_ekf,
      #broadcast_left_front_cam,
      #broadcast_right_front_cam
      #joint_state_publisher_gui  # added by diya 9/6      
    ])
