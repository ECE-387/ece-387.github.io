# 🔬 Lab2: ROS

## 📌 Objectives

- Students should be able to configure and verify a ROS2 environment, including understanding how environment variables and workspace setup influence ROS behavior.
- Students should be able to interact with ROS2 command‑line tools, using nodes, topics, services, parameters, and actions to control and observe system behavior.
- Students should be able to visualize ROS computation graphs and system activity, using tools such as rqt_graph and rqt_console to interpret node interactions and debug runtime events.
- Students should be able to record and replay ROS2 data, creating bag files, managing directory structures, and validating recorded sensor or simulation data.

## 📜 ROS Introduction

The Robot Operating System (ROS) is a flexible framework for writing robot software. It is a collection of tools, libraries, and conventions that aim to simplify the task of creating complex and robust robot behavior across a wide variety of robotic platforms. ROS is sometimes called a meta operating system because it performs many functions of an operating system, but it requires a computer's operating system such as Linux.

Why? Because creating truly robust, general-purpose robot software is hard. From the robot's perspective, problems that seem trivial to humans often vary wildly between instances of tasks and environments. Dealing with these variations is so hard that no single individual, laboratory, or institution can hope to do it on their own.

As a result, ROS was built from the ground up to encourage collaborative robotics software development. For example, one laboratory might have experts in mapping indoor environments, and could contribute a world-class system for producing maps. Another group might have experts at using maps to navigate, and yet another group might have discovered a computer vision approach that works well for recognizing small objects in clutter. ROS was designed specifically for groups like these to collaborate and build upon each other's work, as is described throughout this site.

ROS 2 Jazzy Jalisco: <https://docs.ros.org/en/jazzy/>

## 💻 ROS Command-line tools

The tutorials at [Beginner: CLI Tools](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools.html) are an excellent introduction to ROS2 command‑line tools, but you must follow the lab instructions provided below as you complete them. Do not skip ahead or work through the tutorials on your own - each step in this lab depends on the guidance written [below](configuring-environment).



**Do not complete these tutorials independently.** Each step [below](configuring-environment) adds required, lab-specific instructions that are *not* in the official ROS2 tutorial - skipping them will cost you points on Gradescope. Expect 2–3 hours total.


```{warning}
Each numbered step below **modifies or overrides** the official tutorial instructions. Read the text under each tutorial link *before* running any commands. Following the official tutorial alone will cause you to misconfigure your environment or lose points on deliverables (e.g., Tutorial 1 tells you to *not* run the commands shown there).
```

```{image} ./figures/Lab2_ROS_Tutorials.png
:width: 800
:align: center
```

<br>

```{note}
Graded items in this lab: rqt_graph screenshot (Step 4), 3-turtle screenshot (Step 5), bag file in `lab2/bag_files` (Step 10). Read each step's instructions — the official tutorials alone won't produce a passing submission.
```

(configuring-environment)=
### 1. Configuring environment

```{important}
Do not run the commands in the official tutorial. Follow the steps below instead.
```

- For this firt tutorial, [Configuring Environment](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html), your environment has already been configured. Simply read through the page, but do **NOT** run any commands. Instead, open the `.bashrc` file by running the following commands:

    ```bash
    cd
    gedit .bashrc
    ```

- You should see the following lines at the bottom of the `.bashrc` file.

    ```bash
    # Source the ROS 2 Jazzy environment so ros2 commands are available
    source /opt/ros/jazzy/setup.bash

    # Source the student's own workspace if it has been built.
    # "2>/dev/null || true" suppresses the error if it doesn't exist yet.
    source ~/master_ws/install/setup.bash 2>/dev/null || true

    export TURTLEBOT3_MODEL=burger
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

    # colcon helpers
    source /usr/share/colcon_cd/function/colcon_cd.sh
    export _colcon_cd_root=/opt/ros/jazzy/
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

    # ROS_DOMAIN_ID separates ROS2 traffic between different robot pairs.
    # Each student should set this e.g.: export ROS_DOMAIN_ID=X
    # where X is the robot ID.
    export ROS_DOMAIN_ID=99
    export LDS_MODEL=LDS-02   # Replace with LDS-03 if using new LIDAR
    ```

    Your `ROS_DOMAIN_ID=X` should match your computer ID, where `X` corresponds to the `X` in `RobotX`. Update the file, save the changes, and exit. You can find your `LDS_MODEL` [here](../Appendix/RobotSetupJazzy.md#lds-configuration)

### 2. Using turtlesim, ros2, and rqt

- Do **not** install `rqt` and its plugins, as they are already installed.

### 3. Understanding nodes

- Complete this tutorial.

### 4. Understanding topics

- Try all the options for the checkboxes in `rqt_graph`.

    ```{image} ./figures/Lab2_rqt_graph.png
    :width: 720
    :align: center
    ```

    <br>

- Recreate the graph shown above and save it as a .png file. While the block locations might differ from the example, ensure your graph structure matches. Save the graph by clicking the `Save as image` button in the top-right corner and submit it on Gradescope.

    ```{note}
    Do NOT take pictures of your computer screen using your phone because (i) it can result in sampling aliasing, as explained in ECE215/ECE315, (ii) it will require more steps compared to a simple screen capture, and (iii) the resulting image will always be blurrier than a direct screen capture.
    ```

### 5. Understanding services

- Follow the instruction in this turtorial. At the end, spawn an additional turtle (so there are 3 turtles in total) near the center of the window. Right click on the title bar and select `Take Screenshot`.  You can also take a screenshot using the `Print Screen` key on your keyboard. Then, submit the screenshot on Gradescope.

    ```{image} ./figures/Lab2_Spawn3Turtles.png
    :width: 320
    :align: center
    ```

    <br>

    ```{Warning}
    You will receive a grade of -10 everytime you submit a picture of computer screen taken by your phone or mobile device. 
    ```

### 6. Understanding parameters

- Complete this tutorial.

### 7. Understanding actions

- Complete this tutorial.

### 8. Using rqt_console to view logs

- Complete this tutorial.

### 9. Launching nodes

- Complete this tutorial.

### 10. Recording and playing back data

- Create a directory called `lab2` within your local repository.  Then, create the `bag_files` directory inside the `lab2` directory.  As you follow the instruction in this tutorial, save the `subset` bag file in the `bag_files` directory.  Ensure the recording time is approimately 10 seconds. Push your code to your GitHub repository.

## 🚚 Deliverables

- Go to Gradescope and submit the `Lab2` assignment.
