# Master (Client) Setup

This guide covers setting up a **master computer as a login client** — a machine that authenticates students against the login server (via SSSD) and mounts their home directory over NFS, so any student can sit at any master. It is one of three companion guides:

- [Login Server Setup](login-server.md) — the login server itself
- [Master (Client) Setup](login-client.md) — master computers that authenticate against the login server
- [Master Setup - Standalone](MasterSetupJazzy.md) — a single master with a local account, no login server

Complete [login-server.md](login-server.md) first — the login server must be running before a client can authenticate against it.

---

## Network Planning

Each master needs **two independent network connections**:

| Purpose | Carries | Interface |
|---|---|---|
| **Lab network** (`ECE387`) | LDAP authentication, NFS home directories, internet | Ethernet *or* USB WiFi dongle (`wlan1`) |
| **Robot link** | ROS 2 traffic to the TurtleBot3 | Onboard WiFi (`wlo1`) → robot's access point |

The onboard adapter `wlo1` is **always** dedicated to the robot. Only the lab-network side changes between the two supported topologies:

### Topology A — Ethernet available (preferred)

```
         ┌──────────────────────────┐
         │        master01          │
         │                          │
  wired ─┤ eth  ──► ECE387 network  │   LDAP, NFS, internet
         │ wlo1 ──► robotX AP       │   ROS 2 to the robot
         └──────────────────────────┘
```

Use this wherever a wired drop exists. Ethernet is faster and more reliable than the dongle, and it frees a USB port. No USB WiFi dongle is needed.

### Topology B — No Ethernet

```
         ┌──────────────────────────┐
         │        master01          │
         │                          │
         │ wlan1 ─► ECE387 network  │   LDAP, NFS, internet (USB dongle)
         │ wlo1  ─► robotX AP       │   ROS 2 to the robot
         └──────────────────────────┘
```

The USB dongle is renamed to a fixed name `wlan1` so one config works across all 14 masters regardless of which dongle is plugged in.

### Addresses

| Host | Hostname | IP |
|------|----------|----|
| WiFi router / DHCP / gateway | — | `10.99.1.1` (SSID `ECE387`) |
| Login Server | `ece387server` | `10.99.1.50` (static) |
| Master 01–14 | `master01`–`master14` | DHCP (dynamic) |
| Robot access point | `robotX` | `192.168.50.1` |

> Masters are identified by hostname, not IP, since their IP can change after a reboot or DHCP lease renewal. Ubuntu Desktop ships with `avahi-daemon` (mDNS) enabled, so each master is reachable at `<hostname>.local` from any other machine on `ECE387`. This guide uses the domain `ece387.local` for LDAP.

> **The robot AP hands out its own DHCP lease and default route.** Left alone, `wlo1` will hijack the master's default route and break access to the login server and the internet. Section 1.8 pins the robot connection so this cannot happen — do not skip it.

---

## 1. Master Computer Setup (NUC 9 × 14)

