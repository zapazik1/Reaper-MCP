---
title: "MIDI Transform"
impact: HIGH
tags:
  - midi
  - transpose
  - velocity
  - mapping
---

# MIDI Transform

Note transposition, velocity scaling, CC mapping, and other MIDI transformations.

---

## Note Transposition

```
desc:Transpose
slider1:transpose=0<-24,24,1>Semitones

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  // Transpose note messages
  (status == $x90 || status == $x80) ? (
    new_note = msg2 + transpose;
    // Clamp to valid range
    new_note = max(0, min(127, new_note));
    midisend(offset, msg1, new_note, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Velocity Scaling

```
desc:Velocity Processor
slider1:scale=100<0,200,1>Scale (%)
slider2:offset=0<-127,127,1>Offset
slider3:curve=0<-100,100,1>Curve

@slider
scale_factor = scale / 100;

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    vel = msg3 / 127;  // Normalize

    // Apply curve
    curve > 0 ? (
      vel = pow(vel, 1 + curve / 100);  // Compress
    ) : curve < 0 ? (
      vel = pow(vel, 1 / (1 - curve / 100));  // Expand
    );

    // Scale and offset
    vel = vel * scale_factor + offset / 127;

    // Clamp
    new_vel = floor(max(1, min(127, vel * 127)));
    midisend(offset, msg1, msg2, new_vel);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Note Range Filter

```
desc:Note Filter
slider1:low_note=0<0,127,1>Low Note
slider2:high_note=127<0,127,1>High Note
slider3:mode=0<0,1,1{Pass,Block}>Mode

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  (status == $x90 || status == $x80) ? (
    in_range = msg2 >= low_note && msg2 <= high_note;

    mode == 0 ? (
      // Pass mode: only pass notes in range
      in_range ? midisend(offset, msg1, msg2, msg3);
    ) : (
      // Block mode: block notes in range
      !in_range ? midisend(offset, msg1, msg2, msg3);
    );
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## CC Mapping

```
desc:CC Mapper
slider1:src_cc=1<0,127,1>Source CC
slider2:dst_cc=74<0,127,1>Destination CC
slider3:min_out=0<0,127,1>Min Output
slider4:max_out=127<0,127,1>Max Output

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $xB0 && msg2 == src_cc ? (
    // Map input range to output range
    normalized = msg3 / 127;
    new_val = floor(min_out + normalized * (max_out - min_out));
    midisend(offset, msg1, dst_cc, new_val);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Note to CC

```
desc:Note to CC
slider1:cc_num=1<0,127,1>CC Number
slider2:mode=0<0,2,1{Velocity,Note Number,Gate}>Mode

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;
  channel = msg1 & $x0F;

  status == $x90 && msg3 > 0 ? (
    mode == 0 ? cc_val = msg3 :  // Velocity
    mode == 1 ? cc_val = msg2 :  // Note number
    cc_val = 127;                // Gate on

    midisend(offset, $xB0 | channel, cc_num, cc_val);
    midisend(offset, msg1, msg2, msg3);
  ) : status == $x80 || (status == $x90 && msg3 == 0) ? (
    mode == 2 ? (
      midisend(offset, $xB0 | channel, cc_num, 0);  // Gate off
    );
    midisend(offset, msg1, msg2, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Velocity Switch/Layer

```
desc:Velocity Switch
slider1:split_vel=64<1,127,1>Split Velocity
slider2:low_channel=0<0,15,1>Low Channel
slider3:high_channel=1<0,15,1>High Channel

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    msg3 < split_vel ? (
      midisend(offset, status | low_channel, msg2, msg3);
    ) : (
      midisend(offset, status | high_channel, msg2, msg3);
    );
  ) : status == $x80 || (status == $x90 && msg3 == 0) ? (
    // Send note off to both channels
    midisend(offset, status | low_channel, msg2, msg3);
    midisend(offset, status | high_channel, msg2, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Quantize Note Timing

```
desc:Note Quantizer
slider1:grid=4<1,16,1{1/1,1/2,1/4,1/8,1/16}>Grid

@slider
grid_beats = 4 / pow(2, grid);

@block
beats_per_sample = tempo / (60 * srate);

while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  (status == $x90 || status == $x80) ? (
    // Calculate beat position
    event_beat = beat_position + offset * beats_per_sample;

    // Quantize to grid
    quantized_beat = floor(event_beat / grid_beats + 0.5) * grid_beats;

    // Calculate new offset
    new_offset = (quantized_beat - beat_position) / beats_per_sample;
    new_offset = floor(max(0, min(new_offset, samplesblock - 1)));

    midisend(new_offset, msg1, msg2, msg3);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```

---

## Humanize

```
desc:Humanize
slider1:timing_ms=10<0,50,1>Timing Variation (ms)
slider2:velocity_var=10<0,30,1>Velocity Variation

@slider
timing_samples = timing_ms * srate / 1000;

@block
while(midirecv(offset, msg1, msg2, msg3)) (
  status = msg1 & $xF0;

  status == $x90 && msg3 > 0 ? (
    // Randomize timing
    time_shift = (rand(2) - 1) * timing_samples;
    new_offset = floor(offset + time_shift);
    new_offset = max(0, min(new_offset, samplesblock - 1));

    // Randomize velocity
    vel_shift = floor((rand(2) - 1) * velocity_var);
    new_vel = max(1, min(127, msg3 + vel_shift));

    midisend(new_offset, msg1, msg2, new_vel);
  ) : (
    midisend(offset, msg1, msg2, msg3);
  );
);
```
