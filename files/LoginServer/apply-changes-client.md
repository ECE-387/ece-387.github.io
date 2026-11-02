# Applying Changes — Existing Master (Client)

Brings an already-built master in line with the current [login-client.md](login-client.md). Run **after** the server guide, since Step 1 depends on the `root_squash` change having been applied there.

**Time:** about 30 minutes, plus a 30–60 minute `dlib` compile on one machine only.

Log in locally as `ece387admin`. Several steps touch networking, so do them at the console rather than over SSH — an SSH session riding the interface you are reconfiguring will drop mid-command.

---

## Step 0 — Back up

```bash
BK=/root/pre-migration-$(date +%F); sudo mkdir -p "$BK"
sudo cp /etc/sssd/sssd.conf "$BK/"
sudo cp /etc/auto.students "$BK/" 2>/dev/null
sudo cp /etc/sudoers.d/ece387-students "$BK/" 2>/dev/null
sudo cp -r /etc/netplan "$BK/netplan"
nmcli connection show > "$BK/nmcli-connections.txt" 2>/dev/null
sudo ls -la "$BK"
```

---

## Step 1 — Pick up `root_squash`

The server now refuses root access from clients. Clear any cached mount state:

```bash
sudo systemctl restart autofs
```

Verify — the first must fail, the second must succeed:

```bash
sudo ls /home/students/a27-t02          # expect: Permission denied
sudo su - a27-m0 -c 'touch ~/t && ls ~/t && rm ~/t'   # expect: success
```

If the first still lists files, the server-side `exportfs -rav` did not take. Go back and check `sudo exportfs -v` there.

---

## Step 2 — Add `offline_credentials_expiration`

Without this, cached credentials expire and students cannot log in during an outage even on a machine they have used before.

```bash
sudo nano /etc/sssd/sssd.conf
```

Under `[domain/ece387.local]`, confirm `cache_credentials = true` is present and add below it:

```ini
# Cached credentials never expire (0 = no limit)
offline_credentials_expiration = 0
```

```bash
sudo chmod 600 /etc/sssd/sssd.conf
sudo systemctl restart sssd
id a27-m0                                # expect uid=20000(a27-m0) gid=10000(...)
```

---

## Step 3 — Verify the NFS mount options

```bash
cat /etc/auto.students
```

Should read:

```
*  -fstype=nfs,soft,timeo=30,retrans=2  10.99.1.50:/home/students/&
```

If it says `hard`, or omits `timeo`/`retrans`, edit it to match and `sudo systemctl restart autofs`. A `hard` mount freezes terminals indefinitely when the server is unreachable; `soft` returns an error after about six seconds instead.

---

## Step 4 — Create the rescue account

New in the current guide. This is the fallback when the login server or lab network is down, and the only practical way to debug a hung NFS mount without your own shell living on that mount.

```bash
sudo adduser ece387rescue
sudo usermod -aG dialout,video,plugdev ece387rescue
```

Use a password **different from `ece387admin`** — students will know this one.

```bash
sudo tee -a /home/ece387rescue/.bashrc > /dev/null << 'EOF'

# ECE 387 rescue environment
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-02
export ROS_DOMAIN_ID=99
alias ssh_robot='ssh pi@192.168.50.1'
EOF
```

Verify it works with the network down — this is the whole point of the account:

```bash
# Unplug Ethernet / turn off WiFi first
su - ece387rescue
echo $HOME        # expect /home/ece387rescue
ls -la            # local files present
exit
```

`/home/ece387rescue` sits outside `/home/students`, so autofs never touches it.

---

## Step 4b — Tighten the sudo whitelist

The whitelist you installed originally permits `apt`, `pip`, `systemctl`, `rosdep`, `colcon`, `nmcli`, and `ip`.

**Package management stays** — students installing their own libraries is part of the course. The other four come off: `systemctl edit` opens `$EDITOR` as root, `sudo ip netns exec x /bin/bash` is a documented root shell, `rosdep` just calls apt (already permitted), and `sudo colcon build` needs no privilege while leaving root-owned files in the student's NFS home that they cannot delete.

Check what is currently permitted:

```bash
sudo cat /etc/sudoers.d/ece387-students
sudo -l -U a27-m0
```

Replace it with the version from [login-client.md §1.6](login-client.md), which is now the single definition. The short form:

