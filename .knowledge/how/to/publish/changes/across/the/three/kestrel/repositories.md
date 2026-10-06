---
status: green
revised_at: "2026-10-06T17:23:43+11:00"
---

Commit and push each changed child repository before committing its new gitlink in the superproject. Configured origins are linkin-parks-bassist/m-interface, m-fpga, m-pcb and kestrel on GitHub. GitHub redirects child origins to kestrel-interface, kestrel-core and kestrel-pcb; existing URLs work. Detached submodules need an ordinary topic branch before committing. Push without force and verify local commits against remote refs.

Software is published on knowledge-trees. Interface c1e941c512c5aa2710cd90f2a66ba47fe8e323bb and Core ba709d2b0437f3312f4d2b0c5a84408fdf49041f are pushed; their remote branch heads match. Interface includes descriptor/expression lifetime and reload handling, discovery metadata, bounded desktop discovery views and opt-in renderer experiments. Production catalogue/worker architecture remains for David's review. Core includes compiled-program SPI/controller and full-engine simulation/read32 fixtures. Parent software gitlinks must name those child commits.

Publication checks pass 211 Interface tests, parser-allocation recovery, DSP-core and SPI/controller suites and full-engine mapped read32 checks. These do not establish complete physical audio/UI acceptance. Installed-image identities and experimental qualification limits belong to component owners; unpublished Clockwork's long maximum-delay run remains pending.

PCB 8f8222e42b4ad904c555a4da1915754a677bf668 is pushed and remote-verified on rev-b-integrated-pcb. Hardware state, trial replay evidence and unresolved adoption/qualification belong to what/is/the/pcb/design/status.md and circuit owners. A software checkpoint must preserve unrelated PCB edits and retain its existing gitlink unless publishing a separately verified child update.

David explicitly authorizes firmware, RTL, effects and PCB commits/pushes. Preserve concurrent changes and local KiCad preferences. Mixed spec/plan leaves must retain all current intentions. Exclude Python caches, live locks, local preferences and the embedded electrical .history repository; preserve those files locally. Verify pushed refs and inspect worktrees after publication.

If GitHub denies a push to David-Farrell_avnet, inspect gh auth status and switch to the already authenticated personal owner with gh auth switch --hostname github.com --user linkin-parks-bassist. No tokens belong in the tree.
