# Login Server Setup

This guide covers setting up the **login server** — the machine that hosts OpenLDAP (user accounts) and NFS (shared home directories) for the lab. It is one of three companion guides:

- **Login Server Setup** (this page) — the login server itself
- [Master (Client) Setup](login-client.md) — master computers that authenticate against the login server
- [Master Setup - Standalone](MasterSetupJazzy.md) — a single master with a local account, no login server

## Why a Login Server?

A login server (OpenLDAP + SSSD + NFS) is only worth the setup effort in one specific situation: **a shared lab of fixed, dedicated computers that many different students rotate through.**

**When a login server helps:**

- The lab has a bank of master computers (e.g., 14 NUCs) and students do not own or sit at the same machine every session.
- A student should be able to sit down at *any* master, log in with their own credentials, and immediately have their `.bashrc`, SSH keys, and ROS workspace available — without re-cloning or re-configuring anything.
- You want to manage 20–30 student accounts centrally: create them once, reset a forgotten password in one command, and push a `.bashrc` update to every account at once (see [Maintenance](#3-maintenance)). The shell environment is instructor-owned — every account runs an identical, known-good `.bashrc`, so "it works on my machine" never enters a debugging session.
- You need some isolation between students who share the same physical hardware (restricted sudo, separate home directories, no ability to read another student's files).

**When a login server is overkill:**

- Students each have their own laptop or a personal workstation they always use. In that case there is nothing to "roam" between — a local Ubuntu account already gives each student a persistent home directory, and centralized authentication just adds an extra server to install, patch, and keep running (plus a single point of failure if it goes down). Use [Master Setup - Standalone](MasterSetupJazzy.md) instead — it sets up the same ROS 2 environment with a normal local account and no LDAP/NFS dependency.
- You only have a handful of machines and can simply assign one student (or a fixed pair) per machine for the term.

**The trade-off:** a login server buys you station-independence and central account management, at the cost of standing up and maintaining an extra server, plus a dependency on the network (mitigated in [Master (Client) Setup](login-client.md) with SSSD credential caching and soft NFS mounts). For ECE 387's AFA lab — a fixed set of 14 dedicated NUCs used by a rotating roster of ~30 students across sections — that trade-off is worth it.

## Architecture Overview

```
                    ┌──────────────────────────────────┐
                    │   Login Server (NUC 9 or NUC 11) │
                    │   Ubuntu 24.04                   │
                    │   - OpenLDAP (user accounts)     │
                    │   - SSSD (authentication)        │
                    │   - NFS (shared home directories)│
                    └────────────┬─────────────────────┘
                                 │ Lab Ethernet
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────┴──────┐  ┌────────┴───────┐  ┌──────┴─────────┐
    │  Master 01     │  │  Master 02     │  │  Master N...   │
    │  NUC 9         │  │  NUC 9         │  │  NUC 9         │
    │  Ubuntu 24.04  │  │  Ubuntu 24.04  │  │  Ubuntu 24.04  │
    │  ROS2 Jazzy    │  │  ROS2 Jazzy    │  │  ROS2 Jazzy    │
    │  SSSD client   │  │  SSSD client   │  │  SSSD client   │
    │  NFS client    │  │  NFS client    │  │  NFS client    │
    └────────┬───────┘  └────────┬───────┘  └────────┬───────┘
             │ Internal WiFi (AP)                      │
    ┌────────┴───────┐                       ┌────────┴───────┐
    │  Robot 01      │                       │  Robot N...    │
    │  RPi 4         │                       │  RPi 4         │
    │  Ubuntu 24.04  │                       │  Ubuntu 24.04  │
    │  ROS2 Jazzy    │                       │  ROS2 Jazzy    │
    └────────────────┘                       └────────────────┘
```

**Key concept:** Student home directories live on the login server and are NFS-mounted on every master. When a student logs in to any master (set up per [Master (Client) Setup](login-client.md)), their home directory (`.bashrc`, SSH keys, ROS workspace) is automatically available — no per-machine setup needed.

> **Why not FreeIPA?** `freeipa-server` is not packaged for Ubuntu 24.04. OpenLDAP + SSSD is the standard replacement and provides the same centralized login and shared home directory functionality.

---

## Network Planning

Assign static IPs on your lab's network before starting. All machines must be on the same subnet so they can reach each other.

**Lab network:** WiFi router at `10.99.1.1`, SSID `ece387`, subnet `10.99.1.0/24`.

| Host | Hostname | IP |
|------|----------|----|
| Login Server | `ece387server` | `10.99.1.50` |
| Master 01 | `master01` | `10.99.1.101` |
| Master 02 | `master02` | `10.99.1.102` |
| ... | ... | ... |
| Master 14 | `master14` | `10.99.1.114` |

> The login server IP (`10.99.1.50`) is the AFA lab address, reachable over the `ece387` WiFi network at `10.99.1.1`. Master IPs above (`10.99.1.101`–`150`) are a suggested continuation of that range — adjust if you assign them differently. This guide uses the domain `ece387.local`.

---

## 1. Login Server Setup

### 1.0 Create a Working Directory

All scripts and configuration files for this setup are saved here so you can reference or reuse them later.

```bash
mkdir -p ~/Documents/ece387
```

### 1.1 Install Ubuntu 24.04 Server

1. Boot from Ubuntu 24.04 Server ISO.
2. During install, set:
   - Hostname: `ece387server`
   - Create a local admin account (e.g., `stanbaek`) — this is your admin account, separate from student accounts
   - Enable OpenSSH Server so you can manage the server remotely
3. After install, set a static IP so the server is always reachable at the same address:

```bash
# Find your ethernet interface name (look for something like enp86s0 or eno1)
ip a

# On Ubuntu Server installs, the netplan file created by cloud-init is
# usually 50-cloud-init.yaml, not 00-installer-config.yaml. Check which one
# exists on your machine first:
ls /etc/netplan/

sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp86s0:                      # replace with your actual interface name
      dhcp4: false
      addresses: [10.99.1.50/24]
      routes:
        - to: default
          via: 10.99.1.1          # WiFi router IP (ece387only)
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

```bash
# Apply the network config — takes effect immediately without rebooting
sudo netplan apply
```

> **Careful with `50-cloud-init.yaml`:** cloud-init regenerates this file on every boot by default, which can silently revert your static IP back to DHCP after a reboot. To make the change stick, disable cloud-init's network management:
>
> ```bash
> sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
> ```
>
> ```yaml
> network: {config: disabled}
> ```
>
> This only stops cloud-init from touching networking on future boots — it does not affect the netplan file you just edited.

### 1.2 Set Hostname and /etc/hosts

The hostname tells the machine its own name. `/etc/hosts` maps that name to an IP address locally, which is required for LDAP to work correctly — LDAP uses the hostname to identify the server, and it must match the IP.

```bash
# Set the system hostname
sudo hostnamectl set-hostname ece387server
```

```bash
sudo nano /etc/hosts
```

The file should contain:

```
127.0.0.1   localhost
10.99.1.50  ece387server.ece387.local  ece387server
```

> `ece387server.ece387.local` is the fully qualified domain name (FQDN): machine name + domain. `ece387.local` is a private domain that exists only within your lab network — it is not registered on the public internet.

### 1.3 Install OpenLDAP

OpenLDAP is a directory service — think of it as a database that stores user accounts (usernames, UIDs, home directory paths, passwords). Every master computer will query this database to authenticate students.

```bash
# Update package list, then install:
#   slapd       — the OpenLDAP server daemon
#   ldap-utils  — command-line tools for querying/modifying the LDAP database
#   ldapscripts  — helper scripts for common tasks like adding users
sudo apt update && sudo apt upgrade -y
sudo apt install -y slapd ldap-utils ldapscripts
```

During install you are prompted for an admin password — set a strong one (e.g., `LdapAdmin387!`). This is the LDAP admin password, not your Linux account password.

Now reconfigure the database to use your domain name. This step sets the "root" of the LDAP tree — everything hangs off `dc=ece387,dc=local`:

```bash
sudo dpkg-reconfigure slapd
```

Answer the prompts:

- Omit OpenLDAP server configuration? → **No**
- DNS domain name → `ece387.local`  *(this becomes dc=ece387,dc=local in LDAP)*
- Organization name → `ECE387`
- Admin password → `LdapAdmin387!` (confirm)
- Remove database when slapd is purged? → **No**
- Move old database? → **Yes**

Verify the server is running and the base structure is reachable:

```bash
# Check that slapd is active
sudo systemctl status slapd

# Query the LDAP server — it should return the base entry with no errors.
# -x         = simple authentication (no Kerberos)
# -H         = server URI
# -b         = base DN to search from
# -D         = who you're connecting as (the admin account)
# -W         = prompt for password
ldapsearch -x -H ldap://localhost -b "dc=ece387,dc=local" -D "cn=admin,dc=ece387,dc=local" -W
```

### 1.4 Create LDAP Structure

LDAP organizes entries in a tree. Before adding users, you need to create the "folders" (called organizational units, or `ou`) that hold them. This is like creating directories before putting files inside.

```bash
# Write the structure definition to a file in LDIF format.
# LDIF (LDAP Data Interchange Format) is the text format used to describe
# entries you want to add, modify, or delete in the LDAP database.
cat > ~/Documents/ece387/structure.ldif << 'EOF'
# ou=students: holds all student user accounts
dn: ou=students,dc=ece387,dc=local
objectClass: organizationalUnit
ou: students

# ou=groups: holds group definitions
dn: ou=groups,dc=ece387,dc=local
objectClass: organizationalUnit
ou: groups

# ece387students: the group all students belong to.
# gidNumber 10000 is the shared group ID assigned to all students.
dn: cn=ece387students,ou=groups,dc=ece387,dc=local
objectClass: posixGroup
cn: ece387students
gidNumber: 10000
EOF

# Add these entries to the LDAP database
# -f = read from file instead of stdin
ldapadd -x -H ldap://localhost \
  -D "cn=admin,dc=ece387,dc=local" \
  -W -f ~/Documents/ece387/structure.ldif
```

### 1.5 Create Student Accounts

Student IDs follow two series this term: `a27-m0` through `a27-m30` (31 accounts) and `a27-t0` through `a27-t30` (31 accounts) — 62 accounts total. The script below:

1. Generates a hashed password for all accounts
2. Builds a single LDIF file with all 62 user entries
3. Creates each student's home directory on the server, populated with the `/etc/skel` defaults (the course `.bashrc` is applied in 1.6)
4. Adds all accounts to LDAP in one command

UID numbers are split into two non-overlapping ranges so the two series never collide: `m` series uses `20000`–`20030`, `t` series uses `21000`–`21030`.

```bash
cat > ~/Documents/ece387/create_students.sh << 'EOF'
#!/bin/bash
# Exit immediately if any command fails
set -e

# --- Configuration ---
LDAP_ADMIN_DN="cn=admin,dc=ece387,dc=local"
LDAP_ADMIN_PW="LdapAdmin387!"    # your LDAP admin password
INITIAL_PW="TempPass2024!"        # students change this on first login
LDIF=~/Documents/ece387/students.ldif

# Generate a single password hash to reuse for all accounts.
# slappasswd hashes the password in a format OpenLDAP understands ({SSHA}...).
HASH=$(slappasswd -s "$INITIAL_PW")

# Clear the LDIF file if it already exists from a previous run
> $LDIF

# Two username series this term: a27-m0..a27-m30 and a27-t0..a27-t30.
# UID_BASE keeps the two series in separate, non-overlapping ranges.
create_series() {
  local PREFIX=$1     # "m" or "t"
  local UID_BASE=$2   # 20000 for m-series, 21000 for t-series

  # Loop from 0 to 30, creating one LDAP entry per student
  for i in $(seq 0 30); do
    USERNAME="a27-${PREFIX}${i}"
    UID_NUMBER=$((UID_BASE + i))

    # Append this student's entry to the LDIF file.
    # Each entry is separated by a blank line (required by LDIF format).
    cat >> $LDIF << ENTRY
dn: uid=${USERNAME},ou=students,dc=ece387,dc=local
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: ${USERNAME}
cn: ${USERNAME}
sn: ${USERNAME}
uidNumber: ${UID_NUMBER}
gidNumber: 10000
homeDirectory: /home/students/${USERNAME}
loginShell: /bin/bash
userPassword: ${HASH}

ENTRY

    # Create the student's home directory on the NFS share.
    # /etc/skel contains default files (.bashrc, .profile, etc.) that are
    # copied into every new home directory.
    sudo mkdir -p /home/students/${USERNAME}
    sudo cp -r /etc/skel/. /home/students/${USERNAME}/

    # Set ownership to the student's UID and the shared group GID (10000).
    # chmod 700 means only the student can read/write their own directory.
    sudo chown -R ${UID_NUMBER}:10000 /home/students/${USERNAME}
    sudo chmod 700 /home/students/${USERNAME}

    echo "Prepared: ${USERNAME} (uid=${UID_NUMBER})"
  done
}

create_series "m" 20000
create_series "t" 21000

# Add all 62 entries to LDAP in a single operation.
# -w = password (non-interactive, read from argument)
ldapadd -x -H ldap://localhost \
  -D "$LDAP_ADMIN_DN" \
  -w "$LDAP_ADMIN_PW" \
  -f $LDIF

echo ""
echo "Done. 62 student accounts created (a27-m0..m30, a27-t0..t30)."
EOF

# Make the script executable, then run it
chmod +x ~/Documents/ece387/create_students.sh
bash ~/Documents/ece387/create_students.sh
```

Verify all accounts were created:

```bash
# Search the LDAP students OU and list just the uid field.
# You should see uid: a27-m0 through uid: a27-m30, and uid: a27-t0 through uid: a27-t30.
ldapsearch -x -H ldap://localhost \
  -b "ou=students,dc=ece387,dc=local" \
  -D "cn=admin,dc=ece387,dc=local" \
  -W uid uidNumber homeDirectory | grep "^uid:"
```

### 1.6 Create Course Config Templates

With the accounts created, define the course shell environment. The templates are written here and then distributed to every account by the push at the end of this section — that same command is what you re-run whenever a template changes, so there is no separate first-time install path to drift out of date.

```bash
# Create the directory that will hold course-wide config files
sudo mkdir -p /etc/ece387
```

> **How student edits behave.** Home directories are NFS-mounted from this server, so there is exactly **one** `.bashrc` per student — the copy under `/home/students/` here. Three consequences follow, all of them intended:
>
> 1. **A student edit persists.** Nothing overwrites it at login. There is no login hook, no cron job, no sync daemon; after account creation the template and the student's file are unrelated.
> 2. **An edit follows the student to every machine.** Editing `~/.bashrc` on master07 writes through to this server immediately, so logging into master12 an hour later gets the edited file. There is no per-machine copy to fall out of step.
> 3. **An instructor push replaces it.** The push below overwrites `.bashrc` on all 62 accounts, discarding student edits with no warning and no backup. That is the only thing that reverts a student's changes, and it happens only when you run it by hand.
>
> The file is owned by the student and mode `644`, so they *can* edit it. "Instructor-owned" is a course policy enforced by the push, not a permission setting.

#### .bashrc Template

`.bashrc` is sourced every time a terminal opens. Because `create_students.sh` copies this file *over* the student's `.bashrc`, the template must be a **complete** `.bashrc` — the Ubuntu defaults plus the course environment — not just the ECE 387 additions. A template containing only the course block produces accounts with no prompt, no history settings, and no `ls` colors.

Write it in one shot. The quoted `'TEMPLATE_EOF'` delimiter is required: it stops the shell from expanding `$@`, `$-`, `$(...)`, and `~` while the file is being written.

```bash
sudo tee /etc/ece387/bashrc_template > /dev/null << 'TEMPLATE_EOF'
# ~/.bashrc: executed by bash(1) for non-login shells.
# ECE 387 course template — managed by the instructor, overwritten on every push.
# Do not edit this file on a student account; edit /etc/ece387/bashrc_template
# on the login server and re-push.

# If not running interactively, set the ROS environment and return early.
# This is what makes non-login commands work, e.g.:
#   ssh master05 'ros2 topic list'
if [[ $- != *i* ]]; then
    source /opt/ros/jazzy/setup.bash
    source ~/master_ws/install/setup.bash 2>/dev/null || true
    export TURTLEBOT3_MODEL=burger
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=99     # TURTLEBOT3
    export LDS_MODEL=LDS-02     # Replace with LDS-03 if using new LIDAR

    return
fi

# ---------------- Ubuntu defaults ----------------

# don't put duplicate lines or lines starting with space in the history.
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and update LINES and COLUMNS
shopt -s checkwinsize

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;36m\]\u@\h\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]\n\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# enable programmable completion features
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# ---------------- ECE 387 course environment ----------------

alias gedit='gnome-text-editor'

# Launch the TurtleBot3 bringup on the robot over SSH.
alias bringup='ssh pi@192.168.50.1 '\''ros2 launch turtlebot3_bringup robot.launch.py'\'

# Shortcut to SSH into the robot.
alias ssh_robot='ssh pi@192.168.50.1'

# Build the workspace, passing through any colcon arguments
function ccbuild() {
    cd ~/master_ws && colcon build --symlink-install "$@"
    source ~/master_ws/install/setup.bash
}

# Export the function so it is available in subshells
export -f ccbuild

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
# It MUST match the value set on the robot, which equals the robot number
# (robot7 -> 7). A mismatch is silent: the master simply sees no topics at
# all, with no error message. Students override this per terminal:
#   export ROS_DOMAIN_ID=7
export ROS_DOMAIN_ID=99
export LDS_MODEL=LDS-02   # Replace with LDS-03 if using new LIDAR

# ---- Local working directory ----
# ~/master_ws and ~/.cache are symlinks to /local/$USER on THIS machine.
# Build output and caches are large and change constantly, so they stay on
# local disk rather than crossing NFS. Source code lives in git.
#
# Work does NOT follow you to another bench. Commit and push before you leave.
if [ ! -d "/local/$USER/master_ws" ]; then
    mkdir -p "/local/$USER/master_ws/src" "/local/$USER/cache" 2>/dev/null \
      && chmod 700 "/local/$USER" 2>/dev/null
fi
TEMPLATE_EOF
```

Check the syntax before pushing it to 62 accounts - a typo here breaks every terminal in the lab at once:

```bash
bash -n /etc/ece387/bashrc_template && echo "syntax OK"
```

**Notes on the template:**

- The non-interactive guard sets the ROS variables *before* returning. The stock Ubuntu `.bashrc` returns immediately, which would leave `ssh master05 'ros2 topic list'` with no ROS environment. The variables are intentionally duplicated in the guard and in the course block below it - the guard `return`s before reaching the second copy, so keep the two in sync when you change one.
- Interactivity matters for more than convenience: without the guard, anything the course block prints to stdout corrupts `scp` and `rsync` transfers to and from the robots.
- `source /usr/share/gazebo/setup.sh` is **not** included. That path belongs to Gazebo Classic, which is not part of Jazzy - on a Jazzy master the file does not exist and every terminal opens with a "No such file or directory" error. If a future setup does need it, guard the source: `[ -f /usr/share/gazebo/setup.sh ] && source /usr/share/gazebo/setup.sh`.
- `robotX` in the `bringup` alias is a placeholder. Either replace it before the first push or teach students to use `ssh_robot` and launch bringup by hand.

#### .inputrc Template

`.inputrc` configures readline behavior - used by bash for history search and tab completion.

```bash
sudo tee /etc/ece387/inputrc_template > /dev/null << 'EOF'
# ~/.inputrc: readline initialization file.
# ECE 387 course template — managed by the instructor, overwritten on every push.

# Start from the system defaults. Without this line, ~/.inputrc REPLACES
# /etc/inputrc entirely rather than adding to it.
$include /etc/inputrc

# Arrow keys search history based on what's already typed
"\e[A": history-search-backward
"\e[B": history-search-forward

# Case-insensitive tab completion
set completion-ignore-case on
EOF
```

Readline fails silently on a bad binding — a typo does not error, the key just does nothing. Test before pushing:

```bash
bind -f /etc/ece387/inputrc_template && echo "readline accepted it"
```

> **`$include` is not optional.** Unlike `.bashrc`, a user's `~/.inputrc` does not layer on top of `/etc/inputrc` — readline reads the user file *instead of* the system file. Without the include line, students silently lose the Ubuntu defaults.

> **Readline reads `.inputrc` only at shell startup.** After a push, `source ~/.bashrc` will not pick up `.inputrc` changes; students need a fresh terminal.

#### Pushing Updates to All Students

The templates are copied automatically only when accounts are first created. To push changes to all existing students at any time:

```bash
for dir in /home/students/a27-*/; do
  user=$(basename "$dir")
  # Read the UID from the home directory itself. Do NOT use `id -u "$user"`:
  # the login server hosts LDAP but is not an LDAP *client*, so NSS on this
  # machine cannot resolve student names and `id` fails silently.
  uid=$(stat -c %u "$dir")
  sudo cp /etc/ece387/bashrc_template "${dir}.bashrc"   || { echo "FAILED: $user"; continue; }
  sudo cp /etc/ece387/inputrc_template "${dir}.inputrc" || { echo "FAILED: $user"; continue; }
  sudo chown "${uid}:10000" "${dir}.bashrc" "${dir}.inputrc"
  echo "Updated: $user (uid=$uid)"
done
```

Verify ownership afterward. The glob must be expanded *inside* the elevated shell — student home directories are `chmod 700`, so your own shell cannot expand a path that reaches into them:

```bash
# Empty output = all accounts correct
sudo find /home/students -maxdepth 2 -name '.bashrc' -user root
```

> **This overwrites `.bashrc` and `.inputrc` unconditionally.** Anything a student added to either file is gone. That is the intended behavior — the shell environment is course-managed. `chown` is required because `sudo cp` leaves the copies owned by `root`; inside a `chmod 700` home directory that is confusing to debug later even though bash will still source them.

Run the push from the login server, not from a master — the home directories live here. Students pick up the change at their next login, or immediately with `source ~/.bashrc`.

> **Verify on one account before pushing to all 62.** Copy the template to a single student, log in as them on a master, and confirm the prompt, `ros2 topic list`, and `ccbuild` all behave. A bad template pushed to every account takes down every bench at once.

### 1.7 Configure NFS Home Directories

NFS (Network File System) lets the master computers mount the server's `/home/students` directory as if it were a local disk. When a student logs in to any master, their home directory appears from the server.

```bash
# Install the NFS server package
sudo apt install -y nfs-kernel-server

# Create the parent directory that holds all student home directories.
# Individual student dirs (a27-m0, a27-m1, ..., a27-t0, a27-t1, ...) were already created in 1.6.
sudo mkdir -p /home/students
sudo chmod 755 /home/students
```

Edit the NFS exports file to define what is shared and who can access it:

```bash
sudo nano /etc/exports
```

```
# Share /home/students with all machines on the 10.99.1.0/24 subnet.
# rw             = read and write access
# sync           = write data to disk before acknowledging — safer than async
# no_subtree_check = disables subtree checking, improves reliability
# root_squash = does not allow root on clients to act as root here 
/home/students  10.99.1.0/24(rw,sync,no_subtree_check,root_squash)
# Note: this matches the ece387 WiFi router subnet (10.99.1.0/24)
```

```bash
# Re-read /etc/exports and apply the new export
sudo exportfs -rav

# Enable and start the NFS server
sudo systemctl enable --now nfs-server

# Verify the export is listed — should show /home/students
showmount -e localhost
```

> **`root_squash` isolates students from each other.** It tells the server to rewrite root on any master to an unprivileged anonymous user, so `sudo cat /home/students/a27-t2/lab3.py` run from a master is refused by the server itself. Nothing in this guide needs `no_root_squash`: `create_students.sh` and the push loop both run locally on this server, not over NFS. The tradeoff is that administrative fixes to student files must be made here rather than from a master.
>
> **What it does not cover.** `root_squash` rewrites **UID 0 only**. A student who reaches root on a master can still `su - a27-t2` and read that account's files, because those requests carry UID 21002 and there is nothing to squash. This is inherent to `AUTH_SYS`, NFS's default authentication, where the client asserts its own UID and the server takes its word; closing it needs Kerberos (`sec=krb5`). In practice student file privacy rests on the honor code, with `root_squash` and the sudo whitelist removing the easy paths. See "Grant Students Restricted sudo Access" in [login-client.md](login-client.md).

### 1.8 Open Required Firewall Ports

```bash
# Allow SSH so you can manage the server remotely
sudo ufw allow OpenSSH

# Allow LDAP queries from master computers (port 389)
sudo ufw allow 389/tcp

# Allow NFS traffic (port 2049)
sudo ufw allow 2049/tcp

# Allow rpcbind/portmapper (port 111) — required for showmount and NFS negotiation
sudo ufw allow 111/tcp
sudo ufw allow 111/udp

# Allow all traffic from the lab subnet
sudo ufw allow from 10.99.1.0/24

# Enable the firewall
sudo ufw enable

# Verify the rules
sudo ufw status
```

> **Reconfiguring an already-running server:** if `sudo ufw status` still shows an old subnet (e.g. `10.99.1.0/24`) from a previous setup, `ufw allow` won't replace it — the old rule stays active alongside the new one. Remove it explicitly:
>
> ```bash
> sudo ufw status numbered      # find the rule number for the old subnet
> sudo ufw delete <number>      # delete it
> sudo ufw allow from 10.99.1.0/24
> sudo ufw status
> ```

Once the server is up, continue to [login-client.md](login-client.md) to configure each master to authenticate against it.

---

## 2. Resilience — Server Down or Network Unreliable

**Authentication (SSSD):** Handled on the client side — after a student logs in once, SSSD on each master caches their credentials locally so they can still log in if the login server goes down. See [login-client.md](login-client.md).

**Home directories (NFS):** If the NFS server is unreachable, students lose access to `.bashrc`, SSH keys, and their ROS workspace on any master. Mitigations (GitHub as a safety net, soft NFS mounts) are configured on the client side — see [login-client.md](login-client.md).

---

## 3. Maintenance

### Add a new student

```bash
# Step 1: Generate a hashed password for the new student
slappasswd -s NewStudentPass!
# Copy the {SSHA}... output

# Step 2: Add the account to LDAP
# Use the next free uidNumber in the right series:
#   m series (a27-m0..m30):  20000-20030
#   t series (a27-t0..t30):  21000-21030
# e.g. a new t-series student a27-t31 gets uidNumber 21031
ldapadd -x -H ldap://localhost \
  -D "cn=admin,dc=ece387,dc=local" -W << 'EOF'
dn: uid=a27-t31,ou=students,dc=ece387,dc=local
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: a27-t31
cn: a27-t31
sn: a27-t31
uidNumber: 21031
gidNumber: 10000
homeDirectory: /home/students/a27-t31
loginShell: /bin/bash
userPassword: {SSHA}PASTE_HASH_HERE
EOF

# Step 3: Create the home directory on the server
sudo mkdir -p /home/students/a27-t31
sudo cp -r /etc/skel/. /home/students/a27-t31/
sudo cp /etc/ece387/bashrc_template /home/students/a27-t31/.bashrc
sudo cp /etc/ece387/inputrc_template /home/students/a27-t31/.inputrc
sudo chown -R 21031:10000 /home/students/a27-t31
sudo chmod 700 /home/students/a27-t31
```

### Reset a student password

```bash
# Replace a27-m0 with the student's username, and set the new password with -s
ldappasswd -H ldap://localhost \
  -D "cn=admin,dc=ece387,dc=local" \
  -W -s NewPassword! \
  "uid=a27-m0,ou=students,dc=ece387,dc=local"
```

### Remove all students for a class year (year-end rollover)

Class-year prefixes change every year (`a27` = class of 2027, `a28` = class of 2028, etc.). Run this once at the start of a new year, right before running `create_students.sh` for the incoming class. It takes a prefix, backs up the LDAP database and matching home directories first, then deletes the LDAP entries and home directories for every account matching that prefix (both `m` and `t` series, since they share the same `a27-*` prefix).

```bash
cat > ~/Documents/ece387/remove_students.sh << 'EOF'
#!/bin/bash
# Removes ALL student accounts for a given class-year prefix (e.g. a27)
# and deletes their home directories. Backs up LDAP + home dirs first.
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <prefix>   e.g. $0 a27"
  exit 1
fi

PREFIX=$1
LDAP_ADMIN_DN="cn=admin,dc=ece387,dc=local"
LDAP_ADMIN_PW="LdapAdmin387!"    # your LDAP admin password
BASE_DN="ou=students,dc=ece387,dc=local"

echo "This will PERMANENTLY delete all LDAP accounts and home directories"
echo "matching '${PREFIX}-*' under ${BASE_DN} (covers both m and t series)."
read -p "Type the prefix again to confirm (${PREFIX}): " CONFIRM
if [ "$CONFIRM" != "$PREFIX" ]; then
  echo "Confirmation did not match. Aborting."
  exit 1
fi

# --- Step 1: Back up before deleting anything ---
BACKUP_DIR=~/Documents/ece387/backups/$(date +%Y%m%d)-${PREFIX}
mkdir -p "$BACKUP_DIR/home"

echo "Backing up full LDAP database to ${BACKUP_DIR}/ldap-backup.ldif ..."
sudo slapcat > "${BACKUP_DIR}/ldap-backup.ldif"

echo "Backing up home directories matching ${PREFIX}-* to ${BACKUP_DIR}/home ..."
sudo rsync -av --include="${PREFIX}-*" --include="${PREFIX}-*/**" --exclude="*" \
  /home/students/ "${BACKUP_DIR}/home/"

# --- Step 2: Find all matching uids in LDAP ---
USERS=$(ldapsearch -x -H ldap://localhost \
  -b "$BASE_DN" -D "$LDAP_ADMIN_DN" -w "$LDAP_ADMIN_PW" \
  "(uid=${PREFIX}-*)" uid | grep "^uid:" | awk '{print $2}')

if [ -z "$USERS" ]; then
  echo "No accounts found matching ${PREFIX}-*. Nothing to remove."
  exit 0
fi

echo "Found $(echo "$USERS" | wc -l) accounts to remove:"
echo "$USERS"
echo ""

# --- Step 3: Delete each LDAP entry ---
for USERNAME in $USERS; do
  echo "Deleting LDAP entry: uid=${USERNAME}"
  ldapdelete -x -H ldap://localhost \
    -D "$LDAP_ADMIN_DN" -w "$LDAP_ADMIN_PW" \
    "uid=${USERNAME},${BASE_DN}"
done

# --- Step 4: Remove home directories ---
for USERNAME in $USERS; do
  echo "Removing home directory: /home/students/${USERNAME}"
  sudo rm -rf "/home/students/${USERNAME}"
done

echo ""
echo "Done. Removed accounts matching '${PREFIX}-*'."
echo "Backup saved to: ${BACKUP_DIR}"
EOF

chmod +x ~/Documents/ece387/remove_students.sh
```

Run it with the outgoing class prefix, e.g.:

```bash
bash ~/Documents/ece387/remove_students.sh a27
```

Then create the incoming class with the new prefix by editing the `create_series` calls in `create_students.sh` (or parameterizing them the same way) before re-running it.

> **Group and OU structure are untouched** — this only removes entries under `ou=students`. `ou=groups` and the `ece387students` group (gidNumber 10000) stay in place and are reused every year.

### List all student accounts

```bash
ldapsearch -x -H ldap://localhost \
  -b "ou=students,dc=ece387,dc=local" \
  -D "cn=admin,dc=ece387,dc=local" \
  -W uid cn
```

### Back up home directories and LDAP database

```bash
# Sync all student home directories to a backup location
sudo rsync -av /home/students/ /backup/students/

# Export the entire LDAP database to a text file (LDIF format)
# This file can be used to restore the database on a new server
sudo slapcat > ~/Documents/ece387/ldap-backup-$(date +%Y%m%d).ldif
```

---

## Troubleshooting

| Problem | Command | Fix |
|---------|---------|-----|
| Student can't log in | `ldapsearch -x -H ldap://localhost -b "ou=students,dc=ece387,dc=local" -D "cn=admin,dc=ece387,dc=local" -W "(uid=a27-m0)"` | Check account exists; verify password hash is valid |
| LDAP connection refused | `ldapsearch -x -H ldap://10.99.1.50 -b "dc=ece387,dc=local" -x` | Check `systemctl status slapd` on server |
| NFS mount fails (from a client) | `showmount -e 10.99.1.50` | Check firewall on server; verify `nfs-server` is running |

For client-side symptoms (home directory not mounting, SSSD not resolving users, login hangs or is slow), see the troubleshooting table in [login-client.md](login-client.md).
