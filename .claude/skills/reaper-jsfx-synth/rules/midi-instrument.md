---
title: "MIDI Instrument Handling"
impact: HIGH
tags:
  - midi
  - instrument
  - pitchbend
  - modwheel
  - aftertouch
---

# MIDI Instrument Handling

MIDI message processing for synthesizers including notes, pitch bend, mod wheel, aftertouch, and sustain pedal.

## References

- [JSFX MIDI Functions](https://www.reaper.fm/sdk/js/midi.php)
- [Tale's midi_queue.jsfx-inc](https://www.taletn.com/reaper/mono_synth/)
- [MIDI Specification](https://midi.org/specifications)

---

## MIDI Message Types

| Status | Type | Data 1 | Data 2 |
|--------|------|--------|--------|
| `$x8n` | Note Off | Note number | Velocity |
| `$x9n` | Note On | Note number | Velocity |
| `$xAn` | Poly Aftertouch | Note number | Pressure |
| `$xBn` | Control Change | Controller | Value |
| `$xCn` | Program Change | Program | - |
| `$xDn` | Channel Aftertouch | Pressure | - |
| `$xEn` | Pitch Bend | LSB | MSB |

Where `n` is the MIDI channel (0-15).

---

## Basic MIDI Processing

```
@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;  // Message type
  channel = msg1 & $x0F; // Channel (0-15)

  // Note On
  status == $x90 && msg3 > 0 ? (
    note = msg2;
    velocity = msg3;
    note_on(note, velocity);
  );

  // Note Off (or Note On with velocity 0)
  status == $x80 || (status == $x90 && msg3 == 0) ? (
    note = msg2;
    note_off(note);
  );

  // Control Change
  status == $xB0 ? (
    cc_num = msg2;
    cc_val = msg3;
    handle_cc(cc_num, cc_val);
  );

  // Pitch Bend
  status == $xE0 ? (
    // 14-bit value: 0-16383, center at 8192
    pitch_bend = (msg3 << 7) | msg2;
    handle_pitch_bend(pitch_bend);
  );

  // Channel Aftertouch
  status == $xD0 ? (
    aftertouch = msg2;  // 0-127
    handle_aftertouch(aftertouch);
  );

  // Poly Aftertouch
  status == $xA0 ? (
    note = msg2;
    pressure = msg3;
    handle_poly_aftertouch(note, pressure);
  );
);
```

---

## Pitch Bend

### Standard Pitch Bend

```
@init
pitch_bend_range = 2;  // Semitones (±2 is standard)
pitch_bend_value = 0;  // -1 to +1, normalized

function handle_pitch_bend(raw_bend)
(
  // Convert 14-bit (0-16383) to normalized (-1 to +1)
  pitch_bend_value = (raw_bend - 8192) / 8192;
);

@sample
// Apply to frequency
bend_multiplier = pow(2, pitch_bend_value * pitch_bend_range / 12);
freq = base_freq * bend_multiplier;
```

### Pitch Bend with Smoothing

```
@init
pitch_bend_target = 0;
pitch_bend_smooth = 0;
pitch_bend_coeff = exp(-2 * $pi * 100 / srate);  // 100 Hz smoothing

function handle_pitch_bend(raw_bend)
(
  pitch_bend_target = (raw_bend - 8192) / 8192;
);

@sample
// Smooth pitch bend changes
pitch_bend_smooth = pitch_bend_coeff * pitch_bend_smooth +
                    (1 - pitch_bend_coeff) * pitch_bend_target;

bend_multiplier = pow(2, pitch_bend_smooth * pitch_bend_range / 12);
```

---

## Mod Wheel (CC 1)

```
@init
mod_wheel = 0;  // 0-1 normalized

function handle_cc(cc, val)
(
  cc == 1 ? (  // Mod wheel
    mod_wheel = val / 127;
  );
);

@sample
// Apply mod wheel to vibrato depth
vibrato_depth = base_vibrato_depth * mod_wheel;

// Or to filter cutoff
filter_mod = mod_wheel * filter_mod_amount;
```

---

## Common CCs

```
function handle_cc(cc, val)
(
  cc == 1 ? (   // Mod wheel
    mod_wheel = val / 127;
  ) : cc == 7 ? (   // Volume
    volume = val / 127;
  ) : cc == 10 ? (  // Pan
    pan = (val - 64) / 64;  // -1 to +1
  ) : cc == 11 ? (  // Expression
    expression = val / 127;
  ) : cc == 64 ? (  // Sustain pedal
    sustain_pedal = val >= 64;
  ) : cc == 74 ? (  // Filter cutoff (common mapping)
    filter_cutoff_cc = val / 127;
  ) : cc == 71 ? (  // Resonance (common mapping)
    resonance_cc = val / 127;
  ) : cc == 73 ? (  // Attack
    attack_cc = val / 127;
  ) : cc == 72 ? (  // Release
    release_cc = val / 127;
  ) : cc == 91 ? (  // Reverb send
    reverb_send = val / 127;
  ) : cc == 120 ? ( // All Sound Off
    all_sound_off();
  ) : cc == 123 ? ( // All Notes Off
    all_notes_off();
  );
);
```

---

## Sustain Pedal

```
@init
sustain_pedal = 0;
sustained_notes = 0;  // Bitfield or array of sustained notes

function handle_cc(cc, val)
(
  cc == 64 ? (
    new_pedal_state = val >= 64;

    // Pedal released - release sustained notes
    sustain_pedal && !new_pedal_state ? (
      release_sustained_notes();
    );

    sustain_pedal = new_pedal_state;
  );
);

function note_off(note)
(
  sustain_pedal ? (
    // Mark as sustained instead of releasing
    mark_sustained(note);
  ) : (
    // Actually release
    do_note_off(note);
  );
);

function release_sustained_notes()
  local(i)
(
  i = 0;
  loop(MAX_VOICES,
    voice_sustained[i] ? (
      voice_sustained[i] = 0;
      voice_gate[i] = 0;
      voice_env_stage[i] = 4;  // Release
    );
    i += 1;
  );
);
```

---

## Aftertouch

### Channel Aftertouch

```
@init
aftertouch = 0;
aftertouch_smooth = 0;

function handle_aftertouch(pressure)
(
  aftertouch = pressure / 127;
);

@sample
// Smooth aftertouch
aftertouch_smooth += 0.01 * (aftertouch - aftertouch_smooth);

// Apply to filter cutoff
filter_mod += aftertouch_smooth * aftertouch_to_filter;

// Apply to vibrato
vibrato_depth += aftertouch_smooth * aftertouch_to_vibrato;
```

### Polyphonic Aftertouch

```
@init
voice_aftertouch = 0;  // Per-voice aftertouch array
freembuf(MAX_VOICES);

function handle_poly_aftertouch(note, pressure)
  local(i)
(
  // Find voice playing this note
  i = 0;
  loop(MAX_VOICES,
    voice_note[i] == note && voice_gate[i] ? (
      voice_aftertouch[i] = pressure / 127;
    );
    i += 1;
  );
);

@sample
// In voice processing loop
i = 0;
loop(MAX_VOICES,
  // ... oscillator, envelope ...

  // Apply per-voice aftertouch
  voice_output = osc * env * (1 + voice_aftertouch[i] * at_amount);

  i += 1;
);
```

---

## Sample-Accurate MIDI

For tight timing, process MIDI at exact sample positions.

### Simple Queue

```
@init
midi_queue = 0;
midi_queue_size = 256;
midi_queue_head = 0;
midi_queue_tail = 0;
freembuf(midi_queue_size * 4);  // offset, msg1, msg2, msg3

function midi_queue_add(offset, m1, m2, m3)
(
  midi_queue[midi_queue_tail * 4] = offset;
  midi_queue[midi_queue_tail * 4 + 1] = m1;
  midi_queue[midi_queue_tail * 4 + 2] = m2;
  midi_queue[midi_queue_tail * 4 + 3] = m3;

  midi_queue_tail = (midi_queue_tail + 1) % midi_queue_size;
);

@block
current_sample = 0;

// Queue all MIDI events
while(midirecv(offset, msg1, msg2, msg3)) (
  midi_queue_add(offset, msg1, msg2, msg3);
);

@sample
// Process events for this sample
while(midi_queue_head != midi_queue_tail &&
      midi_queue[midi_queue_head * 4] == current_sample) (

  m1 = midi_queue[midi_queue_head * 4 + 1];
  m2 = midi_queue[midi_queue_head * 4 + 2];
  m3 = midi_queue[midi_queue_head * 4 + 3];

  process_midi(m1, m2, m3);

  midi_queue_head = (midi_queue_head + 1) % midi_queue_size;
);

// ... audio processing ...

current_sample += 1;
```

---

## MPE (MIDI Polyphonic Expression)

```
@init
ext_midi_bus = 1;  // Enable multi-bus for MPE lower/upper zones

// MPE settings
mpe_mode = 1;
mpe_master_channel = 0;  // Channel 1 for global messages
mpe_member_channels_start = 1;  // Channels 2-16 for notes

// Per-channel state (for MPE each note has its own channel)
channel_pitch_bend = 0;
channel_slide = 16;  // CC74
channel_pressure = 32;
freembuf(48);

function is_mpe_member_channel(ch)
(
  mpe_mode && ch >= mpe_member_channels_start && ch <= 15;
);

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  channel = msg1 & $x0F;

  is_mpe_member_channel(channel) ? (
    // Per-note messages
    status == $xE0 ? (
      // Per-note pitch bend
      channel_pitch_bend[channel] = (msg3 << 7 | msg2) - 8192;
    ) : status == $xB0 && msg2 == 74 ? (
      // Slide (CC74)
      channel_slide[channel] = msg3 / 127;
    ) : status == $xD0 ? (
      // Per-note pressure
      channel_pressure[channel] = msg2 / 127;
    );
    // ... handle notes with channel-specific expression
  ) : (
    // Master channel or non-MPE
    // ... handle normally
  );
);
```

---

## MIDI Learn

```
@init
learn_mode = 0;
learn_param = -1;
cc_mappings = 0;  // CC -> parameter mappings
freembuf(128);    // One mapping per CC

function start_learn(param_idx)
(
  learn_mode = 1;
  learn_param = param_idx;
);

function stop_learn()
(
  learn_mode = 0;
  learn_param = -1;
);

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $xB0 ? (
    cc = msg2;

    learn_mode && learn_param >= 0 ? (
      // Assign this CC to the parameter
      cc_mappings[cc] = learn_param;
      stop_learn();
    ) : (
      // Apply mapped CC
      mapped_param = cc_mappings[cc];
      mapped_param >= 0 ? (
        set_param(mapped_param, msg3 / 127);
      );
    );
  );

  // ... other MIDI processing
);
```

---

## Complete Instrument MIDI Handler

```
@init
// State
current_note = -1;
gate = 0;
velocity = 0;
mod_wheel = 0;
pitch_bend = 0;
aftertouch = 0;
sustain_pedal = 0;
expression = 1;
volume = 1;
pan = 0;

// Smoothing
pitch_bend_smooth = 0;
mod_wheel_smooth = 0;
aftertouch_smooth = 0;
smooth_coeff = exp(-2 * $pi * 50 / srate);

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  channel = msg1 & $x0F;

  // Note On
  status == $x90 && msg3 > 0 ? (
    note_on(msg2, msg3);
  );

  // Note Off
  status == $x80 || (status == $x90 && msg3 == 0) ? (
    note_off(msg2);
  );

  // Control Change
  status == $xB0 ? (
    msg2 == 1 ? mod_wheel = msg3 / 127 :
    msg2 == 7 ? volume = msg3 / 127 :
    msg2 == 10 ? pan = (msg3 - 64) / 64 :
    msg2 == 11 ? expression = msg3 / 127 :
    msg2 == 64 ? handle_sustain(msg3 >= 64) :
    msg2 == 120 ? all_sound_off() :
    msg2 == 123 ? all_notes_off();
  );

  // Pitch Bend
  status == $xE0 ? (
    pitch_bend = ((msg3 << 7) | msg2 - 8192) / 8192;
  );

  // Channel Aftertouch
  status == $xD0 ? (
    aftertouch = msg2 / 127;
  );
);

@sample
// Smooth continuous controllers
pitch_bend_smooth = smooth_coeff * pitch_bend_smooth +
                    (1 - smooth_coeff) * pitch_bend;
mod_wheel_smooth = smooth_coeff * mod_wheel_smooth +
                   (1 - smooth_coeff) * mod_wheel;
aftertouch_smooth = smooth_coeff * aftertouch_smooth +
                    (1 - smooth_coeff) * aftertouch;

// Apply pitch bend
bend_mult = pow(2, pitch_bend_smooth * pitch_bend_range / 12);
current_freq = base_freq * bend_mult;

// Apply mod wheel to vibrato
vibrato = sin(vibrato_phase) * vibrato_depth * mod_wheel_smooth;
current_freq *= pow(2, vibrato / 12);

// ... synthesis ...

// Apply volume and expression
output *= volume * expression;

// Apply pan
spl0 = output * sqrt(0.5 - pan * 0.5);
spl1 = output * sqrt(0.5 + pan * 0.5);
```
