---
title: "Interaction"
impact: MEDIUM
tags:
  - interaction
  - mouse
  - keyboard
  - drag
---

# Interaction

Mouse handling, keyboard input, drag behavior, and UI interaction patterns.

---

## Mouse Variables

| Variable | Description |
|----------|-------------|
| `mouse_x` | X position in pixels (physical on retina Mac) |
| `mouse_y` | Y position in pixels (physical on retina Mac) |
| `mouse_cap` | Button/modifier state (bitfield) |
| `mouse_wheel` | Scroll wheel delta |

### Mouse Coordinates with Retina/Scaling

**Important:** On macOS retina displays, `mouse_x` and `mouse_y` are in **physical pixels** (not logical points). When using a scaling system, transform them to base coordinates:

```
// With scaling system from gfx-basics.md
mx = (mouse_x - offset_x) / draw_scale;
my = (mouse_y - offset_y) / draw_scale;

// Now mx, my are in base coordinates (500x380)
// Use mx, my for all hit detection
```

### mouse_cap Bits

| Bit | Value | Meaning |
|-----|-------|---------|
| 0 | 1 | Left button |
| 1 | 2 | Right button |
| 2 | 4 | Ctrl key |
| 3 | 8 | Shift key |
| 4 | 16 | Alt key |
| 5 | 32 | Win/Cmd key |
| 6 | 64 | Middle button |

```
// Check specific buttons/modifiers
left_down = mouse_cap & 1;
right_down = mouse_cap & 2;
ctrl_held = mouse_cap & 4;
shift_held = mouse_cap & 8;
alt_held = mouse_cap & 16;
middle_down = mouse_cap & 64;
```

---

## Click Detection

### Simple Click

```
@init
last_mouse_cap = 0;

@gfx
// Detect click (transition from not-pressed to pressed)
clicked = (mouse_cap & 1) && !(last_mouse_cap & 1);

clicked ? (
  // Handle click at mouse_x, mouse_y
);

last_mouse_cap = mouse_cap;
```

### Click in Region

```
function point_in_rect(px, py, rx, ry, rw, rh)
(
  px >= rx && px < rx + rw && py >= ry && py < ry + rh;
);

@gfx
button_x = 10; button_y = 10;
button_w = 80; button_h = 30;

clicked && point_in_rect(mouse_x, mouse_y, button_x, button_y, button_w, button_h) ? (
  // Button was clicked
  do_button_action();
);
```

### Click Outside to Dismiss (Popups)

**Important:** When detecting clicks outside a popup, `last_mouse_cap` must be updated AFTER the popup handling code, not before. Otherwise the click transition detection won't work.

```
@gfx
// ... main UI code ...

// Release drag
!(mouse_cap & 1) ? drag_active = 0;

// Handle popup BEFORE updating last_mouse_cap
input_active ? (
  // Draw popup...

  // Click outside to dismiss
  (mouse_cap & 1) && !(last_mouse_cap & 1) ? (
    !mouse_in_rect(popup_x, popup_y, popup_w, popup_h) ? (
      input_active = 0;  // Dismiss
    );
  );
);

// Update last_mouse_cap AFTER popup handling
last_mouse_cap = mouse_cap;
```

---

## Drag Behavior

### Vertical Drag (for Knobs)

```
@init
dragging = 0;
drag_start_y = 0;
drag_start_val = 0;

@gfx
// Start drag
(mouse_cap & 1) && !dragging && mouse_in_control ? (
  dragging = 1;
  drag_start_y = mouse_y;
  drag_start_val = slider1;
);

// During drag
dragging ? (
  // Sensitivity: pixels per full range
  sensitivity = 200;
  delta = (drag_start_y - mouse_y) / sensitivity;
  slider1 = drag_start_val + delta * (slider1_max - slider1_min);
  slider1 = max(slider1_min, min(slider1_max, slider1));
  slider_automate(slider1);
);

// End drag
!(mouse_cap & 1) ? dragging = 0;
```

### Horizontal Drag (for Sliders)

