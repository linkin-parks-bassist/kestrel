---
status: "unverified"
source: Source audit and build probes, 2026-09-20; user publication instruction
updated_at: "2026-09-20T00:22:23+10:00"
---
Status: Green

Three local knowledge roots are initialized. Source-backed audit leaves cover broad architecture and fine implementation paths in the Interface and Core, including known stubs, defects and build blockers. The Interface generated Doxygen docs/html tree (14,750 tracked files) was removed; its authored guide and Doxyfile remain. This audit is being published on the knowledge-trees branch in all three repositories, with child commits recorded by the superproject gitlinks. See how/to/publish/changes/across/the/three/kestrel/repositories.md for publication order.

Source comparison found matching numeric command, data request and opcode constants across the MCU/FPGA boundary. No hardware interoperability test, FPGA simulation or ESP-IDF build has been run in this audit. Desktop tests cannot complete here without SDL2 configuration; make lib has a distinct compile failure. The host login-shell .cargo/env error was fixed by removing the obsolete source line from ~/.profile; see the global cargo leaf. That host change is outside these repositories.
