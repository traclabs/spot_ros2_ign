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
  
  # xyz yaw:
  # 5.0, 0.0 0.84  : In the middle of room with pipes, ladder and a small pile of metallic hubris
  # 54.0 -11.85 10.70 (10.526) -1.671: Close to equipment piece that looks like a motor?
  # 35.11 8.819 (10.70) 10.526 3.087: Close to stairs
  # 46.821, 14.213, (20.7) 20.523 0.0: Between both machines
  # 79.183 -3.491 (10.7) 10.513 2.9: Close to pipes
  launch_args = [
    DeclareLaunchArgument(
        'x',
        default_value='6.0',
        description='X at which to spawn Spot. 0.84 for ground plane, 0 for marsyard is good'),
    DeclareLaunchArgument(
        'y',
        default_value='0.0',
        description='y at which to spawn Spot.'), 
    DeclareLaunchArgument(
        'z',
        default_value='2.0',
        description='Height at which to spawn Spot.'), 
    DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Roll at which to spawn Spot.'),  
    DeclareLaunchArgument(
        'yaw',
        default_value='0.7',
        description='Yaw at which to spawn Spot.'),          
    DeclareLaunchArgument(
        'use_simulator',
        default_value='True',
        description='whether to use Gazebo Simulation.'),
    DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='If true, use simulated clock'),
    DeclareLaunchArgument(
        'use_rviz',
        default_value='False',
        description='whether or not to launch rviz'),
    DeclareLaunchArgument(
        'tf_prefix',
        default_value='',
        description='...'),
    DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(
            champ_bringup_share_dir, 'rviz', 'default_view.rviz'),
        description='...'),
    DeclareLaunchArgument('spawn_spot', default_value='True'),
    DeclareLaunchArgument("urdf_file",
        default_value=os.path.join( get_package_share_directory('spot_description'), 'urdf/spot_military.urdf.xacro')),
    DeclareLaunchArgument("urdf_mapping",
        default_value="{'arm': 'True', 'add_ros2_control_tag': 'True', 'hardware_interface_type': 'gazebo', 'simulate_cameras': 'True', 'feet': 'True'}"),
    DeclareLaunchArgument("robot_base_link", default_value="body"),         
    DeclareLaunchArgument('start_quadruped_controller', default_value='True'),
#    DeclareLaunchArgument(
#      'world_file', default_value=os.path.join(
#            get_package_share_directory("champ_gazebo"), 'worlds/industrial_plant.sdf'))
#
#  ]
 
    DeclareLaunchArgument(
      'world_file', default_value=os.path.join(
            get_package_share_directory("champ_gazebo"), 'worlds/search_forest_world.sdf'))

  ] 
  
  use_simulator = LaunchConfiguration('use_simulator')
  use_sim_time = LaunchConfiguration('use_sim_time', default=True)
  use_rviz = LaunchConfiguration("use_rviz")
  tf_prefix = LaunchConfiguration('tf_prefix')
  rviz_config = LaunchConfiguration("rviz_config")
    
  # Gazebo setup
  champ_models_path = get_package_share_directory('champ_gazebo')
    
  sim_resource_path = os.pathsep.join(
            [
                environ.get("GZ_SIM_RESOURCE_PATH", default=""),
                os.path.join( champ_models_path, 'models' )
            ]
  )
  env_gz_sim = SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', sim_resource_path)


  # Start Gazebo
  gz_launch = IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
            launch_arguments = [
               ('gz_args', [
                   LaunchConfiguration("world_file"),
                   ' -r',
                   ' -v 4' 
               ])
            ],
            condition=IfCondition(use_simulator)
  )

  # Spawn Spot
  spawn_spot = IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('champ_bringup'), 'launch', 'spot_spawn.launch.py']),
            launch_arguments={'urdf_file': LaunchConfiguration("urdf_file"),
                      'urdf_mapping': LaunchConfiguration('urdf_mapping'),
                      'robot_base_link': LaunchConfiguration('robot_base_link'),
                      'x': LaunchConfiguration("x"), 
                      "y": LaunchConfiguration("y"),
                      "z": LaunchConfiguration("z"),
                      "roll": LaunchConfiguration("roll"),
                      "yaw": LaunchConfiguration("yaw"),
                      "start_quadruped_controller": LaunchConfiguration("start_quadruped_controller")                                            
                     }.items(),
            condition=IfCondition(LaunchConfiguration("spawn_spot"))
  )
      
  return LaunchDescription(
    launch_args + 
    [
      SetParameter(name='use_sim_time', value=True), 
      env_gz_sim,
      gz_launch,
      spawn_spot
    ])
