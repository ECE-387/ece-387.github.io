# Blocking GenAI Access on Master Computers

Restricting access to generative AI websites and AI coding assistants on the ECE 387 master computers. Written to be applied to a single machine that is then cloned to the rest of the fleet with Clonezilla.

**Companion guides:** [Master (Client) Setup](login-client.md) · [Login Server Setup](login-server.md)

---

## What this can and cannot do

Be clear-eyed about this before investing effort in it.

**What it achieves:** removes the easy paths, makes the policy unambiguous rather than implied, and produces a record of deliberate circumvention. In an honor-code environment that record is usually worth more than the block itself — a student who has to clear an immutable flag to reach ChatGPT cannot claim they wandered there by accident.

**What it does not achieve:** stopping a determined student. They have phones. They have laptops. And, critically, several commands on the current sudo whitelist lead to full root, and root defeats everything here. Section 1 closes those, and **without Section 1 the rest is decoration.**

The honest framing to give students: this is a technical statement of an academic-integrity policy, not a wall.

---

## 1. Close the root escalation paths

**Do this first.** Every other layer assumes students cannot become root.

### Why the current whitelist grants root

`/etc/sudoers.d/ece387-students` currently permits `apt`, `pip`, and `systemctl`. All three are escalation paths, not through bugs but through what those tools do by design:

| Command | Why it is root |
|---|---|
| `sudo apt -o APT::Update::Pre-Invoke::=<cmd>` | apt runs configuration hooks as root; `-o` sets them on the command line |
| `sudo apt install ./anything.deb` | `.deb` packages carry `preinst`/`postinst` scripts that dpkg runs as root. Anyone can build a `.deb` |
| `sudo pip install <sdist>` | pip executes the package's `setup.py` to build it — arbitrary code, as root |
| `sudo systemctl edit <unit>` | Opens `$EDITOR` as root; set `EDITOR` to a shell and you have a root shell |

Package managers install software, and installing software means running someone else's code with privilege. There is no way to permit these safely.

### Why cloning makes removal practical

The reason `apt` and `pip` were on the whitelist is that students occasionally needed a package mid-lab. With Clonezilla, every package is baked into the image instead, so that need largely disappears — and any genuine gap is fixed by re-imaging or an Ansible push, which is the same discipline that keeps 14 benches from drifting apart.

### The change

**The whitelist is defined in [login-client.md §1.6](login-client.md).** Apply the version there — it is the single source of truth, and duplicating it here would guarantee the two drift apart.

**`ECE387_PKG` (apt, apt-get, dpkg, pip) is intentionally retained**, because students resolving their own dependencies is part of the course. That decision has a direct consequence for this document, and it is important to state plainly:

**A student who wants to reach a GenAI site can. Everything below is a deterrent, not a control.** `sudo apt` and `sudo pip` both run arbitrary code as root, root clears `chattr +i`, and cleared flags mean editable hosts files and browser policies.

So the goal shifts. These layers make the policy explicit, remove any claim of stumbling into a violation, and — critically — **produce a timestamped record of deliberate circumvention.** That record is the enforcement mechanism in an honor-code environment; the technical block is what makes reaching for it a conscious act.

Because of this, **§7 audit logging is not optional in this configuration.** Skip it and the rest is unverifiable.

These are excluded and should stay excluded — each is a root path with no offsetting pedagogical value:

```
systemctl  rosdep  colcon  nmcli  ip
```

Verify on the image before cloning:

```bash
sudo cat /etc/sudoers.d/ece387-students
sudo -l -U a27-m0
```

Expect `apt`, `apt-get`, `dpkg`, `pip`, `pip3`, `shutdown`, `reboot` — and nothing else.

> §1.6 also covers `pip install --user --break-system-packages`, which needs no sudo, lands in the student's NFS home, and follows them between benches. Teaching it as the default reduces how often students reach for `sudo pip` at all.

---

## 2. Network-level blocking

The only layer students cannot touch from the master, and the only one that also covers phones and laptops on the same network. Everything else is defense in depth.

