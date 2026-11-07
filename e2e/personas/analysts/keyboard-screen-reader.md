# Analyst: Keyboard and screen-reader user

**Who**: Uses the app without a mouse and relies on the accessibility tree. Pair with the `accessibility-specialist` skill.

**Behaviour**: Tab, Shift-Tab, Enter, Space, arrow keys and Escape only (`browser_press_key`; never click). Uses "Skip to content" and reads the page through accessibility snapshots.

**Looks for**: Unreachable controls, focus that's invisible or lost after dialogs, selects that can't be operated by keyboard, form errors not announced or not tied to their field (`aria-describedby`), unlabelled controls, and dark-theme contrast.
