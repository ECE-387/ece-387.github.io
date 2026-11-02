# Applying Changes — Existing Login Server

Brings an already-built `ece387server` in line with the current [login-server.md](login-server.md). Every step verifies the current state first and only changes what is actually stale, so it is safe to run on a server that is already partly correct.

**Run order across machines:** robot → **server** → client. The client guide restarts `autofs`, which must happen *after* the export change in Step 4 below.

**Time:** about 20 minutes. No student-visible downtime except a few seconds during Step 4.

**Log in as your admin user on the login server** (`stanbaek@ece387server`). Everything here runs locally on the server.

---

## Step 0 — Back up

```bash
sudo mkdir -p /root/pre-migration-$(date +%F)
BK=/root/pre-migration-$(date +%F)
sudo cp /etc/exports "$BK/"
sudo cp -r /etc/ece387 "$BK/"
sudo tar czf "$BK/student-dotfiles.tar.gz" /home/students/a27-*/.bashrc /home/students/a27-*/.inputrc 2>/dev/null
ls -la "$BK"
```

The tarball matters: Step 5 overwrites `.bashrc` on all 62 accounts, and if any student has customized theirs, this is the only copy.

---

## Step 1 — Check what is actually stale

```bash
grep -n "ssh_robot\|bringup\|ROS_DOMAIN_ID" /etc/ece387/bashrc_template
```

Compare against what it should be:

| Line | Current (likely) | Should be |
|---|---|---|
| `ssh_robot` | `ssh pi@192.168.4.1` | `ssh pi@192.168.50.1` |
| `bringup` | `ssh pi@robotX ...` | `ssh pi@192.168.50.1 ...` |
| `ROS_DOMAIN_ID` comment | "Each student should set this..." | states the robot-number matching rule |

Also confirm the structural pieces landed in your earlier work:

```bash
# Should print the interactive guard, the $include, and the colcon_cd lines
grep -c 'if \[\[ \$- != \*i\* \]\]' /etc/ece387/bashrc_template
grep -c 'colcon_cd.sh'              /etc/ece387/bashrc_template
grep -c '\$include /etc/inputrc'    /etc/ece387/inputrc_template
```

All three should print `1`. If any prints `0`, that piece is missing and Step 2 will fix it.

---

## Step 2 — Rewrite `bashrc_template`

Re-run the `sudo tee /etc/ece387/bashrc_template` block from **§1.6 of login-server.md** exactly as written. It is idempotent — it replaces the file wholesale, so it does not matter what state the current one is in.

Do not hand-edit the three stale lines instead. The doc version is the single source of truth; patching by hand is how the file drifted in the first place.

Verify:

```bash
bash -n /etc/ece387/bashrc_template && echo "syntax OK"
grep -n "ssh_robot\|bringup" /etc/ece387/bashrc_template
```

Both aliases should now show `192.168.50.1`.

---

## Step 3 — Verify `inputrc_template`

If Step 1 showed `$include /etc/inputrc` present, this file is already current and needs nothing. Otherwise re-run the `sudo tee /etc/ece387/inputrc_template` block from §1.6.

```bash
bind -f /etc/ece387/inputrc_template && echo "readline accepted it"
```

Readline fails silently on a bad binding, so this check is the only signal you get.

---

## Step 4 — Switch the NFS export to `root_squash`

This is the change that actually isolates students from each other. With `no_root_squash`, any student who obtains root on a master — reachable through `sudo apt` or `sudo pip`, both on the whitelist — can read every other student's home directory.

First, check for root-owned files inside student homes. After the switch these become editable only from the server:

```bash
sudo find /home/students -maxdepth 2 -user root
```

Empty output is expected. If anything appears, `chown` it to the owning student before continuing.

Then flip the option:

```bash
sudo sed -i 's/no_root_squash/root_squash/' /etc/exports
cat /etc/exports
```

The line should read:

```
/home/students  10.99.1.0/24(rw,sync,no_subtree_check,root_squash)
```

Apply it:

```bash
sudo exportfs -rav
sudo exportfs -v
```