Ask whoever administers the `ECE387` router to block the domains in the appendix for that subnet.

> **Your masters have three paths to the internet:** `ECE387`, `AF_ACADEMY_GUEST`, and `ECE` (see login-client.md §1.7). A block applied only to `ECE387` leaves the other two open. Either cover all three, or remove the alternates from the netplan config so masters have exactly one route out.

---

## 3. Browser policy files

### How it works

Chrome and Firefox both read enterprise policy from root-owned files on disk at startup. Policies set this way cannot be overridden from the browser's settings UI, do not appear as an extension the student can disable, and apply to every profile including guest and incognito.

This is strictly better than a hosts file for browsers, for two reasons. It understands **URL paths**, so `huggingface.co/chat` can be blocked while model downloads keep working. And it can **disable DNS-over-HTTPS** — with DoH enabled, the browser resolves names through its own encrypted channel and never consults `/etc/hosts`, which is why hosts-file blocking quietly fails on modern browsers.

### Chrome

```bash
sudo mkdir -p /etc/opt/chrome/policies/managed
sudo tee /etc/opt/chrome/policies/managed/ece387.json > /dev/null << 'EOF'
{
  "URLBlocklist": [
    "chatgpt.com", "chat.openai.com", "openai.com",
    "claude.ai", "anthropic.com",
    "gemini.google.com", "aistudio.google.com", "bard.google.com",
    "copilot.microsoft.com", "bing.com/chat", "github.com/copilot",
    "perplexity.ai", "poe.com", "character.ai",
    "chat.mistral.ai", "chat.deepseek.com",
    "grok.com", "x.ai", "meta.ai",
    "you.com", "phind.com", "blackbox.ai", "v0.dev",
    "codeium.com", "windsurf.com", "tabnine.com", "cursor.com",
    "huggingface.co/chat", "chat.qwen.ai", "kimi.moonshot.cn",
    "notebooklm.google.com", "gamma.app", "quillbot.com"
  ],
  "URLAllowlist": [
    "docs.ros.org", "github.com", "stackoverflow.com"
  ],
  "DnsOverHttpsMode": "off",
  "IncognitoModeAvailability": 1,
  "BrowserSignin": 0
}
EOF
```

`URLAllowlist` takes precedence over the blocklist, so `github.com` stays usable while `github.com/copilot` is blocked — allowlist entries win only where they are at least as specific.

`IncognitoModeAvailability: 1` disables incognito. `BrowserSignin: 0` prevents signing into a Google account, which otherwise syncs a student's own settings down over yours.

### Firefox

```bash
sudo mkdir -p /etc/firefox/policies
sudo tee /etc/firefox/policies/policies.json > /dev/null << 'EOF'
{
  "policies": {
    "WebsiteFilter": {
      "Block": [
        "*://chatgpt.com/*", "*://chat.openai.com/*",
        "*://claude.ai/*", "*://gemini.google.com/*",
        "*://copilot.microsoft.com/*", "*://perplexity.ai/*",
        "*://poe.com/*", "*://character.ai/*",
        "*://chat.deepseek.com/*", "*://grok.com/*",
        "*://you.com/*", "*://phind.com/*"
      ],
      "Exceptions": ["*://docs.ros.org/*"]
    },
    "DNSOverHTTPS": { "Enabled": false, "Locked": true },
    "DisablePrivateBrowsing": true,
    "DisableFirefoxAccounts": true,
    "BlockAboutConfig": true
  }
}
EOF
```

> Firefox's `WebsiteFilter` accepts at most 1000 patterns and requires the `*://` scheme prefix. `BlockAboutConfig` matters — without it a student can re-enable DoH from `about:config`.

Verify after restarting each browser: visit `chrome://policy` or `about:policies`.

---

## 4. `/etc/hosts` backstop

### How it works

Browsers are covered above. This layer catches everything else: `curl`, Python SDKs, VS Code extensions, and any other program that resolves a hostname the ordinary way. Mapping a name to `0.0.0.0` makes the connection fail immediately rather than hang.

