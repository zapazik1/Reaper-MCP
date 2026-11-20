---
title: "Envelopes"
impact: HIGH
tags:
  - envelope
  - adsr
  - modulation
  - synthesis
---

# Envelopes

ADSR envelopes, multi-stage envelopes, and modulation routing for synthesis.

## References

- [Tale's adsr.jsfx-inc](https://www.taletn.com/reaper/mono_synth/)
- [Envelope Design](https://ccrma.stanford.edu/~jos/pasp/ADSR_Envelopes.html)

---

## Basic ADSR Envelope

### Simple ADSR

```
@init
env = 0;
env_stage = 0;  // 0=idle, 1=attack, 2=decay, 3=sustain, 4=release
gate = 0;

@slider
// Convert times to coefficients
// Coefficient = exp(-1 / (time_seconds * srate))
attack_coeff = exp(-1 / (attack_ms * srate / 1000));
decay_coeff = exp(-1 / (decay_ms * srate / 1000));
release_coeff = exp(-1 / (release_ms * srate / 1000));

@sample
env_stage == 1 ? (  // Attack
  env = attack_coeff * env + (1 - attack_coeff);
  env >= 0.999 ? (
    env = 1;
    env_stage = 2;  // -> Decay
  );
) : env_stage == 2 ? (  // Decay
  env = decay_coeff * env + (1 - decay_coeff) * sustain;
  env <= sustain * 1.001 ? (
    env_stage = 3;  // -> Sustain
  );
) : env_stage == 3 ? (  // Sustain
  env = sustain;
) : env_stage == 4 ? (  // Release
  env = release_coeff * env;
  env < 0.0001 ? (
    env = 0;
    env_stage = 0;  // -> Idle
  );
);

// Trigger functions
function env_trigger()
(
  env_stage = 1;  // Start attack
);

function env_release()
(
  env_stage = 4;  // Start release
);
```

### Linear ADSR

For more predictable timing:

```
@slider
// Linear increment per sample
attack_inc = 1 / (attack_ms * srate / 1000);
decay_inc = (1 - sustain) / (decay_ms * srate / 1000);
release_inc = env / (release_ms * srate / 1000);  // Recalc on release

@sample
env_stage == 1 ? (  // Attack
  env += attack_inc;
  env >= 1 ? (
    env = 1;
    env_stage = 2;
  );
) : env_stage == 2 ? (  // Decay
  env -= decay_inc;
  env <= sustain ? (
    env = sustain;
    env_stage = 3;
  );
) : env_stage == 4 ? (  // Release
  env -= release_inc;
  env <= 0 ? (
    env = 0;
    env_stage = 0;
  );
);
```

---

## ADSR Library

```
// adsr.jsfx-inc

function adsr.init()
  instance(env, stage, attack_coeff, decay_coeff, release_coeff, sustain_level)
(
  env = 0;
  stage = 0;
);

function adsr.set_params(attack_ms, decay_ms, sustain, release_ms)
  instance(attack_coeff, decay_coeff, release_coeff, sustain_level)
(
  attack_coeff = attack_ms > 0 ? exp(-1 / (attack_ms * srate / 1000)) : 0;
  decay_coeff = decay_ms > 0 ? exp(-1 / (decay_ms * srate / 1000)) : 0;
  sustain_level = sustain;
  release_coeff = release_ms > 0 ? exp(-1 / (release_ms * srate / 1000)) : 0;
);

function adsr.trigger()
  instance(stage)
(
  stage = 1;
);

function adsr.release()
  instance(stage)
(
  stage == 1 || stage == 2 || stage == 3 ? stage = 4;
);

function adsr.process()
  instance(env, stage, attack_coeff, decay_coeff, release_coeff, sustain_level)
(
  stage == 1 ? (
    env = attack_coeff * env + (1 - attack_coeff);
    env >= 0.999 ? (env = 1; stage = 2);
  ) : stage == 2 ? (
    env = decay_coeff * env + (1 - decay_coeff) * sustain_level;
    env <= sustain_level * 1.001 ? stage = 3;
  ) : stage == 3 ? (
    env = sustain_level;
  ) : stage == 4 ? (
    env = release_coeff * env;
    env < 0.0001 ? (env = 0; stage = 0);
  );
  env;
);

function adsr.is_active()
  instance(stage)
(
  stage > 0;
);

// Usage:
// amp_env.adsr.init();
// amp_env.adsr.set_params(10, 100, 0.7, 200);
// amp_env.adsr.trigger();
// output = oscillator * amp_env.adsr.process();
```

---

## Multi-Stage Envelope

For complex modulation (filter sweeps, etc.):

```
@init
MAX_STAGES = 8;
env_levels = 0;      // Target level for each stage
env_times = MAX_STAGES;  // Time in ms for each stage
env_curves = MAX_STAGES * 2;  // Curve shape
num_stages = 4;

// Default ADSR-like shape
env_levels[0] = 1;    // Attack target
env_levels[1] = 0.7;  // Decay target (sustain)
env_levels[2] = 0.7;  // Sustain (same level)
env_levels[3] = 0;    // Release target

env_times[0] = 10;    // Attack time
env_times[1] = 100;   // Decay time
env_times[2] = 0;     // Sustain (0 = hold)
env_times[3] = 200;   // Release time

current_stage = -1;
env = 0;
stage_start_level = 0;
stage_progress = 0;

function multistage_trigger()
(
  current_stage = 0;
  stage_start_level = env;
  stage_progress = 0;
);

function multistage_release()
(
  // Jump to release stage (last stage)
  current_stage = num_stages - 1;
  stage_start_level = env;
  stage_progress = 0;
);

@sample
current_stage >= 0 && current_stage < num_stages ? (
  target = env_levels[current_stage];
  time_ms = env_times[current_stage];

  time_ms > 0 ? (
    // Timed stage
    stage_progress += 1000 / (time_ms * srate);
    stage_progress >= 1 ? (
      env = target;
      current_stage += 1;
      current_stage < num_stages ? (
        stage_start_level = env;
        stage_progress = 0;
      ) : (
        current_stage = -1;  // Done
      );
    ) : (
      // Interpolate
      env = stage_start_level + (target - stage_start_level) * stage_progress;
    );
  ) : (
    // Hold stage (sustain)
    env = target;
  );
);
```

---

## Envelope Curves

### Exponential Curves

```
@slider
// Curve: -1 to 1, 0 = linear
curve = attack_curve;

@sample
// Linear progress 0-1
t = stage_progress;

// Apply curve
curve > 0 ? (
  // Logarithmic (fast start, slow end)
  t = 1 - pow(1 - t, 1 + curve * 3);
) : curve < 0 ? (
  // Exponential (slow start, fast end)
  t = pow(t, 1 - curve * 3);
);

env = start_level + (target_level - start_level) * t;
```

### S-Curve (Smooth)

```
// Hermite S-curve
t = stage_progress;
t = t * t * (3 - 2 * t);
env = start_level + (target_level - start_level) * t;
```

---

## Velocity Sensitivity

```
@block
// On note on
velocity = msg3 / 127;

// Apply velocity curve
vel_curve == 0 ? (
  // Linear
  vel_scale = velocity;
) : vel_curve == 1 ? (
  // Exponential (more dynamic)
  vel_scale = velocity * velocity;
) : (
  // Logarithmic (more compressed)
  vel_scale = sqrt(velocity);
);

// Scale envelope depth by velocity
amp_env_depth = vel_scale;
```

---

## Modulation Envelope

For filter cutoff, etc.:

```
@init
// Separate envelope for modulation
mod_env = 0;
mod_stage = 0;

@slider
mod_attack_coeff = exp(-1 / (mod_attack_ms * srate / 1000));
mod_decay_coeff = exp(-1 / (mod_decay_ms * srate / 1000));
mod_sustain = mod_sustain_slider;
mod_release_coeff = exp(-1 / (mod_release_ms * srate / 1000));

// Modulation depth and offset
mod_depth = mod_depth_slider;  // How much to modulate
mod_offset = mod_offset_slider;  // Base value

@sample
// Process mod envelope (same as amp envelope)
// ...

// Apply to filter cutoff
filter_cutoff = base_cutoff + mod_env * mod_depth;
// Or
filter_cutoff = base_cutoff * (mod_offset + mod_env * mod_depth);
```

---

## Key Tracking

Adjust envelope times based on note:

```
@block
// On note on
note = msg2;

// Key tracking amount (0 = off, 1 = full)
key_track = 0.5;

// Reference note (middle C = 60)
ref_note = 60;

// Scale factor: higher notes = shorter times
scale = pow(2, (ref_note - note) / 12 * key_track);

// Apply to envelope times
effective_attack = attack_ms * scale;
effective_decay = decay_ms * scale;
effective_release = release_ms * scale;
```

---

## Envelope Retrigger Modes

```
@block
// Note On received
status == $x90 && msg3 > 0 ? (
  retrigger_mode == 0 ? (
    // Hard retrigger: reset to 0
    env = 0;
    env_stage = 1;
  ) : retrigger_mode == 1 ? (
    // Soft retrigger: continue from current level
    env_stage = 1;
  ) : (
    // Legato: only retrigger if not already playing
    env_stage == 0 ? env_stage = 1;
  );
);
```

---

## Complete Modulation Routing

```
@init
// Modulation sources
mod_src_env1 = 0;
mod_src_env2 = 1;
mod_src_lfo1 = 2;
mod_src_lfo2 = 3;
mod_src_vel = 4;
mod_src_key = 5;

// Modulation destinations
mod_dst_pitch = 0;
mod_dst_filter = 1;
mod_dst_amp = 2;
mod_dst_pan = 3;

// Modulation matrix
MAX_MOD_ROUTES = 8;
mod_source = 0;
mod_dest = MAX_MOD_ROUTES;
mod_amount = MAX_MOD_ROUTES * 2;
num_routes = 0;

@sample
// Gather modulation source values
sources[mod_src_env1] = env1.adsr.process();
sources[mod_src_env2] = env2.adsr.process();
sources[mod_src_lfo1] = lfo1.process();
sources[mod_src_lfo2] = lfo2.process();
sources[mod_src_vel] = velocity;
sources[mod_src_key] = (note - 60) / 60;  // Normalized key tracking

// Initialize destination accumulators
pitch_mod = 0;
filter_mod = 0;
amp_mod = 1;
pan_mod = 0;

// Process modulation matrix
i = 0;
loop(num_routes,
  src = mod_source[i];
  dst = mod_dest[i];
  amt = mod_amount[i];

  mod_value = sources[src] * amt;

  dst == mod_dst_pitch ? pitch_mod += mod_value :
  dst == mod_dst_filter ? filter_mod += mod_value :
  dst == mod_dst_amp ? amp_mod *= (1 + mod_value) :
  dst == mod_dst_pan ? pan_mod += mod_value;

  i += 1;
);

// Apply modulations
osc.set_freq(base_freq * pow(2, pitch_mod / 12));
filter.set_cutoff(base_cutoff * pow(2, filter_mod));
output *= amp_mod;
```

---

## Portamento / Glide

```
@init
target_freq = 440;
current_freq = 440;
portamento_active = 0;

@slider
// Portamento time in ms
port_time_ms = portamento;
port_coeff = port_time_ms > 0 ? exp(-1 / (port_time_ms * srate / 1000)) : 0;

@block
// On note change
new_note ? (
  target_freq = 440 * pow(2, (note - 69) / 12);

  legato_mode ? (
    // Portamento only in legato
    portamento_active = notes_held > 0;
  ) : (
    portamento_active = 1;
  );
);

@sample
// Glide to target frequency
portamento_active ? (
  current_freq = port_coeff * current_freq + (1 - port_coeff) * target_freq;

  // Check if arrived
  abs(current_freq - target_freq) < 0.01 ? (
    current_freq = target_freq;
    portamento_active = 0;
  );
) : (
  current_freq = target_freq;
);

osc.set_freq(current_freq);
```
