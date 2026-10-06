---
status: green
revised_at: "2026-10-06T18:09:37+11:00"
---

Use main for David's software work and publication; the knowledge-trees topic branch is not the intended ongoing destination. Preserve existing main changes when integrating a topic branch. Never force-push or discard divergent commits.

Commit and push each changed child repository before committing its new gitlink in the superproject. Configured origins are linkin-parks-bassist/m-interface, m-fpga, m-pcb and kestrel on GitHub. Child URLs redirect to kestrel-interface, kestrel-core and kestrel-pcb and still work. Verify local commits against remote refs.

Interface main 9bea6189433e265b226426c51b9fb8fcd0fd23fb and Core main ba709d2b0437f3312f4d2b0c5a84408fdf49041f are pushed; remote heads match. Interface includes descriptor/expression lifetime and reload handling, discovery metadata, bounded desktop discovery and opt-in renderer experiments. Its merge preserves main's time-expression hooks with checked scope initialization, library compatibility and epoch preservation on rejected program submission. Production catalogue/worker architecture remains for David's review. Core includes compiled-program SPI/controller and full-engine simulation/read32 fixtures. Parent gitlinks must name those child commits.

Checks pass 212 Interface tests, twelve scope-allocation failure boundaries plus discovery-copy fault recovery, DSP-core/SPI-controller suites and full-engine mapped read32. These do not establish complete physical audio/UI acceptance. Installed-image identities and experimental limits belong to component owners; installed firmware predates the time-hook merge. Unpublished Clockwork's long maximum-delay run remains pending.

PCB 8f8222e42b4ad904c555a4da1915754a677bf668 is pushed and remote-verified on rev-b-integrated-pcb. Hardware state, trial replay evidence and unresolved adoption/qualification belong to what/is/the/pcb/design/status.md and circuit owners. Software publication preserves unrelated PCB edits and its gitlink unless publishing a separately verified child update.

David authorizes firmware, RTL, effects and PCB commits/pushes. Preserve concurrent changes and local KiCad preferences. Mixed spec/plan leaves retain all current intentions. Exclude Python caches, live locks, local preferences and the embedded electrical .history repository; preserve them locally. Inspect worktrees after publication.

If GitHub denies a push to David-Farrell_avnet, inspect gh auth status and switch to the authenticated personal owner with gh auth switch --hostname github.com --user linkin-parks-bassist. No tokens belong in the tree.
