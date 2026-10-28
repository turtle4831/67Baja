import os
from datetime import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bag_dir = os.path.join(os.getcwd(), 'bags')
    os.makedirs(bag_dir, exist_ok=True)
    bag_path = os.path.join(bag_dir, datetime.now().strftime('dummy_%Y%m%d_%H%M%S'))

    return LaunchDescription([
        DeclareLaunchArgument('record', default_value='true'),
        Node(
            package='carros',
            executable='dummy_sensor',
            name='dummy_sensor',
            output='screen',
        ),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '--topics', '/sensors/dummy', '-o', bag_path],
            output='screen',
            condition=IfCondition(LaunchConfiguration('record')),
        ),
    ])
