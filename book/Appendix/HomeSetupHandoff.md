# ECE387 Home Server and Client Setup Handoff

Use this handoff to continue the ECE387 setup on a home login server and master client. Give the prompt below to Codex on either machine. The configuration recorded here reflects work through November 20, 2026; inspect the current state before making changes.

## Home client status: elephant (November 20, 2026)

Each system configuration step was approved individually by the user. Retain that workflow for further changes.

### Verified setup

- Client: `elephant`, Intel NUC, Ubuntu 24.04.5, x86-64. During inspection, `wlo1` used DHCP address `192.168.0.63/24` on home Wi-Fi `BAEK-5G`; Ethernet `enp89s0` was disconnected. Hostname and network profiles were preserved.
- Home server: user identified `phoenix` at static address `192.168.0.151`. Do not use the lab address `10.99.1.50` on this client. SSH as `stanbaek` did not authenticate with the client's available credentials; server-side inspection was performed by the user locally.
- Existing home TLS was reused. The user confirmed the server CA path `/etc/ssl/certs/ece387-home-ldap-ca.crt` and certificate path `/etc/ssl/certs/ece387-home-ldap-server.crt`. The server certificate covers `phoenix`, `phoenix.ece387.local`, and `192.168.0.151` and expires February 22, 2029 UTC. The home CA expires November 17, 2036 UTC.
- Public home CA installed on elephant at `/etc/sssd/pki/ece387-home-ldap-ca.crt`, `root:root`, mode `644`. Its SHA-256 fingerprint was checked against output the user obtained on phoenix:

  ```text
  D0:E3:93:F0:E7:97:92:41:E5:E4:EC:F7:AB:36:9E:12:2F:7B:B4:B5:0E:54:F3:79:BA:77:C0:77:57:68:BF:69
  ```

- `/etc/sssd/sssd.conf` is `root:root`, mode `600`; SSSD is enabled and active. Domain `ece387.local` uses LDAP at `192.168.0.151`, required StartTLS, certificate verification, anonymous student/group searches, and credential caching. No LDAP administrator password is stored. Configuration validation passed, encrypted lookups succeeded, and the user confirmed online domain status and a successful `m3a` password login.
- `m3a` resolves to UID `20000`, GID `10000` (`ece387students`), with home `/home/students/m3a`. Phoenix exports `/home/students` to `192.168.0.0/24`. Autofs is enabled and active, with `/etc/auto.master.d/students.autofs` and `/etc/auto.students` configured for a 600-second idle timeout. An actual NFS 4.2 mount was verified with `hard,timeo=30,retrans=2`, ownership `20000:10000`, and home mode `700`.
- ROS Jazzy Desktop, TurtleBot3 packages, `ros-dev-tools`, Gazebo integration through `ros_gz`, and the guide's ROS vision, hardware, and teleoperation packages are installed. Package checks, `rclpy`/`cv_bridge` imports, and the student's ROS environment test passed. The original missing `/opt/ros/jazzy/setup.bash` warning is resolved.
- VS Code was already installed. The active inotify watch limit is already `524288`, persisted in `/etc/sysctl.d/99-megasync-inotify-limit.conf`; no duplicate setting was added. Course utilities include `tree`, `terminator`, `python3-pip`, `qtwayland5`, and `jstest-gtk`. At the user's request, `obs-studio` was removed from the Jazzy client and standalone setup instructions.
- Local `ece387rescue` has a home on the local ext4 disk and belongs to `dialout`, `video`, and `plugdev`, with no membership in `sudo`. Its password login and writable home passed. Its `.bashrc` loads Jazzy and sets `TURTLEBOT3_MODEL=burger`, `LDS_MODEL=LDS-02`, and `ROS_DOMAIN_ID=99`; those values were verified. Effective sudo permissions for the rescue account were not independently checked.
- `/etc/sudoers.d/ece387-students` grants the guide's approved passwordless package-manager and shutdown/reboot commands. Full sudo syntax validation and `sudo -l -U m3a` passed. The user approved the explanation that package-manager access is effectively full root access.
- `/etc/polkit-1/rules.d/50-ece387-network.rules` grants students the three documented NetworkManager actions. A student `nmcli general permissions` check showed `yes` for all three; hostname modification still requires authentication. Before installation, NetworkManager profiles and `/etc/netplan` were backed up under root-only `/etc/NetworkManager/ece387-backup.KYBDZUDp`.
- `/etc/udev/rules.d/99-ece387.rules` grants mode `0666` to serial devices with vendor `0483` and all video devices. File contents and ownership were verified; the user ran the reload and trigger commands. No matching devices were connected for a functional test.
- `/etc/sysctl.d/61-dmesg.conf` persists `kernel.dmesg_restrict=0`. The active value and unprivileged kernel-log access were verified.
- The user approved an NFS workspace for `m3a` and reported creating `~/master_ws/src`; no `/local` workspace was configured. The user subsequently reported that the requested graphical-login and workspace checks looked good; their detailed output was not captured.

