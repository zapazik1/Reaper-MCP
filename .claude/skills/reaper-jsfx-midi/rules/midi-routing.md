---
title: "MIDI Routing"
impact: MEDIUM
tags:
  - midi
  - routing
  - channel
  - bus
---

# MIDI Routing

Channel filtering, splitting, merging, and multi-bus routing.

---

## Channel Filter

```
desc:Channel Filter
slider1:channel=0<0,15,1>Pass Channel (0=All)
slider2:mode=0<0,1,1{Pass,Block}>Mode

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  ch = msg1 & $x0F;

  channel == 0 ? (
    // All channels
    midisend(offset, msg1, msg2, msg3);
  ) : mode == 0 ? (
    // Pass only specified channel
    ch == channel - 1 ? midisend(offset, msg1, msg2, msg3);
  ) : (
    // Block specified channel
    ch != channel - 1 ? midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Channel Remap

```
desc:Channel Remap
slider1:src_channel=1<1,16,1>Source Channel
slider2:dst_channel=1<1,16,1>Destination Channel

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  ch = msg1 & $x0F;

  // Check if channel message
  status < $xF0 ? (
    ch == src_channel - 1 ? (
      // Remap channel
      new_msg1 = status | (dst_channel - 1);
      midisend(offset, new_msg1, msg2, msg3);
    ) : (
      midisend(offset, msg1, msg2, msg3);
    );
  ) : (
    // System messages - pass through
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Keyboard Split

```
desc:Keyboard Split
slider1:split_note=60<0,127,1>Split Point
slider2:low_channel=0<0,15,1>Low Channel
slider3:high_channel=1<0,15,1>High Channel

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  (status == $x90 || status == $x80) ? (
    note = msg2;
    note < split_note ? (
      midisend(offset, status | low_channel, msg2, msg3);
    ) : (
      midisend(offset, status | high_channel, msg2, msg3);
    );
  ) : (
    // Non-note messages to both channels
    midisend(offset, (msg1 & $xF0) | low_channel, msg2, msg3);
    midisend(offset, (msg1 & $xF0) | high_channel, msg2, msg3);
  );
);
```

---

## Channel Merge

```
desc:Channel Merge
slider1:dst_channel=0<0,15,1>Output Channel

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  // Remap all channel messages to destination
  status < $xF0 ? (
    midisend(offset, status | dst_channel, msg2, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Multi-Bus Routing

```
desc:MIDI Bus Router
slider1:input_bus=0<0,15,1>Input Bus
slider2:output_bus=1<0,15,1>Output Bus

@init
ext_midi_bus = 1;  // Enable multi-bus

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  // midi_bus contains current input bus
  midi_bus == input_bus ? (
    // Route to output bus
    midi_bus = output_bus;
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Message Type Filter

```
desc:MIDI Type Filter
slider1:notes=1<0,1,1{Block,Pass}>Notes
slider2:cc=1<0,1,1{Block,Pass}>CC
slider3:pitch_bend=1<0,1,1{Block,Pass}>Pitch Bend
slider4:aftertouch=1<0,1,1{Block,Pass}>Aftertouch
slider5:program=1<0,1,1{Block,Pass}>Program Change

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  pass = 0;

  status == $x90 || status == $x80 ? pass = notes :
  status == $xB0 ? pass = cc :
  status == $xE0 ? pass = pitch_bend :
  status == $xD0 || status == $xA0 ? pass = aftertouch :
  status == $xC0 ? pass = program :
  pass = 1;  // System messages always pass

  pass ? midisend(offset, msg1, msg2, msg3);
);
```

---

## MIDI Thru with Monitor

```
desc:MIDI Thru
slider1:thru=1<0,1,1{Off,On}>Thru Enable

@init
note_count = 0;

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  // Count active notes
  status == $x90 && msg3 > 0 ? note_count += 1;
  status == $x80 || (status == $x90 && msg3 == 0) ? (
    note_count -= 1;
    note_count < 0 ? note_count = 0;
  );

  // Thru
  thru ? midisend(offset, msg1, msg2, msg3);
);

@gfx 200 50
gfx_r = gfx_g = gfx_b = 1;
gfx_x = gfx_y = 10;
gfx_printf("Active Notes: %d", note_count);
```

---

## Panic Button (All Notes Off)

```
desc:MIDI Panic
slider1:panic=0<0,1,1>Panic Button

@slider
panic ? (
  // Send All Notes Off to all channels
  ch = 0;
  loop(16,
    midisend(0, $xB0 | ch, 123, 0);  // All Notes Off
    midisend(0, $xB0 | ch, 120, 0);  // All Sound Off
    midisend(0, $xB0 | ch, 64, 0);   // Sustain Off
    ch += 1;
  );
  panic = 0;
  slider_automate(panic);
);

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  midisend(offset, msg1, msg2, msg3);
);
```

---

## Complete Router Example

```
desc:MIDI Router
slider1:mode=0<0,2,1{Thru,Split,Layer}>Mode
slider2:split_note=60<0,127,1>Split Note
slider3:channel_a=0<0,15,1>Channel A
slider4:channel_b=1<0,15,1>Channel B

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  channel = msg1 & $x0F;

  mode == 0 ? (
    // Thru - pass unchanged
    midisend(offset, msg1, msg2, msg3);

  ) : mode == 1 ? (
    // Split
    (status == $x90 || status == $x80) ? (
      msg2 < split_note ? (
        midisend(offset, status | channel_a, msg2, msg3);
      ) : (
        midisend(offset, status | channel_b, msg2, msg3);
      );
    ) : (
      midisend(offset, msg1, msg2, msg3);
    );

  ) : (
    // Layer - duplicate to both channels
    (status == $x90 || status == $x80) ? (
      midisend(offset, status | channel_a, msg2, msg3);
      midisend(offset, status | channel_b, msg2, msg3);
    ) : (
      midisend(offset, status | channel_a, msg2, msg3);
      midisend(offset, status | channel_b, msg2, msg3);
    );
  );
);
```
