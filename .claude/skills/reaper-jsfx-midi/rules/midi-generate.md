---
title: "MIDI Generation"
impact: HIGH
tags:
  - midi
  - arpeggiator
  - sequencer
  - chord
---

# MIDI Generation

Arpeggiators, sequencers, chord generators, and pattern generators.

---

## Simple Arpeggiator

```
desc:Arpeggiator
slider1:rate=2<0,4,1{1/1,1/2,1/4,1/8,1/16}>Rate
slider2:mode=0<0,3,1{Up,Down,Up-Down,Random}>Mode

@init
MAX_NOTES = 16;
held_notes = 0;
num_held = 0;
freembuf(MAX_NOTES);

arp_pos = 0;
arp_dir = 1;
last_note = -1;
last_beat = -1;

@slider
rate_beats = 4 / pow(2, rate);

@block
// Handle input notes
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    // Add note to held list
    num_held < MAX_NOTES ? (
      held_notes[num_held] = msg2;
      num_held += 1;
      // Sort notes (for up/down modes)
      sort_notes();
    );
  ) : status == $x80 || (status == $x90 && msg3 == 0) ? (
    // Remove note from held list
    remove_note(msg2);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);

// Generate arp notes on beat
num_held > 0 && play_state == 1 ? (
  current_beat = floor(beat_position / rate_beats);

  current_beat != last_beat ? (
    last_beat = current_beat;

    // Note off previous
    last_note >= 0 ? (
      midisend(0, $x80, last_note, 64);
    );

    // Get next note based on mode
    mode == 0 ? (  // Up
      arp_pos = (arp_pos + 1) % num_held;
    ) : mode == 1 ? (  // Down
      arp_pos -= 1;
      arp_pos < 0 ? arp_pos = num_held - 1;
    ) : mode == 2 ? (  // Up-Down
      arp_pos += arp_dir;
      (arp_pos >= num_held - 1 || arp_pos <= 0) ? arp_dir = -arp_dir;
      arp_pos = max(0, min(arp_pos, num_held - 1));
    ) : (  // Random
      arp_pos = floor(rand(num_held));
    );

    // Note on
    last_note = held_notes[arp_pos];
    midisend(0, $x90, last_note, 100);
  );
);
```

---

## Chord Generator

```
desc:Chord Generator
slider1:chord_type=0<0,7,1{Major,Minor,7th,Maj7,Min7,Sus2,Sus4,Dim}>Chord Type

@init
// Intervals from root for each chord type
chord_intervals = 0;
freembuf(8 * 6);  // 8 chords, up to 6 notes each

// Major: 0, 4, 7
chord_intervals[0] = 0; chord_intervals[1] = 4; chord_intervals[2] = 7;
chord_notes[0] = 3;
// Minor: 0, 3, 7
chord_intervals[6] = 0; chord_intervals[7] = 3; chord_intervals[8] = 7;
chord_notes[1] = 3;
// ... etc

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  channel = msg1 & $x0F;

  status == $x90 && msg3 > 0 ? (
    root = msg2;
    vel = msg3;

    // Send chord notes
    base = chord_type * 6;
    num = chord_notes[chord_type];
    i = 0;
    loop(num,
      note = root + chord_intervals[base + i];
      note >= 0 && note <= 127 ? (
        midisend(offset, $x90 | channel, note, vel);
      );
      i += 1;
    );
  ) : status == $x80 || (status == $x90 && msg3 == 0) ? (
    root = msg2;

    // Send note offs for all chord notes
    base = chord_type * 6;
    num = chord_notes[chord_type];
    i = 0;
    loop(num,
      note = root + chord_intervals[base + i];
      note >= 0 && note <= 127 ? (
        midisend(offset, $x80 | channel, note, 64);
      );
      i += 1;
    );
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Simple Step Sequencer

```
desc:Step Sequencer
slider1:steps=8<1,16,1>Steps
slider2:rate=3<0,4,1{1/1,1/2,1/4,1/8,1/16}>Rate

