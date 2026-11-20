---
title: "UI Widgets"
impact: HIGH
tags:
  - widgets
  - knob
  - slider
  - button
---

# UI Widgets

Knobs, sliders, buttons, toggles, and other interactive controls.

---

## Scaling Note

For retina/HiDPI support and resizable windows, wrap widget drawing with the scaling system from [gfx-basics](./gfx-basics.md). Pass base coordinates to widgets, and use `sx()`, `sy()`, `s()` helpers internally.

```
// Widget using scaling system
function draw_knob_scaled(bx, by, bradius, value, ...) (
  // Convert to physical pixels for drawing
  cx = sx(bx + bradius);
  cy = sy(by + bradius);
  radius = s(bradius);
  // ... draw using cx, cy, radius ...
);

// Hit detection uses mx, my (base coordinates)
in_knob = mouse_in_rect(bx - bradius, by - bradius, bradius*2, bradius*2);
```

---

## Panels with Rounded Corners

```
// Draw rounded rectangle (base coordinates, auto-scaled)
function draw_rounded_rect(bx, by, bw, bh, radius, filled) (
  gfx_roundrect(sx(bx), sy(by), s(bw), s(bh), s(radius), filled);
);

// Panel with rounded corners and proper padding
function draw_panel(bx, by, bw, bh, title) local(corner_radius, padding) (
  corner_radius = 6;
  padding = 12;

  // Dark fill with rounded corners
  set_color(0.055, 0.055, 0.075, 0.95);
  draw_rounded_rect(bx, by, bw, bh, corner_radius, 1);

  // Subtle border with rounded corners
  set_color(0.2, 0.2, 0.25, 0.5);
  draw_rounded_rect(bx, by, bw, bh, corner_radius, 0);

  // Title with padding - leave ~25-30px vertical space before content
  set_font("Arial", 11);
  set_color(0.45, 0.45, 0.5, 1);
  draw_text(bx + padding, by + 8, title);
);
```

**Layout tip:** Leave at least 25-30px between panel top and first control to avoid title overlap.

---

## Knob

### Basic Knob

```
function draw_knob(x, y, radius, value, min_val, max_val)
  local(normalized, angle, start_angle, end_angle, indicator_angle, pointer_x, pointer_y)
(
  // Normalize value 0-1
  normalized = (value - min_val) / (max_val - min_val);

  // Angle range: 135° to 405° (270° total sweep)
  start_angle = $pi * 0.75;   // 135° - lower left
  end_angle = $pi * 2.25;     // 405° - lower right
  angle = start_angle + normalized * (end_angle - start_angle);

  // Background arc
  gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.3; gfx_a = 1;
  gfx_arc(x, y, radius, start_angle, end_angle, 1);

  // Value arc
  gfx_r = 0.2; gfx_g = 0.8; gfx_b = 0.4;
  gfx_arc(x, y, radius, start_angle, angle, 1);

  // Pointer line - IMPORTANT: offset by -π/2 to align with gfx_arc
  // gfx_arc and cos/sin have different angle conventions
  indicator_angle = angle - $pi * 0.5;
  gfx_r = gfx_g = gfx_b = 1;
  pointer_x = x + cos(indicator_angle) * radius * 0.7;
  pointer_y = y + sin(indicator_angle) * radius * 0.7;
  gfx_line(x, y, pointer_x, pointer_y, 1);

  // Center circle
  gfx_r = 0.2; gfx_g = 0.2; gfx_b = 0.25;
  gfx_circle(x, y, radius * 0.4, 1, 1);
);
```

### Interactive Knob

```
@init
knob_dragging = 0;
knob_drag_start_y = 0;
knob_drag_start_val = 0;

@gfx
knob_x = 100;
knob_y = 100;
knob_radius = 40;
knob_min = 0;
knob_max = 100;

// Draw
draw_knob(knob_x, knob_y, knob_radius, slider1, knob_min, knob_max);

// Interaction
mouse_in_knob = sqrt(sqr(mouse_x - knob_x) + sqr(mouse_y - knob_y)) < knob_radius;

// Start drag
mouse_cap & 1 && !knob_dragging && mouse_in_knob ? (
  knob_dragging = 1;
  knob_drag_start_y = mouse_y;
  knob_drag_start_val = slider1;
);

// During drag
knob_dragging ? (
  delta = (knob_drag_start_y - mouse_y) / 100;  // Sensitivity
  slider1 = knob_drag_start_val + delta * (knob_max - knob_min);
  slider1 = max(knob_min, min(knob_max, slider1));
  slider_automate(slider1);
);

// End drag
!(mouse_cap & 1) ? knob_dragging = 0;
```

