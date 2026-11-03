#!/usr/bin/env python3

# BSD 3-Clause License
#
# Copyright (c) 2025, Stan Baek
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Stan Baek
# Date Created: Feb 23, 2025

import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Bool
from visualization_msgs.msg import Marker


class LineFollower(Node):
    """
    A ROS2 node that follows a center line using odometry and a detected line.
    It calculates the robot's position relative to the line and adjusts its movement to stay aligned.
    """

    def __init__(self):
        super().__init__("line_follower")

        # Subscribe to IMU data to get the robot's current orientation
        self.imu_sub = self.create_subscription(Imu, "/imu", self.imu_callback, 10)

        # Subscribe to the ctrl relinquish topic to take control
        self.ctrl_sub = self.create_subscription(
            Bool, "/ctrl_relinq", self.ctrl_relinq_callback, 1
        )

        # TODO: Subscribe to the center line marker to get the detected line to follow
        # Create a subscriber that listens to the center line marker topic and calls 'self.follow_line'
        # when new data arrives. The topic name and message type should match the publisher in the wall detector.
        self.center_line_sub = 0  # Update this line to create the subscriber

        # Publish velocity commands to control the robot's movement
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        # Variables to store the robot's current orientation
        self.current_orientation = None

    def imu_callback(self, msg: Imu) -> None:
        """
        Callback function for IMU data.
        Updates the robot's current orientation using the quaternion data from the IMU.
        """
        self.current_orientation = msg.orientation

    def ctrl_relinq_callback(self, relinq_msg: Bool) -> None:
        """
        Callback function for handling control relinquishment messages.
        Updates the control status based on received messages.
        """

        # Update the has_control flag based on the received message
        self.has_control = relinq_msg.data

        # Log a message indicating whether control has been gained or lost
        if self.has_control:
            # Log a message indicating that control has been taken
            self.get_logger().info("line_follower has taken the control")
        else:
            # Log a message indicating that control has been lost
            self.get_logger().info("line_follwer has lost the control")

    def follow_line(self, center_line: Marker) -> None:
        """
        Callback function for the center line marker.
        Computes the robot's alignment with the line and adjusts its movement to follow it.
        """

        if not self.has_control:
            return

        if self.current_orientation is None:
            return  # Wait until we have IMU data

        # Extract the first and last points of the center line
        if len(center_line.points) < 2:
            return  # Not enough points to follow a line

        start_point = center_line.points[0]
        end_point = center_line.points[-1]

        # TODO: Compute the slope of the line and its angle relative to the x-axis.
        # The angle of the line relative to the x-axis is the arctangent of the slope.
        line_dx = 0  # Update this line to compute the change in x (x2 - x1)
        line_dy = 0  # Update this line to compute the change in y (y2 - y1)
        line_angle = 0  # Update this line to compute the angle of the line
        m = 0  # Update this line to compute the slope (m)
        k = 0  # Update this line to compute the y-intercept (k)

        # TODO: Convert the line equation y = mx + k into the standard form ax + by + c = 0
        # Here, a = -m, b = 1, c = -k
        a = 0  # Update this line to compute a
        b = 0  # Update this line to compute b
        c = 0  # Update this line to compute c

        # TODO: Compute the perpendicular distance (d) from the robot to the line
        # Note that the robot is at the origin (0, 0).
        distance_error = 0  # Update this line to compute the distance error

        # Convert quaternion to yaw angle (robot's current orientation)
        q = self.current_orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        robot_yaw = np.arctan2(siny_cosp, cosy_cosp)

        # TODO: Compute angular error to align with the center line
        angle_error = 0  # Update this line to compute the angle error

        # Normalize angle error to range [-pi, pi] to avoid large jumps
        angle_error = (angle_error + np.pi) % (2 * np.pi) - np.pi

        # TODO: Pick your controller gains
        kh = 0.0  # Heading controller gain (adjusts rotation based on angle error)
        kd = 0.0  # Distance controller gain (adjusts rotation based on distance error)

        # Adjust rotation speed based on angle error and distance error
        gamma = 0  # Update this line to compute gamma (rotation speed)

        # To see this message in real-time, run the node with the `--log-level DEBUG` argument:
        # ros2 run lab8_lidar wall_detector --log-level DEBUG
        self.get_logger().debug(
            f"distance error: {distance_error}, angle error: {angle_error}, gamma={gamma}"
        )

        # TODO: Publish the velocity command
        # The forward speed should be constant.


def main(args=None):
    """
    Main function to initialize and run the ROS2 node.
    """
    rclpy.init(args=args)
    line_follower = LineFollower()
    rclpy.spin(line_follower)  # Keep the node running
    line_follower.destroy_node()  # Clean up the node
    rclpy.shutdown()  # Shutdown ROS2


if __name__ == "__main__":
    main()
