# ECE387 Home Server and Client Setup Handoff

Use this handoff to continue the ECE387 setup on a home login server and master client. Give the prompt below to Codex on either machine. The configuration recorded here reflects work through November 19, 2026; inspect the current state before making changes.

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