Do this on each of the 14 master computers. Most steps can be scripted and run via Ansible — see [Ansible Automation](#4-ansible-automation-recommended-for-14-machines).

Recommended order: get one master fully working by hand, verify it end to end, then push the rest with Ansible.

### 1.1 Fresh Install Ubuntu 24.04 Desktop

1. Boot from the Ubuntu 24.04 Desktop ISO.
2. During install:
   - Hostname: `master01`, `master02`, ... `master14`
   - Local admin account: `ece387admin`
   - Connect to `ECE387` (or plug in Ethernet) during setup — DHCP by default, which is what we want. No static IP on masters.
3. After install, confirm connectivity:

```bash
# Identify the interfaces present on this machine.
# Expect: lo, an ethernet device (eno1 / enp*), and wlo1 (onboard WiFi).
# A USB dongle appears as wlx<mac> until renamed in 1.7.
ip addr

# Confirm a DHCP lease and that the login server is reachable
ping -c 3 10.99.1.50

# mDNS — lets other machines find this master as masterNN.local
systemctl status avahi-daemon
```

> If `avahi-daemon` isn't running: `sudo apt install -y avahi-daemon && sudo systemctl enable --now avahi-daemon`.

#### Do you actually need mDNS?

Nothing students do depends on it. Both connections they use are addressed numerically:

| Path | Uses `.local` names? |
|---|---|
| Master → login server (LDAP, NFS) | No — hardcoded `10.99.1.50` |
| Master → robot | No — `192.168.50.1` |
| Student login and workflow | No |
| **Login server → masters** (Ansible, Section 4; the `who` check in Section 5) | **Yes** |

So mDNS exists purely so *you* can reach the masters by name from the login server, without caring what address DHCP handed out this week.

Keep it unless you have a reason not to. `avahi-daemon` ships enabled on Ubuntu Desktop, uses roughly 3–5 MB of RAM, and is idle otherwise — not a meaningful load on a NUC 9. Check on a running machine with:

```bash
systemctl status avahi-daemon | grep Memory
```

**If you prefer to disable it,** you need another way to address 14 machines for Ansible. The robust option is DHCP reservations on the `ECE387` router — pin each master's MAC to a fixed address, then use plain IPs everywhere. That is more reliable than mDNS (no multicast, no name resolution to fail) at the cost of some time in the router's admin page.

To disable, on each master:

```bash
sudo systemctl disable --now avahi-daemon
```

On the login server:

```bash
sudo systemctl disable --now avahi-daemon
sudo apt remove -y libnss-mdns
```

Then replace the `ansible_host=masterNN.local` entries in the Section 4 inventory with the reserved IP addresses, and use IPs in the Section 5 loop.

> Disabling mDNS without setting up DHCP reservations first will leave you walking to each NUC with a keyboard whenever a config changes. Do the reservations first, confirm they hold across a reboot, then disable.

Note the exact Ethernet and WiFi interface names from `ip addr` — you need them in 1.7. The onboard WiFi is `wlo1` on the NUC 9; confirm rather than assume.

### 1.2 Install ROS 2 Jazzy and Course Packages

```bash
# Prerequisites for adding a new apt repository
sudo apt install -y software-properties-common curl

# ROS 2 package signing key
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

# ROS 2 apt repository for Ubuntu Noble (24.04)
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update

# ROS 2 Jazzy Desktop (rviz2, rqt, etc.) plus TurtleBot3 packages
sudo apt install -y ros-jazzy-desktop ros-jazzy-turtlebot3* ros-dev-tools
```

Course-specific packages:

```bash
# Simulation — Gazebo Sim (Harmonic) via ros_gz.
# NOTE: Gazebo Classic (the old `gazebo` / ros-*-gazebo-* packages) is end-of-life
# and is NOT available for Jazzy. There is no /usr/share/gazebo/setup.sh to source.
sudo apt install -y ros-jazzy-ros-gz

# Robot hardware and transforms
sudo apt install -y ros-jazzy-dynamixel-sdk ros-jazzy-tf-transformations

# Vision
sudo apt install -y ros-jazzy-usb-cam ros-jazzy-image-proc \
                    ros-jazzy-v4l2-camera ros-jazzy-cv-bridge \
                    ros-jazzy-camera-calibration \
                    ros-jazzy-apriltag ros-jazzy-apriltag-ros libapriltag-dev

# Teleop
sudo apt install -y ros-jazzy-joy ros-jazzy-teleop-twist-joy jstest-gtk

# Utilities
sudo apt install -y tree terminator python3-pip obs-studio qtwayland5
```

> This list must stay in step with [MasterSetupJazzy.md](MasterSetupJazzy.md), which covers the standalone master. Students run identical labs on both, so a package present on one and missing on the other produces a lab that works at one bench and not another.

Python packages are installed system-wide, not in a per-student virtual environment. Ubuntu 24.04 blocks pip from writing to the system Python ([PEP 668](https://peps.python.org/pep-0668/)), so `--break-system-packages` is required:

```bash
sudo pip install --break-system-packages "pydantic<2"
sudo pip install --break-system-packages imutils
sudo pip install --break-system-packages pupil-apriltags
```

**`dlib` is installed from a prebuilt wheel, not from source.** PyPI ships dlib only as C++ source, so a plain `pip install dlib` compiles it — 30–60 minutes per machine, or over ten hours across fourteen masters. Build the wheel once and install the binary everywhere else in seconds. See [Building a dlib Wheel](building-a-dlib-wheel) in the standalone master guide for the build procedure and the reasoning.

```bash
# Fetch the prebuilt wheel from the login server and install it
scp ece387admin@ece387server:/srv/ece387/wheels/dlib-*.whl ~/
sudo pip install --break-system-packages ~/dlib-*.whl
```

> The wheel is architecture-specific. A master needs the `linux_x86_64` build; the robots' `linux_aarch64` wheel will not install here. Keep them in separate directories on the server so they cannot be confused.

**This is an instructor task, not a student one.** These packages live on the master's local disk, not in the student's NFS home directory, so they do not follow a student to another bench. Every master must have an identical set or a lab will work at one bench and fail at the next — which is exactly the failure mode that is hardest to diagnose during class. Students have `pip` in their sudo whitelist for the occasional one-off, but anything a lab depends on belongs in this list and in the Ansible playbook.

> Package names occasionally differ between distros. If any line fails, check availability with `apt-cache search <name>` before assuming the mirror is broken.

**The shell environment is not configured here.** `.bashrc` for student accounts comes from `/etc/ece387/bashrc_template` on the login server and is distributed by the push procedure in [login-server.md §1.7](login-server.md). Do not add ROS environment lines to student `.bashrc` files on the master — home directories are on NFS, so a local edit would be overwritten by the next push and would silently diverge from the other 13 machines.

### 1.2b Install Visual Studio Code

Install from the `.deb`, not the snap. Snap confinement interferes with serial device access and with picking up the ROS environment from the student's shell.

```bash
wget -O /tmp/code.deb 'https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64'
sudo apt install -y /tmp/code.deb
rm /tmp/code.deb
```

The package registers Microsoft's apt repository and key itself, so updates arrive through `sudo apt upgrade`. Do **not** add the repository manually first — configuring both leaves a duplicate source and floods every `apt update` with `configured multiple times` warnings.

Remove a pre-existing snap install if there is one:

```bash
snap list | grep code && sudo snap remove code
```

Verify:

```bash
code --version
apt-cache policy code      # expect a single packages.microsoft.com origin
```

If two origins appear, a hand-made source file is left over:

```bash
sudo rm -f /etc/apt/sources.list.d/vscode.list    # keep vscode.sources
sudo apt update
```

#### Raise the file watcher limit

Required on every master. VS Code watches every file in an open folder, and a built `master_ws` has tens of thousands across `build/` and `install/` — well past the default inotify ceiling. Students hit "file watcher limit reached" the first time they open their workspace.

```bash
echo "fs.inotify.max_user_watches=524288" | sudo tee /etc/sysctl.d/60-inotify.conf
sudo sysctl -p /etc/sysctl.d/60-inotify.conf
```

#### Seed workspace settings for students

Because home directories are on NFS, VS Code's per-user configuration follows students between benches — extensions and settings install once and are available everywhere. Two consequences worth planning for:

- **The first extension install is slow.** Something like Pylance writes thousands of small files over NFS. Have students install extensions early in the term, not at the start of a lab.
- **Extensions are unavailable during a server outage.** They live in `~/.vscode/extensions` on the server, like everything else in the home directory.

Seed sensible defaults so students are not each discovering the build-directory problem themselves. Add to `/etc/skel` on the **login server**, so new accounts pick it up:

```bash
# On ece387server
sudo mkdir -p /etc/skel/.config/Code/User
sudo tee /etc/skel/.config/Code/User/settings.json > /dev/null << 'EOF'
{
  "files.watcherExclude": {
    "**/build/**": true,
    "**/install/**": true,
    "**/log/**": true
  },
  "search.exclude": {
    "**/build/**": true,
    "**/install/**": true,
    "**/log/**": true
  }
}
EOF
```

`search.exclude` matters as much as `files.watcherExclude`: without it a project-wide search returns thousands of matches from compiled artifacts and `--symlink-install` symlinks.

> `/etc/skel` is copied only when an account is created, so existing students will not receive this. To apply it to the current 62, copy the file into each home directory with a loop modeled on the push in [login-server.md](login-server.md) — and be aware it overwrites any VS Code settings a student has already chosen.

### 1.3 Configure SSSD for LDAP Authentication

SSSD is the bridge between the master and the login server's LDAP database. When a student types their username and password, SSSD verifies it against LDAP.

```bash
sudo apt install -y sssd sssd-ldap libpam-sss libnss-sss oddjob oddjob-mkhomedir
```

```bash
sudo nano /etc/sssd/sssd.conf
```

```ini
[sssd]
# nss = name lookups ("id username", "getent passwd")
# pam = login authentication
services = nss, pam
domains = ece387.local
config_file_version = 2

[domain/ece387.local]
id_provider = ldap
auth_provider = ldap

ldap_uri = ldap://10.99.1.50
ldap_search_base = dc=ece387,dc=local
ldap_user_search_base = ou=students,dc=ece387,dc=local
ldap_group_search_base = ou=groups,dc=ece387,dc=local

ldap_default_bind_dn = cn=admin,dc=ece387,dc=local
ldap_default_authtok_type = password
ldap_default_authtok = LdapAdmin387!

# No TLS on the isolated lab network
ldap_id_use_start_tls = false

# Cache credentials so students can log in when the server is unreachable.
# Applies only to accounts that have logged into THIS machine before.
cache_credentials = true

# Cached credentials never expire (0 = no limit). Without this, offline logins
# stop working after a number of days.
offline_credentials_expiration = 0

# Pre-load all accounts so getent and tab-completion work
enumerate = true
```

```bash
# SSSD refuses to start if this file is readable by others
sudo chmod 600 /etc/sssd/sssd.conf

sudo systemctl enable --now sssd

# Create a home directory on first login if one does not exist
sudo pam-auth-update --enable mkhomedir

# SSSD may cache "offline" responses during the first seconds after boot,
# before the LDAP connection is established. Clear the cache for fresh lookups.
sudo systemctl stop sssd
sudo rm -rf /var/lib/sss/db/*
sudo systemctl start sssd
sleep 5

# Expected: uid=20000(a27-m0) gid=10000(ece387students) groups=10000(ece387students)
id a27-m0
```

### 1.4 Mount NFS Home Directories

autofs mounts a network directory on first access and unmounts it after a period of inactivity — more efficient than a static `/etc/fstab` mount.

```bash
sudo apt install -y autofs nfs-common
```

```bash
sudo nano /etc/auto.master.d/students.autofs
```

```
# Anything accessed under /home/students uses the rules in /etc/auto.students.
# --timeout=600 unmounts after 10 minutes of inactivity.
/home/students  /etc/auto.students  --timeout=600
```

```bash
sudo nano /etc/auto.students
```

```
# The * wildcard matches any username; & substitutes the matched name.
# Accessing /home/students/a27-m0 mounts 10.99.1.50:/home/students/a27-m0
#
# soft      = return an error if the server is unreachable, rather than hanging
# timeo=30  = 3.0 seconds per attempt (units are 0.1s)
# retrans=2 = retry twice, so failure surfaces after roughly 6 seconds
*  -fstype=nfs,soft,timeo=30,retrans=2  10.99.1.50:/home/students/&
```

```bash
sudo systemctl enable --now autofs
sudo systemctl restart autofs

# Test: the home directory should mount on access
sudo su - a27-m0
pwd          # /home/students/a27-m0
ls -la       # .bashrc, .profile, etc.
exit
```

> **`soft` trades a hang for an error.** With a `hard` mount (the NFS default) an unreachable server freezes the terminal indefinitely. With `soft`, I/O fails after ~6 seconds instead — the student sees `Input/output error` and keeps a usable session, but a write interrupted mid-operation can leave a truncated file. See [Section 2](#2-resilience--server-down-or-network-unreliable).

### 1.5 Create the Local Rescue Account

A **local** account — not LDAP, not NFS — on every master. It is the fallback when the login server or the lab network is down, and it is how you debug a hung NFS mount without your own shell living on the mount that is hung.

```bash
sudo adduser ece387rescue

# Hardware access for robot and camera work
sudo usermod -aG dialout,video,plugdev ece387rescue
```

Give it a home on local disk (the default `/home/ece387rescue` already is — it is outside `/home/students`, so autofs never touches it) and a minimal ROS environment:

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

Post the password where students can find it during a lab — it is a shared convenience account, not a security boundary. It has no access to student home directories, which is the point.

> Use a different password than `ece387admin`. Students will know the rescue password; they should not be able to become the machine's administrator with it.

Verify it works with the network unplugged:

```bash
# Physically disconnect Ethernet / disable WiFi, then:
su - ece387rescue
echo $HOME    # /home/ece387rescue
ls -la        # local files present
exit
```

### 1.6 Grant Students Restricted sudo Access

This section is the **single definition of the student sudo whitelist**. Other guides reference it rather than restating it.

Two layers work together, and they protect different things:

- **`root_squash` on the NFS server** rewrites root from any master to an unprivileged anonymous user, so `sudo cat /home/students/a27-t02/file` is refused by the server itself
- **The sudoers whitelist** limits what can be run with sudo at all

#### Server side — `root_squash`

```bash
sudo nano /etc/exports
```

```
/home/students  10.99.1.0/24(rw,sync,no_subtree_check,root_squash)
```

```bash
sudo exportfs -rav
sudo exportfs -v          # confirm root_squash appears in the options
```

> **This must be `root_squash`, not `no_root_squash`.** `no_root_squash` gives every master's root full write access to every student's home directory. It does not affect the instructor push loop in [login-server.md](login-server.md) — that runs locally on the server, not over NFS.

> **What `root_squash` does and does not cover.** It rewrites **UID 0 only**. A student who reaches root on a master can still `su - a27-t02` and read that account's files, because those requests carry UID 21002 and there is nothing to squash. This is inherent to `AUTH_SYS`, NFS's default authentication, where the client asserts its own UID and the server takes its word. Closing it entirely requires Kerberos (`sec=krb5`), which is a substantial addition. In practice, student file privacy here rests on the honor code, with `root_squash` and the whitelist removing the easy paths.

#### Master side — the whitelist

**The guiding principle: never whitelist a general-purpose binary.** Package managers, service managers, and network tools all execute code or open editors as root by design, so permitting any of them is equivalent to granting a root shell. Most things students actually need are solved by group membership or udev rules instead, with no privilege involved at all.

```bash
sudo nano /etc/sudoers.d/ece387-students
```

```
# ECE387 student sudo permissions
# The % prefix applies the rule to a group rather than a user.
# NOPASSWD avoids a password prompt — practical in a lab setting.

# Package management — students install their own libraries during labs.
# See "What this grants" below: this is equivalent to full root.
Cmnd_Alias ECE387_PKG = /usr/bin/apt, /usr/bin/apt-get, /usr/bin/dpkg, \
                        /usr/bin/pip, /usr/bin/pip3

# Power — Lab 1 teaches sudo shutdown and sudo reboot.
# (polkit already permits this for a local console user; kept because the
#  lab teaches the command.)
Cmnd_Alias ECE387_PWR = /usr/sbin/shutdown, /usr/sbin/reboot

%ece387students ALL=(ALL) NOPASSWD: ECE387_PKG, ECE387_PWR
```

```bash
# sudoers files must be mode 440 — sudo silently ignores files with wrong permissions
sudo chmod 440 /etc/sudoers.d/ece387-students

# Verify syntax before logging out. A malformed sudoers file can lock out sudo entirely.
sudo visudo -c -f /etc/sudoers.d/ece387-students

# Confirm what a student can actually run
sudo -l -U a27-m0
```

#### What `ECE387_PKG` grants

Package management is on the list deliberately: resolving their own dependencies is part of what students are learning. Be clear about what it costs, because it shapes what the rest of this setup can promise.

Package installation means running someone else's code with privilege — that is what installing software *is*. So `ECE387_PKG` is functionally equivalent to unrestricted root:

| Command | Path to root |
|---|---|
| `apt`, `apt-get` | Runs configuration hooks as root; `-o APT::Update::Pre-Invoke::=<cmd>` sets one from the command line |
| `dpkg`, `apt install ./x.deb` | `.deb` packages carry `preinst`/`postinst` scripts that run as root, and anyone can build a `.deb` |
| `pip`, `pip3` | Executes the package's `setup.py` to build it — arbitrary code, as root |

Two consequences to plan around:

- **Host-level restrictions become deterrents, not controls.** Immutable files, hosts-file blocking, and browser policy files can all be undone by a student who escalates to root. Where such restrictions are used, audit logging stops being optional — it is what converts an unenforceable rule into a recorded action.
- **`root_squash` still holds for the casual case but not the determined one.** See the note above: a student with root can `su - a27-t02`, and those requests carry a legitimate UID.

This is a reasonable trade in an honor-code environment. It is just worth making knowingly.

#### Prefer `pip install --user` over `sudo pip`

For Python specifically there is a better option that needs no sudo at all:

```bash
pip install --user --break-system-packages imutils     # any package name
```

This writes to `~/.local/lib/python3.12/site-packages`, which is **in the student's NFS home** — so the package follows them to every bench, needs no privilege, and cannot break the machine for the next student. `--break-system-packages` is still required (Ubuntu 24.04 marks the environment as externally managed even for `--user`), but nothing runs as root.

Teach this as the default and reserve `sudo pip` for the rare case where a package must be system-wide. `sudo pip` on a shared master installs for everyone and is wiped by the next re-image; `--user` is per-student and portable.

#### What is still left out, and why

| Command | Why it is excluded |
|---|---|
| `systemctl` | `systemctl edit` opens `$EDITOR` as root; set `EDITOR` to a shell and you have a root shell. If a lab needs one specific unit, permit the full invocation: `/usr/bin/systemctl restart ece387-camera` |
| `rosdep` | Redundant — it resolves dependencies from a student-written `package.xml` and then calls apt, which is already permitted directly |
| `colcon` | `colcon build` needs no privilege at all, and `sudo colcon build` creates root-owned files in the student's NFS home that they cannot then delete |
| `nmcli`, `ip` | Neither needs sudo: `ip addr`/`ip route` work unprivileged, and connecting to WiFi through the GUI goes through polkit |

#### Solve hardware access with groups and udev, not sudo

Serial and camera access is a permissions problem, not a privilege problem:

```bash
# Device permissions set at plug-in time — no sudo needed by anyone
sudo tee /etc/udev/rules.d/99-ece387.rules > /dev/null << 'EOF'
# OpenCR / Dynamixel controller
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", MODE="0666"
# USB cameras
KERNEL=="video[0-9]*", MODE="0666"
EOF

sudo udevadm control --reload
sudo udevadm trigger
```

`dmesg` is restricted to root on Ubuntu, which students need when debugging USB. Open it rather than whitelisting it:

```bash
echo "kernel.dmesg_restrict=0" | sudo tee /etc/sysctl.d/61-dmesg.conf
sudo sysctl -p /etc/sysctl.d/61-dmesg.conf
```

#### If a lab genuinely needs root

Write a wrapper that does exactly one thing, rather than whitelisting a general binary. For example,

```bash
sudo tee /usr/local/sbin/ece387-flash-opencr > /dev/null << 'EOF'
#!/bin/bash
set -e
exec /opt/ece387/opencr_update/update.sh /dev/ttyACM0 burger.opencr
EOF
sudo chmod 755 /usr/local/sbin/ece387-flash-opencr
sudo chattr +i /usr/local/sbin/ece387-flash-opencr
```

Then add only that path:

```
Cmnd_Alias ECE387_TOOLS = /usr/local/sbin/ece387-flash-opencr
%ece387students ALL=(ALL) NOPASSWD: ECE387_PWR, ECE387_TOOLS
```

Root-owned, immutable, no student-controlled arguments, no shell. That is a permission; `sudo systemctl` is a root shell.

#### Allow students to manage network connections

By default polkit grants `org.freedesktop.NetworkManager.settings.modify.system` only to members of `sudo` or `admin`. Students are in neither, so the GUI refuses with *"System policy prevents modification of network settings for all users."*

**polkit and sudo are separate systems.** The sudoers whitelist above has no effect here — polkit checks group membership, not sudo rules. Granting network management therefore does not widen what students can run in a terminal.

Benches are shared, lab WiFi is not always reliable, and students need to attach to robot access points without waiting for an instructor:

```bash
sudo tee /etc/polkit-1/rules.d/50-ece387-network.rules > /dev/null << 'EOF'
// Allow ECE387 students to manage network connections from the GUI.
polkit.addRule(function(action, subject) {
    if (subject.isInGroup("ece387students")) {
        switch (action.id) {
            case "org.freedesktop.NetworkManager.settings.modify.system":
            case "org.freedesktop.NetworkManager.network-control":
            case "org.freedesktop.NetworkManager.enable-disable-wifi":
                return polkit.Result.YES;
        }
    }
});
EOF

sudo systemctl restart polkit
```

`settings.modify.hostname` is deliberately excluded — hostnames identify the master in the Ansible inventory and in mDNS lookups, and a renamed machine is an annoying problem to trace.

Students can now also break the `ECE387` profile for whoever sits there next. Keep a known-good copy:

```bash
sudo cp -r /etc/NetworkManager/system-connections \
           /etc/NetworkManager/system-connections.ece387-backup
```

Restore with:

```bash
sudo cp /etc/NetworkManager/system-connections.ece387-backup/* \
        /etc/NetworkManager/system-connections/
sudo chmod 600 /etc/NetworkManager/system-connections/*
sudo systemctl restart NetworkManager
```

#### Discover what students actually need

Rather than guessing, log real usage for a week of labs:

```bash
echo 'Defaults log_input, log_output' | sudo tee /etc/sudoers.d/00-logging
sudo chmod 440 /etc/sudoers.d/00-logging
```

```bash
sudo journalctl -t sudo | grep COMMAND
```

Build the whitelist from that evidence. Anything appearing repeatedly probably belongs in the machine image rather than the whitelist.

### 1.7 Configure the Lab Network Connection

Follow **Option A** if the bench has a wired drop, **Option B** if it does not.

#### Option A — Ethernet (preferred)

Ubuntu Desktop's NetworkManager brings up a wired interface with DHCP automatically, so there is usually nothing to configure. Confirm:

```bash
# Substitute your ethernet interface name from 1.1
ip addr show eno1
nmcli connection show --active

ping -c 3 10.99.1.1     # router
ping -c 3 10.99.1.50    # login server
```

Give the wired connection a better route metric than any WiFi, so it is preferred whenever the cable is plugged in:

```bash
# Find the connection name (usually "Wired connection 1")
nmcli connection show

nmcli connection modify "Wired connection 1" ipv4.route-metric 50
nmcli connection up "Wired connection 1"
```

No USB dongle is required in this topology. Skip to 1.8.

#### Option B — USB WiFi Dongle

**a. Rename the dongle to a fixed `wlan1`.** Each master's dongle has a different MAC, so match on bus and type instead — the same config then works on every machine:

```bash
sudo nano /etc/systemd/network/10-usb-wifi.link
```

```ini
[Match]
Type=wlan
Property=ID_BUS=usb

[Link]
Name=wlan1
```

```bash
sudo udevadm control --reload
sudo udevadm trigger --subsystem-match=net --action=add
# Unplug and replug the dongle (or reboot) so it re-enumerates under the new name

ip addr show wlan1     # confirm; the old wlx<mac> name should be gone
```

> This `.link` file matches *any* USB WiFi adapter. It has no effect on `wlo1`, which is a PCIe device, so the onboard adapter keeps its name and stays available for the robot.

**b. Configure the lab networks on `wlan1`.** Ubuntu Desktop uses NetworkManager, and netplan hands control to it. `ls /etc/netplan/` typically shows:

| File | What it is | Edit it? |
|------|------------|----------|
| `01-network-manager-all.yaml` | Ships by default; tells netplan to let NetworkManager handle everything | No |
| `90-NM-*.yaml` | Auto-generated per connection profile; rewritten whenever a profile changes | No — hand edits are overwritten |
| `50-cloud-init.yaml` | Written by the installer at provisioning | **Yes** |

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  renderer: NetworkManager
  wifis:
    wlan1:
      dhcp4: true
      access-points:
        "ECE387":
          password: "ece387only"
          networkmanager:
            passthrough:
              connection.autoconnect-priority: "20"
        "AF_ACADEMY_GUEST":
          networkmanager:
            passthrough:
              connection.autoconnect-priority: "10"
        "ECE":
          password: "dfec3141"
          networkmanager:
            passthrough:
              connection.autoconnect-priority: "5"
```

Higher `autoconnect-priority` wins when several networks are in range: `ECE387` (lab) first, then `AF_ACADEMY_GUEST` (internet), then `ECE` (backup internet).

**c. Fix permissions** — these files hold WiFi passwords in plaintext, and netplan warns if they are world-readable:

```bash
sudo chmod 600 /etc/netplan/*.yaml
```

**d. Apply and verify:**

```bash
sudo netplan apply

ip addr show wlan1
nmcli connection show --active
ping -c 3 10.99.1.50
```

**e. Stop cloud-init from reverting the file on next boot:**

```bash
sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
```

```yaml
network: {config: disabled}
```

**f. Reconnecting manually.** NetworkManager does not preempt an active connection when a higher-priority network reappears. If `wlan1` is on `ECE` and `ECE387` comes back into range:

```bash
nmcli connection up "ECE387"
```

### 1.8 The Robot Link on `wlo1`

The onboard adapter `wlo1` connects to the robot's access point `robotX`, where X is the robot ID. The robot is at `192.168.50.1`.

**Students connect through the GUI**, using the AP password provided in lab — there is nothing in `/etc/netplan` for the robot, and no pre-created profile. The connection is deliberately manual: benches are shared and robots move, so an auto-connecting profile would put students on whichever robot happened to be in range, including their neighbor's.

Students select the network from the top-right network menu (or **Settings → Network → Wi-Fi**), pick `robotX`, and enter the password. NetworkManager saves the profile, so subsequent sessions at that bench are one click.

#### The one setting that must be changed

The robot's access point runs its own DHCP server and advertises itself as a default gateway. If NetworkManager accepts that, the master's default route points at the robot and **LDAP, NFS, and internet access all stop working** — while the robot itself responds normally, so it presents as a server outage rather than a routing problem.

After connecting to `robotX` for the first time:

**Settings → Network → `robotX` (gear icon) → IPv4 tab → check "Use this connection only for resources on its network"**

Do the same on the **IPv6** tab, then click Apply and reconnect.

That checkbox tells NetworkManager to route only the robot's own subnet over `wlo1` and to ignore its gateway and DNS offers. It is stored in the saved profile, so it only has to be set once per robot per master.

> **The robot can fix this for every master at once.** DHCP option 3 is what carries the gateway offer, and it is set on the robot's `dnsmasq`, not here. Adding `dhcp-option=3` and `dhcp-option=6` to `/etc/dnsmasq.conf` on each robot stops the offer at the source — see the dnsmasq step in [RobotSetupJazzy.md](RobotSetupJazzy.md). With that in place the checkbox below is belt-and-braces rather than load-bearing. Set it anyway on any master that may meet a robot flashed from an older image.

The equivalent from a terminal, if you are configuring a machine yourself:

```bash
nmcli connection modify robotX \
  ipv4.never-default yes \
  ipv6.never-default yes \
  ipv4.ignore-auto-dns yes
nmcli connection up robotX
```

#### How much this matters depends on your topology

| Topology | Risk |
|---|---|
| **A — Ethernet** | Lower. NetworkManager assigns wired connections a much better route metric (~100) than WiFi (~600), so Ethernet usually keeps the default route regardless. DNS can still be affected. |
| **B — Two WiFi links** | **High.** `wlan1` and `wlo1` receive comparable metrics and the winner is not predictable. Assume it will go wrong. |

Set the checkbox in both cases. It costs one click and removes the uncertainty.

#### Verify

Run this after connecting to a robot. All three must pass:

```bash
# The robot is reachable
ping -c 3 192.168.50.1

# The lab network still works — this is the one that fails if the route was hijacked
ping -c 3 10.99.1.50

# The default route must NOT be via 192.168.50.1
ip route | grep default
```

The last command should show the default via `10.99.1.1` on the Ethernet or `wlan1` interface. A default route via `192.168.50.1` means the checkbox was not applied.

Then SSH in:

```bash
ssh pi@192.168.50.1

# Or use the alias from the course .bashrc
ssh_robot
```

> **ROS 2 discovery across two interfaces.** DDS multicasts on every active interface, so a master can see nodes on both the robot subnet and the lab subnet. Distinct `ROS_DOMAIN_ID` values per bench keep benches isolated from each other; if node discovery behaves strangely, check that first.

---

## 2. Resilience — Server Down or Network Unreliable

Two subsystems fail differently. Authentication degrades gracefully; home directories do not.

### Authentication — survives an outage

`cache_credentials = true` means SSSD stores a credential hash locally after each successful login. With `offline_credentials_expiration = 0` it never expires.

The limit is that the cache is **per-machine**. A student who has used master07 before can log into master07 with the server down. A student who has never used master07 cannot — there is no cached hash to check.

### Home directories — fail, and do not resync

**NFS has no offline mode.** There is no local replica on the master; every read and write is a network round-trip. When the server is unreachable there is nothing local to fall back to.

What actually happens at login:

1. autofs attempts the mount, gets no response, gives up after ~6 seconds
2. `/home/students/<uid>` does not exist
3. `pam_mkhomedir` tries to create it from `/etc/skel` — and fails, because `/home/students` is an autofs-managed mount point where `mkdir` is not permitted

That third step failing is fortunate. If `/home/students` were an ordinary directory, `pam_mkhomedir` would succeed and the student would get a *local* home directory shadowing their NFS one — they would work in it all period, and when the server returned, autofs could not mount over the now-occupied path. Fourteen masters would each hold a divergent local copy. autofs prevents this, but by side effect rather than design.

The result: `$HOME` points at a path that does not exist. Text console and SSH sessions start but land in `/` with no `.bashrc`, so no ROS environment, no aliases, no `ccbuild`. **Graphical login typically fails outright**, since GNOME needs a writable `$HOME` for dconf and D-Bus — expect a bounce back to the GDM login screen.

> Verify this behavior on your hardware before you need it. On the server: `sudo systemctl stop nfs-kernel-server`. Then try both a graphical and an SSH login on a master, and note which works. This determines whether students can reach the rescue account from the login screen or need `Ctrl+Alt+F3`.

### Mid-session failure

If the server dies while students are working, `soft` mounts return `EIO` after ~6 seconds rather than hanging:

- `colcon build` fails partway, possibly leaving a corrupt `build/` or `install/` tree
- Editor saves fail; unsaved work is lost
- An interrupted write can truncate a file without an obvious error

Tell students that `Input/output error` means **stop and wait**, not retry.

### When the server returns

**Nothing syncs back.** There is no local copy and no queued writes — the writes never landed anywhere. Students see exactly the state the server had when it went down; anything attempted during the outage is gone.

autofs recovers on next access. A stale mount occasionally needs a nudge:

```bash
sudo systemctl restart autofs
```

### Recovery procedure for students

Post this by the benches.

**1. Log into the rescue account** (Section 1.5) — local, needs no server:

```
username: ece387rescue
password: <posted in lab>
```

If the graphical login refuses, switch to a text console with `Ctrl+Alt+F3` and log in there.

**2. Clone the workspace from GitHub to local disk:**

```bash
mkdir -p /tmp/rescue && cd /tmp/rescue
git clone https://github.com/<username>/<repo>.git master_ws
cd master_ws && colcon build --symlink-install
source install/setup.bash
```

`AF_ACADEMY_GUEST` provides internet independently of the lab network, so GitHub stays reachable when the login server does not.

**3. Push before logging out.** `/tmp` is cleared on reboot and the rescue account is shared:

```bash
git add -A && git commit -m "work from <date>" && git push
```

> **Git is the actual safety net.** SSSD caching and `soft` mounts limit the damage; only a pushed commit preserves the work. Make an end-of-lab commit and push a graded habit early in the term, not an emergency procedure students read for the first time during an outage.

### Checking status during an outage

```bash
# From a master
ping -c 3 10.99.1.50
showmount -e 10.99.1.50          # lists exports; errors or hangs if NFS is down
mount | grep students            # what is actually mounted
systemctl status autofs sssd

# Is SSSD in offline mode?
sudo sssctl domain-status ece387.local
```

---

## 3. Student Workflow

When a student sits down at a master:

1. **Log in** with the LDAP username (e.g. `a27-m0`) and password. SSSD authenticates against the login server; the home directory mounts automatically over NFS.
2. **`.bashrc`, `.ssh/`, and the workspace are already there** — same files at every bench, no re-setup. This is what the login server is for.
3. **Connect to the robot** from the network menu in the top-right corner: select `robotX` and enter the AP password. First time on a given master, also tick **"Use this connection only for resources on its network"** under Settings → Network → robotX → IPv4 and IPv6 (see Section 1.8) — without it, the lab network drops.

   ```bash
   # Robot reachable
   ping -c 2 192.168.50.1

   # Lab network still working
   ping -c 2 10.99.1.50

   # SSH into the robot
   ssh_robot                  # alias for: ssh pi@192.168.50.1
   ```

4. **Set the bench's ROS domain** so benches do not see each other's traffic:

   ```bash
   export ROS_DOMAIN_ID=7          # use your robot's ID
   ```

5. **Build and run:**

   ```bash
   ccbuild                    # builds ~/master_ws and sources it
   ```

6. **`git push` at the end of every session.** The GitHub SSH key lives in `~/.ssh/` and follows the student to any master.

---

## 4. Ansible Automation (Recommended for 14 Machines)

Rather than repeating Section 1 on each master by hand, Ansible runs the same steps on all 14 from the login server.

```bash
# On the login server
sudo apt install -y ansible

# Ubuntu Server does not ship mDNS resolution; install it so *.local resolves
sudo apt install -y avahi-daemon libnss-mdns
sudo systemctl enable --now avahi-daemon

# Should resolve to master01's current DHCP address
ping -c 1 master01.local

# Inventory. Masters use DHCP, so address them by mDNS hostname rather than IP —
# this keeps working after a reboot changes the lease.
cat > ~/Documents/ece387/masters-inventory.ini << 'EOF'
[masters]
master01 ansible_host=master01.local
master02 ansible_host=master02.local
master03 ansible_host=master03.local
master04 ansible_host=master04.local
master05 ansible_host=master05.local
master06 ansible_host=master06.local
master07 ansible_host=master07.local
master08 ansible_host=master08.local
master09 ansible_host=master09.local
master10 ansible_host=master10.local
master11 ansible_host=master11.local
master12 ansible_host=master12.local
master13 ansible_host=master13.local
master14 ansible_host=master14.local

[masters:vars]
ansible_user=ece387admin
ansible_become=yes
EOF

# Write setup-masters.yml covering sections 1.2-1.8, then:
ansible-playbook -i ~/Documents/ece387/masters-inventory.ini setup-masters.yml
```

> **Get one master fully working first.** Verify login, NFS mount, robot connectivity, and the rescue account by hand before pushing to the other 13 — a mistake applied simultaneously to 14 machines is much harder to unwind than one applied to a single machine you were watching.

> **Be careful with network steps over SSH.** Applying a netplan or NetworkManager change to the interface carrying your SSH session will drop the connection mid-play. Run 1.7 and 1.8 at the console, or accept that Ansible will report a failure it cannot recover from.

---

## 5. Maintenance

### Check who is logged in across all masters

```bash
for i in $(seq -w 1 14); do
  echo "=== master$i ==="
  ssh ece387admin@master$i.local who 2>/dev/null
done
```

### Verify a master's full configuration

```bash
# Run on the master; every line should succeed
id a27-m0                                    # LDAP lookup works
ls /home/students/a27-m0 > /dev/null          # NFS mount works
id ece387rescue                              # rescue account exists
ip route | grep default                       # default route is NOT 192.168.50.1
sudo -l -U a27-m0                             # sudo whitelist is in effect
```

### Update the shell environment

Student `.bashrc` and `.inputrc` live on the login server, not here. See [login-server.md §1.7](login-server.md). Nothing needs to be done on the masters.

---

## Troubleshooting

| Problem | Command | Fix |
|---------|---------|-----|
| Home dir not mounting | `automount -v` | Check NFS exports on server, autofs config on master, server reachable |
| SSSD not resolving users | `sssctl user-checks a27-m0` | `systemctl restart sssd` |
| NFS mount fails | `showmount -e 10.99.1.50` | Check server firewall; verify `nfs-kernel-server` is running |
| Login slow (~30s) | `journalctl -u sssd` | Check LDAP URI is reachable: `ping 10.99.1.50` |
| Can't reach a master by hostname | `ping masterNN.local` | Check `avahi-daemon` on both machines |
| **Lab network dies when connecting to robot** | `ip route \| grep default` | Default route was taken by the robot AP — apply `ipv4.never-default yes` (Section 1.8) |
| **Robot unreachable after `nmcli up`** | `nmcli device status` | Confirm the profile is bound to `wlo1`, not `wlan1` |
| **Dongle not named `wlan1`** | `ip addr` | Re-run `udevadm` commands and replug; confirm `10-usb-wifi.link` exists |
| **Graphical login bounces to GDM** | `journalctl -b -u gdm` | Usually a missing `$HOME` — check NFS; use rescue account meanwhile |
| **`Input/output error` in a student session** | `mount \| grep students` | NFS server unreachable; `soft` mount timed out. Stop work, see Section 2 |
| `sudo` stops working for students | `sudo visudo -c` | Check `/etc/sudoers.d/ece387-students` is mode 440 and syntactically valid |
| ROS 2 nodes not discovered | `ros2 topic list` on both ends | Confirm matching `ROS_DOMAIN_ID`, and that `wlo1` is connected to the right robot |

For server-side symptoms (student account issues, LDAP connection refused), see the troubleshooting table in [login-server.md](login-server.md).