`exportfs -v` should now show `root_squash` in the option list. No service restart is needed and logged-in students are not disconnected.

> **What you give up:** administrative edits to student files from a master stop working. Do them here on the server instead, where `sudo` still means what it always did.

---

## Step 5 — Push the templates to all 62 accounts

See what you are about to overwrite:

```bash
sudo bash -c 'for f in /home/students/a27-*/.bashrc; do
  cmp -s /etc/ece387/bashrc_template "$f" || echo "MODIFIED: $f"
done'
```

Every account will be listed, since Step 2 just changed the template. If you want to know whether any student had *also* customized theirs, compare against the backup from Step 0 instead.

Push:

```bash
for dir in /home/students/a27-*/; do
  user=$(basename "$dir")
  uid=$(stat -c %u "$dir")
  sudo cp /etc/ece387/bashrc_template "${dir}.bashrc"   || { echo "FAILED: $user"; continue; }
  sudo cp /etc/ece387/inputrc_template "${dir}.inputrc" || { echo "FAILED: $user"; continue; }
  sudo chown "${uid}:10000" "${dir}.bashrc" "${dir}.inputrc"
  echo "Updated: $user (uid=$uid)"
done
```

Expect 62 `Updated:` lines with sensible UIDs (`20000`–`20030`, `21000`–`21030`) and no `FAILED:` lines.

> Use `stat -c %u`, not `id -u "$user"`. This server hosts LDAP but is not an LDAP *client*, so NSS here cannot resolve student names and `id` fails silently — leaving `chown` a no-op.

Verify ownership. The glob must be expanded inside the elevated shell, because student home directories are `chmod 700`:

```bash
# Empty output = all 62 correct
sudo find /home/students -maxdepth 2 -name '.bashrc' -user root
```

---

## Step 6 — Create the wheel directory

The masters fetch a prebuilt `dlib` wheel from here rather than compiling for 45 minutes each.

```bash
sudo mkdir -p /srv/ece387/wheels/x86_64 /srv/ece387/wheels/aarch64
sudo chmod 755 /srv/ece387/wheels
```

Separate directories per architecture — a wheel built on a robot is tagged `linux_aarch64` and will not install on a master. Populate them when you build the wheels (client guide, Step 6).

---

## Step 7 — Update `create_students.sh`

Only matters if you ever rebuild or add students, but fix it now while you are here. Open it:

```bash
nano ~/Documents/ece387/create_students.sh
```

Delete these two lines if present:

```bash
sudo cp /etc/ece387/bashrc_template /home/students/${USERNAME}/.bashrc
sudo cp /etc/ece387/inputrc_template /home/students/${USERNAME}/.inputrc
```

The script now creates home directories from `/etc/skel` only; the templates arrive via the Step 5 push. This removes a build-order trap — as written, the script copies from `/etc/ece387` before that directory exists in a fresh build, and `set -e` aborts on the first student.

```bash
bash -n ~/Documents/ece387/create_students.sh && echo "syntax OK"
```

---

## Verification

```bash
# Templates current
grep -c "192.168.50.1" /etc/ece387/bashrc_template        # expect 2
bash -n /etc/ece387/bashrc_template && echo "template OK"

# Export correct
sudo exportfs -v | grep root_squash

# All accounts pushed and owned correctly
sudo find /home/students -maxdepth 2 -name '.bashrc' -user root   # expect no output
sudo ls -ln /home/students/a27-m0/.bashrc                          # expect 20000 10000

# Services healthy
sudo systemctl status slapd nfs-kernel-server --no-pager | grep Active
```

Then continue to the **client** guide. `root_squash` does not fully take effect on a master until its `autofs` is restarted.

---

## Rolling back

```bash
BK=/root/pre-migration-$(date +%F)
sudo cp "$BK/exports" /etc/exports && sudo exportfs -rav
sudo cp -r "$BK/ece387/." /etc/ece387/
sudo tar xzf "$BK/student-dotfiles.tar.gz" -C /
```

The tarball restores paths relative to `/`, so it puts each `.bashrc` back where it came from.
