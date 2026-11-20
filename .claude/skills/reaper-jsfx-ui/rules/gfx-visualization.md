---
title: "Visualization"
impact: HIGH
tags:
  - visualization
  - meter
  - waveform
  - spectrum
---

# Visualization

Level meters, waveform displays, spectrum analyzers, and other visualizations.

---

## Level Meter

### Vertical Meter

```
function draw_vmeter(x, y, w, h, level_db, peak_db)
  local(level_y, peak_y, seg_h, i, seg_db)
(
  // Background
  gfx_r = 0.15; gfx_g = 0.15; gfx_b = 0.18;
  gfx_rect(x, y, w, h);

  // Convert dB to height (0dB at top, -60dB at bottom)
  level_y = y + h * (1 - max(0, (level_db + 60) / 60));
  peak_y = y + h * (1 - max(0, (peak_db + 60) / 60));

  // Draw segments
  seg_h = h / 30;  // 30 segments
  i = 0;
  loop(30,
    seg_db = -60 + i * 2;  // 2dB per segment

    // Color based on level
    seg_db > -6 ? (
      gfx_r = 1; gfx_g = 0.2; gfx_b = 0.2;  // Red
    ) : seg_db > -18 ? (
      gfx_r = 1; gfx_g = 0.8; gfx_b = 0.2;  // Yellow
    ) : (
      gfx_r = 0.2; gfx_g = 0.8; gfx_b = 0.3;  // Green
    );

    // Only draw if level reaches this segment
    seg_db < level_db ? (
      gfx_rect(x + 1, y + h - (i + 1) * seg_h + 1, w - 2, seg_h - 2);
    );

    i += 1;
  );

  // Peak indicator
  gfx_r = gfx_g = gfx_b = 1;
  gfx_rect(x, peak_y, w, 2);
);
```

### Stereo Meter

```
@init
peak_l = peak_r = -100;
peak_hold = 0;

@sample
// Track levels
level_l = 20 * log10(max(0.000001, abs(spl0)));
level_r = 20 * log10(max(0.000001, abs(spl1)));

// Peak hold
level_l > peak_l ? peak_l = level_l;
level_r > peak_r ? peak_r = level_r;

@block
// Peak decay
peak_hold += samplesblock;
peak_hold > srate * 2 ? (  // 2 second hold
  peak_l -= 0.5;
  peak_r -= 0.5;
  peak_l < -60 ? peak_l = -60;
  peak_r < -60 ? peak_r = -60;
);

@gfx 100 200
// Draw stereo meters
draw_vmeter(10, 10, 35, 180, level_l, peak_l);
draw_vmeter(55, 10, 35, 180, level_r, peak_r);

// Labels
gfx_r = gfx_g = gfx_b = 0.7;
gfx_x = 20; gfx_y = 190;
gfx_drawstr("L");
gfx_x = 65;
gfx_drawstr("R");
```

---

## Waveform Display

### Scrolling Waveform

```
@init
waveform_buf = 0;
waveform_size = 512;
waveform_pos = 0;
freembuf(waveform_size);

@sample
waveform_buf[waveform_pos] = (spl0 + spl1) * 0.5;
waveform_pos = (waveform_pos + 1) % waveform_size;

@gfx 400 150
// Background
gfx_r = 0.1; gfx_g = 0.1; gfx_b = 0.12;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Center line
gfx_r = 0.3; gfx_g = 0.3; gfx_b = 0.35;
gfx_line(0, gfx_h/2, gfx_w, gfx_h/2, 0);

// Waveform
gfx_r = 0.3; gfx_g = 0.8; gfx_b = 0.4;
x_scale = gfx_w / waveform_size;

i = 0;
loop(waveform_size - 1,
  idx = (waveform_pos + i) % waveform_size;
  idx_next = (waveform_pos + i + 1) % waveform_size;

  x1 = i * x_scale;
  x2 = (i + 1) * x_scale;
  y1 = gfx_h/2 - waveform_buf[idx] * gfx_h/2 * 0.9;
  y2 = gfx_h/2 - waveform_buf[idx_next] * gfx_h/2 * 0.9;

  gfx_line(x1, y1, x2, y2, 1);
  i += 1;
);
```

---

## Spectrum Analyzer

### FFT-Based Spectrum

```
@init
fft_size = 1024;
fft_buf = 0;
fft_pos = 0;
spectrum = fft_size;  // Store magnitude
freembuf(fft_size * 2 + fft_size);

// Window function (Hanning)
window = fft_size * 2 + fft_size;
freembuf(window + fft_size);
i = 0;
loop(fft_size,
  window[i] = 0.5 * (1 - cos(2 * $pi * i / (fft_size - 1)));
  i += 1;
);

@sample
// Collect samples
fft_buf[fft_pos] = (spl0 + spl1) * 0.5 * window[fft_pos];
fft_buf[fft_pos + 1] = 0;  // Imaginary = 0
fft_pos += 2;

fft_pos >= fft_size * 2 ? (
  // Perform FFT
  fft(fft_buf, fft_size);

  // Calculate magnitude
  i = 0;
  loop(fft_size / 2,
    re = fft_buf[i * 2];
    im = fft_buf[i * 2 + 1];
    spectrum[i] = sqrt(re * re + im * im);
    i += 1;
  );

  fft_pos = 0;
);

@gfx 400 200
// Background
gfx_r = 0.08; gfx_g = 0.08; gfx_b = 0.1;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Draw spectrum
gfx_r = 0.3; gfx_g = 0.6; gfx_b = 0.9;
num_bins = fft_size / 2;

i = 0;
loop(num_bins,
  // Logarithmic frequency scale
  log_i = log(1 + i) / log(num_bins) * gfx_w;
  log_i_next = log(2 + i) / log(num_bins) * gfx_w;

  // Convert to dB
  mag_db = 20 * log10(max(0.00001, spectrum[i]));
  height = max(0, (mag_db + 60) / 60) * gfx_h;

  gfx_rect(log_i, gfx_h - height, max(1, log_i_next - log_i), height);
  i += 1;
);
```

