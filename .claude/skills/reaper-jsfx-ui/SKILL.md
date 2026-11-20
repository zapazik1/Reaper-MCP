---
name: 'reaper-jsfx-ui'
description: 'Graphics and UI patterns for JSFX plugins. Use when building custom interfaces with knobs, sliders, meters, waveform displays, or spectrum analyzers. Triggers on requests for JSFX graphics, custom UI, visualization, or @gfx implementation.'
disable-model-invocation: true
license: MIT
metadata:
  author: mthines
  author_name: Mads Thines Coello
  author_email: madsthines@gmail.com
  version: '1.0.0'
  workflow_type: 'implementation'
  tags:
    - jsfx
    - reaper
    - graphics
    - ui
    - visualization
---

# REAPER JSFX Graphics & UI

Patterns for custom graphical interfaces in JSFX including drawing primitives, widgets, visualizations, and mouse interaction.

**Requires:** [reaper-jsfx-core](../reaper-jsfx-core/SKILL.md) for language fundamentals.

## Rules

| Rule | Description |
|------|-------------|
| [gfx-basics](./rules/gfx-basics.md) | @gfx section, coordinate system, colors, drawing primitives |
| [gfx-widgets](./rules/gfx-widgets.md) | Knobs, sliders, buttons, toggles, dropdowns |
| [gfx-visualization](./rules/gfx-visualization.md) | Waveform display, spectrum analyzer, level meters |
| [gfx-interaction](./rules/gfx-interaction.md) | Mouse handling, keyboard input, drag behavior |

## Official Documentation

- [JSFX Graphics Functions](https://www.reaper.fm/sdk/js/gfx.php)
- [Geraint's UI Library](https://geraintluff.github.io/jsfx-ui-lib/)

## Key Principles

### 1. @gfx Runs in Separate Thread

```
@gfx 400 300  // Request 400x300 initial size

// Runs ~30 times per second
// gfx_w, gfx_h contain actual dimensions
// Do NOT modify audio state here (race conditions)
```

### 2. Coordinate System

```
// Origin (0,0) is top-left
// X increases rightward
// Y increases downward

gfx_x = 0;      // Left edge
gfx_y = 0;      // Top edge
gfx_x = gfx_w;  // Right edge
gfx_y = gfx_h;  // Bottom edge
```

### 3. Color Before Drawing

```
// Set color first (0-1 range)
gfx_r = 1; gfx_g = 0; gfx_b = 0; gfx_a = 1;  // Red, full opacity

// Then draw
gfx_circle(100, 100, 50, 1);  // Filled red circle
```

### 4. Handle Retina/HiDPI (Critical for macOS)

**Platform difference:** On macOS retina, `gfx_w/gfx_h` are **physical pixels** (2x logical).

```
@init
base_w = 500; base_h = 380;

@gfx 500 380  // Preferred size (resizable)

// Request retina - REAPER updates to actual value (1.0 or 2.0)
!gfx_ext_retina ? gfx_ext_retina = 1;
retina = gfx_ext_retina > 0 ? gfx_ext_retina : 1;

// Calculate logical window size and scale
logical_w = gfx_w / retina;
logical_h = gfx_h / retina;
scale = min(logical_w / base_w, logical_h / base_h);

// Centering offset and combined draw scale
offset_x = (logical_w - base_w * scale) * 0.5 * retina;
offset_y = (logical_h - base_h * scale) * 0.5 * retina;
draw_scale = scale * retina;

// Mouse in base coordinates
mx = (mouse_x - offset_x) / draw_scale;
my = (mouse_y - offset_y) / draw_scale;

// Helper: scale size
function s(v) ( v * draw_scale; );
// Helper: scale X with offset
function sx(v) ( v * draw_scale + offset_x; );
// Helper: scale Y with offset
function sy(v) ( v * draw_scale + offset_y; );
```

See [gfx-basics](./rules/gfx-basics.md) for complete scaling system.

## Quick Reference

| Use Case | Rule |
|----------|------|
| Drawing shapes/text | [gfx-basics](./rules/gfx-basics.md) |
| Knobs and buttons | [gfx-widgets](./rules/gfx-widgets.md) |
| Meters and displays | [gfx-visualization](./rules/gfx-visualization.md) |
| Mouse interaction | [gfx-interaction](./rules/gfx-interaction.md) |

## Minimal UI Example

```
@gfx 200 100

// Background
gfx_r = gfx_g = gfx_b = 0.1; gfx_a = 1;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Level meter
gfx_r = 0; gfx_g = 0.8; gfx_b = 0.2;
meter_h = gfx_h * current_level;
gfx_x = 10;
gfx_y = gfx_h - meter_h;
gfx_rectto(50, gfx_h);

// Label
gfx_r = gfx_g = gfx_b = 1;
gfx_x = 60; gfx_y = 10;
gfx_drawstr("Level");
```
