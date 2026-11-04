# Skills library (installed)

These skills were installed by `skillpack` from the Claude_Skills master library
(master commit `058b511`). Routing starts at `_orchestrator/SKILL.md`.

**Do not edit a skill outside its tailoring block.** Updates from the master replace everything
else in a skill. Put project facts in one of two places:

- at the end of the skill's `SKILL.md`, between these markers:

  ```
  <!-- project-tailoring:begin -->
  ## Project tailoring
  ...commands, paths, conventions, decisions for this project...
  <!-- project-tailoring:end -->
  ```

- in files under the skill's own `project/` folder.

A skill edited anywhere else stops receiving updates until someone merges it by hand.

Common commands, run from the master clone:

```bash
python tools/skillpack check  --target <this-project>        # what is stale, tailored, new, or project-only
python tools/skillpack update --target <this-project>        # update untouched skills, keep tailoring blocks
python tools/skillpack install --target <this-project> --exclude <skill>   # remove a skill for good
```

Skills that exist only in this project belong in their own folders. List them in the
orchestrator's tailoring block, and generalise them into the master if another project could use them.
