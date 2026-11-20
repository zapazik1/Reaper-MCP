---
title: "Voice Management"
impact: HIGH
tags:
  - polyphony
  - voices
  - allocation
  - synthesis
---

# Voice Management

Polyphonic voice allocation, stealing, and management for synthesizers.

## References

- [Tale's JSFX Libraries](https://www.taletn.com/reaper/mono_synth/)
- [Voice Allocation Strategies](https://www.musicdsp.org/)

---

## Voice Architecture

### Memory Layout

```
@init
MAX_VOICES = 8;

// Voice state arrays (each voice has these properties)
voice_note = 0;                    // MIDI note number
voice_gate = MAX_VOICES;           // Gate state (on/off)
voice_velocity = MAX_VOICES * 2;   // Note velocity
voice_age = MAX_VOICES * 3;        // For voice stealing
voice_phase = MAX_VOICES * 4;      // Oscillator phase
voice_env = MAX_VOICES * 5;        // Envelope value
voice_env_stage = MAX_VOICES * 6;  // Envelope stage

// Initialize all voices
freembuf(MAX_VOICES * 7);

i = 0;
loop(MAX_VOICES,
  voice_note[i] = -1;
  voice_gate[i] = 0;
  voice_velocity[i] = 0;
  voice_age[i] = 0;
  voice_phase[i] = 0;
  voice_env[i] = 0;
  voice_env_stage[i] = 0;
  i += 1;
);

global_age = 0;  // Incremented on each note
```

---

## Voice Allocation

### Find Free Voice

```
function find_free_voice()
  local(i, v)
(
  v = -1;

  // First pass: find idle voice
  i = 0;
  loop(MAX_VOICES,
    voice_gate[i] == 0 && voice_env[i] < 0.001 ? (
      v = i;
      i = MAX_VOICES;  // Break
    );
    i += 1;
  );

  v;
);
```

### Find Voice Playing Note

```
function find_voice_with_note(note)
  local(i, v)
(
  v = -1;
  i = 0;
  loop(MAX_VOICES,
    voice_note[i] == note && voice_gate[i] ? (
      v = i;
      i = MAX_VOICES;  // Break
    );
    i += 1;
  );
  v;
);
```

---

## Voice Stealing

When all voices are busy, steal the least important one.

### Oldest Voice

```
function steal_oldest_voice()
  local(i, oldest, oldest_age)
(
  oldest = 0;
  oldest_age = voice_age[0];

  i = 1;
  loop(MAX_VOICES - 1,
    voice_age[i] < oldest_age ? (
      oldest = i;
      oldest_age = voice_age[i];
    );
    i += 1;
  );

  oldest;
);
```

### Lowest Velocity

```
function steal_quietest_voice()
  local(i, quietest, quietest_vel)
(
  quietest = 0;
  quietest_vel = voice_velocity[0];

  i = 1;
  loop(MAX_VOICES - 1,
    voice_velocity[i] < quietest_vel ? (
      quietest = i;
      quietest_vel = voice_velocity[i];
    );
    i += 1;
  );

  quietest;
);
```

### Releasing Voice (Prefer Stealing Release)

```
function steal_voice()
  local(i, v, oldest_releasing, oldest_held)
  local(oldest_rel_age, oldest_held_age)
(
  oldest_releasing = -1;
  oldest_held = -1;
  oldest_rel_age = global_age + 1;
  oldest_held_age = global_age + 1;

  i = 0;
  loop(MAX_VOICES,
    voice_gate[i] == 0 ? (
      // Releasing voice
      voice_age[i] < oldest_rel_age ? (
        oldest_releasing = i;
        oldest_rel_age = voice_age[i];
      );
    ) : (
      // Held voice
      voice_age[i] < oldest_held_age ? (
        oldest_held = i;
        oldest_held_age = voice_age[i];
      );
    );
    i += 1;
  );

  // Prefer stealing releasing voices
  oldest_releasing >= 0 ? oldest_releasing : oldest_held;
);
```

---

## Complete Voice Allocator

```
function allocate_voice(note, velocity)
  local(v)
(
  // Try to find free voice
  v = find_free_voice();

  // If no free voice, steal one
  v < 0 ? v = steal_voice();

  // Initialize voice
  voice_note[v] = note;
  voice_gate[v] = 1;
  voice_velocity[v] = velocity / 127;
  voice_age[v] = global_age;
  global_age += 1;

  // Reset oscillator (or not, for smooth transitions)
  reset_phase_on_trigger ? voice_phase[v] = 0;

  // Trigger envelope
  voice_env_stage[v] = 1;

  v;
);

function release_voice(note)
  local(i)
(
  i = 0;
  loop(MAX_VOICES,
    voice_note[i] == note && voice_gate[i] ? (
      voice_gate[i] = 0;
      voice_env_stage[i] = 4;  // Release stage
    );
    i += 1;
  );
);

function release_all_voices()
  local(i)
(
  i = 0;
  loop(MAX_VOICES,
    voice_gate[i] ? (
      voice_gate[i] = 0;
      voice_env_stage[i] = 4;
    );
    i += 1;
  );
);
```

---

## Processing Voices

### Per-Voice Processing

```
@sample
output_l = output_r = 0;

i = 0;
loop(MAX_VOICES,
  // Skip completely idle voices
  voice_env[i] > 0.0001 || voice_gate[i] ? (

    // Calculate frequency
    freq = 440 * pow(2, (voice_note[i] - 69) / 12);
    dt = freq / srate;

    // Oscillator
    voice_phase[i] += dt;
    voice_phase[i] >= 1 ? voice_phase[i] -= 1;
    osc = voice_phase[i] * 2 - 1;  // Saw
    osc -= polyblep(voice_phase[i], dt);

    // Envelope
    voice_gate[i] ? (
      voice_env_stage[i] == 1 ? (
        voice_env[i] = attack_coeff * voice_env[i] + (1 - attack_coeff);
        voice_env[i] >= 0.999 ? voice_env_stage[i] = 2;
      ) : voice_env_stage[i] == 2 ? (
        voice_env[i] = decay_coeff * voice_env[i] + (1 - decay_coeff) * sustain;
      );
    ) : (
      voice_env[i] = release_coeff * voice_env[i];
    );

    // Add to output
    voice_out = osc * voice_env[i] * voice_velocity[i];
    output_l += voice_out;
    output_r += voice_out;
  );

  i += 1;
);

// Scale output
spl0 = output_l * 0.2;
spl1 = output_r * 0.2;
```

---

## Mono Modes

### Last Note Priority

```
@init
note_stack = 0;  // Stack of held notes
stack_size = 0;
MAX_STACK = 16;
freembuf(MAX_STACK);

function push_note(note)
(
  stack_size < MAX_STACK ? (
    note_stack[stack_size] = note;
    stack_size += 1;
  );
);

function pop_note()
  local(n)
(
  stack_size > 0 ? (
    stack_size -= 1;
    note_stack[stack_size];
  ) : -1;
);

function remove_note(note)
  local(i, j)
(
  i = 0;
  loop(stack_size,
    note_stack[i] == note ? (
      // Shift remaining notes down
      j = i;
      loop(stack_size - i - 1,
        note_stack[j] = note_stack[j + 1];
        j += 1;
      );
      stack_size -= 1;
      i = stack_size;  // Break
    );
    i += 1;
  );
);

@block
// Note On
status == $x90 && msg3 > 0 ? (
  push_note(msg2);
  current_note = msg2;
  gate = 1;

  legato ? (
    // Don't retrigger envelope if notes held
    stack_size == 1 ? trigger_envelope();
  ) : (
    trigger_envelope();
  );
);

// Note Off
status == $x80 || (status == $x90 && msg3 == 0) ? (
  remove_note(msg2);

  stack_size > 0 ? (
    // Play previous note
    current_note = note_stack[stack_size - 1];
  ) : (
    // No notes held
    gate = 0;
    release_envelope();
  );
);
```

### Low/High Note Priority

```
function get_lowest_note()
  local(i, lowest)
(
  lowest = 127;
  i = 0;
  loop(stack_size,
    note_stack[i] < lowest ? lowest = note_stack[i];
    i += 1;
  );
  stack_size > 0 ? lowest : -1;
);

function get_highest_note()
  local(i, highest)
(
  highest = 0;
  i = 0;
  loop(stack_size,
    note_stack[i] > highest ? highest = note_stack[i];
    i += 1;
  );
  stack_size > 0 ? highest : -1;
);
```

---

## Unison Mode

All voices play same note:

```
function trigger_unison(note, velocity)
  local(i, detune)
(
  i = 0;
  loop(MAX_VOICES,
    voice_note[i] = note;
    voice_gate[i] = 1;
    voice_velocity[i] = velocity / 127;

    // Spread detune across voices
    detune = (i - (MAX_VOICES - 1) / 2) * unison_detune;
    voice_detune[i] = detune;

    // Trigger envelope
    voice_env_stage[i] = 1;

    i += 1;
  );
);

function release_unison()
  local(i)
(
  i = 0;
  loop(MAX_VOICES,
    voice_gate[i] = 0;
    voice_env_stage[i] = 4;
    i += 1;
  );
);
```

---

## Voice Panning

### Round-Robin Pan

```
@init
pan_positions[0] = -0.8;
pan_positions[1] = 0.8;
pan_positions[2] = -0.4;
pan_positions[3] = 0.4;
pan_positions[4] = -0.6;
pan_positions[5] = 0.6;
pan_positions[6] = -0.2;
pan_positions[7] = 0.2;

@sample
i = 0;
loop(MAX_VOICES,
  // ... process voice ...

  pan = pan_positions[i];
  left_gain = cos((pan + 1) * $pi / 4);
  right_gain = sin((pan + 1) * $pi / 4);

  output_l += voice_out * left_gain;
  output_r += voice_out * right_gain;

  i += 1;
);
```

### Voice Spread

```
@slider
voice_spread = spread_slider;  // 0-1

@sample
// Calculate pan based on voice index
pan = (i / (MAX_VOICES - 1) * 2 - 1) * voice_spread;
```

---

## Complete Polyphonic Synth Structure

```
desc:Polyphonic Synth
tags:instrument synthesizer

slider1:attack_ms=10<1,1000,1:log>Attack
slider2:decay_ms=100<1,1000,1:log>Decay
slider3:sustain=0.7<0,1,0.01>Sustain
slider4:release_ms=200<1,2000,1:log>Release

in_pin:none
out_pin:left output
out_pin:right output

@init
MAX_VOICES = 8;

// Allocate voice state
voice_note = 0;
voice_gate = MAX_VOICES;
voice_velocity = MAX_VOICES * 2;
voice_phase = MAX_VOICES * 3;
voice_env = MAX_VOICES * 4;
voice_env_stage = MAX_VOICES * 5;
voice_age = MAX_VOICES * 6;
freembuf(MAX_VOICES * 7);

// Initialize
i = 0;
loop(MAX_VOICES,
  voice_note[i] = -1;
  voice_gate[i] = 0;
  i += 1;
);

global_age = 0;

@slider
attack_coeff = exp(-1 / (attack_ms * srate / 1000));
decay_coeff = exp(-1 / (decay_ms * srate / 1000));
release_coeff = exp(-1 / (release_ms * srate / 1000));

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    // Note On - allocate voice
    v = find_free_voice();
    v < 0 ? v = steal_voice();

    voice_note[v] = msg2;
    voice_gate[v] = 1;
    voice_velocity[v] = msg3 / 127;
    voice_phase[v] = 0;
    voice_env_stage[v] = 1;
    voice_age[v] = global_age;
    global_age += 1;
  );

  status == $x80 || (status == $x90 && msg3 == 0) ? (
    // Note Off
    i = 0;
    loop(MAX_VOICES,
      voice_note[i] == msg2 && voice_gate[i] ? (
        voice_gate[i] = 0;
        voice_env_stage[i] = 4;
      );
      i += 1;
    );
  );
);

@sample
output_l = output_r = 0;

i = 0;
loop(MAX_VOICES,
  (voice_env[i] > 0.0001 || voice_gate[i]) ? (
    // Frequency
    freq = 440 * pow(2, (voice_note[i] - 69) / 12);
    dt = freq / srate;

    // Oscillator (PolyBLEP saw)
    voice_phase[i] += dt;
    voice_phase[i] >= 1 ? voice_phase[i] -= 1;
    osc = voice_phase[i] * 2 - 1;
    t = voice_phase[i] / dt;
    t < 1 ? osc -= t + t - t * t - 1;
    t = voice_phase[i] - 1;
    t > -dt ? (t = (t + dt) / dt; osc -= t * t + t + t + 1);

    // Envelope
    stage = voice_env_stage[i];
    stage == 1 ? (
      voice_env[i] = attack_coeff * voice_env[i] + (1 - attack_coeff);
      voice_env[i] >= 0.999 ? voice_env_stage[i] = 2;
    ) : stage == 2 ? (
      voice_env[i] = decay_coeff * voice_env[i] + (1 - decay_coeff) * sustain;
    ) : stage == 4 ? (
      voice_env[i] = release_coeff * voice_env[i];
    );

    // Mix
    voice_out = osc * voice_env[i] * voice_velocity[i];
    output_l += voice_out;
    output_r += voice_out;
  );
  i += 1;
);

spl0 = output_l * 0.15;
spl1 = output_r * 0.15;
```
