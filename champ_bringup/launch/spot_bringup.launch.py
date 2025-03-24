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
    DeclareLaunchArgument(
        'champ_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'champ_params.yaml'),
        description='path to locks params.'),
    DeclareLaunchArgument(
        'localization_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'robot_localization_params.yaml'),
        description='Path to the vox_nav parameters file.')
  ]
  
  use_simulator = LaunchConfiguration('use_simulator')
  use_sim_time = LaunchConfiguration('use_sim_time', default=True)
  use_rviz = LaunchConfiguration("use_rviz")
  tf_prefix = LaunchConfiguration('tf_prefix')
  rviz_config = LaunchConfiguration("rviz_config")
  champ_params = LaunchConfiguration('champ_params')  
    
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
  ground_plane_sdf=PathJoinSubstitution([FindPackageShare('champ_gazebo'), 'worlds', 'ground_plane.sdf'])
  marsyard_sdf=PathJoinSubstitution([FindPackageShare('champ_gazebo'), 'worlds', 'marsyard2020.sdf'])
  gz_launch = IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
            launch_arguments = [
               ('gz_args', [
                   marsyard_sdf,
                   ' -r',
                   ' -v 4' 
               ])
            ],
            condition=IfCondition(use_simulator)
  )

  # Bridge
  bridge_config_file = os.path.join(
      champ_bringup_share_dir, 'config', "spot_bridge.yaml")

  bridge = Node(
      package='ros_gz_bridge',
      executable='parameter_bridge',
      parameters=[{'config_file': bridge_config_file}],
      #arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
      output='screen'
  )

  # Robot spawn/publisher
  xacro_full_dir = os.path.join(champ_description_share_dir, 'urdf', 'spot/spot.urdf.xacro') #'champ/champ.urdf.xacro'
  xacro_mappings = {'simulate_cameras': 'True', 'visualize': 'False'}
  #spot_description_share_dir = get_package_share_directory('spot_description')
  #xacro_full_dir = os.path.join(spot_description_share_dir, 'urdf', 'spot.urdf.xacro')
  #xacro_mappings={'arm': 'True', 'add_ros2_control_tag': 'True', 'hardware_interface_type': 'gazebo'}

  print(xacro_full_dir)

  robot_description = xacro.process_file( 
     xacro_full_dir,
     mappings=xacro_mappings).toprettyxml(indent="  ")

  robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{"use_sim_time": use_sim_time},
                    {'robot_description': robot_description}],
        remappings=[('/tf', 'tf'),
                    ('/tf_static', 'tf_static')],
        output='screen'
  )


  # Spawn the robot in Ignition Gazebo
  spawn_entity_to_gazebo_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'spot',
                   '-topic', '/robot_description', "-z", "0.0"], # 0.84
        parameters=[{"use_sim_time": use_sim_time}],
        output='screen',
        condition=IfCondition(use_simulator)        
  )

  load_joint_state_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        name="start_joint_state_broadcaster",
        output='screen'
  )


  load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
        name="start_joint_trajectory_controller",
        output='screen',
  )

  load_arm_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_trajectory_controller", "-c", "/controller_manager"],
        name="start_arm_trajectory_controller",
        output='screen',
  )

  quadruped_controller_node = Node(
        package='champ_base',
        executable='quadruped_controller',
        # name='quadruped_controller',
        output='screen',
        # namespace='',
        arguments=['--ros-args', '--log-level', 'INFO'],
        # prefix=['xterm -e gdb -ex run --args'],
        parameters=[
            # {"use_sim_time": use_sim_time},
                    champ_params],
        remappings=[('cmd_vel', 'vox_nav/cmd_vel')]
        )
    
  return LaunchDescription(
    launch_args + 
    [
      SetParameter(name='use_sim_time', value=True), 
      env_gz_sim,
      bridge,
      gz_launch,
      robot_state_publisher_node,
      spawn_entity_to_gazebo_node,      
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=spawn_entity_to_gazebo_node,
              on_exit=[load_joint_state_controller],
          )
      ),
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=load_joint_state_controller,
              on_exit=[load_joint_trajectory_controller, load_arm_trajectory_controller],
          )
      ),
      #quadruped_controller_node,
      #declare_state_estimation_node,
      #declare_rviz_launch_include,
      #declare_localization_params,
      #footprint_to_odom_ekf,
      #base_to_footprint_ekf,
      #broadcast_left_front_cam,
      #broadcast_right_front_cam
      #joint_state_publisher_gui  # added by diya 9/6
    ])
