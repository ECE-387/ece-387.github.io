from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('lab11_apriltag')
    config_dir = os.path.join(pkg_share, 'config')

    stop_detector_model = os.path.join(config_dir, 'stop_detector.svm')
    camera_info_path = os.path.join(config_dir, 'default_cam.yaml')
    camera_info_url = 'file://' + camera_info_path

    return LaunchDescription([
        Node(
            # TODO: Complete this function call

            arguments=['-d', stop_detector_model],
        ),
        Node(
            # TODO: Complete this function call


            parameters=[{
                'video_device': '/dev/video0',
                'framerate': 15.0,
                'camera_info_url': camera_info_url
            }]
        ),
        Node(
            # TODO: Complete this function call


            parameters=[{
                'camera_info_file': camera_info_path
            }]
        ),
    ])
