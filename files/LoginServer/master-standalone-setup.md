
# 🔧 Master Computer Setup — Standalone (No Login Server)

This guide walks through installing Ubuntu Desktop 24.04 LTS, ROS 2 Jazzy, and all dependencies on a standalone desktop computer with a single local Ubuntu account. This computer system is utilized in the United States Air Force Academy's Electrical and Computer Engineering department in an embedded network with the ground robot, a TurtleBot3 Burger. The master system is used to run ROS GUI tools and create secure connections with the TurtleBot3.

> Use this guide for a single master with a local Ubuntu account. If you are setting up the centralized multi-student lab (shared logins across many masters), see [login-server.md](login-server.md) and [login-client.md](login-client.md) instead.

This guide is adapted from the [TurtleBot3 e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/#overview).

---

## Hardware
For our application, we are using [Intel NUC Kits](https://www.intel.com/content/www/us/en/products/details/nuc/kits.html) but these instructions will work on any AMD64 architecture.


## Software

### Ubuntu 24.04
For the desktop machine you will first need to download [Ubuntu Desktop 24.04 LTS](https://releases.ubuntu.com/noble/).

Once downloaded, follow the instructions to create a [bootable Ubuntu USB stick](https://ubuntu.com/tutorials/create-a-usb-stick-on-ubuntu#1-overview) within Ubuntu. The guide provides links to create USB sticks from Windows and macOS as well.

Once the bootable USB stick is created, follow the guide to [Install Ubuntu desktop](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview) selecting a useful computer name such as `master0`. The NUC requires you to press and hold F10 on startup to boot from a USB stick.


### Update Alternatives
Python3 is installed in Ubuntu 24.04 by default. Some packages utilize the `python` command instead of `python3` so we need to create a new executable, `/usr/bin/python` that will call Python3 (basically use the command `python` to call `Python3`):

```bash
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
```
After running this command, `/usr/bin/python` will point to `/usr/bin/python3` with a priority of 10, allowing us to set and manage different versions of Python easily.


### ROS2 Jazzy

At this point, the Ubuntu environment is set up. Now we will install the ROS 2 requirements for the master. All of these instructions are adapted from the [ROS 2 Documentation: Jazzy](https://docs.ros.org/en/jazzy/Installation.html). ROS 2 Jazzy is the ROS 2 release that supports Ubuntu 24.04 LTS (Noble Numbat).

#### Installation

Follow [the official ROS2 documentation](https://docs.ros.org/en/jazzy/Installation.html) to install ROS2 Jazzy.
- For most Linux users, the [Debian package installation method](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html) is strongly recommended.
- Install `ros-jazzy-desktop`.

```bash
sudo apt install -y software-properties-common curl

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update
sudo apt install -y ros-jazzy-desktop
```

`ros-dev-tools` (installed below) already bundles `colcon`, `rosdep`, and `vcstool`, so a separate `python3-colcon-common-extensions` install is no longer needed on Jazzy.

Install ROS dependencies for building packages:

```bash
# Gazebo Classic is end-of-life and is not packaged for Jazzy. Jazzy pairs with
# Gazebo Harmonic, integrated through the ros_gz vendor packages.
sudo apt install -y ros-jazzy-ros-gz
# cartographer / cartographer-ros are NOT installed separately here — the
# turtlebot3 metapackage (below) already exec_depends on turtlebot3_cartographer,
# which pulls in cartographer_ros (and cartographer transitively) via apt.
sudo apt install -y ros-jazzy-tf-transformations
sudo apt install -y ros-jazzy-usb-cam ros-jazzy-image-proc
sudo apt install -y ros-jazzy-v4l2-camera
sudo apt install -y ros-jazzy-camera-calibration
sudo apt install -y ros-jazzy-apriltag ros-jazzy-apriltag-ros libapriltag-dev
sudo apt install -y python3-pip
sudo apt install -y obs-studio qtwayland5
sudo apt install -y tree
sudo apt install -y ros-jazzy-cv-bridge
sudo apt install -y ros-jazzy-joy
sudo apt install -y ros-jazzy-teleop-twist-joy
sudo apt install -y jstest-gtk
sudo apt install -y ros-dev-tools
```

Install TurtleBot3 packages:

```bash
source ~/.bashrc
sudo apt install -y ros-jazzy-dynamixel-sdk
sudo apt install -y ros-jazzy-turtlebot3-msgs
sudo apt install -y ros-jazzy-turtlebot3
```

Create a ROS workspace:

```bash
mkdir -p ~/master_ws/src
cd ~/master_ws/
```

#### TurtleBot3 Simulation Package

```bash
cd ~/master_ws/src/
git clone -b jazzy https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
cd ~/master_ws && colcon build --symlink-install
```

#### ROS Environment

Set up ROS environment variables and setup scripts within the `~/.bashrc` file. Open the `~/.bashrc` file with your favorite command line editor and add the following to the bottom:

```bash
source /opt/ros/jazzy/setup.bash
source ~/master_ws/install/setup.bash
source /usr/share/colcon_cd/function/colcon_cd.sh
export ROS_DOMAIN_ID=0  # For master0 and robot0
export _colcon_cd_root=/opt/ros/jazzy/
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01 # replace with LDS-02 if using new LIDAR
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
```

> The old `source /usr/share/gazebo/setup.sh` line from Gazebo Classic is no longer needed — Gazebo Harmonic is sourced automatically through the `ros_gz` packages installed above.

Any time you make changes to your `~/.bashrc` file you must source it:

```bash
source ~/.bashrc
```

### TP-Link AC600 Archer T2U Plus Driver

```{image} ./figures/tp-link-archer.jpg
:width: 380
:align: center
```

> **Check before installing.** The Archer T2U Plus line has shipped with different Realtek chipsets across hardware revisions (RTL8812AU or RTL8821AU), and RTL8812AU only recently gained proper in-kernel support (via the `rtw88` driver, merged around Linux 6.14). Ubuntu 24.04 LTS ships kernel 6.8 by default — whether your install already has a new enough kernel depends on which HWE point-release kernel it has picked up. Rather than assume, check first: if the adapter already works out of the box, skip the driver build below.

1. Plug in the wireless dual-band USB adapter and identify the chipset:

    ```bash
    $ lsusb
    Bus 005 Device 002: ID 2357:0120 TP-Link 802.11ac WLAN Adapter
    ```

2. Check whether Ubuntu already recognizes it as a wireless interface before installing anything:

    ```bash
    $ uname -r          # confirm your running kernel version
    $ nmcli device status
    ```

    If a new `wlx...` (or similar) device shows up as available/connected, the in-kernel driver already covers your chipset — **skip step 3.**

3. If the adapter is not detected, build and install the out-of-tree driver:
    ```bash
    $ sudo apt install git dkms
    $ git clone https://github.com/aircrack-ng/rtl8812au.git
    $ cd rtl8812au
    $ sudo make dkms_install
    ```

    If you don't have permission try to execute:
    ```bash
    $ chmod 777 rtl8812au
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
