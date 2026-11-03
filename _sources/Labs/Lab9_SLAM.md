# 🔬 Lab9: SLAM


## 📌 Objectives

- Students should be able to implement a ROS2 node to detect walls using LiDAR data.
- This lab focuses on simulating autonomous exploration and navigation using SLAM in both Gazebo and real-world TurtleBot3 environments. You'll work with a prebuilt map and create new maps using Cartographer.


## 📜 Overview

In this project, we will enable our robot to autonomously navigate an unknown maze and build a map of the environment. As in the previous lab, we will use LiDAR to detect the walls of the maze (or obstacles) surrounding the robot. We will be utilizing the Simultaneous Localization and Mapping (SLAM) library provided by ROS2 and TurtleBot3.

SLAM, or Simultaneous Localization and Mapping, is a process used in robotics to enable a robot to build a map of an unknown environment while simultaneously determining its location within that map. It involves combining sensor data, algorithms, and probabilistic methods to perform real-time mapping and localization. SLAM is crucial for autonomous robots to operate effectively in environments where pre-existing maps are not available.

SLAM is one of the fundamental algorithms in robotics and is widely used in applications such as autonomous vehicles, drone navigation, and robotic vacuum cleaners. It enables robots to navigate dynamic and unfamiliar environments without relying on GPS or pre-defined maps, which is essential for many real-world scenarios.

SLAM integrates data from sensors like LiDAR and odometry to construct and update a map while estimating the robot's position. Through statistical methods like Kalman Filters or Particle Filters, SLAM corrects errors in localization and mapping to achieve accurate results. While the underlying mathematics involves advanced topics in statistics and optimization, libraries provided in ROS2 simplify SLAM's implementation, making it accessible for practical applications.

We will use Cartographer in this lab because it provides an efficient and accurate SLAM solution for 2D environments like the maze we’ll be mapping. Its ability to handle LiDAR data and update maps in real time makes it ideal for this project. Furthermore, its compatibility with TurtleBot3 and ROS2 simplifies the setup, allowing us to focus on understanding the SLAM process and its applications.

## 🌱 Pre-Lab: ROS2 Client Libraries  