```bash
sudo cp /etc/sudoers.d/ece387-students /root/pre-migration-$(date +%F)/
sudo tee /etc/sudoers.d/ece387-students > /dev/null << 'EOF'
# ECE387 student sudo permissions

# Package management — students install their own libraries during labs.
Cmnd_Alias ECE387_PKG = /usr/bin/apt, /usr/bin/apt-get, /usr/bin/dpkg, \
                        /usr/bin/pip, /usr/bin/pip3

# Power — Lab 1 teaches sudo shutdown and sudo reboot.
Cmnd_Alias ECE387_PWR = /usr/sbin/shutdown, /usr/sbin/reboot

%ece387students ALL=(ALL) NOPASSWD: ECE387_PKG, ECE387_PWR
EOF

sudo chmod 440 /etc/sudoers.d/ece387-students
sudo visudo -c -f /etc/sudoers.d/ece387-students
sudo -l -U a27-m0
```

> Because `apt` and `pip` remain, students retain a path to root. Any host-level restriction — immutable files, hosts-file blocking — is a deterrent rather than a control, which is why the audit logging in [genai-blocking.md §7](genai-blocking.md) matters more than the blocking itself.

Teach `pip install --user --break-system-packages <package>` as the default for Python. It needs no sudo, installs into the student's NFS home so it follows them between benches, and cannot break the machine for the next student.

### Replace what you removed

Hardware access is a permissions problem, not a privilege problem. These make sudo unnecessary rather than merely unavailable:

```bash
sudo tee /etc/udev/rules.d/99-ece387.rules > /dev/null << 'EOF'
# OpenCR / Dynamixel controller — verify idVendor with lsusb on your hardware
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", MODE="0666"
# USB cameras
KERNEL=="video[0-9]*", MODE="0666"
EOF

sudo udevadm control --reload
sudo udevadm trigger
```

`dmesg` is root-only on Ubuntu and students need it for USB debugging:

```bash
echo "kernel.dmesg_restrict=0" | sudo tee /etc/sysctl.d/61-dmesg.conf
sudo sysctl -p /etc/sysctl.d/61-dmesg.conf
```

Verify as a student before moving on:

```bash
sudo su - a27-m0 -c 'ls -l /dev/ttyACM0 /dev/video0 2>/dev/null; dmesg | tail -3'
```

Device modes should be `crw-rw-rw-` and `dmesg` should produce output without sudo.

### Find out what students actually need

If you are unsure whether removing something will break a lab, log real usage for a week before committing:

```bash
echo 'Defaults log_input, log_output' | sudo tee /etc/sudoers.d/00-logging
sudo chmod 440 /etc/sudoers.d/00-logging
sudo journalctl -t sudo | grep COMMAND
```

Anything appearing repeatedly probably belongs in the machine image rather than the whitelist.

---

## Step 5 — Install the missing packages

Earlier versions of the guide had a shorter list, and one section installed `ros-humble-*` packages that do not exist on Jazzy. Check whether any got installed:

```bash
dpkg -l | grep ros-humble
```

If anything appears, remove it — those are stale and cannot work here:

```bash
sudo apt remove --purge -y 'ros-humble-*'
sudo apt autoremove -y
```

Install the current set. Already-present packages are skipped, so this is safe to run as-is:

```bash
sudo apt install -y ros-jazzy-desktop ros-jazzy-turtlebot3* ros-dev-tools
sudo apt install -y ros-jazzy-ros-gz
sudo apt install -y ros-jazzy-dynamixel-sdk ros-jazzy-tf-transformations
sudo apt install -y ros-jazzy-usb-cam ros-jazzy-image-proc \
                    ros-jazzy-v4l2-camera ros-jazzy-cv-bridge \
                    ros-jazzy-camera-calibration \
                    ros-jazzy-apriltag ros-jazzy-apriltag-ros libapriltag-dev
sudo apt install -y ros-jazzy-joy ros-jazzy-teleop-twist-joy jstest-gtk
sudo apt install -y tree terminator python3-pip obs-studio qtwayland5
```

This list must match [MasterSetupJazzy.md](MasterSetupJazzy.md). A package present on one master and missing on another produces a lab that works at one bench and fails at the next — the hardest kind of problem to diagnose during class.

---

## Step 6 — Python packages and the dlib wheel

```bash
sudo pip install --break-system-packages "pydantic<2"
sudo pip install --break-system-packages imutils
sudo pip install --break-system-packages pupil-apriltags
```

`--break-system-packages` is required because Ubuntu 24.04 blocks pip from writing to the system Python. That protection exists so pip cannot break other apt-managed applications; a master runs ROS 2 and nothing else and is re-imaged rather than repaired, so it does not apply here.

