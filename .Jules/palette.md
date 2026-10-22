## 2026-10-22 - Adding Pointer Cursor to CustomTkinter Cards
**Learning:** In CustomTkinter, custom frames acting as clickable cards don't natively show a pointer cursor on hover or cascade hover states smoothly to children.
**Action:** Assign `cursor="hand2"` to the main frame and all child labels, then explicitly bind `<Enter>` and `<Leave>` events on all internal sub-widgets to simulate a unified interactive card.