```
@gfx
slider_x = 20;
slider_w = 200;

(mouse_cap & 1) && point_in_rect(mouse_x, mouse_y, slider_x, slider_y, slider_w, slider_h) ? (
  // Direct position mapping
  normalized = (mouse_x - slider_x) / slider_w;
  normalized = max(0, min(1, normalized));
  slider1 = slider1_min + normalized * (slider1_max - slider1_min);
  slider_automate(slider1);
);
```

### 2D Drag (for XY Pads)

```
@init
xy_dragging = 0;

@gfx
pad_x = 20; pad_y = 20;
pad_w = 160; pad_h = 160;

in_pad = point_in_rect(mouse_x, mouse_y, pad_x, pad_y, pad_w, pad_h);

(mouse_cap & 1) && (xy_dragging || in_pad) ? (
  xy_dragging = 1;
  norm_x = (mouse_x - pad_x) / pad_w;
  norm_y = (mouse_y - pad_y) / pad_h;
  norm_x = max(0, min(1, norm_x));
  norm_y = max(0, min(1, norm_y));

  slider1 = slider1_min + norm_x * (slider1_max - slider1_min);
  slider2 = slider2_max - norm_y * (slider2_max - slider2_min);  // Invert Y
  slider_automate(slider1);
  slider_automate(slider2);
);

!(mouse_cap & 1) ? xy_dragging = 0;
```

---

## Modifier Keys

### Shift for Fine Control

```
dragging ? (
  shift_held = mouse_cap & 8;
  sensitivity = shift_held ? 1000 : 200;  // 5x finer with shift

  delta = (drag_start_y - mouse_y) / sensitivity;
  // ...
);
```

### Ctrl-Click for Reset

```
clicked && (mouse_cap & 4) && mouse_in_control ? (
  // Reset to default
  slider1 = slider1_default;
  slider_automate(slider1);
);
```

### Alt-Drag for Alternate Behavior

```
dragging && (mouse_cap & 16) ? (
  // Horizontal drag instead of vertical
  delta = (mouse_x - drag_start_x) / sensitivity;
) : (
  delta = (drag_start_y - mouse_y) / sensitivity;
);
```

---

## Scroll Wheel

```
@init
last_wheel = 0;

@gfx
// mouse_wheel is cumulative, track delta
wheel_delta = mouse_wheel - last_wheel;
last_wheel = mouse_wheel;

wheel_delta != 0 && mouse_in_control ? (
  // Adjust value
  step = (slider1_max - slider1_min) / 100;
  slider1 += wheel_delta * step;
  slider1 = max(slider1_min, min(slider1_max, slider1));
  slider_automate(slider1);
);
```

---

## Keyboard Input

### Reading Keys

```
@gfx
// gfx_getchar returns ASCII code or special key
char = gfx_getchar();

char > 0 ? (
  char == 27 ? (  // Escape
    close_popup();
  ) : char == 13 ? (  // Enter
    confirm_input();
  ) : char == 8 ? (  // Backspace
    delete_char();
  ) : char >= 32 && char < 127 ? (
    // Printable character
    append_char(char);
  );
);
```

### Consuming All Keys (for Popups/Input Fields)

**Important:** When an input popup is active, use a `while` loop to consume ALL queued key events. This prevents keys like Escape from propagating to REAPER and closing the plugin window.

```
// When input is active, consume ALL keys
input_active ? (
  while ((key = gfx_getchar()) > 0) (
    key >= 48 && key <= 57 ? (  // 0-9
      input_value = input_value * 10 + (key - 48);
    );
    key == 8 ? (  // Backspace
      input_value = floor(input_value / 10);
    );
    key == 13 ? (  // Enter - confirm
      apply_value(input_value);
      input_active = 0;
    );
    key == 27 ? (  // Escape - cancel (consumed, won't close plugin)
      input_active = 0;
    );
  );
);
```

### Special Keys

```
// Arrow keys
char == 1919379572 ? move_left();   // Left
char == 1919379573 ? move_right();  // Right
char == 1919379574 ? move_up();     // Up
char == 1919379575 ? move_down();   // Down

// Enable all keyboard input
// Add to file: options:want_all_kb
```

---

## Context Menu

