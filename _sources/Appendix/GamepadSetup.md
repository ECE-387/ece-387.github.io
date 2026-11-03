
# Gamepad Setup

## Purpose

Set up a Logitech Gamepad on the `Master` to work with ROS2 Humble on Ubuntu. This will allow you to use a Logitech Gamepad for controlling robots. Follow these steps to install dependencies, configure the gamepads, and test them in your ROS2 workspace.

```{image} ./figures/LogitechGamepad.png  
:width: 340  
:align: center  
```  

## **Steps**  

### 1. Install the `joy` Package  
(*Note: This package is already installed on the Master computer.*)  
The `joy` package in ROS2 is required to read inputs from gamepads. If needed, install it with the following commands:  
```bash  
sudo apt update  
sudo apt install ros-humble-joy  
```  

### 2. Install the `teleop_twist_joy` Package  
(*Note: This package is also pre-installed on the Master computer.*)  
If you plan to control a robot with the gamepad, install the `teleop_twist_joy` package:  
```bash  
sudo apt install ros-humble-teleop-twist-joy  
```  

### 3. Plug in Your Gamepads  
Connect your **Logitech Gamepad** to your computer via USB.  

### 4. Verify Gamepad Detection  
To ensure the gamepads are detected:  
1. Open a terminal and run:  
   ```bash  
   ls /dev/input/js*  
   ```  
2. You should see output like `js0`, `js1`, etc., corresponding to your connected gamepads.  

### 5. Install and Use the Joystick GUI Calibration Tool  
1. Install the joystick calibration tool:  
   (*Note: This package is already installed on the Master computer.*)  
   ```bash  
   sudo apt-get install jstest-gtk  
   ```  

   If it throws the following error
   ```bash
   Gtk-Message: 10:19:54.335: Failed to load module "canberra-gtk-module"
   ```

   run 
   ```
   sudo apt install libcanberra-gtk-module libcanberra-gtk3-module
   ```


2. Launch the calibration tool:  
   ```bash  
   jstest-gtk  
   ```  
   The following window should appear:
   ```{image} ./figures/LogitechGamepad_jstest-gtk.png  
   :width: 340  
   :align: center  
   ```  

3. Configure and inspect the joystick  
   - Double-click your gamepad to open its settings.  
   - Move the joysticks and press buttons to observe which axes and buttons correspond to the output values.  
   - If the joystick values do not return to zero in the neutral position, click the **Calibration** button and follow the on-screen instrution to calibrate the gamepad.  

   ```{image} ./figures/LogitechGamepad_jstest-gtk_axes.png  
   :width: 480  
   :align: center  
   ```  
4. The left stick should be mapped to `Axis 0` and `Axis 1`, and the right stick should be mapped to `Axis 3` and `Axis 4`. If this is not the case, press the `mode` button on the game.


### 6. Launch the `joy` Node  
The `joy` node reads input from your gamepads and publishes joystick data to ROS topics. To start the node, run:  
   ```bash  
   ros2 run joy joy_node  
   ```  

### 7. Test Joystick Output  
1. Check that the gamepad is working by echoing the `/joy` topic:  
   ```bash  
   ros2 topic echo /joy  
   ```  
2. Move the joysticks or press buttons on your gamepad. You should see data being published in the terminal.  

<!--

### Step 4: Configure Teleoperation (Optional)
If you want to use the gamepad to control a robot using teleoperation, follow these steps.

1. **Configure `teleop_twist_joy`**:
   Create a configuration file for `teleop_twist_joy`. The default configuration should be good, but you can adjust it to your needs. The configuration file typically looks like this:
   
   Create the file: `~/.ros/teleop_twist_joy.yaml` with the following contents:
   ```yaml
   joy_node:
     ros__parameters:
       device: "/dev/input/js0"  # Adjust the device based on your gamepad (e.g., js0 for the first gamepad)
   teleop_twist_joy:
     ros__parameters:
       axis_linear: 1  # Axis for linear movement (usually left joystick)
       axis_angular: 3  # Axis for angular movement (usually right joystick)
       button_forward: 4  # Button for moving forward
       button_backward: 5  # Button for moving backward
       button_left: 6  # Button for turning left
       button_right: 7  # Button for turning right
   ```

2. **Run the teleop node**:
   Launch the `teleop_twist_joy` node to control your robot via the gamepad:
   ```
   ros2 run teleop_twist_joy teleop_twist_joy_node --ros-args -p joy_node.device:=/dev/input/js0
   ```
   Replace `/dev/input/js0` with the correct device file if necessary.



### Step 6: Test Everything
1. **Control the robot (if applicable)**:
   If you're using `teleop_twist_joy` to control a robot, the gamepads should now send commands to move the robot.

2. **Check input from both gamepads**:
   If you’re using both gamepads to control different aspects of the robot, make sure both are publishing data correctly by echoing the topics.

### Troubleshooting:
- **Device not found**: If your gamepad isn't detected, check if the device file (`/dev/input/js0`, etc.) exists.
- **Buttons or axes not responding**: Adjust the button/axis mappings in the configuration YAML file (`teleop_twist_joy.yaml`).

### Conclusion:
You should now have both the Logitech and Xbox One gamepads working with ROS2 Humble on Ubuntu! You can either use them for teleoperation or just gather joystick data for further processing in your ROS2 nodes.

Let me know if you run into any issues!


-->