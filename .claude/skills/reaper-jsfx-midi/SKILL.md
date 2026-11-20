---
name: 'reaper-jsfx-midi'
description: 'MIDI processing patterns for JSFX plugins. Use when building MIDI utilities, arpeggiators, chord generators, note filters, or CC processors. Triggers on requests for MIDI effects, arpeggiator, chord, transpose, or MIDI routing in JSFX.'
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
    - midi
    - arpeggiator
    - chord
---

# REAPER JSFX MIDI Processing

Patterns for MIDI utility plugins including note processing, arpeggiators, chord generators, and CC manipulation.

**Requires:** [reaper-jsfx-core](../reaper-jsfx-core/SKILL.md) for language fundamentals.

## Rules

| Rule | Description |
|------|-------------|
| [midi-basics](./rules/midi-basics.md) | MIDI message structure, receive/send, SysEx handling |
| [midi-transform](./rules/midi-transform.md) | Note transposition, velocity scaling, CC mapping |
| [midi-generate](./rules/midi-generate.md) | Arpeggiators, sequencers, chord generators |
| [midi-routing](./rules/midi-routing.md) | Multi-bus routing, channel filtering, splitting |

## Official Documentation

- [JSFX MIDI Functions](https://www.reaper.fm/sdk/js/midi.php)

## Key Principles

### 1. MIDI-Only Plugin Structure

```
desc:MIDI Utility
tags:midi

in_pin:none
out_pin:none

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  // Process and forward
  midisend(offset, msg1, msg2, msg3);
);
```

### 2. Always Forward or Handle All Messages

```
@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 || status == $x80 ? (
    // Process notes
    process_note(offset, msg1, msg2, msg3);
  ) : (
    // Pass through everything else unchanged
    midisend(offset, msg1, msg2, msg3);
  );
);
```

### 3. Preserve Timing

```
@block
// Use original offset for timing-critical events
while(midirecv(offset, msg1, msg2, msg3)) (
  // Transform but keep original offset
  midisend(offset, new_msg1, new_msg2, new_msg3);
);
```

## Quick Reference

| Use Case | Rule |
|----------|------|
| Understanding MIDI | [midi-basics](./rules/midi-basics.md) |
| Transpose / Velocity | [midi-transform](./rules/midi-transform.md) |
| Arpeggiator | [midi-generate](./rules/midi-generate.md) |
| Channel Filter | [midi-routing](./rules/midi-routing.md) |
