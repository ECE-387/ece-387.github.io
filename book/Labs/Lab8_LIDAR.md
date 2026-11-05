# 🔬 Lab8: LiDAR

## 📌 Objectives
- Students should be able to implement a ROS2 node to detect walls using LiDAR data.
- Students should be able to visualize detected walls in RViz.
- Students should be able to test their implementation using Gazebo.
- Students should be able to use ROS2 launch files to manage multiple nodes efficiently.

## 📜 Overview

In this lab, we’ll enable our robot to detect and follow walls using LiDAR. While various sensors like cameras, sonar, and infrared can detect objects, we’ll focus on LiDAR due to its affordability and effectiveness.

The [Robotis LDS-01 LiDAR](https://www.robotis.us/360-laser-distance-sensor-lds-01-lidar/) is a 360-degree Laser Distance Sensor (LDS) that measures distances over 1,800 times per second. It has a range of 0.12m to 3.5m with an angular resolution of 1 degree and an accuracy of $\pm$0.015m for close distances, increasing to $\pm$5% beyond 0.5m.

```{image} ./figures/rplidar.png
:width: 300  
:align: center  
```

### 📹 How LiDAR Works
<center>
<iframe width="560" height="315" src="https://www.youtube.com/embed/EYbhNSUnIdU?si=idFVZOttywfaJ_Ys" title="YouTube video player" frameborder="0" allowfullscreen></iframe>
</center>

### 📹 TurtleBot3 LiDAR Example
<center>
<iframe width="560" height="315" src="https://www.youtube.com/embed/9oic8aT3wIc?si=nedLzJ4oj7beh2Xk" title="YouTube video player" frameborder="0" allowfullscreen></iframe>
</center>

## 🌱 Pre-Lab: Setting Up and Testing LiDAR

Before we dive into wall detection, we need to ensure that our setup is working correctly.

(Lidar:Launch)=
### Using ROS2 Launch Files

Managing multiple ROS nodes can become overwhelming, especially as our system grows. Instead of running each node in separate terminals, we’ll use ROS2 launch files to simplify the process.

1. **Navigate to Your Package**: Open a terminal and move to the `lab4_gamepad` package.
   ```bash
   cd ~/master_ws/src/ece387_ws/lab4_gamepad
   ```

2. **Create a Launch Directory**: Create a `launch` directory:

3. **Create a Launch File**: Inside the `launch` directory, create a new file named `gamepad.launch.py`:

4. **Open the File in VS Code**: Open the newly created file in your code editor.

5. **Copy and Paste the Following Code**:
   ```python
   import launch
   import launch_ros.actions

   def generate_launch_description():
       """
       Launches the gamepad node from lab4_gamepad
       and the joy_node from the joy package.
       """
       return launch.LaunchDescription([
           launch_ros.actions.Node(
               package='joy',
               executable='joy_node',
               name='joy_node',
               output='screen'
           ),
           launch_ros.actions.Node(
               package='lab4_gamepad',
               executable='gamepad',
               name='gamepad_node',
               output='screen'
           ),
       ])
   ```
6. **Modify `setup.py` to Include the Launch File**: Open `setup.py` and add:
   ```python
   import os
   from glob import glob
   ```
   Then, add this line inside `data_files`:
   ```python
   (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
   ```
7. **Update `package.xml`**: Ensure the dependencies include:
   ```xml
   <depend>launch</depend>
   <depend>launch_ros</depend>
   ```
8. **Build the Package**:
   ```bash
   ccbuild --packages-select lab4_gamepad
   ```
9. **Run the Launch File**:
   ```bash
   ros2 launch lab4_gamepad gamepad.1aunch.py
   ```
10. **Verify Nodes Are Running**:
    ```bash
    ros2 node list
    ```
    You should see `gamepad_node` and `joy_node` listed.

### Install Packages

1. Use the following command to install the `scikit-learn` machine learning package for Python:
    ```bash
    pip install scikit-learn
    ```

1. Download the [`square path Gazebo files`](../files/squarepath_gazebo.tar.xz). Extract the files and move them inside the appropriate directories in `~/master_ws/src/turtlebot3_simulations/turtlebot3_gazebo`. Ensure each new directory is moved to the existing directory with the same name.

1. Return to the ROS2 workspace root and build the package or simply run `ccbuild`.

1. Open the Gazebo simulation:
    ```bash
    ros2 launch turtlebot3_gazebo square_path.launch.py
    ```
    It will open the Gazebo simulation as shown in the figure below.
    ```{image} ./figures/Lab8_SquarePathGazebo.png
    :width: 500  
    :align: center  
    ```  

1. Type the following and observe the command output:
    ```bash
    ros2 topic list
    ros2 topic info /scan
    ros2 topic echo /scan
    ```  

1. Find the message type of the `/scan` topic:
    ```bash
    ros2 topic type /scan
    ```
    Then, examine the details of the message type.

1. Open the RViz visualization tool:
    ```bash
    ros2 launch turtlebot3_bringup rviz.launch.py
    ```
    This should open an RViz window where we can visualize ROS components of our system. In the `Displays` menu on the left, you should see two submenus of interest: `LaserScan` and `RobotModel`. These allow us to depict the TurtleBot3 and LiDAR data. You should see red dots fill the **rviz** map where obstacles exist, as shown below.
    ```{image} ./figures/Lab8_SquarePathRViz.png
    :width: 500  
    :align: center  
    ```  



## 💻 Lab Procedure: LiDAR-Based Wall Detection

Follow the steps below to set up your ROS 2 package, implement the required scripts, and run the simulation or real robot.

### Setting Up Your ROS2 Package

1. **Navigate to Your Workspace:** Open a terminal and move into your ROS 2 workspace directory:
   ```bash
   cd ~/master_ws/src/ece387_ws
   ```

1. **Create a New ROS2 Package:** Create a new package named `lab8_lidar` with the BSD-3 license:

1. **Add Dependencies:** Edit `package.xml` to include the following dependencies:
    ```xml
    <depend>rclpy</depend>
    <depend>sensor_msgs</depend>
    <depend>geometry_msgs</depend>
    <depend>nav2_msgs</depend>
    <depend>tf2_ros</depend>
    <depend>visualization_msgs</depend>
    <depend>numpy</depend>
    <depend>scikit-learn</depend>
    ```

3. **Download Required Scripts**: Download the following scripts and save them in the `lab8_lidar/lab8_lidar` directory:

   - [`wall_detector.py`](../files/wall_detector.py)
   - [`line_follower.py`](../files/line_follower.py)

1. **Modify `setup.py`**: Add your scripts under `entry_points`.

### Implementing the Python Scripts

1. **Complete `wall_detector.py`**  
   Open the `wall_detector.py` script and implement the missing functionality as described in the comments. This script will process LiDAR data to detect walls and publish visualization markers.

2. **Complete `line_follower.py`**  
   Open the `line_follower.py` script and implement the missing functionality as described in the comments. This script will enable the robot to follow the detected center line between walls.

3. **Build the Package**  
   After completing the scripts, build the package:
   ```bash
   ccbuild --packages-select lab8_lidar
   ```

### **Running the Simulation**

1. **Launch Gazebo with TurtleBot3** Start the Gazebo simulation with the TurtleBot3 robot:
   ```bash
   ros2 launch turtlebot3_gazebo square_path.launch.py
   ```

2. **Open RViz for Visualization** Launch RViz to visualize the detected walls and determine the center line:
   ```bash
   ros2 launch turtlebot3_bringup rviz.launch.py
   ```

3. **Run the Wall Detector Node**  Start the wall detection node:
   ```bash
   ros2 run lab8_lidar wall_detector
   ```

4. **Observe the Detected Walls in RViz**  
   - Unselect `TF` and `Odometry` in RViz.  
   - Click the `Add` button in the bottom left of the RViz window, select the `By topic` tab, and add the `Marker` messages under the `/center_line` and `/wall_markers` topics.

5. **Debug If Needed** If you encounter issues, run the wall detector node in debug mode:
   ```bash
   ros2 run lab8lidar wall_detector --ros-args --log-level debug
   ```

6. **Update Parameters** Adjust the parameters for the `DBSCAN` clustering function and the `RANSACRegressor` function to improve wall detection.

7. **Run the Line Follower Node** Once the center line is detected, start the line follower node:
   ```bash
   ros2 run lab8_lidar line_follower
   ```
   Ensure you also launch `gamepad.launch.py` to relinquish control. 

8. **Tune the Controller Gains**  
   Adjust the `kh` (heading gain) and `kd` (distance gain) values in the `line_follower.py` script to optimize the robot's line-following performance.

### Running the Real Robot

1. **Close the Gazebo Simulation** Ensure the Gazebo simulation is closed before running the real robot. Never run the simulation and the real robot simultaneously.

2. **Reopen RViz** Launch RViz to visualize the wall detection on the real robot:
   ```bash
   ros2 launch turtlebot3_bringup rviz.launch.py
   ```

3. **Run the Wall Detector Node** Start the wall detection node:
   ```bash
   ros2 run lab8lidar wall_detector
   ```

4. **Fix QoS Warning** If you see the following warning:
   ```bash
   [WARN] [wall_detector]: New publisher discovered on topic '/scan', offering incompatible QoS. No messages will be received from it. Last incompatible policy: RELIABILITY
   ```
   Investigate the warning and fix it using the `qos_profile` provided in the `wall_detector.py` script. You can use Google or ChatGPT to learn more about ROS 2 QoS (Quality of Service).

5. **Run the Line Follower Node** Start the line follower node:
   ```bash
   ros2 run lab8_lidar line_follower
   ```

6. **Demo the Robot** Demonstrate the robot following the walls in a straight path. **Ensure the robot starts 10 cm from the center line as shown below.**

<center>
<iframe width="560" height="315" src="https://www.youtube.com/embed/yf1iLbKwU3E?si=f9wdUHjrpu-KqkSU" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</center>


## 🚚 Deliverables

1. **[20 Points] Complete the `wall_detector.py` Script**
    - Ensure the script is fully functional and implements all required features.
    - Push your code to GitHub and confirm that it has been successfully uploaded.
    **NOTE:** _If the instructor can't find your code in your repository, you will receive a grade of 0 for the coding part._

2. **[15 Points] Complete the `line_follower.py` Script**
    - Ensure the script is fully functional and implements all required features.
    - Push your code to GitHub and confirm that it has been successfully uploaded.
    **NOTE:** _If the instructor can't find your code in your repository, you will receive a grade of 0 for the coding part._

3. **[15 Points] Demonstration**
    - Show the robot successfully move between two walls.