
# Master Setup (ROS2 Humble)

This guide will walk through the steps to install Ubuntu Desktop 22.04 LTS, ROS2 Humble, and all dependencies on a desktop computer. This computer system is utilized in the United States Air Force Academy's Electrical and Computer Engineering department in an embedded network with the ground robot, a TurtleBot3 Burger. The master system is used to utilize ROS GUI tools and create secure connections with the TurtleBot3.

This guide is adapted from the [TurtleBot3 e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/#overview).

---

## Hardware

For our application, we are using [Intel NUC Kits](https://www.intel.com/content/www/us/en/products/details/nuc/kits.html) but these instructions will work on any AMD64 architecture.

## Software

### Ubuntu 22.04

For the desktop machine you will first need to download [Ubuntu Desktop 22.04 LTS](https://releases.ubuntu.com/jammy/).

Once downloaded, follow the instructions to create a [bootable Ubuntu USB stick](https://ubuntu.com/tutorials/create-a-usb-stick-on-ubuntu#1-overview) within Ubuntu. The guide provides links to create USB sticks from Windows and macOS as well.

Once the bootable USB stick is created, follow the guide to [Install Ubuntu desktop](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview) selecting a useful computer name such as `master0`. The NUC requires you to press and hold F10 on startup to boot from a USB stick.

### Update Alternatives

Python3 is installed in Ubuntu 22.04 by default. Some ROS packages utilize the `python` command instead of `python3` so we need to create a new executable, `/usr/bin/python` that will call Python3 (basically use the command `python` to call `Python3`):

```bash
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
```

After running this command, `/usr/bin/python` will point to `/usr/bin/python3` with a priority of 10, allowing us to set and manage different versions of Python easily.

### ROS2 Humble

At this point, the Ubuntu environment is setup. Now we will setup the ROS 2 requirements for the master. All of these instructions are adapted from the [ROS 2 Documentation: Humble](https://docs.ros.org/en/humble/Installation.html). ROS 2 Humble is the latest version of ROS 2 that supports Ubuntu 22.04 LTS (Jammy Jellyfish).

#### Installation

Follow [the official ROS2 documentation](https://docs.ros.org/en/humble/Installation.html) to install the ROS2 Humble.

- For most Linux users, [Debian package installation method](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) is strongly recommended.
- Install ``ros-humble-desktop``.

Install colcon:

```bash
sudo apt install python3-colcon-common-extensions
```

Install ROS dependencies for building packages:

```bash
sudo apt install -y ros-humble-gazebo-*
sudo apt install -y ros-humble-cartographer ros-humble-cartographer-ros
sudo apt install -y ros-humble-tf-transformations
sudo apt install -y ros-humble-usb-cam ros-humble-image-proc 
sudo apt install -y ros-humble-v4l2-camera 
sudo apt install -y ros-humble-camera-calibration
sudo apt install -y ros-humble-apriltag ros-humble-apriltag-ros libapriltag-dev
sudo apt install -y python3-pip
sudo apt install -y obs-studio qtwayland5
sudo apt install -y tree
sudo apt install -y ros-humble-cv-bridge
sudo apt install -y ros-humble-joy
sudo apt install -y ros-humble-teleop-twist-joy
sudo apt install -y jstest-gtk  
```

Install TurtleBot3 packages

```bash
source ~/.bashrc
sudo apt install ros-humble-dynamixel-sdk
sudo apt install ros-humble-turtlebot3-msgs
sudo apt install ros-humble-turtlebot3
```

Create a ROS workspace:

```bash
mkdir -p ~/master_ws/src
cd ~/master_ws/
```

#### TurtleBot3 Simulation Package

```bash
cd ~/master_ws/src/
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
cd ~/master_ws && colcon build --symlink-install
```

#### ROS Environment

Setup ROS environment variables and setup scripts within the `~/.bashrc` file. Open the `~/.bashrc` file with your favorite command line editor and add the following to the bottom:

```bash
source /opt/ros/humble/setup.bash
source ~/master_ws/install/setup.bash
source /usr/share/gazebo/setup.sh
source /usr/share/colcon_cd/function/colcon_cd.sh
export ROS_DOMAIN_ID=0  # For master0 and robot0
export _colcon_cd_root=/opt/ros/humble/
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01 # replace with LDS-02 if using new LIDAR
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
```

Any time you make changes to your `~/.bashrc` file you must source it:

```bash
source ~/.bashrc
```

### TP-Link AC600 Archer T2U Plus Driver

```{image} ./figures/tp-link-archer.jpg
:width: 380
:align: center
```

1. Ensure the wireless dual-band USB adapter is plugged in.

    ```bash
    $ lsusb 
    Bus 005 Device 002: ID 2357:0120 TP-Link 802.11ac WLAN Adapter
    ```

2. Install the driver with this commands:

    ```bash
    sudo apt install git dkms
    git clone https://github.com/aircrack-ng/rtl8812au.git
    cd rtl8812au
    sudo make dkms_install
    ```

    If you don't hace permission try to execute:

    ```bash
    chmod 777 rtl8812au
    ```

### PIP

For all users:

```bash
sudo pip install "pydantic<2"   # pip3 install pydantic 
sudo pip install dlib
sudo pip install imutils
sudo pip install pupil-apriltags
```

```{note}
The `dlib` package will take quite a while to install.
```

For each user:

```bash
sudo adduser $USER video
```

Then, reboot the system.
