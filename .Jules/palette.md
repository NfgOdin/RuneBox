## 2026-10-22 - Adding Pointer Cursor to CustomTkinter Cards
**Learning:** In CustomTkinter, custom frames acting as clickable cards don't natively show a pointer cursor on hover or cascade hover states smoothly to children.
**Action:** Assign `cursor="hand2"` to the main frame and all child labels, then explicitly bind `<Enter>` and `<Leave>` events on all internal sub-widgets to simulate a unified interactive card.

## 2024-05-24 - Add Inline Validation to GUI Forms
**Learning:** Silent fallbacks (e.g. quietly reverting to a default value when parsing a number fails) in desktop GUI applications cause user confusion, because the user isn't notified that their input was invalid. Adding inline visual validation (like red borders on invalid entries) provides immediate feedback that reduces cognitive load.
**Action:** Always add inline validation (e.g., color-coded borders) on form inputs so users know immediately if their data is invalid, rather than relying solely on silent fallbacks.
