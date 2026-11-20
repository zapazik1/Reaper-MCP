---
title: "MIDI Basics"
impact: CRITICAL
tags:
  - midi
  - messages
  - sysex
---

# MIDI Basics

MIDI message structure, receiving, sending, and SysEx handling in JSFX.

## References

- [JSFX MIDI Functions](https://www.reaper.fm/sdk/js/midi.php)
- [MIDI Specification](https://midi.org/specifications)

---

## MIDI Message Structure

| Byte | Name | Description |
|------|------|-------------|
| 1 | Status | Message type (high nibble) + Channel (low nibble) |
| 2 | Data 1 | Note number, CC number, etc. |
| 3 | Data 2 | Velocity, CC value, etc. (not all messages) |

### Status Bytes

```
$x8n = Note Off          (2 data bytes: note, velocity)
$x9n = Note On           (2 data bytes: note, velocity)
$xAn = Poly Aftertouch   (2 data bytes: note, pressure)
$xBn = Control Change    (2 data bytes: cc#, value)
$xCn = Program Change    (1 data byte: program)
$xDn = Channel Pressure  (1 data byte: pressure)
$xEn = Pitch Bend        (2 data bytes: LSB, MSB)
$xF0 = System Exclusive  (variable length)
$xF1-$xFF = System Common/Real-Time
```

Where `n` = channel (0-15, displayed as 1-16).

---

## Receiving MIDI

### Basic Receive Loop

```
@block
while(midirecv(offset, msg1, msg2, msg3)) (
  // offset = sample position within block
  // msg1 = status byte
  // msg2 = data byte 1
  // msg3 = data byte 2

  status = msg1 & $xF0;  // Message type
  channel = msg1 & $x0F; // Channel (0-15)

  // Process...

  // Forward (important!)
  midisend(offset, msg1, msg2, msg3);
);
```

### Parsing Common Messages

```
@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    // Note On
    note = msg2;      // 0-127
    velocity = msg3;  // 1-127
  ) : status == $x80 || (status == $x90 && msg3 == 0) ? (
    // Note Off
    note = msg2;
    velocity = msg3;
  ) : status == $xB0 ? (
    // Control Change
    cc_num = msg2;    // 0-127
    cc_val = msg3;    // 0-127
  ) : status == $xE0 ? (
    // Pitch Bend (14-bit value)
    bend = (msg3 << 7) | msg2;  // 0-16383, center = 8192
    bend_normalized = (bend - 8192) / 8192;  // -1 to +1
  ) : status == $xD0 ? (
    // Channel Aftertouch
    pressure = msg2;  // 0-127
  ) : status == $xC0 ? (
    // Program Change
    program = msg2;   // 0-127
  );

  midisend(offset, msg1, msg2, msg3);
);
```

---

## Sending MIDI

### Send Functions

```
// Send 3-byte message
midisend(offset, status, data1, data2);

// Send 2-byte message (program change, channel pressure)
midisend(offset, status, data1);

// Send from buffer (for SysEx or variable length)
midisend_buf(offset, buffer, length);

// Send from string
midisend_str(offset, string);
```

### Common Send Patterns

```
// Send Note On
midisend(offset, $x90 | channel, note, velocity);

// Send Note Off
midisend(offset, $x80 | channel, note, velocity);

// Send CC
midisend(offset, $xB0 | channel, cc_number, cc_value);

// Send Pitch Bend
lsb = bend & $x7F;
msb = (bend >> 7) & $x7F;
midisend(offset, $xE0 | channel, lsb, msb);

// Send Program Change
midisend(offset, $xC0 | channel, program);
```

---

## SysEx Handling

### Receive SysEx

```
@init
sysex_buffer = 0;
sysex_max_len = 256;
freembuf(sysex_max_len);

@block
while(midirecv_buf(offset, sysex_buffer, sysex_max_len)) (
  // Check if it's SysEx
  sysex_buffer[0] == $xF0 ? (
    // Process SysEx
    // Length returned includes F0 and F7
    process_sysex(sysex_buffer, length);
  ) : (
    // Regular message (3 bytes or less)
    msg1 = sysex_buffer[0];
    msg2 = sysex_buffer[1];
    msg3 = sysex_buffer[2];
    // ...
  );
);
```

### Send SysEx

```
// From buffer
sysex[0] = $xF0;       // Start
sysex[1] = $x7E;       // Manufacturer ID
sysex[2] = ...;        // Data
sysex[n] = $xF7;       // End
midisend_buf(offset, sysex, n + 1);

// From string
midisend_str(offset, "\xF0\x7E\x00\x06\x01\xF7");
```

---

## MIDI Timing

### Sample Offset

```
@block
// samplesblock = samples until next @block call
// offset = sample position within block (0 to samplesblock-1)

while(midirecv(offset, msg1, msg2, msg3)) (
  // offset tells when in the block this event occurs
  // Use same offset when sending to preserve timing
  midisend(offset, msg1, msg2, msg3);
);
```

### Delayed Events

```
@block
// Schedule event later in block
delay_samples = 100;
new_offset = min(offset + delay_samples, samplesblock - 1);
midisend(new_offset, msg1, msg2, msg3);
```

### Beat-Synced Events

```
@block
// Use transport info for timing
beats_per_sample = tempo / (60 * srate);

while(midirecv(offset, msg1, msg2, msg3)) (
  // Calculate beat position of this event
  event_beat = beat_position + offset * beats_per_sample;

  // Quantize to grid
  grid = 0.25;  // 16th notes
  quantized_beat = floor(event_beat / grid + 0.5) * grid;
  quantized_offset = floor((quantized_beat - beat_position) / beats_per_sample);
  quantized_offset = max(0, min(quantized_offset, samplesblock - 1));

  midisend(quantized_offset, msg1, msg2, msg3);
);
```

---

## Running Status

MIDI allows omitting repeated status bytes. JSFX handles this automatically for receive, but you can optimize sends:

```
// Manual running status (rarely needed in JSFX)
last_status != status ? (
  midisend(offset, status, data1, data2);
  last_status = status;
) : (
  // Omit status byte... but JSFX doesn't expose this
);
```

---

## Complete MIDI Pass-Through

```
desc:MIDI Pass-Through
tags:midi

in_pin:none
out_pin:none

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  midisend(offset, msg1, msg2, msg3);
);
```

---

## MIDI Monitor

```
desc:MIDI Monitor
tags:midi utility

@init
last_msg1 = last_msg2 = last_msg3 = 0;
msg_count = 0;

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  last_msg1 = msg1;
  last_msg2 = msg2;
  last_msg3 = msg3;
  msg_count += 1;

  midisend(offset, msg1, msg2, msg3);
);

@gfx 300 100
gfx_r = gfx_g = gfx_b = 1;
gfx_x = gfx_y = 10;

status = last_msg1 & $xF0;
channel = (last_msg1 & $x0F) + 1;

gfx_printf("Messages: %d\n", msg_count);
gfx_printf("Last: %02X %02X %02X\n", last_msg1, last_msg2, last_msg3);
gfx_printf("Channel: %d\n", channel);

status == $x90 ? gfx_printf("Note On: %d vel %d", last_msg2, last_msg3) :
status == $x80 ? gfx_printf("Note Off: %d", last_msg2) :
status == $xB0 ? gfx_printf("CC %d: %d", last_msg2, last_msg3) :
status == $xE0 ? gfx_printf("Pitch Bend: %d", (last_msg3 << 7) | last_msg2);
```
