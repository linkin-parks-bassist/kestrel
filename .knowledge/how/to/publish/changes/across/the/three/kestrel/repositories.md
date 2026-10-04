---
status: green
revised_at: "2026-10-04T11:42:25+11:00"
---

Commit and push kestrel_interface and kestrel_core before committing their new gitlink references in the superproject. Configured origins are linkin-parks-bassist/m-interface, linkin-parks-bassist/m-fpga and linkin-parks-bassist/kestrel on GitHub. Successful pushes reported redirects from m-interface to kestrel-interface and from m-fpga to kestrel-core; the existing remote URLs still work. Submodule checkouts can have detached HEADs; create an ordinary topic branch before committing so commits have durable branch names, then push without force. The software work is published on knowledge-trees branches in all three repositories; Interface commit ee1d395a and Core commit 8cb8e2f are pushed. Current software publication excludes the concurrent PCB work. Stage the relevant parent knowledge leaves and two gitlinks after child commits exist. Preserve concurrent PCB changes and mixed hardware planning/orientation documentation rather than bundling them into a software-only publication. Verify pushed branches against remote refs and check all three worktrees.

If GitHub denies the push to David-Farrell_avnet, inspect gh auth status and switch to the already authenticated personal owner account with gh auth switch --hostname github.com --user linkin-parks-bassist. This resolved the Interface 403 in this publication. David authorizes committing and pushing the firmware, RTL and effects work across these repositories. No tokens belong in the tree.
