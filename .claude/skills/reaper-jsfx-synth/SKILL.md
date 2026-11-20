---
name: 'reaper-jsfx-synth'
description: 'Synthesis and instrument patterns for JSFX plugins. Use when building synthesizers, samplers, or virtual instruments. Covers oscillators, envelopes, voice management, and MIDI instrument handling. Triggers on requests for synth, oscillator, ADSR, polyphony, or instrument development in JSFX.'
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
    - synthesis
    - oscillator
    - instrument
    - synth
---

# REAPER JSFX Synthesis

Patterns for building synthesizers and virtual instruments in JSFX. Covers oscillators, envelopes, polyphony, and MIDI instrument handling.

**Requires:** [reaper-jsfx-core](../reaper-jsfx-core/SKILL.md) for language fundamentals.

## Rules

| Rule | Description |
|------|-------------|
| [oscillators](./rules/oscillators.md) | Anti-aliased oscillators (PolyBLEP), wavetable, FM synthesis |
| [envelopes](./rules/envelopes.md) | ADSR, multi-stage envelopes, modulation routing |
| [voices](./rules/voices.md) | Polyphonic voice management, allocation, stealing |
| [midi-instrument](./rules/midi-instrument.md) | Note handling, pitch bend, mod wheel, aftertouch |

## Official Documentation

- [JSFX Programming Reference](https://www.reaper.fm/sdk/js/js.php)
- [JSFX MIDI Functions](https://www.reaper.fm/sdk/js/midi.php)

## External References

- [Tale's JSFX Libraries](https://www.taletn.com/reaper/mono_synth/) - poly_blep, adsr, midi_queue
- [PolyBLEP Oscillators](https://www.kvraudio.com/forum/viewtopic.php?t=398553)

## Key Principles

### 1. Mark as Instrument

```
desc:My Synthesizer
tags:instrument synthesizer

// For instruments: no audio input, MIDI input expected
in_pin:none
out_pin:left output
out_pin:right output
```

### 2. Anti-Alias Oscillators

Naive oscillators create aliasing. Use PolyBLEP or wavetable:

```
// BAD: Naive saw (aliases)
phase += freq / srate;
phase >= 1 ? phase -= 1;
output = phase * 2 - 1;

// GOOD: PolyBLEP saw (anti-aliased)
phase += freq / srate;
phase >= 1 ? phase -= 1;
output = phase * 2 - 1;
// Apply PolyBLEP correction at discontinuities
t = phase / dt;  // Normalized position
t < 1 ? output -= polyblep(t);
```

### 3. Sample-Accurate MIDI

For tight timing, process MIDI at sample level:

```
@block
while(midirecv(offset, msg1, msg2, msg3)) (
  // Store event with sample offset
  midi_queue_add(offset, msg1, msg2, msg3);
);

@sample
// Check for events at this sample
while(midi_queue_peek(current_sample) >= 0) (
  midi_queue_get(msg1, msg2, msg3);
  process_midi(msg1, msg2, msg3);
);
current_sample += 1;
```

### 4. Efficient Polyphony

Allocate voice arrays once, manage with indexes:

```
@init
MAX_VOICES = 8;
voice_note = 0;
voice_gate = MAX_VOICES;
voice_env = MAX_VOICES * 2;
// ... allocate all voice state arrays

freembuf(MAX_VOICES * 10);  // Total state size
```

## Quick Reference

| Use Case | Rule |
|----------|------|
| Saw/Square/Sine oscillators | [oscillators](./rules/oscillators.md) |
| ADSR envelope | [envelopes](./rules/envelopes.md) |
| Polyphonic synth | [voices](./rules/voices.md) |
| MIDI note handling | [midi-instrument](./rules/midi-instrument.md) |

## Minimal Synth Template

```
desc:Simple Mono Synth
tags:instrument synthesizer

in_pin:none
out_pin:left output
out_pin:right output

slider1:attack_ms=10<1,1000,1:log>Attack (ms)
slider2:decay_ms=100<1,1000,1:log>Decay (ms)
slider3:sustain=0.7<0,1,0.01>Sustain
slider4:release_ms=200<1,2000,1:log>Release (ms)

@init
note = -1;
gate = 0;
env = 0;
phase = 0;

@slider
attack_coeff = exp(-1 / (attack_ms * srate / 1000));
decay_coeff = exp(-1 / (decay_ms * srate / 1000));
release_coeff = exp(-1 / (release_ms * srate / 1000));

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (  // Note On
    note = msg2;
    velocity = msg3 / 127;
    gate = 1;
    freq = 440 * pow(2, (note - 69) / 12);
    dt = freq / srate;
  ) : (status == $x80 || (status == $x90 && msg3 == 0)) && msg2 == note ? (
    gate = 0;
  );
);

@sample
// Simple saw oscillator
phase += dt;
phase >= 1 ? phase -= 1;
osc = phase * 2 - 1;

// ADSR envelope
gate ? (
  env < 1 ? (
    env = attack_coeff * env + (1 - attack_coeff);
  ) : (
    env = decay_coeff * env + (1 - decay_coeff) * sustain;
  );
) : (
  env = release_coeff * env;
);

// Output
output = osc * env * velocity * 0.3;
spl0 = spl1 = output;
```