```bash
sudo tee -a /etc/hosts > /dev/null << 'EOF'

# ECE 387 — GenAI block
0.0.0.0 chatgpt.com www.chatgpt.com chat.openai.com api.openai.com
0.0.0.0 claude.ai www.claude.ai api.anthropic.com
0.0.0.0 gemini.google.com generativelanguage.googleapis.com
0.0.0.0 copilot.microsoft.com
0.0.0.0 perplexity.ai www.perplexity.ai
0.0.0.0 poe.com character.ai
0.0.0.0 chat.deepseek.com api.deepseek.com
0.0.0.0 api.x.ai grok.com
0.0.0.0 you.com phind.com blackbox.ai

# AI coding assistants — API endpoints, not just the websites
0.0.0.0 api.githubcopilot.com copilot-proxy.githubusercontent.com
0.0.0.0 api.individual.githubcopilot.com proxy.individual.githubcopilot.com
0.0.0.0 default.exp-tas.com
0.0.0.0 codeium.com server.codeium.com inference.codeium.com
0.0.0.0 api.tabnine.com update.tabnine.com
0.0.0.0 api.continue.dev
0.0.0.0 sourcegraph.com cody-gateway.sourcegraph.com
EOF
```

The API endpoints matter more than the websites. Blocking `api.githubcopilot.com` disables Copilot even if a student installs the extension — the completions simply never return.

---

## 5. VS Code

Three mechanisms, in increasing order of durability.

### 5a. Extension allowlist

VS Code 1.96+ supports blocking extensions by ID. Add to the settings file seeded from `/etc/skel` on the login server:

```bash
# On ece387server
sudo mkdir -p /etc/skel/.config/Code/User
sudo tee /etc/skel/.config/Code/User/settings.json > /dev/null << 'EOF'
{
  "extensions.allowed": {
    "*": true,
    "github.copilot": false,
    "github.copilot-chat": false,
    "codeium.codeium": false,
    "tabnine.tabnine-vscode": false,
    "continue.continue": false,
    "sourcegraph.cody-ai": false,
    "amazonwebservices.amazon-q-vscode": false,
    "google.geminicodeassist": false,
    "blackboxapp.blackbox": false
  },
  "chat.commandCenter.enabled": false,
  "github.copilot.enable": { "*": false },
  "workbench.commandPalette.experimental.suggestCommands": false,

  "files.watcherExclude": {
    "**/build/**": true, "**/install/**": true, "**/log/**": true
  },
  "search.exclude": {
    "**/build/**": true, "**/install/**": true, "**/log/**": true
  }
}
EOF
```

This is a blocklist, so it needs maintenance as new AI extensions appear. Fine as a layer, not sufficient alone.

### 5b. Block the marketplace (recommended)

Far more durable, and cloning makes it practical. Pre-install every extension students need into the image, then make the marketplace unreachable:

```bash
# In the image, as the account whose extensions get cloned
code --install-extension ms-python.python
code --install-extension ms-vscode.cpptools
code --install-extension ms-iot.vscode-ros
code --install-extension twxs.cmake
code --install-extension redhat.vscode-yaml
```

```bash
sudo tee -a /etc/hosts > /dev/null << 'EOF'

# VS Code marketplace — extensions are pre-installed in the image
0.0.0.0 marketplace.visualstudio.com
0.0.0.0 vscode.blob.core.windows.net
0.0.0.0 vscode.download.prss.microsoft.com
EOF
```

No new extension can be installed at all, so there is no blocklist to keep current. The cost: every legitimate extension request comes to you and is handled by re-imaging or Ansible.

> **Extensions live in `~/.vscode/extensions`, which is on NFS.** If you pre-install into the image, they land on the *master's local disk* under the build account and students will not see them. Either install them into `/etc/skel/.vscode/extensions` on the login server so new accounts inherit them, or push them into the existing 62 home directories with a loop. Verify this before cloning — it is the step most likely to be missed.

### 5c. Disable telemetry and remote sign-in

```json
"telemetry.telemetryLevel": "off",
"workbench.enableExperiments": false
```

Prevents VS Code fetching remote configuration that could re-enable chat features.