```
@gfx
// Right-click menu
right_clicked = (mouse_cap & 2) && !(last_mouse_cap & 2);

right_clicked && point_in_rect(mouse_x, mouse_y, control_x, control_y, control_w, control_h) ? (
  // Show menu (items separated by |)
  gfx_x = mouse_x;
  gfx_y = mouse_y;
  result = gfx_showmenu("Reset|Copy|Paste|>Presets|Preset 1|Preset 2|<");

  result == 1 ? reset_value() :
  result == 2 ? copy_value() :
  result == 3 ? paste_value() :
  result == 4 ? load_preset(1) :
  result == 5 ? load_preset(2);
);
```

### Menu Syntax

```
// Basic items
"Item 1|Item 2|Item 3"

// Submenu
">Submenu|Sub Item 1|Sub Item 2|<|Back to Main"

// Grayed out
"#Disabled Item|Normal Item"

// Checked
"!Checked Item|Unchecked Item"

// Separator
"Item 1||Item 2"  // Double pipe
```

---

## Hover Effects

```
@gfx
button_hovered = point_in_rect(mouse_x, mouse_y, button_x, button_y, button_w, button_h);

// Draw with hover effect
button_hovered ? (
  gfx_r = 0.5; gfx_g = 0.5; gfx_b = 0.55;  // Lighter
) : (
  gfx_r = 0.4; gfx_g = 0.4; gfx_b = 0.45;  // Normal
);
gfx_rect(button_x, button_y, button_w, button_h);
```

---

## Cursor Control

```
@gfx
// Set cursor based on context
mouse_in_resize_area ? (
  gfx_setcursor(32646);  // Resize cursor
) : mouse_in_link ? (
  gfx_setcursor(32649);  // Hand cursor
) : (
  gfx_setcursor(0);  // Default
);

// Common cursor IDs:
// 0 = Default
// 32512 = Arrow
// 32513 = I-beam
// 32514 = Wait
// 32515 = Cross
// 32516 = Up arrow
// 32642 = Size NW-SE
// 32643 = Size NE-SW
// 32644 = Size W-E
// 32645 = Size N-S
// 32646 = Size all
// 32648 = No
// 32649 = Hand
```

---

## Complete Interactive Control

```
@init
control_value = 50;
control_min = 0;
control_max = 100;
control_default = 50;

dragging = 0;
drag_y = 0;
drag_val = 0;
last_cap = 0;

@gfx 200 200
cx = 100; cy = 100; cr = 40;

// Hover detection
in_control = sqr(mouse_x - cx) + sqr(mouse_y - cy) < sqr(cr);

// Draw (with hover highlight)
in_control || dragging ? (
  gfx_r = 0.4; gfx_g = 0.4; gfx_b = 0.5;
) : (
  gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.35;
);
gfx_circle(cx, cy, cr, 1, 1);

// Value indicator
norm = (control_value - control_min) / (control_max - control_min);
angle = $pi * 0.75 + norm * $pi * 1.5;
gfx_r = gfx_g = gfx_b = 1;
gfx_line(cx, cy, cx + cos(angle) * cr * 0.7, cy + sin(angle) * cr * 0.7, 1);

// Click detection
clicked = (mouse_cap & 1) && !(last_cap & 1);

// Ctrl-click to reset
clicked && (mouse_cap & 4) && in_control ? (
  control_value = control_default;
);

// Start drag
clicked && in_control ? (
  dragging = 1;
  drag_y = mouse_y;
  drag_val = control_value;
);

// Drag
dragging ? (
  sens = (mouse_cap & 8) ? 500 : 100;  // Shift = fine
  delta = (drag_y - mouse_y) / sens * (control_max - control_min);
  control_value = max(control_min, min(control_max, drag_val + delta));
);

// End drag
!(mouse_cap & 1) ? dragging = 0;

// Scroll wheel
in_control && mouse_wheel != last_wheel ? (
  step = (control_max - control_min) / 50;
  control_value += (mouse_wheel - last_wheel) * step;
  control_value = max(control_min, min(control_max, control_value));
  last_wheel = mouse_wheel;
);

// Value display
gfx_x = cx - 15; gfx_y = cy + cr + 10;
gfx_printf("%.1f", control_value);

last_cap = mouse_cap;
```