---

## Gain Reduction Meter

```
@init
gr_history = 0;
gr_size = 128;
gr_pos = 0;
freembuf(gr_size);

@sample
// Assuming gr_linear is 0-1 (1 = no reduction)
gr_db = 20 * log10(max(0.001, gr_linear));
gr_history[gr_pos] = gr_db;
gr_pos = (gr_pos + 1) % gr_size;

@gfx 200 50
// Background
gfx_r = 0.12; gfx_g = 0.12; gfx_b = 0.15;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Draw GR history
gfx_r = 0.9; gfx_g = 0.5; gfx_b = 0.2;
x_scale = gfx_w / gr_size;

i = 0;
loop(gr_size,
  idx = (gr_pos + i) % gr_size;
  x = i * x_scale;
  // Scale: 0dB at top, -20dB at bottom
  y = -gr_history[idx] / 20 * gfx_h;
  y = max(0, min(gfx_h, y));
  gfx_rect(x, 0, max(1, x_scale), y);
  i += 1;
);

// Current GR value
gfx_r = gfx_g = gfx_b = 1;
gfx_x = 5; gfx_y = 5;
gfx_printf("GR: %.1f dB", gr_history[(gr_pos - 1 + gr_size) % gr_size]);
```

---

## Phase Correlation Meter

```
@init
correlation = 0;
corr_smooth = 0;

@sample
// Calculate instantaneous correlation
// +1 = mono, 0 = uncorrelated, -1 = out of phase
l = spl0;
r = spl1;
sum_lr = l * r;
sum_ll = l * l;
sum_rr = r * r;

// Running averages
sum_lr_avg += 0.001 * (sum_lr - sum_lr_avg);
sum_ll_avg += 0.001 * (sum_ll - sum_ll_avg);
sum_rr_avg += 0.001 * (sum_rr - sum_rr_avg);

denom = sqrt(sum_ll_avg * sum_rr_avg);
denom > 0.00001 ? correlation = sum_lr_avg / denom : correlation = 0;

@gfx 200 30
// Background
gfx_r = 0.15; gfx_g = 0.15; gfx_b = 0.18;
gfx_rect(0, 0, gfx_w, gfx_h);

// Meter bar
center_x = gfx_w / 2;
bar_w = (gfx_w - 20) / 2;

// Background bar
gfx_r = 0.25; gfx_g = 0.25; gfx_b = 0.28;
gfx_rect(10, 10, gfx_w - 20, 10);

// Correlation bar
correlation > 0 ? (
  gfx_r = 0.3; gfx_g = 0.8; gfx_b = 0.3;  // Green
  gfx_rect(center_x, 10, correlation * bar_w, 10);
) : (
  gfx_r = 0.9; gfx_g = 0.3; gfx_b = 0.3;  // Red
  gfx_rect(center_x + correlation * bar_w, 10, -correlation * bar_w, 10);
);

// Center mark
gfx_r = gfx_g = gfx_b = 0.6;
gfx_rect(center_x - 1, 8, 2, 14);

// Labels
gfx_r = gfx_g = gfx_b = 0.5;
gfx_x = 5; gfx_y = 8;
gfx_drawstr("-1");
gfx_x = gfx_w - 15;
gfx_drawstr("+1");
```

---

## Vectorscope

```
@init
scope_buf_l = 0;
scope_buf_r = 4096;
scope_size = 4096;
scope_pos = 0;
freembuf(8192);

@sample
scope_buf_l[scope_pos] = spl0;
scope_buf_r[scope_pos] = spl1;
scope_pos = (scope_pos + 1) % scope_size;

@gfx 200 200
// Background
gfx_r = 0.05; gfx_g = 0.05; gfx_b = 0.08;
gfx_x = gfx_y = 0;
gfx_rectto(gfx_w, gfx_h);

// Crosshairs
gfx_r = 0.2; gfx_g = 0.2; gfx_b = 0.25;
gfx_line(gfx_w/2, 0, gfx_w/2, gfx_h, 0);
gfx_line(0, gfx_h/2, gfx_w, gfx_h/2, 0);

// Scope trace
gfx_r = 0.3; gfx_g = 0.9; gfx_b = 0.4; gfx_a = 0.5;
scale = gfx_w * 0.4;

i = 0;
loop(scope_size,
  idx = (scope_pos + i) % scope_size;
  l = scope_buf_l[idx];
  r = scope_buf_r[idx];

  // X = L+R (sum), Y = L-R (difference)
  // Or traditional: X = R, Y = L rotated 45°
  x = gfx_w/2 + (l + r) * scale * 0.707;
  y = gfx_h/2 - (l - r) * scale * 0.707;

  gfx_setpixel(gfx_r, gfx_g, gfx_b);
  gfx_x = x; gfx_y = y;
  gfx_setpixel(gfx_r, gfx_g, gfx_b);
  i += 1;
);
```