---

## 6. Protect the configuration from tampering

### How the immutable flag works

`chattr +i` sets a flag in the file's **inode** — filesystem metadata, separate from the `rwx` permission bits. The kernel checks it in the VFS layer *before* consulting ownership, so the file cannot be modified, deleted, renamed, or hard-linked. Not by its owner, not by root.

```bash
for f in /etc/hosts \
         /etc/opt/chrome/policies/managed/ece387.json \
         /etc/firefox/policies/policies.json \
         /etc/sudoers.d/ece387-students; do
    sudo chattr +i "$f"
done

lsattr /etc/hosts       # expect ----i---------e-------
```

Test it:

```bash
sudo sh -c 'echo test >> /etc/hosts'
# sh: /etc/hosts: Operation not permitted
```

**To edit a protected file yourself:**

```bash
sudo chattr -i /etc/hosts
sudo nano /etc/hosts
sudo chattr +i /etc/hosts
```

**The limit:** clearing the flag needs the `CAP_LINUX_IMMUTABLE` capability, which root has. So `chattr +i` is only as strong as the guarantee that students cannot become root — which is Section 1's job. With Section 1 applied there is no supported path to root, and the flag holds. Without it, `chattr -i` is one command away.

The flag lives in the inode and Clonezilla copies blocks, so **flagged files stay flagged through cloning.** Set them during image prep.

> Apply the flag *after* setting the machine's hostname. If `cloud-init` has `manage_etc_hosts` enabled it rewrites `/etc/hosts` at boot, and an immutable file will make that fail — possibly silently — on every clone.

### Self-healing backstop

Restores the file if the flag is ever cleared, and logs the event:

```bash
sudo cp /etc/hosts /etc/hosts.ece387
sudo chattr +i /etc/hosts.ece387

sudo tee /usr/local/sbin/restore-hosts.sh > /dev/null << 'EOF'
#!/bin/bash
if ! cmp -s /etc/hosts.ece387 /etc/hosts; then
    WHO=$(ausearch -k ece387_hosts -ts recent -i 2>/dev/null \
          | grep -oP 'AUID="\K[^"]+' | tail -1)
    logger -t ece387 "hosts modified on $(hostname) by ${WHO:-unknown} — restoring"
    chattr -i /etc/hosts 2>/dev/null
    cp /etc/hosts.ece387 /etc/hosts
    chattr +i /etc/hosts
fi
EOF
sudo chmod 700 /usr/local/sbin/restore-hosts.sh
```

```bash
sudo tee /etc/systemd/system/ece387-restore-hosts.service > /dev/null << 'EOF'
[Unit]
Description=Restore ECE387 hosts file if modified
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/restore-hosts.sh
EOF

sudo tee /etc/systemd/system/ece387-restore-hosts.timer > /dev/null << 'EOF'
[Unit]
Description=Check ECE387 hosts file every 2 minutes
[Timer]
OnBootSec=2min
OnUnitActiveSec=2min
[Install]
WantedBy=timers.target
EOF

sudo systemctl enable --now ece387-restore-hosts.timer
sudo systemctl list-timers ece387-restore-hosts.timer
```

---

## 7. Audit logging

### How it works

`auditd` records syscalls at the kernel level. The field that matters is **`auid`** — the audit UID, set at login and **immutable through `sudo` and `su`**. A student who escalates to root still shows their own `auid`, so the log identifies the person rather than "root."

```bash
sudo apt install -y auditd

sudo tee /etc/audit/rules.d/ece387.rules > /dev/null << 'EOF'
# Writes and attribute changes to protected files
-w /etc/hosts -p wa -k ece387_hosts
-w /etc/sudoers.d/ece387-students -p wa -k ece387_sudoers
-w /etc/opt/chrome/policies/managed/ -p wa -k ece387_policy
-w /etc/firefox/policies/ -p wa -k ece387_policy

# Any non-system user running chattr — the only way to clear the immutable flag
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/chattr \
   -F auid>=1000 -F auid!=unset -k ece387_chattr
EOF

sudo augenrules --load
sudo auditctl -l
```

