# REAPER JSFX Synthesis

Patterns for building synthesizers and virtual instruments in JSFX. Covers oscillators, envelopes, polyphony, and MIDI instrument handling.

## Installation

```bash
npx skills add mthines/jsfx-agent-skills
```

## Prerequisites

Requires [reaper-jsfx-core](../reaper-jsfx-core/README.md) for language fundamentals.

## When to Use

Use this skill when building:
- Synthesizers (mono or polyphonic)
- Virtual instruments
- Samplers
- Sound generators

## Rules

| Rule | Impact | Description |
|------|--------|-------------|
| [oscillators](./rules/oscillators.md) | CRITICAL | Anti-aliased oscillators (PolyBLEP), wavetable, FM synthesis |
| [envelopes](./rules/envelopes.md) | HIGH | ADSR, multi-stage envelopes, modulation routing |
| [voices](./rules/voices.md) | HIGH | Polyphonic voice management, allocation, stealing |
| [midi-instrument](./rules/midi-instrument.md) | HIGH | Note handling, pitch bend, mod wheel, aftertouch |

## Quick Start

Minimal mono synth:

```
desc:Mono Synth
tags:instrument synthesizer

in_pin:none
out_pin:left output
out_pin:right output

@init
phase = 0;
gate = 0;
env = 0;

@slider
attack_coeff = exp(-1 / (10 * srate / 1000));
release_coeff = exp(-1 / (200 * srate / 1000));

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  status == $x90 && msg3 > 0 ? (
    note = msg2;
    freq = 440 * pow(2, (note - 69) / 12);
    dt = freq / srate;
    gate = 1;
  );
  status == $x80 ? gate = 0;
);

@sample
// Oscillator
phase += dt;
phase >= 1 ? phase -= 1;
osc = phase * 2 - 1;

// Envelope
gate ? (
  env = attack_coeff * env + (1 - attack_coeff);
) : (
  env = release_coeff * env;
);

spl0 = spl1 = osc * env * 0.3;
```

## Resources

- [Tale's JSFX Libraries](https://www.taletn.com/reaper/mono_synth/)
- [PolyBLEP Oscillators](https://www.kvraudio.com/forum/viewtopic.php?t=398553)
- [MIDI Specification](https://midi.org/specifications)

## Related Skills

- **reaper-jsfx-core** - Required foundation
- **reaper-jsfx-audio** - Filters for synth voices
- **reaper-jsfx-ui** - Custom synth interfaces

## License

MIT