---

## Slider (Horizontal)

```
function draw_hslider(x, y, w, h, value, min_val, max_val)
  local(normalized, handle_x)
(
  normalized = (value - min_val) / (max_val - min_val);
  handle_x = x + normalized * w;

  // Track
  gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.3;
  gfx_rect(x, y + h/2 - 2, w, 4);

  // Filled portion
  gfx_r = 0.2; gfx_g = 0.7; gfx_b = 0.9;
  gfx_rect(x, y + h/2 - 2, handle_x - x, 4);

  // Handle
  gfx_r = gfx_g = gfx_b = 0.9;
  gfx_circle(handle_x, y + h/2, h/2 - 2, 1, 1);
);

// Interaction
function handle_hslider(x, y, w, h, value, min_val, max_val, slider_idx)
  local(normalized, new_val)
(
  mouse_cap & 1 &&
  mouse_x >= x && mouse_x <= x + w &&
  mouse_y >= y && mouse_y <= y + h ? (
    normalized = (mouse_x - x) / w;
    new_val = min_val + normalized * (max_val - min_val);
    slider(slider_idx) = new_val;
    slider_automate(slider(slider_idx));
  );
);
```

---

## Vertical Slider (Fader)

```
function draw_vslider(x, y, w, h, value, min_val, max_val)
  local(normalized, handle_y)
(
  normalized = (value - min_val) / (max_val - min_val);
  handle_y = y + h - normalized * h;

  // Track
  gfx_r = 0.25; gfx_g = 0.25; gfx_b = 0.28;
  gfx_rect(x + w/2 - 3, y, 6, h);

  // Handle
  gfx_r = 0.7; gfx_g = 0.7; gfx_b = 0.75;
  gfx_rect(x, handle_y - 10, w, 20);
  // Handle groove
  gfx_r = 0.4; gfx_g = 0.4; gfx_b = 0.45;
  gfx_rect(x + 2, handle_y - 1, w - 4, 2);
);
```

---

## Button

```
function draw_button(x, y, w, h, label, pressed)
(
  // Background
  pressed ? (
    gfx_r = 0.3; gfx_g = 0.5; gfx_b = 0.8;
  ) : (
    gfx_r = 0.4; gfx_g = 0.4; gfx_b = 0.45;
  );
  gfx_rect(x, y, w, h);

  // Border
  gfx_r = gfx_g = gfx_b = 0.6;
  gfx_rect(x, y, w, 1);
  gfx_rect(x, y, 1, h);
  gfx_r = gfx_g = gfx_b = 0.2;
  gfx_rect(x, y + h - 1, w, 1);
  gfx_rect(x + w - 1, y, 1, h);

  // Label
  gfx_r = gfx_g = gfx_b = 1;
  gfx_measurestr(label, tw, th);
  gfx_x = x + (w - tw) / 2;
  gfx_y = y + (h - th) / 2;
  gfx_drawstr(label);
);

// Click detection
function button_clicked(x, y, w, h)
(
  mouse_cap & 1 &&
  mouse_x >= x && mouse_x <= x + w &&
  mouse_y >= y && mouse_y <= y + h;
);
```

---

## Toggle Switch

```
function draw_toggle(x, y, w, h, state)
  local(handle_x)
(
  // Background
  state ? (
    gfx_r = 0.2; gfx_g = 0.7; gfx_b = 0.3;
  ) : (
    gfx_r = 0.4; gfx_g = 0.4; gfx_b = 0.4;
  );
  gfx_roundrect(x, y, w, h, h/2, 1);

  // Handle
  gfx_r = gfx_g = gfx_b = 0.95;
  handle_x = state ? x + w - h/2 - 2 : x + h/2 + 2;
  gfx_circle(handle_x, y + h/2, h/2 - 3, 1, 1);
);

@gfx
// Handle click
mouse_cap & 1 && !last_mouse_cap &&
mouse_x >= toggle_x && mouse_x <= toggle_x + toggle_w &&
mouse_y >= toggle_y && mouse_y <= toggle_y + toggle_h ? (
  slider1 = !slider1;
  slider_automate(slider1);
);
last_mouse_cap = mouse_cap;
```