**dlib — build the wheel once, on this machine only:**

```bash
sudo apt install -y build-essential cmake python3-dev
pip install --break-system-packages wheel
pip download dlib
python3 -m pip wheel dlib-*.tar.gz          # 30-60 minutes
```

Store it on the server so the other 13 masters and any future re-image can install in seconds:

```bash
scp dlib-*-linux_x86_64.whl ece387admin@ece387server:/srv/ece387/wheels/x86_64/
sudo pip install --break-system-packages ./dlib-*.whl
python3 -c "import dlib; print(dlib.__version__)"
```

**On every other master**, skip the compile entirely:

```bash
scp ece387admin@ece387server:/srv/ece387/wheels/x86_64/dlib-*.whl ~/
sudo pip install --break-system-packages ~/dlib-*.whl
```

> Do not use a wheel built on a robot. It is tagged `linux_aarch64` and will not install here.

---

## Step 7 — Fix the network configuration

Earlier guidance used different interface names and a different robot address. The current layout:

| Interface | Connects to | Carries |
|---|---|---|
| Ethernet, or USB dongle as `wlan1` | `ECE387` | LDAP, NFS, internet |
| `wlo1` (onboard) | robot AP `robotX` | ROS 2 |

```bash
ip addr
nmcli connection show
```

**If this bench has Ethernet** (Topology A), it needs no netplan config — NetworkManager handles wired DHCP. Prefer it over WiFi:

```bash
nmcli connection modify "Wired connection 1" ipv4.route-metric 50
nmcli connection up "Wired connection 1"
```

Remove any old dongle netplan config so it cannot fight the wired link:

```bash
sudo nano /etc/netplan/50-cloud-init.yaml     # delete stale wifis: blocks
sudo netplan apply
```

**If this bench has no Ethernet** (Topology B), follow §1.7 Option B of login-client.md to rename the dongle to `wlan1` and configure `ECE387`.

**Remove any stale robot profile.** Old guidance used `10.42.0.1`, user `ubuntu`, and interface `wlan0`:

```bash
nmcli connection show
nmcli connection delete "<old robot profile name>"     # if one exists
```

Students now create the robot connection themselves through the GUI. Nothing to pre-configure.

---

## Step 8 — Verify the robot link does not hijack the default route

Do this once with a robot powered on, before students touch it.

Connect to `robotX` from the network menu, then:

```bash
ping -c 3 192.168.50.1     # robot reachable
ping -c 3 10.99.1.50       # lab network STILL reachable
ip route | grep default
```

The default route must be via `10.99.1.1` on Ethernet or `wlan1`. A default route via `192.168.50.1` means the robot hijacked it.

The robot guide fixes this at the source with `dhcp-option=3`. If you have applied it and still see a hijacked route, the robot's `dnsmasq` did not restart. As a per-master fallback:

**Settings → Network → robotX (gear) → IPv4 → check "Use this connection only for resources on its network"**, and the same on the IPv6 tab.

---

## Step 9 — Confirm the pushed template arrived

```bash
sudo su - a27-m0
grep -n "ssh_robot\|bringup" ~/.bashrc      # both should show 192.168.50.1
which ros2 && echo $ROS_DOMAIN_ID
ccbuild --help > /dev/null 2>&1 && echo "ccbuild defined"
exit
```

If the aliases still show `192.168.4.1` or `robotX`, the server-side push has not run. Return to Step 5 of the server guide.

---

## Full verification

```bash
id a27-m0                                          # LDAP resolves
ls /home/students/a27-m0 > /dev/null && echo "NFS OK"
sudo ls /home/students/a27-t02 2>&1 | grep -q denied && echo "root_squash OK"
id ece387rescue > /dev/null && echo "rescue account OK"
python3 -c "import dlib" && echo "dlib OK"
ip route | grep default                            # not via 192.168.50.1
sudo -l -U a27-m0 | tail -5                        # apt/pip/shutdown/reboot only
ls -l /dev/video0 | grep -q 'rw-rw-rw' && echo "udev OK"
sysctl kernel.dmesg_restrict                       # expect 0
```

---

## Rolling out to the remaining 13 masters

Do not repeat this by hand. Once this master is verified end to end, use Ansible from the login server (§4 of login-client.md), and skip the wheel build — every other machine installs the `.whl` from Step 6.

Run network steps (7 and 8) at each console, not over SSH.
