---
title: "Graphics Basics"
impact: CRITICAL
tags:
  - graphics
  - drawing
  - primitives
  - text
---

# Graphics Basics

The @gfx section, coordinate system, colors, and drawing primitives.

## References

- [JSFX Graphics Functions](https://www.reaper.fm/sdk/js/gfx.php)

---

## The @gfx Section

```
@gfx [width] [height]

// Runs approximately 30 times per second
// Optional width/height specify initial size
// Actual size available in gfx_w and gfx_h
```

### Key Variables

| Variable | Description |
|----------|-------------|
| `gfx_w` | Current width in pixels |
| `gfx_h` | Current height in pixels |
| `gfx_x` | Current drawing X position |
| `gfx_y` | Current drawing Y position |
| `gfx_r` | Red component (0-1) |
| `gfx_g` | Green component (0-1) |
| `gfx_b` | Blue component (0-1) |
| `gfx_a` | Alpha/opacity (0-1) |
| `gfx_ext_retina` | HiDPI scale factor |

---

## Coordinate System

```
(0,0) ─────────────────────► X (gfx_w)
  │
  │
  │
  │
  ▼
  Y (gfx_h)
```

Origin is top-left. X increases right, Y increases down.

---

## Colors

### Setting Color

```
// Set color before drawing
gfx_r = 1;   // Red (0-1)
gfx_g = 0;   // Green (0-1)
gfx_b = 0;   // Blue (0-1)
gfx_a = 1;   // Alpha (0-1)

// Or set all at once (helper function)
function set_color(r, g, b, a)
(
  gfx_r = r; gfx_g = g; gfx_b = b; gfx_a = a;
);

set_color(1, 0.5, 0, 1);  // Orange
```

### Common Colors

```
// Grayscale
gfx_r = gfx_g = gfx_b = 0;    // Black
gfx_r = gfx_g = gfx_b = 0.5;  // Gray
gfx_r = gfx_g = gfx_b = 1;    // White

// Primary
gfx_r = 1; gfx_g = 0; gfx_b = 0;  // Red
gfx_r = 0; gfx_g = 1; gfx_b = 0;  // Green
gfx_r = 0; gfx_g = 0; gfx_b = 1;  // Blue

// HSV to RGB conversion
function hsv_to_rgb(h, s, v)
  local(i, f, p, q, t)
(
  i = floor(h * 6);
  f = h * 6 - i;
  p = v * (1 - s);
  q = v * (1 - f * s);
  t = v * (1 - (1 - f) * s);

  i % 6 == 0 ? (gfx_r = v; gfx_g = t; gfx_b = p) :
  i % 6 == 1 ? (gfx_r = q; gfx_g = v; gfx_b = p) :
  i % 6 == 2 ? (gfx_r = p; gfx_g = v; gfx_b = t) :
  i % 6 == 3 ? (gfx_r = p; gfx_g = q; gfx_b = v) :
  i % 6 == 4 ? (gfx_r = t; gfx_g = p; gfx_b = v) :
              (gfx_r = v; gfx_g = p; gfx_b = q);
);
```

---

## Drawing Primitives

### Clear/Fill Background

```
// Fill entire background
gfx_r = gfx_g = gfx_b = 0.1; gfx_a = 1;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Or use gfx_clear (packed RGB)
gfx_clear = 0x1A1A1A;  // Dark gray
```

### Rectangles

```
// Filled rectangle from current position to (x, y)
gfx_x = 10; gfx_y = 10;
gfx_rectto(100, 50);

// Rectangle at position with width/height
gfx_rect(x, y, width, height);

// Rounded rectangle
gfx_roundrect(x, y, width, height, radius, antialias);
```

### Lines

```
// Line from current position to (x, y)
gfx_x = 10; gfx_y = 10;
gfx_lineto(100, 100, 1);  // 1 = antialiased

// Direct line
gfx_line(x1, y1, x2, y2, antialias);
```

### Circles and Arcs

```
// Circle (center x, y, radius, filled, antialiased)
gfx_circle(100, 100, 50, 1, 1);  // Filled
gfx_circle(100, 100, 50, 0, 1);  // Outline

// Arc (center x, y, radius, start_angle, end_angle, antialias)
// Angles in radians, 0 = right, increases clockwise
gfx_arc(100, 100, 50, 0, $pi, 1);  // Half circle
```

### Arc and Indicator Alignment (Important!)

**When drawing an indicator line (e.g., knob pointer) to match a `gfx_arc` position, you must offset the angle by -π/2 (90°):**

```
// Arc from lower-left to lower-right (typical knob)
start_angle = $pi * 0.75;   // 135° - lower left
end_angle = $pi * 2.25;     // 405° - lower right
arc_angle = start_angle + normalized * (end_angle - start_angle);

// Draw the arc
gfx_arc(cx, cy, radius, start_angle, arc_angle, 1);

// Indicator line - MUST offset by -π/2 to align with arc
indicator_angle = arc_angle - $pi * 0.5;
ix = cx + cos(indicator_angle) * radius;
iy = cy + sin(indicator_angle) * radius;
gfx_line(cx, cy, ix, iy, 1);
```

This offset is needed because `gfx_arc` and `cos()`/`sin()` have different angle reference points in JSFX.

### Triangles and Polygons

```
// Triangle
gfx_triangle(x1, y1, x2, y2, x3, y3);

// Filled convex polygon (up to 32 points)
gfx_triangle(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5);
```

---

## Text

### Basic Text

```
gfx_x = 10; gfx_y = 10;
gfx_drawstr("Hello World");

// With number
gfx_drawnumber(value, num_digits);

// Formatted (like printf)
gfx_printf("Value: %.2f dB", value);
```

### Fonts

```
// Set font (index, face, size, flags)
// flags: 'B'=bold, 'I'=italic, 'U'=underline
gfx_setfont(1, "Arial", 14);
gfx_setfont(2, "Courier New", 12, 'B');

// Use font
gfx_setfont(1);
gfx_drawstr("Regular text");
gfx_setfont(2);
gfx_drawstr("Bold mono");
```

### Measuring Text

```
// Get text dimensions
gfx_measurestr("Sample text", w, h);

// Center text
text = "Centered";
gfx_measurestr(text, w, h);
gfx_x = (gfx_w - w) / 2;
gfx_y = (gfx_h - h) / 2;
gfx_drawstr(text);
```

### Text Alignment

```
// gfx_drawstr with flags
// flags: 1=right, 2=bottom, 4=center horiz, 8=center vert
gfx_x = 10; gfx_y = 10;
gfx_drawstr("Left aligned", 0, gfx_w - 10, gfx_h);
gfx_drawstr("Right aligned", 1, gfx_w - 10, gfx_h);
gfx_drawstr("Centered", 5, gfx_w - 10, gfx_h);  // 4+1 = center
```

---

## Gradients

```
// Gradient rectangle
// gfx_gradrect(x, y, w, h, r, g, b, a, drdx, dgdx, dbdx, dadx, drdy, dgdy, dbdy, dady)
// Values are per-pixel change rates

// Horizontal gradient (red to blue)
gfx_gradrect(0, 0, gfx_w, gfx_h,
  1, 0, 0, 1,     // Start color (red)
  -1/gfx_w, 0, 1/gfx_w, 0,  // Change per X pixel
  0, 0, 0, 0);    // No change per Y

// Vertical gradient (dark to light)
gfx_gradrect(0, 0, gfx_w, gfx_h,
  0.1, 0.1, 0.1, 1,
  0, 0, 0, 0,
  0.9/gfx_h, 0.9/gfx_h, 0.9/gfx_h, 0);
```

---

## Images and Blitting

```
@init
// Load image (index, filename)
img = gfx_loadimg(0, "background.png");

@gfx
// Get dimensions
gfx_getimgdim(0, w, h);

// Draw image at position
gfx_x = 0; gfx_y = 0;
gfx_blit(0, 1, 0);  // source, scale, rotation

// Draw portion of image
// gfx_blitext(source, coords, rotation)
// coords: destx, desty, destw, desth, srcx, srcy, srcw, srch
```

### Off-Screen Buffer

```
@init
// Create off-screen buffer (index -1 to -1024)
buffer_idx = -1;
gfx_setimgdim(buffer_idx, 200, 200);

@gfx
// Draw to buffer
gfx_dest = buffer_idx;
gfx_r = gfx_g = gfx_b = 0;
gfx_rect(0, 0, 200, 200);
// ... more drawing ...

// Switch back to screen
gfx_dest = -1;

// Blit buffer to screen
gfx_x = 10; gfx_y = 10;
gfx_blit(buffer_idx, 1, 0);
```

---

## HiDPI/Retina Support & Resizable Windows

### Understanding gfx_ext_retina

**Critical platform difference:**
- **macOS retina**: `gfx_w` and `gfx_h` are **physical pixels** (2x logical)
- **Other systems**: `gfx_w` and `gfx_h` remain logical, `gfx_ext_retina` is a scaling hint

```
@gfx 500 380  // Preferred size (hint only, user can resize)

// Request retina support - REAPER updates this to actual value
!gfx_ext_retina ? gfx_ext_retina = 1;

// Get actual retina factor (1.0 standard, 2.0 retina Mac)
retina = gfx_ext_retina > 0 ? gfx_ext_retina : 1;

// On macOS retina: gfx_w=1000 for 500pt window
// Calculate logical window size
logical_w = gfx_w / retina;
logical_h = gfx_h / retina;
```

### Resizable Window Support

The `@gfx` dimensions are **hints**, not fixed sizes. Users can resize the window.

```
@gfx 500 380  // Preferred initial size
// @gfx 0 0   // No preference - accept any size
// @gfx       // Same as 0 0

// Always use gfx_w/gfx_h for actual dimensions
// Never hardcode sizes based on @gfx parameters
```

### Complete Scaling System

This pattern provides sharp rendering on retina displays with resizable windows:

```
@init
base_w = 500;  // Design width
base_h = 380;  // Design height

@gfx 500 380

// ============= SCALING SETUP =============
// Request retina (REAPER updates to actual value, e.g., 2.0)
!gfx_ext_retina ? gfx_ext_retina = 1;

// Get retina factor
retina = gfx_ext_retina > 0 ? gfx_ext_retina : 1;

// Calculate logical window size (physical pixels / retina)
logical_w = gfx_w / retina;
logical_h = gfx_h / retina;

// Calculate scale to fit base design, maintain aspect ratio
scale = min(logical_w / base_w, logical_h / base_h);
scale = max(0.5, scale);  // Minimum 50% to prevent tiny UI

// Centering offset for letterboxing
offset_x = (logical_w - base_w * scale) * 0.5 * retina;
offset_y = (logical_h - base_h * scale) * 0.5 * retina;

// Combined draw scale (includes retina factor)
draw_scale = scale * retina;

// Mouse coordinates: physical pixels → base coordinates
mx = (mouse_x - offset_x) / draw_scale;
my = (mouse_y - offset_y) / draw_scale;

// ============= HELPER FUNCTIONS =============
// Scale a size value (radius, width, height)
function s(v) ( v * draw_scale; );

// Scale X coordinate (with centering offset)
function sx(v) ( v * draw_scale + offset_x; );

// Scale Y coordinate (with centering offset)
function sy(v) ( v * draw_scale + offset_y; );

// Set font with auto-scaling
function set_font(name, base_size) (
  gfx_setfont(1, name, base_size * draw_scale);
);

// Hit detection in base coordinates
function mouse_in_rect(bx, by, bw, bh) (
  mx >= bx && mx <= bx + bw && my >= by && my <= by + bh;
);

// Draw rectangle (base coordinates, auto-scaled)
function draw_rect(bx, by, bw, bh) (
  gfx_rect(sx(bx), sy(by), s(bw), s(bh));
);

// Draw circle (base coordinates, auto-scaled)
function draw_circle(bcx, bcy, bradius, fill) (
  gfx_circle(sx(bcx), sy(bcy), s(bradius), fill);
);

// Draw text (base coordinates, auto-scaled)
function draw_text(bx, by, str) (
  gfx_x = sx(bx); gfx_y = sy(by);
  gfx_drawstr(str);
);
```

### Using the Scaling System

```
// All coordinates are in BASE (500x380), scaling is automatic

// Background (full window in physical pixels for letterbox areas)
gfx_clear = 0x020204;

// Content area background
set_color(0.1, 0.1, 0.12, 1);
gfx_rect(offset_x, offset_y, base_w * draw_scale, base_h * draw_scale);

// Draw elements using base coordinates
set_font("Arial", 16);
draw_text(10, 10, "My Plugin");

draw_circle(100, 100, 40, 1);  // 40px radius at base size
draw_rect(20, 200, 100, 30);   // Button at base coordinates

// Hit detection uses mx, my (already in base coordinates)
button_hovered = mouse_in_rect(20, 200, 100, 30);
```

### Key Points

| Concept | Explanation |
|---------|-------------|
| `gfx_ext_retina` | Set to 1, REAPER updates to actual (1.0 or 2.0) |
| `gfx_w/gfx_h` | Physical pixels on macOS retina (doubled) |
| `logical_w/h` | `gfx_w / retina` - actual window size in points |
| `scale` | Ratio to fit base design into window |
| `draw_scale` | `scale * retina` - for drawing in physical pixels |
| `offset_x/y` | Centering offset for aspect ratio mismatch |
| `mx/my` | Mouse position converted to base coordinates |

### References

- [REAPER JSFX Graphics Reference](https://www.reaper.fm/sdk/js/gfx.php)
- [geraintluff's jsfx-ui-lib](https://github.com/geraintluff/jsfx-ui-lib)

---

## Complete Example

```
@gfx 300 200

// Clear background
gfx_r = 0.15; gfx_g = 0.15; gfx_b = 0.18; gfx_a = 1;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Title
gfx_setfont(1, "Arial", 16);
gfx_r = gfx_g = gfx_b = 1;
gfx_x = 10; gfx_y = 10;
gfx_drawstr("My Plugin");

// Value display
gfx_setfont(2, "Courier New", 24, 'B');
gfx_r = 0.2; gfx_g = 0.8; gfx_b = 0.4;
gfx_x = 10; gfx_y = 40;
gfx_printf("%.1f dB", slider1);

// Meter bar
gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.3;
gfx_rect(10, 80, 280, 20);
gfx_r = 0.2; gfx_g = 0.7; gfx_b = 0.3;
gfx_rect(10, 80, 280 * level, 20);

// Decorative circle
gfx_r = 0.5; gfx_g = 0.5; gfx_b = 0.6;
gfx_circle(gfx_w - 30, gfx_h - 30, 15, 0, 1);
```