`auid>=1000` excludes system daemons, so only human actions appear.

Reading the log — `-i` resolves numeric IDs through NSS, which means SSSD turns them into LDAP usernames:

```bash
sudo ausearch -k ece387_hosts -i --start today
sudo ausearch -k ece387_chattr -i --start today | grep -E 'AUID|EXE'
```

### Forward logs off the machine

Local logs sit on a machine the student may control. Off-box copies are what hold up if something becomes an honor case:

```bash
echo '*.* @@10.99.1.50:514' | sudo tee /etc/rsyslog.d/60-ece387.conf
sudo systemctl restart rsyslog
```

Enable the receiver on `ece387server` (`imtcp` in `/etc/rsyslog.conf`) and open the port to the lab subnet only:

```bash
# On ece387server
sudo ufw allow from 10.99.1.0/24 to any port 514 proto tcp
```

---

## 8. Verification before cloning

Run every check on the source image. A mistake here propagates to all 14 machines.

```bash
# 1. Students cannot escalate — expect NO apt, pip, dpkg, or systemctl
sudo -l -U a27-m0

# 2. Immutable flags set
lsattr /etc/hosts /etc/sudoers.d/ece387-students \
       /etc/opt/chrome/policies/managed/ece387.json | grep -c '^....i'

# 3. Hosts blocking works
getent hosts chatgpt.com          # expect 0.0.0.0
curl -sS --max-time 5 https://api.githubcopilot.com ; echo "exit=$?"

# 4. Audit rules loaded
sudo auditctl -l | grep ece387

# 5. Self-heal timer running
sudo systemctl is-active ece387-restore-hosts.timer

# 6. Log forwarding
logger -t ece387 "clone image verification test"
# then on ece387server: sudo journalctl -t ece387 --since "5 min ago"
```

Then log in as a real student account and confirm by hand:

- Chrome: `chrome://policy` lists the blocklist; visiting `chatgpt.com` is blocked
- Firefox: `about:policies` shows the filter; `about:config` is inaccessible
- VS Code: Extensions view cannot reach the marketplace; the required extensions are present
- Terminal: `sudo apt install cowsay` is refused

---

## 9. Ongoing maintenance

New services appear constantly, so treat the domain list as living. Once a term:

```bash
sudo chattr -i /etc/hosts
sudo nano /etc/hosts
sudo chattr +i /etc/hosts
sudo systemctl restart ece387-restore-hosts.timer   # picks up the new baseline
sudo cp /etc/hosts /etc/hosts.ece387                # update the pristine copy first!
```

> Update `/etc/hosts.ece387` whenever you change `/etc/hosts`, or the timer will revert your edit within two minutes and it will look as though the change did not save.

Push changes to the fleet with Ansible rather than re-cloning — see login-client.md §4. Remember to `chattr -i` before writing and `+i` after, on each host.

---

## Appendix — Domain reference

| Category | Domains |
|---|---|
| **General chat** | chatgpt.com, chat.openai.com, claude.ai, gemini.google.com, copilot.microsoft.com, perplexity.ai, poe.com, character.ai, meta.ai, grok.com, chat.deepseek.com, chat.mistral.ai, chat.qwen.ai |
| **Search-style** | you.com, phind.com, blackbox.ai, notebooklm.google.com |
| **Coding assistants (sites)** | codeium.com, windsurf.com, tabnine.com, cursor.com, v0.dev, continue.dev |
| **Coding assistants (APIs)** | api.githubcopilot.com, copilot-proxy.githubusercontent.com, api.individual.githubcopilot.com, server.codeium.com, api.tabnine.com, api.continue.dev, cody-gateway.sourcegraph.com |
| **Model APIs** | api.openai.com, api.anthropic.com, generativelanguage.googleapis.com, api.deepseek.com, api.x.ai |
| **Writing tools** | quillbot.com, gamma.app |
| **VS Code marketplace** | marketplace.visualstudio.com, vscode.blob.core.windows.net, vscode.download.prss.microsoft.com |
