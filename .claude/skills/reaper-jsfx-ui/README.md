# REAPER JSFX Graphics & UI

Patterns for custom graphical interfaces in JSFX. Covers drawing primitives, interactive widgets, audio visualizations, and mouse/keyboard interaction.

## Installation

```bash
npx skills add mthines/jsfx-agent-skills
```

## Prerequisites

Requires [reaper-jsfx-core](../reaper-jsfx-core/README.md) for language fundamentals.

## When to Use

Use this skill when building:
- Custom plugin interfaces
- Knobs, sliders, buttons
- Level meters and VU displays
- Waveform visualizations
- Spectrum analyzers
- Interactive XY pads

## Rules

| Rule | Impact | Description |
|------|--------|-------------|
| [gfx-basics](./rules/gfx-basics.md) | CRITICAL | @gfx section, coordinate system, colors, drawing primitives, text |
| [gfx-widgets](./rules/gfx-widgets.md) | HIGH | Knobs, sliders, buttons, toggles, dropdowns |
| [gfx-visualization](./rules/gfx-visualization.md) | HIGH | Level meters, waveform display, spectrum analyzer, vectorscope |
| [gfx-interaction](./rules/gfx-interaction.md) | MEDIUM | Mouse handling, keyboard input, drag behavior, context menus |

## Quick Start

Simple level meter:

```
desc:Simple Meter
@init
level_l = level_r = 0;
decay = exp(-1 / (srate * 0.3));  // 300ms decay

@sample
level_l = max(abs(spl0), level_l * decay);
level_r = max(abs(spl1), level_r * decay);

@gfx 100 200
// Background
gfx_r = gfx_g = gfx_b = 0.1; gfx_a = 1;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Left meter
gfx_r = 0.2; gfx_g = 0.8; gfx_b = 0.3;
meter_h = gfx_h * min(1, level_l);
gfx_rect(10, gfx_h - meter_h, 35, meter_h);

// Right meter
meter_h = gfx_h * min(1, level_r);
gfx_rect(55, gfx_h - meter_h, 35, meter_h);

// Labels
gfx_r = gfx_g = gfx_b = 0.7;
gfx_x = 22; gfx_y = 5;
gfx_drawstr("L");
gfx_x = 67;
gfx_drawstr("R");
```

## Key Concepts

### @gfx Runs Separately

```
@gfx 400 300  // Initial size request

// Runs ~30 fps in separate thread
// Do NOT modify audio state here
// Use gfx_w/gfx_h for actual dimensions
```

### Color Before Drawing

```
// Set color (0-1 range), then draw
gfx_r = 1; gfx_g = 0.5; gfx_b = 0; gfx_a = 1;
gfx_circle(100, 100, 30, 1);  // Filled orange circle
```

### Mouse Interaction

```
// Check if mouse is in control area
in_knob = sqr(mouse_x - cx) + sqr(mouse_y - cy) < sqr(radius);

// Detect click (edge detection)
clicked = (mouse_cap & 1) && !(last_cap & 1);
last_cap = mouse_cap;
```

## Resources

- [JSFX Graphics Reference](https://www.reaper.fm/sdk/js/gfx.php)
- [Geraint's UI Library](https://geraintluff.github.io/jsfx-ui-lib/)

## Related Skills

- **reaper-jsfx-core** - Required foundation
- **reaper-jsfx-audio** - DSP for visualizations (level detection, FFT)

## License

MIT
