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
# Date Created: Mar 10, 2025

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import numpy as np
import time


class MazeNavigator(Node):
    """
    A ROS 2 node for autonomously navigating a robot through a predefined set of waypoints.

    This class uses the Navigation2 (Nav2) stack to send navigation goals and handle the robot's
    movement. It is designed to follow a sequence of waypoints, forming a square path, and includes
    error handling for failed or canceled goals.
    """

    def __init__(self):
        """
        Initialize the MazeNavigator node.
        - Creates an action client for the NavigateToPose action.
        - Creates a publisher for setting the robot's initial pose.
        - Defines a list of waypoints to form a square path.
        - Publishes the initial pose and starts navigation.
        """

        super().__init__('maze_navigator')

        # TODO: Create an action client for the NavigateToPose action
        # Create a connection between your code (the "client") and an external action server named
        # 'navigate_to_pose' to send navigation requests (using NavigateToPose) to this server,
        # which can perform tasks moving a robot to a specific pose.
        self.client = 0

        # TODO: Initialize a publisher to broadcast the robot's initial pose with associated uncertainty.
        # This publisher uses the PoseWithCovarianceStamped message type and sends data on 
        # the /initialpose topic.
        # It is typically used to set the robot's starting position on the map.
        self.initial_pose_publisher = 0
        
        # Define waypoints (x, y, theta) to form a path in the maze
        # Each waypoint is a tuple of (x, y, theta), where:
        # - x, y: Position in meters.
        # - theta: Orientation in radians.
        self.waypoints = [
            (0.5, 0.0, 0.0),        # Move forward to (0.5, 0.0)
            (2.34, 0.0, np.pi/2),   # Move forward to (2.34, 0.0) and then turn 90 degree
            (2.34, 1.26, np.pi),    # Move to (2.34, 1.26) and then turn 90 degrees 
            (1.8, 1.26, -np.pi/2),  # Move to (1.8, 1.26) and then turn 90 degrees 
            (1.8, 0.54, np.pi),     # Move to (1.8, 0.54) and then Turn -90 degrees  
            (0.0, 0.54, -np.pi/2),  # Move to (0.0, 0.54) and then Turn 90 degrees
            (0.0, 0.0, 0.0),   # Move to (0.0, 0.0) and then Turn 90 degrees
        ]
        self.current_index = 0  # Tracks the current waypoint index

        # Publish the initial pose to set the robot's starting position
        self.publish_initial_pose()

        # Wait for the Nav2 action server to become available
        self.client.wait_for_server()
        self.get_logger().info('Nav2 server available, starting navigation...')

        # Send the first goal to start navigation
        self.send_next_goal()

    def publish_initial_pose(self):
        """
        Publish the initial pose of the robot.
        - This sets the robot's starting position on the map.
        - The initial pose is published to the `/initialpose` topic.
        """
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'  # Use the 'map' frame

        # Set initial pose (x, y, yaw)
        msg.pose.pose.position.x = 0.0  # Start at x = 0.0
        msg.pose.pose.position.y = 0.0  # Start at y = 0.0
        msg.pose.pose.orientation.z = 0.0  # sin(yaw/2) - facing forward
        msg.pose.pose.orientation.w = 1.0  # cos(yaw/2)

        # Set covariance (higher values = less confidence)
        # The covariance matrix represents uncertainty in the initial pose.
        msg.pose.covariance = [
            0.25, 0.0, 0.0, 0.0, 0.0, 0.0,  # Variance in x
            0.0, 0.25, 0.0, 0.0, 0.0, 0.0,  # Variance in y
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # Variance in z (not used in 2D)
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # Variance in roll, pitch, yaw
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.068  # Variance in yaw
        ]

        # TODO: Publish the initial pose
               
        
        self.get_logger().info('Initial pose published')

    def send_next_goal(self):
        """
        Send the next goal in the waypoints list to the Nav2 action server.
        - If there are more waypoints, send the next one.
        - If all waypoints are completed, log a message.
        """
        if self.current_index < len(self.waypoints):
            # Get the current waypoint (x, y, theta)
            x, y, theta = self.waypoints[self.current_index]

            # Create a goal message for the NavigateToPose action
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose.header.frame_id = 'map'  # Use the 'map' frame
            goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

            # Set the goal position and orientation
            goal_msg.pose.pose.position.x = x
            goal_msg.pose.pose.position.y = y
            goal_msg.pose.pose.orientation.z = np.sin(theta / 2)  # sin(yaw/2)
            goal_msg.pose.pose.orientation.w = np.cos(theta / 2)  # cos(yaw/2)

            # Log the goal being sent
            self.get_logger().info(f'Sending goal {self.current_index + 1}: ({x}, {y})')

            # TODO: Send the goal asynchronously and attach a callback for the response. 
            # The following lines ensure that the process of sending the goal and handling 
            # the server's response happens in a non-blocking (asynchronous) way.
            # This allows our program to continue running other tasks while waiting for 
            # the response from the action server. The callback function handles the response 
            # when it arrives, making the code efficient and responsive.
            # 1. Send the goal asynchronously to the action server through the action client 
            # to start the process of sending the goal and returns a "future" object (send_goal_future). 
            # A future represents a value that will be available later when the action server responds.
            send_goal_future = 0
            # 2. Attach a callback function to the future object, send_goal_future. 
            # The callback is triggered automatically once the future is "done" - when the action server 
            # responds to the goal request. The callback function (goal_response_callback) typically processes 
            # the server's response, such as confirming if the goal was accepted or rejected.
            # send_goal_future.add_done_callback(#callback function#)
        else:
            # All waypoints completed
            self.get_logger().info('Completed square path!')

    def goal_response_callback(self, future):
        """
        Callback for handling the response from the Nav2 action server.
        - Checks if the goal was accepted.
        - If accepted, waits for the result.
        """
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected')
            return

        self.get_logger().info('Goal accepted, waiting for result...')

        # Request the result of the goal asynchronously. It initiates the process to fetch 
        # the result but does not block the program while waiting for the result.
        result_future = goal_handle.get_result_async()
        
        # TODO: Attach a callback function (self.goal_result_callback) to the future object. 
        # The callback will be triggered automatically when the result becomes available.
        # The function goal_result_callback is typically responsible for processing the result, 
        # such as checking if the goal was successfully completed, retrieving the resulting data, 
        # or handling errors if they occurred.
        # result_future.add_done_callback(#callback function#)

    def goal_result_callback(self, future):
        """
        Callback for handling the result of the goal.
        - Checks the status of the goal (SUCCEEDED, CANCELED, FAILED).
        - Sends the next goal if the current one succeeded.
        - Retries the goal if it failed or was canceled.
        """
        result = future.result()

        # Check the status of the goal
        if result.status == 4:  # SUCCEEDED
            self.get_logger().info(f'Goal {self.current_index + 1} reached!')
            self.current_index += 1  # Move to the next waypoint
            time.sleep(1.0)  # Wait before sending the next goal
            self.send_next_goal()
        elif result.status == 2:  # CANCELED
            self.get_logger().warn('Goal canceled. Retrying...')
            time.sleep(1.0)  # Wait before retrying
            self.send_next_goal()
        elif result.status == 6:  # FAILED
            self.get_logger().warn('Goal failed. Retrying...')
            time.sleep(1.0)  # Wait before retrying
            self.send_next_goal()
        else:
            self.get_logger().warn(f'Unknown result status: {result.status}')
            time.sleep(1.0)  # Wait before retrying
            self.send_next_goal()


def main():
    """
    Main function to initialize and run the MazeNavigator node.
    """
    rclpy.init()
    node = MazeNavigator()
    try:
        rclpy.spin(node)  # Keep the node running
    except KeyboardInterrupt:
        pass  # Handle Ctrl+C gracefully
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()