@init
MAX_STEPS = 16;
step_notes = 0;
step_vels = MAX_STEPS;
step_gates = MAX_STEPS * 2;
freembuf(MAX_STEPS * 3);

// Initialize pattern
loop(MAX_STEPS,
  step_notes[i] = 60 + (i % 12);
  step_vels[i] = 100;
  step_gates[i] = 1;
  i += 1;
);

current_step = 0;
last_step = -1;
last_note = -1;

@slider
rate_beats = 4 / pow(2, rate);

@block
// Process input (could be for recording or triggering)
while(midirecv(offset, msg1, msg2, msg3)) (
  // Pass through or record
);

// Sequencer playback
play_state == 1 ? (
  step_beat = floor(beat_position / rate_beats);
  current_step = step_beat % steps;

  current_step != last_step ? (
    // Note off previous
    last_note >= 0 ? (
      midisend(0, $x80, last_note, 64);
      last_note = -1;
    );

    // Note on current step
    step_gates[current_step] ? (
      note = step_notes[current_step];
      vel = step_vels[current_step];
      midisend(0, $x90, note, vel);
      last_note = note;
    );

    last_step = current_step;
  );
);
```

---

## Note Echo/Delay

```
desc:MIDI Delay
slider1:delay_ms=250<0,2000,1>Delay (ms)
slider2:repeats=3<0,8,1>Repeats
slider3:vel_decay=0.7<0,1,0.01>Velocity Decay

@init
MAX_EVENTS = 256;
event_time = 0;
event_msg1 = MAX_EVENTS;
event_msg2 = MAX_EVENTS * 2;
event_msg3 = MAX_EVENTS * 3;
event_count = 0;
freembuf(MAX_EVENTS * 4);

current_time = 0;

@slider
delay_samples = delay_ms * srate / 1000;

@block
// Add new events with delays
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  // Pass original
  midisend(offset, msg1, msg2, msg3);

  // Schedule echoes for notes
  status == $x90 && msg3 > 0 ? (
    vel = msg3;
    r = 0;
    loop(repeats,
      r += 1;
      vel = floor(vel * vel_decay);
      vel > 0 ? (
        schedule_event(
          current_time + offset + delay_samples * r,
          msg1, msg2, vel
        );
      );
    );
  );
);

// Output scheduled events
process_scheduled_events();

current_time += samplesblock;
```

---

## LFO to CC

```
desc:LFO to CC
slider1:rate=1<0.01,20,0.01>Rate (Hz)
slider2:cc_num=1<0,127,1>CC Number
slider3:min_val=0<0,127,1>Min Value
slider4:max_val=127<0,127,1>Max Value
slider5:shape=0<0,3,1{Sine,Triangle,Saw,Square}>Shape

@init
lfo_phase = 0;
last_cc_val = -1;

@slider
lfo_inc = rate / srate;

@block
// Update LFO
samples_in_block = samplesblock;
end_phase = lfo_phase + lfo_inc * samples_in_block;

// Calculate LFO value
shape == 0 ? lfo = sin(2 * $pi * lfo_phase) :
shape == 1 ? lfo = abs(lfo_phase * 4 - 2) - 1 :
shape == 2 ? lfo = lfo_phase * 2 - 1 :
lfo = lfo_phase < 0.5 ? 1 : -1;

// Map to CC range
cc_val = floor(min_val + (lfo * 0.5 + 0.5) * (max_val - min_val));
cc_val = max(0, min(127, cc_val));

// Only send if changed
cc_val != last_cc_val ? (
  midisend(0, $xB0, cc_num, cc_val);
  last_cc_val = cc_val;
);

// Update phase
lfo_phase = end_phase;
lfo_phase >= 1 ? lfo_phase -= 1;

// Pass through input
while(midirecv(offset, msg1, msg2, msg3)) (
  midisend(offset, msg1, msg2, msg3);
);
```