### Deferred or untested

- Robot Wi-Fi is reserved for the user. No robot profiles, interface renaming, or robot connectivity changes were made.
- `dlib`, `pydantic`, `imutils`, and `pupil-apriltags` installation or changes remain deferred. Generative AI blocking was not implemented.
- Reboot persistence, offline student authentication, rescue login during a network outage, actual student network changes, connected hardware access, and a ROS workspace build remain untested.
- Server export options such as `root_squash` were not inspected; `showmount` verified the export path and allowed subnet only. No server configuration changes were made in this client session.
- VS Code student settings seeding was not performed. Review the actual home-server shell template before considering any local-workspace changes; the lab template contains `/local` assumptions, while this home client deliberately uses an NFS workspace.

## Prompt for Codex

```text
Help me configure my home ECE387 login server and master client, using
work completed on master99 and phoenix on November 19, 2026 as a reference.

First, read these files from the latest main branch of the ECE387 repo:
- book/Appendix/login-server.md
- book/Appendix/login-client.md
- book/Appendix/RobotSetupJazzy.md, if needed for network context

The reference documentation was updated in commit f5f7ada:
https://github.com/ECE-387/ece-387.github.io/commit/f5f7adaf9d30b5df00f835aa5a1404677d7986ee

Important working preferences:
- Inspect the existing configuration before changing it.
- Explain each proposed configuration, including its purpose and any
  meaningful tradeoffs, and let me make the final decision before applying it.
- Preserve existing accounts, files, network access, and configurations
  unless I approve a change.
- Do not implement generative AI blocking.
- Do not install or change dlib, pydantic, imutils, or pupil-apriltags
  until we discuss them.
- I will handle robot Wi-Fi connections separately unless I ask for help.
- Do not assume the home machines use the same IP addresses, interface
  names, hardware, or certificates as the lab machines.

Reference: what was completed on master99 and phoenix:
- phoenix was confirmed at 10.99.1.50, serving the LDAP base
  dc=ece387,dc=local.
- phoenix was configured for StartTLS with certificate verification.
  Existing unencrypted LDAP remained available for other clients.
- A dedicated LDAP CA was created. Its private key remains root-only on
  phoenix; only the public CA certificate is distributed to clients.
- master99 uses SSSD with required StartTLS and certificate verification
  for identity lookup and authentication. Anonymous student and group
  lookups work, so the active SSSD configuration does not store the
  LDAP administrator password.
- An online student lookup and password login were tested successfully.
- The student-home autofs map on master99 was changed to hard NFS mounts.
  An existing m3a mount still showed soft and needed to expire or be
  safely remounted before verifying the new option.
- master99 temporarily uses two USB Wi-Fi adapters: one for the lab
  network and one reserved for robots. Students were granted NetworkManager
  permissions, but that access still needs a student test.

For the home setup:
1. Identify the server and client, their addresses, network interfaces,
   operating systems, and existing LDAP, NFS, ROS, and Wi-Fi configuration.
2. Check whether the home server already has TLS and a trusted CA.
   Reuse an existing valid configuration when appropriate; do not
   regenerate or replace a CA without discussing it with me.
3. Propose server TLS and client SSSD settings. The server certificate
   must match the actual address or hostname used by the client.
4. Test encrypted student and group lookups and, when I can enter a
   password locally, test student authentication.
5. Review NFS home directories and discuss hard-mount behavior before
   changing it. Verify actual mount options after any change.
6. Review the local rescue account, student privileges, network-management
   permissions, and workspace location with me before changing them.
7. Keep a record of what was verified, what remains untested, and any
   differences between the home and lab setups.

Start with a read-only inspection and tell me what you find.
```
