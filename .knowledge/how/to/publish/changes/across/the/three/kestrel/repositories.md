---
status: green
revised_at: "2026-10-04T11:48:10+11:00"
---

Commit and push each changed child repository before committing its new gitlink in the superproject. Configured origins are linkin-parks-bassist/m-interface, m-fpga, m-pcb and kestrel on GitHub. GitHub redirects the child origins to kestrel-interface, kestrel-core and kestrel-pcb; existing remote URLs work. Detached submodule checkouts need an ordinary topic branch before committing so commits have durable branch names. Push without force and verify local commits against remote refs.

Software work is published on knowledge-trees branches: Interface ee1d395a and Core 8cb8e2f are pushed. PCB Rev-B draft f4ded2592a28076221ea9f90410893daada10c20 is pushed on rev-b-integrated-pcb, including schematic, electrical board, local-route manifests/tools/checks, generated review artifacts and mechanical studies. Hardware remains an engineering draft with unfinished placement/routing and qualification. David explicitly authorizes continued PCB commits and pushes. Stage the PCB gitlink and its relevant parent hardware leaves after the child push; preserve concurrent software/effect changes and local KiCad preference files. Mixed spec/plan leaves must retain current concurrent intentions when publishing hardware projections. Exclude Python caches, live locks, local KiCad preferences and the embedded electrical .history repository; preserve those local files. Verify pushed branches and inspect worktrees after publication.

If GitHub denies a push to David-Farrell_avnet, inspect gh auth status and switch to the already authenticated personal owner account with gh auth switch --hostname github.com --user linkin-parks-bassist. David also authorizes committing and pushing firmware, RTL and effects across their repositories. No tokens belong in the tree.
