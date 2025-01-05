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
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.actions import RegisterEventHandler
from launch.actions import IncludeLaunchDescription
from launch.actions import ExecuteProcess
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import Command
from launch.substitutions import PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os
import xacro

# This will only take in effect if you are running in Simulation
os.environ['GAZEBO_MODEL_PATH'] = os.path.join(get_package_share_directory('champ_gazebo'),
                                               'models')


def generate_launch_description():

    # Get here directories of packages
    champ_bringup_share_dir = get_package_share_directory(
        'champ_bringup')
    champ_description_share_dir = get_package_share_directory(
        'champ_description')

    use_simulator = LaunchConfiguration('use_simulator')
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)
    use_rviz = LaunchConfiguration("use_rviz")
    tf_prefix = LaunchConfiguration('tf_prefix')
    rviz_config = LaunchConfiguration("rviz_config")
    champ_params = LaunchConfiguration('champ_params')

    declare_use_simulator = DeclareLaunchArgument(
        'use_simulator',
        default_value='True',
        description='whether to use Gazebo Simulation.')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='If true, use simulated clock')
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='whether or not to launch rviz')
    declare_tf_prefix = DeclareLaunchArgument(
        'tf_prefix',
        default_value='',
        description='...')
    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(
            champ_bringup_share_dir, 'rviz', 'default_view.rviz'),
        description='...')
    declare_champ_params = DeclareLaunchArgument(
        'champ_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'champ_params.yaml'),
        description='path to locks params.')

    # DECLARE THE msg relay ROS2 NODE
    declare_quadruped_controller_node = Node(
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

    # DECLARE THE msg relay ROS2 NODE
    declare_state_estimation_node = Node(
        package='champ_base',
        executable='state_estimation',
        # name='state_estimation',
        output='screen',
        # namespace='',
        parameters=[
            # {"use_sim_time": use_sim_time},
                    champ_params],
        remappings=[('cmd_vel', 'vox_nav/cmd_vel')]
        #prefix=['xterm -e gdb -ex run --args'],
    )

    #xacro_file_name = 'champ/champ.urdf.xacro'
    xacro_file_name = 'spot/spot.urdf.xacro'

    xacro_full_dir = os.path.join(
        champ_description_share_dir, 'urdf', xacro_file_name)

    print(xacro_full_dir)

    robot_description = xacro.process_file( 
       xacro_full_dir,
       mappings={"simulate_cameras": "True",
                 "visualize": "False"}).toprettyxml(indent="  ")

    declare_robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{"use_sim_time": use_sim_time},
                    {'robot_description': robot_description}],
        remappings=[('/tf', 'tf'),
                    ('/tf_static', 'tf_static')])

    # Spawn the robot in Ignition Gazebo
    declare_spawn_entity_to_gazebo_node = Node(
        package='ros_gz_sim',
        executable='create',
        condition=IfCondition(use_simulator),
        arguments=['-name', 'spot',
                   '-topic', '/robot_description', "-z", "0.84"],
        output='screen',
        parameters=[{"use_sim_time": use_sim_time}])

    # Start Ignition Gazebo
    # gazebo_world = os.path.join(get_package_share_directory('champ_gazebo'), 'worlds/', 'ground_plane.sdf')
    # declare_start_gazebo_cmd = ExecuteProcess(
    #     cmd=['ign', 'gazebo', gazebo_world],
    #     condition=IfCondition(PythonExpression([use_simulator])),
    #     output='screen')  


    #  INCLUDE RVIZ LAUNCH FILE IF use_rviz IS SET TO TRUE
    declare_rviz_launch_include = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(champ_bringup_share_dir,
                     'launch',
                     'rviz.launch.py')),
        condition=IfCondition(use_rviz),
        launch_arguments={
        'rviz_config': rviz_config
    }.items())

    localization_params = LaunchConfiguration('localization_params')
    declare_localization_params = DeclareLaunchArgument(
        'localization_params',
        default_value=os.path.join(
            champ_bringup_share_dir, 'config', 'robot_localization_params.yaml'),
        description='Path to the vox_nav parameters file.')

    base_to_footprint_ekf = Node(package='robot_localization',
                                 executable='ekf_node',
                                 name='base_to_footprint_ekf',
                                 output='screen',
                                 parameters=[localization_params],
                                 remappings=[('odometry/filtered', 'odometry/local')])

    footprint_to_odom_ekf = Node(package='robot_localization',
                                 executable='ekf_node',
                                 name='footprint_to_odom_ekf',
                                 output='screen',
                                 parameters=[localization_params],
                                 remappings=[('odometry/filtered', 'odom')])

    load_joint_state_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen'
    )

    load_joint_trajectory_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_trajectory_controller'],
        output='screen'
    )

    # added by diya 9/4
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )


    ground_plane_path=os.path.join(get_package_share_directory('champ_gazebo'), 'worlds', 'ground_plane.sdf')
    marsyard_path=os.path.join(get_package_share_directory('champ_gazebo'), 'worlds', 'marsyard2020.sdf')

    return LaunchDescription([
        bridge,
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [os.path.join(get_package_share_directory('ros_ign_gazebo'),
                              'launch', 'ign_gazebo.launch.py')]),
            launch_arguments=[('gz_args', [' -r -v 4 ', marsyard_path])]),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=declare_spawn_entity_to_gazebo_node,
                on_exit=[load_joint_state_controller],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_controller,
                on_exit=[load_joint_trajectory_controller],
            )
        ),
        declare_use_simulator,
        declare_use_rviz,
        declare_tf_prefix,
        declare_rviz_config,
        declare_champ_params,
        declare_quadruped_controller_node,
        declare_state_estimation_node,
        declare_robot_state_publisher_node,
        declare_rviz_launch_include,
        declare_spawn_entity_to_gazebo_node,
        declare_localization_params,
        footprint_to_odom_ekf,
        base_to_footprint_ekf,
        declare_use_sim_time,
        joint_state_publisher_gui  # added by diya 9/6
    ])
