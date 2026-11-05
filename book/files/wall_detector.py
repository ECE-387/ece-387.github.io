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

import rclpy
from rclpy.node import Node
import numpy as np
from sensor_msgs.msg import LaserScan, Imu
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from sklearn.linear_model import RANSACRegressor
from sklearn.cluster import DBSCAN
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy

# Define a list of colors for visualization
Colors = [
    [1.0, 0.0, 0.0],  # Red
    [0.0, 1.0, 0.0],  # Green
    [0.0, 0.0, 1.0],  # Blue
    [1.0, 1.0, 0.0],  # Yellow
    [0.0, 1.0, 1.0],  # Cyan
    [1.0, 0.0, 1.0],  # Magenta
    [0.5, 0.5, 0.5],  # Gray
]


class WallDetector(Node):
    """
    A ROS2 node that detects walls using LiDAR data.
    It clusters LiDAR points, applies RANSAC to fit lines, and publishes detected walls and center lines.
    """
    def __init__(self):
        super().__init__('wall_detector')

        # Define a QoS profile that matches the publisher
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Match the publisher's reliability
            durability=QoSDurabilityPolicy.VOLATILE,        # Match the publisher's durability
            depth=10                                        # Set the queue size
        )

        # TODO: Subscribe to the LiDAR topic '/scan' to detect walls
        # Create a subscriber that listens to the '/scan' topic and calls 'self.scan_callback'
        # when new LiDAR data arrives. 
        self.scan_sub = 0  # Update this line to create the subscriber

        # Subscribe to IMU data to get the robot's current orientation
        self.imu_sub = self.create_subscription(Imu, '/imu', self.imu_callback, 10)

        self.yaw = 0  # Robot's current orientation (yaw angle)

        # Publisher for RViz visualization
        self.wall_marker_pub = self.create_publisher(Marker, 'wall_markers', 10)  # Publish detected walls
        
        # Publisher for line follower
        self.center_marker_pub = self.create_publisher(Marker, 'center_line', 10)  # Publish the center line
        
        self.get_logger().info("Wall Detector Node Started")

    def imu_callback(self, msg: Imu) -> None:
        """
        Callback function for IMU data to extract yaw (orientation of the robot).
        Converts the quaternion orientation to a yaw angle.
        """
        q = msg.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = np.arctan2(siny_cosp, cosy_cosp)

    def scan_callback(self, msg: LaserScan) -> None:
        """
        Callback function for LiDAR scan data.
        It processes the LiDAR points, applies clustering and RANSAC, and detects wall lines.
        """
        # Extract LiDAR scan angles and ranges
        angles = np.linspace(msg.angle_min, msg.angle_max, len(msg.ranges))

        # Create a boolean mask to filter points:
        # 1. Points in front of the robot (angles < pi/2 or angles > 3*pi/2)
        # 2. Points within the specified range (min_range <= r <= max_range)
        mask = ((angles < np.pi / 2) | (angles > 3 * np.pi / 2)) & \
            (np.array(msg.ranges) >= msg.range_min) & \
            (np.array(msg.ranges) <= msg.range_max)
                
        angles = angles[mask]
        r = np.array(msg.ranges)[mask]

        # TODO: Convert polar coordinates (angle, range) to Cartesian coordinates (x, y)
        x_vals = 0  # Update this line to compute x values
        y_vals = 0  # Update this line to compute y values

        # Stack x and y values into a 2D array representing points
        points = np.column_stack((x_vals, y_vals))

        # TODO: Cluster LiDAR points using DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
        # - eps: The maximum distance between two points for them to be considered as in the same neighborhood
        # - min_samples: The minimum number of points required to form a dense region (cluster)
        clustering = DBSCAN(eps=10, min_samples=2).fit(points)  # Update this line with appropriate parameters

        # Get unique cluster labels. The label -1 is used for noise points.
        unique_labels = set(clustering.labels_)

        # To see this message in real-time, run the node with the --log-level DEBUG argument:
        # ros2 run lab8_lidar wall_detector --log-level DEBUG
        self.get_logger().debug(f'unique labels: {unique_labels}')
                
        wall_lines = []  # Stores detected wall lines (slope, intercept)
        color_index = 0  # Index to cycle through colors for visualization
        wall_clusters = []  # Stores points belonging to detected walls

        for label in unique_labels:
            if label == -1:
                continue  # Ignore noise points (DBSCAN labels noise as -1)

            # Extract points belonging to the current cluster
            cluster_points = points[clustering.labels_ == label]
            
            # To see this message in real-time, run the node with the --log-level DEBUG argument:
            # ros2 run lab8_lidar wall_detector --log-level DEBUG
            self.get_logger().debug(f'label={label}, cluster size={len(cluster_points)}')
 
            # TODO: Skip clusters with too few points for reliable line fitting
            if len(cluster_points) < 1:  # Update this line with an appropriate threshold    
                continue

            # Visualize the cluster in RViz (blue color)
            self.publish_marker(cluster_points[:, 0], cluster_points[:, 1], self.wall_marker_pub, [0.0, 0.0, 1.0])

            # Use RANSAC to detect lines within the cluster
            remaining_points = cluster_points.copy()

            for _ in range(2):  # Try to find up to 2 walls in the cluster
                if len(remaining_points) < 12:  # Feel free to change this line as needed
                    break  # Not enough points left for line fitting

                # TODO: Initialize RANSAC for robust line fitting
                # - min_samples: The minimum number of points required to fit a line
                # - residual_threshold: The maximum distance (in meters) a point can be from the fitted line to be considered an inlier
                ransac = RANSACRegressor(min_samples=2, residual_threshold=0.5)  # Update this line with appropriate parameters

                # Fit the RANSAC model using the x-coordinates as input and y-coordinates as output
                ransac.fit(remaining_points[:, 0].reshape(-1, 1), remaining_points[:, 1])

                # Get the mask of inliers (points that fit the line)
                inliers = ransac.inlier_mask_
                if inliers is None or not any(inliers):
                    break  # No valid inliers found, exit the loop

                # At this point, RANSAC has successfully fitted a line, and we have valid inliers

                # Extract points that belong to the fitted line
                fitted_points = remaining_points[inliers]

                # Assign a color to the detected wall from the predefined list of colors
                color = Colors[color_index]
                # Increment the color index and wrap around if necessary to cycle through the list of colors
                color_index = (color_index + 1) % len(Colors)

                # TODO: Visualize the detected wall in RViz with a color from the predefined list of colors
                # Call self.publish_marker to publish the fitted points.
                                
                
                # Extract the slope and intercept of the fitted line
                slope = ransac.estimator_.coef_[0]
                intercept = ransac.estimator_.intercept_

                # To see this message in real-time, run the node with the --log-level DEBUG argument:
                # ros2 run lab8_lidar wall_detector --log-level DEBUG
                self.get_logger().debug(f'slope={slope}, intercept={intercept}')
 
                # Store the line parameters and corresponding points
                wall_lines.append((slope, intercept))
                wall_clusters.append(fitted_points)

                # Remove inliers for the next iteration to find additional lines
                remaining_points = remaining_points[~inliers]

        # To see this message in real-time, run the node with the --log-level DEBUG argument:
        # ros2 run lab8_lidar wall_detector --log-level DEBUG
        self.get_logger().debug(f'Detected walls: [{", ".join(f"({m:.3f}, {c:.3f})" for m, c in wall_lines)}]')

        # If at least 2 walls are detected, compute the center line
        if len(wall_lines) >= 2:
            # Sort walls by their alignment with the robot's orientation
            wall_lines.sort(key=lambda line: abs(np.arctan2(line[0], 1) - self.yaw))
            parallel_walls = wall_lines[:2]  # Select the two most parallel walls

            # Compute the midpoint between the two walls
            m1, c1 = parallel_walls[0]
            m2, c2 = parallel_walls[1]
            mid_c = (c1 + c2) / 2
            mid_m = (m1 + m2) / 2

            # Generate points for the center line
            mid_x = np.linspace(min(x_vals), max(x_vals), num=10)
            mid_y = mid_m * mid_x + mid_c

            # TODO: Visualize the center line in RViz (green color)
            # Call self.publish_marker to publish the center-line points.

    def publish_marker(self, x_vals, y_vals, publisher, color):
        """
        Helper function to publish a line marker in RViz.
        """
        marker = Marker()
        marker.header.frame_id = 'base_link'  # Reference frame for the marker
        marker.type = Marker.LINE_STRIP  # Type of marker (a line strip)
        marker.action = Marker.ADD
        marker.scale.x = 0.02  # Line width
        marker.color.r, marker.color.g, marker.color.b = color  # Line color
        marker.color.a = 1.0  # Line opacity
        marker.points = []

        # Add points to the line strip
        for x, y in zip(x_vals, y_vals):
            p = Point()
            p.x, p.y, p.z = x, y, 0.0
            marker.points.append(p)

        # Publish the marker
        publisher.publish(marker)


def main(args=None):
    """
    Main function to initialize and run the ROS2 node.
    """
    rclpy.init(args=args)
    detector = WallDetector()
    rclpy.spin(detector)
    detector.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
