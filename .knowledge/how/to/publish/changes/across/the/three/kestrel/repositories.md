---
status: "unverified"
source: Git branch, remote and status inspection plus successful child push output, 2026-09-20
updated_at: "2026-09-20T00:23:23+10:00"
---
Status: Green

Commit and push kestrel_interface and kestrel_core before committing their new gitlink references in the superproject. Configured origins are linkin-parks-bassist/m-interface, linkin-parks-bassist/m-fpga and linkin-parks-bassist/kestrel on GitHub. Successful pushes reported redirects from m-interface to kestrel-interface and from m-fpga to kestrel-core; the existing remote URLs still work. Submodule checkouts can have detached HEADs; create an ordinary topic branch before committing so commits have durable branch names, then push without force. This audit uses knowledge-trees in all three repositories. Stage the parent knowledge tree and two gitlinks after child commits exist. Verify pushed branches against remote refs and check all three worktrees.

If GitHub denies the push to David-Farrell_avnet, inspect gh auth status and switch to the already authenticated personal owner account with gh auth switch --hostname github.com --user linkin-parks-bassist. This resolved the Interface 403 in this publication. The user explicitly authorized committing and pushing all three repositories. No tokens belong in the tree.
