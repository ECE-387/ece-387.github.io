# ECE Department Network Topology

## Overview

The ECE department runs a single flat wireless network (SSID `ECE`) fed by
one gateway router, distributed through switches to roughly 20 access
points across classrooms. Two isolated sub-networks — one for ECE387, one
for RobotTeaming — sit behind that main network as private, NAT'd LANs.

```
Comcast (1 Gbps)
      │
      ▼
Main router  10.1.10.1
(NAT + DHCP + DNS for the whole ECE network)
      │
      ├──────────────┐
      ▼              ▼
  Switch 1        Switch 2
      │              │
      ▼              ▼
 ~10 APs         ~10 APs
 (classrooms,    (classrooms,
  SSID: ECE)      SSID: ECE)
      │
      ▼ (one AP also has a private router plugged into it)
  ECE387 WiFi router → 10.99.1.0/24 (own DHCP)
      │
      ▼ (a Netgear Nighthawk, similarly)
  RobotTeaming router → 10.20.1.0/24 (own DHCP)
```

## Main ECE network (10.1.10.0/24)

| Component | Detail |
|---|---|
| Internet uplink | Comcast, 1 Gbps |
| Gateway router | `10.1.10.1` — in the department tech's office |
| DHCP server | Runs on the main router (`10.1.10.1`), leases addresses across the whole `10.1.10.0/24` range |
| DNS server | Also `10.1.10.1` — the main router forwards DNS queries upstream (to Comcast's or a public resolver) for all clients on the subnet |
| Switches | 2 unmanaged/managed switches distributing wired uplinks from the main router to each AP |
| Access points | ~20 total, roughly 10 per switch, one per classroom, all broadcasting SSID `ECE` |
| Subnet | Single flat `/24` — every AP bridges onto the same LAN and DHCP scope, so there is **no per-classroom network segmentation** |

**Why this matters:** because it's one flat subnet, ROS2/DDS multicast
discovery traffic, broadcast traffic, and any misbehaving device on one
classroom's AP are all visible to every other classroom on the same
network.

## ECE387 WiFi (10.99.1.0/24)

This is a **private network riding on top of the main ECE network**, not a
separate physical connection:

1. A router (the ECE387 WiFi router) has its **WAN port plugged into the
   main ECE switch/AP infrastructure**. On that WAN side, it behaves like
   any other client — it gets a `10.1.10.x` address from the main
   network's DHCP server.
2. On its **LAN side**, that same router runs its own independent DHCP
   server, handing out `10.99.1.x` addresses to anything connected to its
   WiFi or LAN ports.
3. NAT on the router means devices on `10.99.1.0/24` can reach the
   internet/main ECE network (through the router), but devices on the
   main ECE network **cannot** see into `10.99.1.0/24` unless the router
   is explicitly configured to forward ports.

This is the same pattern used for the RobotTeaming network below —
just a different subnet.

### Devices on ECE387

| Device | IP | Role |
|---|---|---|
| ECE387 WiFi router | `10.99.1.1` | Router, DHCP for this subnet |
| `ece387server` (NUC9i7QNX1) | `10.99.1.50` | Login server (LDAP, NFS) — static IP |
| `master01`–`master14` | DHCP | Master computers |

## RobotTeaming WiFi (10.20.1.0/24)

Built the same way, using a Netgear Nighthawk router:

1. **WAN side** (optional): plug the Nighthawk's WAN port into the main
   ECE switch/AP if you want RobotTeaming devices to reach the internet
   or the wider ECE network. Leave it unplugged for a fully isolated
   robot-only network.
2. **LAN side**: the Nighthawk's own IP is `10.20.1.1`, with its own DHCP
   server handing out addresses in `10.20.1.0/24` (e.g.
   `10.20.1.10`–`10.20.1.200`) to TurtleBots, the file/login server, and
   any laptops joining the RobotTeaming SSID.

### Configuration steps (Nighthawk admin UI)

1. Connect to the router's factory setup network (label on the unit) and
   log into `http://192.168.1.1` (or `routerlogin.net`).
2. **Advanced → Setup → LAN Setup**: set router IP to `10.20.1.1`,
   subnet mask `255.255.255.0`.
3. Enable **Use Router as DHCP Server**, range `10.20.1.10`–`10.20.1.200`.
4. **Wireless Setup**: SSID `RobotTeaming`, WPA2/WPA3-Personal, strong
   passphrase.
5. **Internet Setup**: set to DHCP if the WAN port is plugged into the
   ECE network; otherwise leave WAN disconnected for full isolation.
6. Apply, then reboot and reconnect devices to confirm they receive
   `10.20.1.x` addresses.

### Devices currently on RobotTeaming

| Device | IP | Role |
|---|---|---|
| Netgear Nighthawk | `10.20.1.1` | Router, DHCP/DNS for this subnet |
| GTX1080 desktop | `10.20.1.50` | Login/file server (SSH, NFS) — static IP, dual-homed with WiFi used only for internet egress (split-routing, not a gateway for this subnet) |

## Home network (192.168.0.0/24)

Not part of the ECE network. It holds `phoenix`, a second login server that is
nearly identical to `ece387server`.

| Device | IP | Role |
|---|---|---|
| Home router | `192.168.0.1` | Router, DHCP for this subnet |
| `phoenix` (NUC9i7QNX1) | `192.168.0.151` | Login server (LDAP, NFS) — static IP on Wi-Fi (`wlp4s0`) |

## Key takeaways

- The ECE network is a **single flat subnet** with no VLAN segmentation
  between classrooms — a real consideration for ROS2/DDS multicast
  traffic.
- ECE387 and RobotTeaming are both **private NAT'd sub-networks**,
  logically isolated from the main ECE network and from each other,
  each with their own DHCP scope.
- Any server placed on RobotTeaming (e.g. the file/login server) should
  keep its default route pointed at whichever interface provides
  internet access, while treating `10.20.1.0/24` as a directly-connected,
  gateway-less subnet for local traffic only.
