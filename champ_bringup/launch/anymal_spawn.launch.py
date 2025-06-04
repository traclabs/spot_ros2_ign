from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, SetParameter
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, OpaqueFunction
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
import yaml

def evaluate_nodes(context, *args, **kwargs):

  urdf_path = LaunchConfiguration("urdf_file").perform(context)
  mapping_dict = LaunchConfiguration("urdf_mapping").perform(context)
  mapping_yaml = yaml.safe_load(mapping_dict) 

  robot_description = xacro.process_file( 
     urdf_path, mappings=mapping_yaml).toprettyxml(indent="  ")
  robot_description = xacro.process_file( 
     urdf_path).toprettyxml(indent="  ")

  robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {'robot_description': robot_description}],
        remappings=[('/tf', 'tf'),
                    ('/tf_static', 'tf_static')],
        output='screen'
  )
  
  return [robot_state_publisher_node]

##################################################################
def generate_launch_description():

  launch_args = [
    DeclareLaunchArgument("urdf_file",
        default_value=os.path.join( get_package_share_directory('champ_description'), 'urdf/military/anymal_military.urdf.xacro')),
    DeclareLaunchArgument("urdf_mapping",
        default_value="{'add_ros2_control_tag': 'True', 'hardware_interface_type': 'gazebo', 'feet': 'True'}"),
    DeclareLaunchArgument("robot_base_link", default_value="base"),
    DeclareLaunchArgument(
        'x',
        default_value='5.0',
        description='X at which to spawn Spot. 0.84 for ground plane, 0 for marsyard is good'),
    DeclareLaunchArgument(
        'y',
        default_value='0.0',
        description='y at which to spawn Spot.'), 
    DeclareLaunchArgument(
        'z',
        default_value='0.84',
        description='Height at which to spawn Spot.'), 
    DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Roll at which to spawn Spot.'),  
    DeclareLaunchArgument(
        'yaw',
        default_value='-0.5',
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
        'tf_prefix',
        default_value='',
        description='...'),
    DeclareLaunchArgument(
        'localization_params',
        default_value=os.path.join(
            get_package_share_directory('champ_bringup'), 'config', 'robot_localization_params.yaml'),
        description='Path to the vox_nav parameters file.'),
    DeclareLaunchArgument(
      'start_quadruped_controller', default_value='False')
  ]
  
  use_simulator = LaunchConfiguration('use_simulator')
  use_sim_time = LaunchConfiguration('use_sim_time', default=True)
  tf_prefix = LaunchConfiguration('tf_prefix')
    
  # Robot publisher
  nodes_eval = OpaqueFunction(function=evaluate_nodes)
    
  # Bridge
  bridge_config_file = os.path.join(get_package_share_directory('champ_bringup'), 'config', "anymal_bridge.yaml")

  bridge = Node(
      package='ros_gz_bridge',
      executable='parameter_bridge',
      parameters=[{'config_file': bridge_config_file}],
      output='screen'
  )

  # Spawn the robot in Ignition Gazebo
  spawn_entity_to_gazebo_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'anymal',
                   '-topic', '/robot_description',
                    "-x", LaunchConfiguration("x"),
                    "-y", LaunchConfiguration("y"),                     
                   "-z", LaunchConfiguration("z"),
                   "-R", LaunchConfiguration("roll"),
                   "-Y", LaunchConfiguration("yaw"),
                  ],
        parameters=[{"use_sim_time": use_sim_time}],
        output='screen',
        condition=IfCondition(use_simulator)        
  )
  
  # Fix up the robot's ground truth to publish w.r.t. world
  # by default it is published w.r.t. the world's name, rather than "world"
  ground_truth_node = Node(
        package="champ_gazebo",
        executable="republish_ground_truth",
        name="republish_ground_truth",
        output="screen",
        parameters=[{"robot_pose_topic": "/model/anymal/pose", "fixed_frame": "world", "robot_frame": LaunchConfiguration("robot_base_link")}]
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

  load_gripper_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_trajectory_controller", "-c", "/controller_manager"],
        name="start_gripper_trajectory_controller",
        output='screen',
  )


  odom_republish_node = Node(
        package='champ_gazebo',
        executable='helper_publish_base_pose',
        output='screen',
  )

  # Start quadruped controller
  launch_quadruped_controller = IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('champ_bringup'), 'launch', 'anymal_quadruped_controller.launch.py']),
            condition=IfCondition(LaunchConfiguration("start_quadruped_controller"))
  )
    
  return LaunchDescription(
    launch_args + 
    [
      SetParameter(name='use_sim_time', value=True), 
      nodes_eval,
      bridge,
      spawn_entity_to_gazebo_node,
      ground_truth_node,
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=spawn_entity_to_gazebo_node,
              on_exit=[load_joint_state_controller],
          )
      ),
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=load_joint_state_controller,
              on_exit=[load_joint_trajectory_controller],
          )
      ),
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=load_joint_trajectory_controller,
              on_exit=[launch_quadruped_controller],
          )
      ),
      odom_republish_node
    ])