The [ROS2 Intermediate Tutorials](https://docs.ros.org/en/humble/Tutorials/Intermediate.html) on `actions`  are a great starting point for learning about ROS2 action servers and clients.  

```{image} ./figures/Lab9_ROS2_ActionTutorials.png  
:width: 800  
:align: center  
```  
<br>  

Complete the following three tutorials. **Important:** Skip **C++** tutorials and focus only on the **Python** tutorials.  

1. **Managing Dependencies with rosdep**  
   - No need to install anything - your computer already has all the required packages set up.

1. **Creating an action**  
   - Make sure you’re working in the `ros2_ws` workspace. Avoid using the `master_ws` workspace for this one. 

1. **Writing an action server and client (Python)**  
   - As instructed at the end of this tutorial, run the action client.  When the feedback appears on the screen, capture a screenshot and upload it to Gradescope.


## 🛠️ Lab Procedures

### **1. Setting Up TurtleBot3 with SLAM in Gazebo**

Follow these steps to simulate SLAM with TurtleBot3 in the Gazebo environment.

1. Download the [`maze Gazebo files`](../files/maze.tar.xz). Extract the files and place them in the appropriate directories within `~/master_ws/src/turtlebot3_simulations/turtlebot3_gazebo`. Make sure to merge the new directories with the existing ones.

1. Run the following command to start the Gazebo simulation with the maze world:

    ```bash
    ros2 launch turtlebot3_gazebo maze.launch.py
    ```

    This will launch the Gazebo environment with the maze, as shown below:

    ```{image} ./figures/Proj1_GazeboInit.png
    :width: 400  
    :align: center  
    ```  

1. Open a new terminal and start the Cartographer SLAM process:

    ```bash
    ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true
    ```
    The use_sim_time:=true parameter ensures proper synchronization with the simulation clock.  Cartographer will begin building a map as you move the robot. The initial map will look like this:

    ```{image} ./figures/Proj1_CartographerInit.png
    :width: 400  
    :align: center  
    ```  

1. Use a gamepad to manually control the robot and navigate the maze. Run the following command to start the gamepad controller:

    ```bash
    ros2 launch lab4_gamepad gamepad.launch.py
    ```

    - Black pixels represent obstacles (walls).
    - Gray pixels indicate noise or uncertainty. As you complete multiple laps, the uncertainty decreases, and light gray pixels become darker.

    Once the map is complete, it should look like this:

    ```{image} ./figures/Proj1_CartographerDone.png
    :width: 400  
    :align: center  
    ```  

1. After mapping the maze, save the map using the following command:

    ```bash
    ros2 run nav2_map_server map_saver_cli -f ~/map
    ```

1. Confirm that two files, `map.yaml` and `map.pgm`, have been created in your home directory. Then view the contents of `map.yaml` using the `cat` command:

    ```bash
    cat map.yaml
    ```
    Example output:
    ```bash
    image: map.pgm
    mode: trinary
    resolution: 0.05
    origin: [-0.5, -0.7, 0]
    negate: 0
    occupied_thresh: 0.65
    free_thresh: 0.25
    ```
    - resolution: Each pixel represents 0.05 m x 0.05 m in the real world.
    - origin:  [-0.5, -0.7, 0] means the map starts at (-0.5 m, -0.7 m, 0 m) in the world frame
    - occupied_thresh: The occupancy grid values greater than 65 are considered "occupied"
    - free_thresh: The occupancy grid values less than 25 are considered "free space"
    

1. Download [`map_plotter.py`](../files/map_plotter.py) to your home directory. Then, make the script executable:

   ```bash
   chmod +x map_plotter.py
   ```

1. Verify the file permissions using `ls -l`.

   ```{important}
   If asked about the command to make a file executable only for the owner, you should know the answer for your GR. 😉
   ```

1. Complete the `TODO` section in `map_plotter.py`, and then run the script to generate the map.
1. Run the script to plot the map:

   ```bash
   ./map_plotter.py
   ```

1. Verify that the map dimensions match the actual maze. Each wall piece is **0.18 meters** long.

### **2. Navigation with SLAM**

Now, let’s set up **autonomous SLAM** using **Cartographer** and **Navigation2** to navigate the environment dynamically.

1. Start the TurtleBot3 simulation in the Gazebo world:

    ```bash
    ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
    ```

    The Gazebo environment will look like this:

    ```{image} ./figures/Lab9_GazeboWorld.png
    :width: 400  
    :align: center  
    ```  

1. Run Cartographer to begin building the map in real-time:

    ```bash
    ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true
    ```

    The initial map will appear as shown below:

    ```{image} ./figures/Lab9_CartographerInit.png
    :width: 400  
    :align: center  
    ```  

1. Run Navigation2 alongside Cartographer to allow the robot to navigate autonomously:

    ```bash
    ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true
    ```

    The RViz2 interface will look like this:

    ```{image} ./figures/Lab9_Nav2WorldInit.png
    :width: 400  
    :align: center  
    ```  

1. You can show or hide the `Global Costmap` and `Local Costmap` on RViz2 using the checkboxes on the  the `Display` sidebar:  

    ```{image} ./figures/Lab9_Nav2CostMap.png
    :width: 400  
    :align: center  
    ```  

1. Use the **2D Pose Estimate** tool in RViz2 to set the robot’s initial position:
   - Click on the map where the robot is located.
   - Drag the green arrow to match the robot’s orientation.

1. Use the **2D Nav Goal** tool to set navigation targets. The robot will autonomously explore the maze, updating the map dynamically as it moves.

    As the robot explores, the map will evolve, as shown below:

    ```{image} ./figures/Lab9_Nav2WorldInProgress.png
    :width: 400  
    :align: center  
    ```  

    The Gazebo simulation will reflect the robot’s progress:

    ```{image} ./figures/Lab9_GazeboWorldInProgress.png
    :width: 400  
    :align: center  
    ```  

1. Explore the entire world and create a map. Ensure you have dark gray obstacles.

1. Take a screenshot of the cartographer window by right clicking the title bar.  Submit the screenshot on Gradescope.


### **3. Autonomous Navigation with SLAM in Gazebo**

1. Create a package named `lab9_slam` with the `BSD-3-Clause` license and dependencies:
    - `rclpy`
    - `geometry_msgs`
    - `nav2_msgs`
    - `action_msgs`
    - `numpy`

    _Hint: There’s a way to include all dependencies at the time of package creation._

1. Download the [`navigate_maze.py`](../files/navigate_maze.py) script and save it in the appropriate folder within your package (You should know where this file should go by now).

1. Update the `setup.py` file by correctly adding the entry point for `navigate_maze.py`. This is necessary to ensure that the script runs as a node.

1. Open the `navigate_maze.py` script and fill in the `TODO` sections. Pay attention to:
    - Setting the target pose for the robot.
    - Utilizing the Nav2 action server/client.

1. Ensure you build the package correctly to make the script executable.

1. Start the TurtleBot3 simulation in Gazebo.
   ```bash
   ros2 launch turtlebot3_gazebo maze.launch.py
   ```

1. Launch Cartographer to enable SLAM
   ```bash
   ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true
   ```

1. Start Navigation2 for path planning and exploration.
   ```bash
   ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true
   ```

1. Finally, run the `navigate_maze.py` script to let the robot autonomously navigate the maze, building and updating a dynamic map.

    ```bash
    ros2 run lab9_slam navigate
    ```
    
    You may observe it take some time for the robot to get the correct orientation at a corner.  

    The output should be something similar to
    ```bash
    [INFO] [1742273732.645040148] [maze_navigator]: Initial pose published
    [INFO] [1742273733.398096942] [maze_navigator]: Nav2 server available, starting navigation...
    [INFO] [1742273733.399054077] [maze_navigator]: Sending goal 1: (0.5, 0.0)
    [INFO] [1742273733.401044101] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273737.764679146] [maze_navigator]: Goal 1 reached!
    [INFO] [1742273738.766196490] [maze_navigator]: Sending goal 2: (2.34, 0.0)
    [INFO] [1742273738.767399121] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273760.849179777] [maze_navigator]: Goal 2 reached!
    [INFO] [1742273761.851515638] [maze_navigator]: Sending goal 3: (2.34, 1.26)
    [INFO] [1742273761.853327625] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273771.914192259] [maze_navigator]: Goal 3 reached!
    [INFO] [1742273772.916137851] [maze_navigator]: Sending goal 4: (1.8, 1.26)
    [INFO] [1742273772.918236311] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273775.779635353] [maze_navigator]: Goal 4 reached!
    [INFO] [1742273776.780995770] [maze_navigator]: Sending goal 5: (1.8, 0.54)
    [INFO] [1742273776.783869671] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273796.064376706] [maze_navigator]: Goal 5 reached!
    [INFO] [1742273797.066189894] [maze_navigator]: Sending goal 6: (0.0, 0.54)
    [INFO] [1742273797.068158332] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273807.929930815] [maze_navigator]: Goal 6 reached!
    [INFO] [1742273808.931021374] [maze_navigator]: Sending goal 7: (0.0, 0.0)
    [INFO] [1742273808.933491318] [maze_navigator]: Goal accepted, waiting for result...
    [INFO] [1742273816.294277081] [maze_navigator]: Goal 7 reached!
    [INFO] [1742273817.295986020] [maze_navigator]: Completed navigating the maze!
    ```


### **4. Autonomous Navigation with Prebuilt Map in Gazebo**

Follow these steps to simulate autonomous navigation with **prebuilt map** in the Gazebo environment.

1. Launch the TurtleBot3 simulation in Gazebo.
   ```bash
   ros2 launch turtlebot3_gazebo maze.launch.py
   ```

1. For this part of the lab, we are working with a prebuilt map. Cartographer, which is used for real-time map creation, is not required here.


1. Run
    ```bash
    ros2 run tf2_ros tf2_echo1 map odom
    ```
    This command listens for the transform between the map frame and the odom frame and continuously prints the transformation (translation and rotation). It helps verify if the transform exists and provides real-time values. It will print something similar to
    ```bash
    At time 132.100000000
    - Translation: [-0.227, -0.274, -0.088]
    - Rotation: in Quaternion [-0.000, -0.003, 0.001, 1.000]
    - Rotation: in RPY (radian) [-0.000, -0.006, 0.002]
    - Rotation: in RPY (degree) [-0.006, -0.328, 0.131]
    ```
    It means
    - The map to odom transform was eventually found.
    - The robot’s odometry (odom) is offset from map by:
        - Position: (-0.227, -0.274, -0.088)
        - Orientation (rotation as quaternion & RPY)
    So, the map and odom frames are not identical and need a static transformation to be set correctly.

1. Publish a Static Transform Between Frames:
    ```bash
    $ ros2 run tf2_ros static_transform_publisher -0.227 -0.274 -0.088 0.0 0.0 0.0 map odom
    ```
    This command establishes a static relationship between the `map` and `odom` frames, assuming they are aligned without any offset. It's a prerequisite for linking the global (map) frame to the local (odom) frame in a robot's TF (Transform) tree. We set the orientation offset to zeros because they are techinicall all zeros.

1. Start the AMCL (Adaptive Monte Carlo Localization) node to localize the robot within the prebuilt map (map.yaml).
    ```bash
    ros2 run nav2_amcl amcl --ros-args -p use_sim_time:=true -p yaml_filename:=$HOME/map.yaml
    ```

1. Start the Navigation2 stack with the prebuilt map (`map.yaml`). Confirm that the robot can load and utilize the map effectively.

    ```bash
    ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true map:=$HOME/map.yaml 
    ```
    You should be able to find the prebuilt map. 

1. Run the SLAM exploration node:
    ```bash
    ros2 run lab9_slam navigate
    ```

1. **Reflect on Differences**: Compare the robot's performance with a prebuilt map to its performance when generating a map in real-time. Note any improvements or challenges.


### **5. (Optional) Autonomous Navigation with Cartographer (TurtleBot3, Real Environment)**

1. First, you need to ensure that the data and time on the robot match those on the master computer. 

    - Log on to the raspberry pi using SSH, and run
        ```bash
        date    
        ```
        Run the same command on the master. If they do not match, run the following command on the master:
        ```bash
        echo 'your_password' | ssh pi@192.168.4.1 "echo 'your_password' | sudo -S date -s \"$(date '+%Y-%m-%d %H:%M:%S')\""
        ```
        Ensure that 'your_password' should be replaced with your actual password. 
    - In case you have an error similar to
        ```bash
        sudo: unable to resolve host robot99: Temporary failure in name resolution
        ```
        Log on to the robot, and run
        ```bash
        sudo nano /etc/hosts
        ```
        Then, add the following line
        ```bash
        127.0.0.1   robotX        
        ```
        where `X` is your robot number.

    - Run the `date` command on the robot to verify that they match. Make sure the time zone also matches. If the robot's time zone is not MDT, change it by using
        ```bash
        sudo timedatectl set-timezone America/Denver
        ```

1. Start the `bringup` process to initialize the robot in a real environment.

1. Launch Cartographer to perform SLAM in real time and create a map.
    ```bash
    ros2 launch turtlebot3_cartographer cartographer.launch.py
    ```
    Ensure that `base-link`, `odom`, and `map` frames are displayed on the map. You also need to check there is no error or warnong on `TF` on the `Display` sidebar.

1. Start the Navigation2 stack to enable autonomous exploration and navigation.
    ```bash
    ros2 launch turtlebot3_navigation2 navigation2.launch.py
    ```

1. Execute the SLAM exploration node and observe the robot autonomously navigate its surroundings while dynamically updating its map.
    ```bash
    ros2 run lab9_slam navigate
    ```

### **6. (Optional) Autonomous Navigation with Prebuilt Map (TurtleBot3, Real Environment)**

1. Start the `bringup` process for the real TurtleBot3 environment.

2. Use AMCL and the prebuilt map for localization. Ensure you set a static transform between `map` and `odom`.

3. Start the Navigation2 stack with the prebuilt map, ensuring the robot can locate itself within the map.

4. Execute the SLAM exploration node. Observe and evaluate how the robot navigates with a prebuilt map.

5. **Analyze Performance**
   - Discuss and note differences in navigation performance between using a real-time generated map and a prebuilt map.

## 🚚 Deliverables

1. **[10 Points] Complete the `map_plotter.py` Script**
    - Ensure the script is fully functional and implements all required features.
    - Push your code to GitHub and confirm that it has been successfully uploaded.
    **NOTE:** _If the instructor can't find your code in your repository, you will receive a grade of 0 for the coding part._

1. **[10 Points] Complete the `navigate_maze.py` Script**
    - Ensure the script is fully functional and implements all required features.
    - Push your code to GitHub and confirm that it has been successfully uploaded.
    **NOTE:** _If the instructor can't find your code in your repository, you will receive a grade of 0 for the coding part._

1. **[10 Points] Submit Screenshots**
    - Submit the two screenshots on Gradescope

1. **[10 Points] Demonstration**
    - Show the robot successfully move between two walls in the simulation environment.

1. **[10 Points] Reflection and Analysis**
    - Provide your reflection and analysis on Gradescope

<!--
To determine the origins of the `map` and `odom` frames with respect to the world frame, you'll need to analyze the relationships in your robot's **TF (Transform) tree**. Here’s how you can do it:

---

### 1. **Visualize the TF Tree**
Use the TF visualization tools to observe the transform hierarchy:
   - Run the following in a terminal to visualize the TF tree:
     ```bash
     ros2 run tf2_tools view_frames
     ```
     This will generate a PDF (`frames.pdf`) showing the entire TF tree, including the origins of frames like `map` and `odom`.

   - Alternatively, in RViz2, add the **TF display** plugin to view the transform frames in real time and see how `map` and `odom` are positioned relative to each other and other frames.

---

### 2. **Query Specific Transforms**
To find the exact transform between `map` and `odom` (or any other frames), use the `tf2_echo` command:
   ```bash
   ros2 run tf2_ros tf2_echo map odom
   ```
   This will display the translation (x, y, z) and rotation (quaternion) values of the `odom` frame relative to the `map` frame. If you're looking for the relationship with a world frame, replace `map` or `odom` with the name of your world frame.

   - **Translation:** Gives you the position of the origin (in meters).
   - **Rotation:** Indicates orientation as a quaternion, which you can convert to roll, pitch, and yaw if needed.

---

### 3. **Check Static Transforms**
If static transforms are being used (like in your earlier command), the transformation values might already be predefined. You can inspect the parameters or commands to see the exact translation and rotation settings used when broadcasting those frames.

---

### 4. **Understand Frame Association**
- In most robot setups, the `map` frame is typically aligned with the global reference frame, representing a fixed coordinate system for localization.
- The `odom` frame, on the other hand, is aligned with the odometry system, which can drift over time. The transform between `map` and `odom` is often determined by the robot's localization system (e.g., AMCL, SLAM).

---

Let me know if you'd like guidance on any of these steps! I can also assist with debugging transforms or interpreting the output from `tf2_echo`.
-->