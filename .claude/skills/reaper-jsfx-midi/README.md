# REAPER JSFX MIDI Processing

Patterns for MIDI utility plugins including note processing, arpeggiators, chord generators, and CC manipulation.

## Installation

```bash
npx skills add mthines/jsfx-agent-skills
```

## Prerequisites

Requires [reaper-jsfx-core](../reaper-jsfx-core/README.md) for language fundamentals.

## When to Use

Use this skill when building:
- MIDI filters and transformers
- Arpeggiators and sequencers
- Chord generators
- CC mappers and controllers
- MIDI routing utilities

## Rules

| Rule | Impact | Description |
|------|--------|-------------|
| [midi-basics](./rules/midi-basics.md) | CRITICAL | MIDI message structure, receive/send, SysEx |
| [midi-transform](./rules/midi-transform.md) | HIGH | Transpose, velocity scaling, CC mapping |
| [midi-generate](./rules/midi-generate.md) | HIGH | Arpeggiators, sequencers, chord generators |
| [midi-routing](./rules/midi-routing.md) | MEDIUM | Channel filtering, splitting, bus routing |

## Quick Start

Simple transpose:

```
desc:Transpose
slider1:semitones=0<-24,24,1>Semitones

in_pin:none
out_pin:none

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  (status == $x90 || status == $x80) ? (
    new_note = max(0, min(127, msg2 + semitones));
    midisend(offset, msg1, new_note, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

## Resources

- [JSFX MIDI Functions](https://www.reaper.fm/sdk/js/midi.php)
- [MIDI Specification](https://midi.org/specifications)

## Related Skills

- **reaper-jsfx-core** - Required foundation
- **reaper-jsfx-synth** - For instrument MIDI handling

## License

MIT