---

## Dropdown/Menu

```
function draw_dropdown(x, y, w, h, current_idx, options)
  local(i)
(
  // Main button
  gfx_r = 0.35; gfx_g = 0.35; gfx_b = 0.4;
  gfx_rect(x, y, w, h);

  // Arrow
  gfx_r = gfx_g = gfx_b = 0.7;
  gfx_triangle(x + w - 15, y + h/2 - 3,
               x + w - 5, y + h/2 - 3,
               x + w - 10, y + h/2 + 3);

  // Current value text
  gfx_r = gfx_g = gfx_b = 1;
  gfx_x = x + 5;
  gfx_y = y + (h - gfx_texth) / 2;
  gfx_drawstr(options[current_idx]);
);

// Use gfx_showmenu for actual menu
@gfx
menu_clicked ? (
  result = gfx_showmenu("Option 1|Option 2|Option 3");
  result > 0 ? (
    slider1 = result - 1;
    slider_automate(slider1);
  );
);
```

---

## Widget Library Pattern

```
// widgets.jsfx-inc

function widget.knob(id, x, y, r, value, min_v, max_v, label)
  instance(dragging, drag_y, drag_val)
  local(norm, angle, px, py, in_knob)
(
  // Draw
  norm = (value - min_v) / (max_v - min_v);
  angle = $pi * 0.75 + norm * $pi * 1.5;

  gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.35;
  gfx_circle(x, y, r, 1, 1);

  gfx_r = 0.5; gfx_g = 0.8; gfx_b = 0.5;
  px = x + cos(angle) * r * 0.7;
  py = y + sin(angle) * r * 0.7;
  gfx_line(x, y, px, py, 1);

  // Label
  gfx_r = gfx_g = gfx_b = 0.8;
  gfx_x = x - 20; gfx_y = y + r + 5;
  gfx_drawstr(label);

  // Interaction
  in_knob = sqr(mouse_x - x) + sqr(mouse_y - y) < sqr(r);

  mouse_cap & 1 && !dragging && in_knob ? (
    dragging = 1;
    drag_y = mouse_y;
    drag_val = value;
  );

  dragging ? (
    value = drag_val + (drag_y - mouse_y) / 100 * (max_v - min_v);
    value = max(min_v, min(max_v, value));
  );

  !(mouse_cap & 1) ? dragging = 0;

  value;  // Return new value
);

// Usage:
// slider1 = knob1.widget.knob(1, 100, 100, 30, slider1, 0, 100, "Gain");
```

---

## Complete Widget Panel

```
@gfx 400 300

// Background
gfx_r = 0.12; gfx_g = 0.12; gfx_b = 0.14;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Title
gfx_setfont(1, "Arial", 18);
gfx_r = gfx_g = gfx_b = 1;
gfx_x = 10; gfx_y = 10;
gfx_drawstr("My Plugin");

// Knobs row
gfx_setfont(2, "Arial", 11);
slider1 = gain_knob.widget.knob(1, 80, 100, 35, slider1, -24, 24, "Gain");
slider2 = freq_knob.widget.knob(2, 180, 100, 35, slider2, 20, 20000, "Freq");
slider3 = res_knob.widget.knob(3, 280, 100, 35, slider3, 0.1, 10, "Res");

// Buttons
bypass_pressed = button_clicked(20, 200, 80, 30);
draw_button(20, 200, 80, 30, "Bypass", slider4);
bypass_pressed && !last_bypass ? (
  slider4 = !slider4;
  slider_automate(slider4);
);
last_bypass = bypass_pressed;

// Value displays
gfx_setfont(3, "Courier New", 14);
gfx_r = 0.6; gfx_g = 0.9; gfx_b = 0.6;
gfx_x = 60; gfx_y = 150;
gfx_printf("%.1f dB", slider1);
gfx_x = 160;
gfx_printf("%.0f Hz", slider2);
gfx_x = 265;
gfx_printf("%.2f", slider3);
```
