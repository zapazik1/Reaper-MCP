---
title: "Oscillators"
impact: CRITICAL
tags:
  - oscillator
  - polyblep
  - wavetable
  - fm
  - synthesis
---

# Oscillators

Anti-aliased oscillator implementations including PolyBLEP, wavetable, and FM synthesis.

## References

- [Tale's poly_blep.jsfx-inc](https://www.taletn.com/reaper/mono_synth/)
- [PolyBLEP Oscillators](https://www.kvraudio.com/forum/viewtopic.php?t=398553)
- [Wavetable Synthesis](https://ccrma.stanford.edu/~jos/pasp/Wavetable_Synthesis.html)

---

## The Aliasing Problem

Naive digital oscillators with sharp transitions (saw, square, pulse) create harmonics above Nyquist, which fold back as aliasing artifacts.

```
// BAD: Naive saw (aliases badly at high frequencies)
phase += freq / srate;
phase >= 1 ? phase -= 1;
output = phase * 2 - 1;  // Discontinuity causes aliasing

// At 5kHz with 44.1kHz sample rate, harmonics at 10k, 15k, 20k...
// Frequencies above 22.05kHz fold back as audible aliasing
```

**Solutions:**
1. **PolyBLEP** - Correct discontinuities in time domain
2. **Wavetable** - Pre-computed band-limited waveforms
3. **Oversampling** - Generate at higher rate, filter down

---

## PolyBLEP Oscillators

Polynomial Band-Limited Step correction. Smooths discontinuities.

### PolyBLEP Function

```
// Polynomial correction for step discontinuities
// t = phase position normalized to one sample (0-1 at discontinuity)
function polyblep(t, dt)
  local(t2)
(
  t < dt ? (
    t /= dt;
    t + t - t * t - 1;
  ) : t > 1 - dt ? (
    t = (t - 1) / dt;
    t * t + t + t + 1;
  ) : 0;
);
```

### PolyBLEP Saw

```
@init
phase = 0;

@slider
freq = 440;
dt = freq / srate;

@sample
// Increment phase
phase += dt;
phase >= 1 ? phase -= 1;

// Naive saw
output = phase * 2 - 1;

// Apply PolyBLEP at wrap point
output -= polyblep(phase, dt);

spl0 = spl1 = output * 0.5;
```

### PolyBLEP Square

```
@sample
phase += dt;
phase >= 1 ? phase -= 1;

// Naive square
output = phase < 0.5 ? 1 : -1;

// PolyBLEP at both transitions
output += polyblep(phase, dt);              // Rising edge at 0
output -= polyblep(fmod(phase + 0.5, 1), dt);  // Falling edge at 0.5

spl0 = spl1 = output * 0.5;
```

### PolyBLEP Pulse (Variable Width)

```
@slider
pulse_width = 0.3;  // 0-1

@sample
phase += dt;
phase >= 1 ? phase -= 1;

// Naive pulse
output = phase < pulse_width ? 1 : -1;

// PolyBLEP at both transitions
output += polyblep(phase, dt);
output -= polyblep(fmod(phase + (1 - pulse_width), 1), dt);

// DC compensation
output -= pulse_width * 2 - 1;

spl0 = spl1 = output * 0.5;
```

### PolyBLEP Triangle

Integrate a square wave (differentiated triangle = square):

```
@init
phase = 0;
tri_state = 0;

@sample
phase += dt;
phase >= 1 ? phase -= 1;

// Square wave (PolyBLEP corrected)
square = phase < 0.5 ? 1 : -1;
square += polyblep(phase, dt);
square -= polyblep(fmod(phase + 0.5, 1), dt);

// Leaky integrator for triangle
// Adjust coefficient for proper amplitude
tri_state = 0.999 * tri_state + square * dt * 4;

spl0 = spl1 = tri_state * 0.5;
```

---

## Complete PolyBLEP Oscillator Library

```
// osc.jsfx-inc

function osc.init()
  instance(phase, last_phase)
(
  phase = 0;
  last_phase = 0;
);

function osc.set_freq(freq)
  instance(dt)
(
  dt = freq / srate;
);

function osc.set_note(note)
  instance(dt)
(
  dt = 440 * pow(2, (note - 69) / 12) / srate;
);

function osc.polyblep(t)
  instance(dt)
  local(t2)
(
  t < dt ? (
    t /= dt;
    t + t - t * t - 1;
  ) : t > 1 - dt ? (
    t = (t - 1) / dt;
    t * t + t + t + 1;
  ) : 0;
);

function osc.saw()
  instance(phase, dt)
  local(output)
(
  phase += dt;
  phase >= 1 ? phase -= 1;

  output = phase * 2 - 1;
  output -= this.polyblep(phase);
  output;
);

function osc.square()
  instance(phase, dt)
  local(output, t2)
(
  phase += dt;
  phase >= 1 ? phase -= 1;

  output = phase < 0.5 ? 1 : -1;
  output += this.polyblep(phase);
  t2 = phase + 0.5;
  t2 >= 1 ? t2 -= 1;
  output -= this.polyblep(t2);
  output;
);

function osc.pulse(width)
  instance(phase, dt)
  local(output, t2)
(
  phase += dt;
  phase >= 1 ? phase -= 1;

  output = phase < width ? 1 : -1;
  output += this.polyblep(phase);
  t2 = phase + (1 - width);
  t2 >= 1 ? t2 -= 1;
  output -= this.polyblep(t2);
  output -= width * 2 - 1;  // DC offset
  output;
);

function osc.sine()
  instance(phase, dt)
(
  phase += dt;
  phase >= 1 ? phase -= 1;
  sin(2 * $pi * phase);
);

function osc.tri()
  instance(phase, dt, tri_state)
  local(sq)
(
  phase += dt;
  phase >= 1 ? phase -= 1;

  sq = phase < 0.5 ? 1 : -1;
  sq += this.polyblep(phase);
  sq -= this.polyblep(phase + 0.5 >= 1 ? phase - 0.5 : phase + 0.5);

  tri_state = 0.999 * tri_state + sq * dt * 4;
  tri_state;
);

// Usage:
// my_osc.osc.init();
// my_osc.osc.set_note(60);
// output = my_osc.osc.saw();
```

---

## Wavetable Oscillator

Pre-computed band-limited tables for different octaves.

### Single Table (Simple)

```
@init
table_size = 2048;
wavetable = 0;
freembuf(table_size);

// Generate saw wavetable
i = 0;
loop(table_size,
  wavetable[i] = i / table_size * 2 - 1;
  i += 1;
);

@sample
// Read from wavetable with linear interpolation
table_pos = phase * table_size;
idx = floor(table_pos);
frac = table_pos - idx;
idx_next = (idx + 1) % table_size;

output = wavetable[idx] * (1 - frac) + wavetable[idx_next] * frac;

phase += dt;
phase >= 1 ? phase -= 1;

spl0 = spl1 = output * 0.5;
```

### Multi-Table (Band-Limited)

```
@init
table_size = 2048;
num_tables = 10;  // One per octave
tables = 0;
freembuf(table_size * num_tables);

// Generate band-limited tables for each octave
table = 0;
loop(num_tables,
  // Number of harmonics for this octave
  // Octave 0 = full harmonics, higher = fewer
  max_harmonic = floor((srate / 2) / (440 * pow(2, table - 5)));
  max_harmonic = max(1, min(max_harmonic, table_size / 2));

  // Generate table via additive synthesis
  i = 0;
  loop(table_size,
    sum = 0;
    h = 1;
    loop(max_harmonic,
      // Saw: all harmonics, amplitude 1/h
      sum += sin(2 * $pi * h * i / table_size) / h;
      h += 1;
    );
    tables[table * table_size + i] = sum * 2 / $pi;
    i += 1;
  );

  table += 1;
);

@slider
// Select table based on frequency
octave = log(freq / 440) / log(2) + 5;
table_idx = floor(max(0, min(num_tables - 1, octave)));

@sample
// Read from appropriate table
table_base = table_idx * table_size;
table_pos = phase * table_size;
idx = floor(table_pos);
frac = table_pos - idx;
idx_next = (idx + 1) % table_size;

output = tables[table_base + idx] * (1 - frac) +
         tables[table_base + idx_next] * frac;

phase += dt;
phase >= 1 ? phase -= 1;
```

---

## FM Synthesis

### Two-Operator FM

```
desc:Simple FM Synth
slider1:ratio=2<0.5,8,0.01>Ratio
slider2:mod_depth=100<0,1000,1>Mod Depth

@init
carrier_phase = 0;
mod_phase = 0;

@block
// Get note from MIDI
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  status == $x90 && msg3 > 0 ? (
    note = msg2;
    carrier_freq = 440 * pow(2, (note - 69) / 12);
    mod_freq = carrier_freq * ratio;
    carrier_dt = carrier_freq / srate;
    mod_dt = mod_freq / srate;
    gate = 1;
  );
  status == $x80 ? gate = 0;
);

@sample
// Modulator
mod_phase += mod_dt;
mod_phase >= 1 ? mod_phase -= 1;
modulator = sin(2 * $pi * mod_phase);

// Carrier with FM
// Modulation index = mod_depth / mod_freq
fm = modulator * mod_depth / srate;
carrier_phase += carrier_dt + fm;
carrier_phase >= 1 ? carrier_phase -= 1;
carrier_phase < 0 ? carrier_phase += 1;

output = sin(2 * $pi * carrier_phase);

spl0 = spl1 = output * gate * 0.3;
```

### DX7-Style FM (6 Operators)

```
// Simplified 6-op structure
// Each operator: phase, freq_ratio, output_level, feedback
// Algorithms define routing

@init
NUM_OPS = 6;
op_phase = 0;
op_ratio = NUM_OPS;
op_level = NUM_OPS * 2;
op_feedback = NUM_OPS * 3;
op_output = NUM_OPS * 4;
freembuf(NUM_OPS * 5);

// Algorithm 1: 6->5->4->3->2->1 (all in series)
// Algorithm 2: (6->5) + (4->3) -> 2 -> 1

@sample
// Process operators in reverse order (modulators first)
// Op 6
op_output[5] = sin(2 * $pi * op_phase[5]) * op_level[5];
op_phase[5] += base_freq * op_ratio[5] / srate;

// Op 5 (modulated by op 6)
op_output[4] = sin(2 * $pi * op_phase[4] + op_output[5]) * op_level[4];
op_phase[4] += base_freq * op_ratio[4] / srate;

// ... continue for all operators

// Final output from carrier(s)
output = op_output[0];
```

---

## Noise Generator

### White Noise

```
@sample
noise = rand(2) - 1;  // Random -1 to 1
spl0 = spl1 = noise * level;
```

### Pink Noise (1/f)

Paul Kellet's algorithm:

```
@init
b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0;

@sample
white = rand(2) - 1;

b0 = 0.99886 * b0 + white * 0.0555179;
b1 = 0.99332 * b1 + white * 0.0750759;
b2 = 0.96900 * b2 + white * 0.1538520;
b3 = 0.86650 * b3 + white * 0.3104856;
b4 = 0.55000 * b4 + white * 0.5329522;
b5 = -0.7616 * b5 - white * 0.0168980;

pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
b6 = white * 0.115926;

spl0 = spl1 = pink * 0.11;  // Normalize
```

### Brown Noise (1/f²)

```
@init
brown_state = 0;

@sample
white = rand(2) - 1;
brown_state = (brown_state + white * 0.02) * 0.998;
brown_state = max(-1, min(1, brown_state));

spl0 = spl1 = brown_state;
```

---

## Sub-Oscillator

```
@init
main_phase = 0;
sub_phase = 0;

@slider
sub_level = 0.5;  // -1 to 1 octaves below

@sample
// Main oscillator
main_phase += main_dt;
main_phase >= 1 ? main_phase -= 1;
main = main_osc.saw();

// Sub oscillator (one octave down)
sub_phase += main_dt * 0.5;  // Half frequency
sub_phase >= 1 ? sub_phase -= 1;
sub = sin(2 * $pi * sub_phase);  // Sine sub is common

// Mix
output = main * (1 - sub_level) + sub * sub_level;
```

---

## Unison / Detune

```
@init
NUM_UNISON = 7;
unison_phase = 0;
unison_detune = NUM_UNISON;
freembuf(NUM_UNISON * 2);

// Set detune amounts (symmetric around center)
unison_detune[0] = 0;     // Center
unison_detune[1] = 0.1;   // +10 cents
unison_detune[2] = -0.1;  // -10 cents
unison_detune[3] = 0.2;
unison_detune[4] = -0.2;
unison_detune[5] = 0.3;
unison_detune[6] = -0.3;

@slider
base_freq = 440;
detune_amount = 0.02;  // Max detune in semitones

@sample
output = 0;
i = 0;
loop(NUM_UNISON,
  // Frequency with detune
  detune_semitones = unison_detune[i] * detune_amount;
  freq = base_freq * pow(2, detune_semitones / 12);
  dt = freq / srate;

  // Increment phase
  unison_phase[i] += dt;
  unison_phase[i] >= 1 ? unison_phase[i] -= 1;

  // Add to output (saw with polyblep)
  osc = unison_phase[i] * 2 - 1;
  osc -= polyblep(unison_phase[i], dt);
  output += osc;

  i += 1;
);

output /= NUM_UNISON;  // Normalize
spl0 = spl1 = output * 0.3;
```
