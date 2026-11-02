# Applying Changes — Existing Robot

Brings an already-built TurtleBot3 in line with the current [RobotSetupJazzy.md](RobotSetupJazzy.md).

**Run this first**, before the server and client guides. It is independent of both, and Step 1 fixes a problem the client guide otherwise has to work around on all 14 masters individually.

**Time:** about 10 minutes per robot. Repeat on every robot in the fleet.

Connect to the robot's access point from a master, then:

```bash
ssh pi@192.168.50.1
```

---

## Step 0 — Back up

```bash
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.pre-migration
cp ~/.bashrc ~/.bashrc.pre-migration
```

---

## Step 1 — Stop the robot advertising itself as a gateway

**This is the important one.** The robot runs a DHCP server for whatever connects to its access point. By default `dnsmasq` sends DHCP option 3 — the default gateway — pointing at itself.

The consequence: the moment a student connects a master to this robot, the master is told to route *all* traffic through `192.168.50.1`. The login server, NFS home directories, and internet all become unreachable, while the robot itself keeps responding normally. It presents as a server outage, and students will spend the period checking the wrong thing.

The master only ever needs to reach `192.168.50.0/24`, and it gets a direct route to that subnet automatically from its own address on it. No gateway is required.

```bash
sudo nano /etc/dnsmasq.conf
```

Check whether the fix is already present:

```bash
grep -n "dhcp-option" /etc/dnsmasq.conf
```

If nothing is returned, add this after the `dhcp-range` line:

```ini
# Do NOT advertise a default gateway. An empty value means "send nothing".
#
# Without this, dnsmasq offers itself (192.168.50.1) as the default route, and
# any master that connects loses the login server, NFS, and the internet.
dhcp-option=3
```

Apply:

```bash
sudo systemctl restart dnsmasq
sudo systemctl status dnsmasq --no-pager | grep Active
```

> You do **not** need `dhcp-option=6` (DNS). The existing `port=0` already disables dnsmasq's DNS server entirely, so it cannot advertise a resolver it is not running. Nothing on the robot link resolves names — the master reaches the robot at a hardcoded `192.168.50.1`, and ROS 2 discovery advertises IP addresses rather than hostnames.

**Verify from a master.** Reconnect to this robot's AP so it picks up a fresh lease, then:

```bash
ping -c 3 192.168.50.1        # robot still reachable
ping -c 3 10.99.1.50          # lab network still reachable
ip route | grep default        # must NOT be via 192.168.50.1
```

A client holding an old lease will keep the stale gateway until the lease renews. Toggling the WiFi connection off and on forces it.

---

## Step 2 — Set `ROS_DOMAIN_ID` to the robot number

Earlier guidance gave a self-contradictory example (`ROS_DOMAIN_ID=9` for `robot99`). The rule is simple: **the domain ID equals the robot number, and the master must use the same value.**

A mismatch fails silently — `ros2 topic list` on the master returns nothing at all, with no error message, which looks exactly like a network problem.

```bash
hostname                              # e.g. robot7
grep ROS_DOMAIN_ID ~/.bashrc
```

If the value does not match the number in the hostname, fix it:

```bash
sed -i '/ROS_DOMAIN_ID/d' ~/.bashrc
echo "export ROS_DOMAIN_ID=7" >> ~/.bashrc      # replace 7 with this robot's number
source ~/.bashrc
echo $ROS_DOMAIN_ID
```

Valid range is 0–101, so robot numbers 0–30 are all safe.

Repeat for every user account on the robot that runs ROS.

---

## Step 3 — Confirm the SSID matches the hostname

`hostapd` generates its config from the hostname at boot, so `robot7` should broadcast an access point named `robot7`. No zero padding — the fleet is `robot0` through `robot30`, not `robot00`.

```bash
hostname
grep "^ssid" /etc/hostapd/hostapd.conf
```

The two must agree. If they do not, the generator did not run:

```bash
sudo systemctl status hostapd-config --no-pager      # or whichever unit generates it
sudo systemctl restart hostapd
```

If the hostname itself is wrong:

```bash
sudo hostnamectl set-hostname robot7
sudo reboot
```

---

## Step 4 — Check the ROS environment matches the masters

These must agree with the master's `.bashrc` or nodes will not interoperate:

```bash
grep -E "TURTLEBOT3_MODEL|LDS_MODEL|RMW_IMPLEMENTATION|ROS_DISTRO" ~/.bashrc
echo $ROS_DISTRO
```

Expected:

| Variable | Value |
|---|---|
| `TURTLEBOT3_MODEL` | `burger` |
| `LDS_MODEL` | `LDS-02` (or `LDS-03` if this robot has the newer LIDAR) |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` |
| `ROS_DISTRO` | `jazzy` |

If `RMW_IMPLEMENTATION` is missing, add it — the masters set it explicitly, and a mismatched DDS implementation is another silent, total failure:

```bash
echo "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp" >> ~/.bashrc
source ~/.bashrc
```

If `LDS_MODEL` is wrong for the hardware, the LIDAR will connect but return garbage. Check the sensor before assuming.

---

## Step 5 — Build the aarch64 dlib wheel (once for the fleet)

Only needed if the robots use `dlib`, and only on **one** robot. Everything else installs the result.

```bash
source ~/robot_env/bin/activate
pip install wheel
pip download dlib
python3 -m pip wheel dlib-*.tar.gz          # slow on a Pi; leave it running
```

Copy it to the login server so it survives re-imaging:

```bash
scp dlib-*-linux_aarch64.whl stanbaek@10.99.1.50:/srv/ece387/wheels/aarch64/
```

On every other robot:

```bash
source ~/robot_env/bin/activate
scp stanbaek@10.99.1.50:/srv/ece387/wheels/aarch64/dlib-*.whl ~/
pip install ~/dlib-*.whl
```

> The robots keep their virtual environment; the masters install system-wide. That difference is intentional — do not "fix" it. The wheels are **not** interchangeable: `linux_aarch64` here, `linux_x86_64` on the masters.

---

## Verification

On the robot:

```bash
hostname
echo $ROS_DOMAIN_ID $TURTLEBOT3_MODEL $LDS_MODEL $ROS_DISTRO
grep dhcp-option /etc/dnsmasq.conf
systemctl is-active dnsmasq hostapd
```

From a master connected to this robot:

```bash
ip route | grep default              # NOT via 192.168.50.1
ping -c 2 10.99.1.50                 # lab network alive
export ROS_DOMAIN_ID=7               # this robot's number
ssh pi@192.168.50.1 'ros2 launch turtlebot3_bringup robot.launch.py' &
sleep 10
ros2 topic list                      # expect /scan, /odom, /cmd_vel, ...
```

An empty `ros2 topic list` with the robot otherwise reachable means a `ROS_DOMAIN_ID` or `RMW_IMPLEMENTATION` mismatch, not a network fault.

---

## Repeat for every robot

Steps 1–4 are per-robot. Step 5 is once for the whole fleet.

Track which robots are done — a fleet where some advertise a gateway and some do not produces intermittent, bench-dependent failures that are considerably harder to diagnose than a uniform breakage.

---

## Rolling back

```bash
sudo cp /etc/dnsmasq.conf.pre-migration /etc/dnsmasq.conf
sudo systemctl restart dnsmasq
cp ~/.bashrc.pre-migration ~/.bashrc
```
