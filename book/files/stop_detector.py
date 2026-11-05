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
# Date Created: Mar 21, 2025

# This script implements a ROS2 node for detecting stop signs in images using dlib's object detector.

import rclpy  # ROS2 Python client library
from rclpy.node import Node  # Base class for ROS2 nodes
import argparse  # Library for parsing command-line arguments
from pathlib import Path  # Helps manage file paths
import cv2  # OpenCV library for image processing
import dlib  # dlib for object detection
from cv_bridge import CvBridge  # Converts ROS image messages to OpenCV format
from sensor_msgs.msg import Image  # ROS message type for images
from std_msgs.msg import Float32


class StopDetector(Node):
    """
    ROS2 Node for detecting stop signs in real-time images using a trained detector.
    """

    FOCAL = 1
    STOP_WIDTH = 1

    def __init__(self, detector_loc):
        super().__init__("stop_detector")  # Initializes the ROS2 node with the name "stop_detector"

        self.ctrl_c = False  # Flag to track shutdown state
        self.bridge = CvBridge()  # Handles conversion between ROS Image messages and OpenCV format
        self.stop_dist = Float32()
        
        # Load the stop sign detector model from the given file path
        self.detector = dlib.simple_object_detector(detector_loc)
        self.get_logger().info(f"Loaded detector from: {detector_loc}")

        # TODO: Subscribe to the image topic where the camera publishes frames



        self.declare_parameter("detector", "")  # Declares a ROS2 parameter (can be used for detector config)
        self.get_logger().info("Stop detector node ready")
                

    def camera_callback(self, msg):
        """
        Callback function triggered whenever a new image message is received from the topic.
        It detects stop signs and visually marks them.
        """
        if self.ctrl_c:
            return  # If the node is shutting down, stop further processing

        try:
            # Convert the incoming ROS2 Image message to an OpenCV format (BGR color space)
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            # Run the stop sign detector on the image
            detections = self.detector(cv_image)

            # TODO: Loop through each detection and draw bounding boxes
            for detection in detections:
                l, t, r, b = detection.left(), detection.top(), detection.right(), detection.bottom()
                
                # TODO: Draw a red rectangle around the detected stop sign
                
                
                # TODO: Label the detection with "STOP"

                
            # TODO: Display the processed image in a window


            
        except Exception as e:
            self.get_logger().error(f"Error processing image: {str(e)}")  # Log errors if image processing fails

    def shutdownhook(self):
        """
        Gracefully handles shutdown by closing OpenCV windows.
        """
        self.get_logger().info("Shutting down")
        self.ctrl_c = True  # Sets shutdown flag to True
        cv2.destroyAllWindows()  # Closes all OpenCV windows


def main(args=None):
    """
    Main function to initialize and run the StopDetector node.
    """
    rclpy.init(args=args)  # Initialize ROS2 Python interface

    # Set up argument parsing to allow specifying a detector model via command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--detector", required=True, help="Path to the trained HOG detector file")
    args, _ = parser.parse_known_args()  # Parse command-line arguments

    stop_detector = StopDetector(args.detector)  # Create an instance of the StopDetector node

    try:
        rclpy.spin(stop_detector)  # Keep the node running until manually stopped
    except KeyboardInterrupt:
        pass  # Allow graceful shutdown on Ctrl+C
    finally:
        stop_detector.shutdownhook()  # Call shutdown cleanup function
        stop_detector.destroy_node()  # Cleanup ROS2 node resources
        rclpy.shutdown()  # Shutdown ROS2 system


if __name__ == "__main__":
    main()  # Entry point of the script