# Prototype 1 – simple model with the vendor MOSFET model

This directory holds the [simple model](../simulation_simple/README.md) with
one change: the MOSFET is the Texas Instruments PSpice model of the
CSD18533KCS, used unmodified, instead of the switch and constant capacitors.

**Status: the simulation does not run.** ngspice 42 cannot load the
unmodified vendor file, even with PSpice compatibility switched on. This
README is the report of what was tried and what was found. Nothing was fixed:
the vendor file is byte-for-byte as committed, and there are no results.

| File | Contents |
|---|---|
| `flyback_vendor.cir` | The simple netlist with the MOSFET replaced by `XQ1 drain gate 0 CSD18533KCS` |
| `.spiceinit` | `set ngbehavior=psa`: PSpice compatibility for the whole netlist |
| `models/CSD18533KCS.lib` | TI model, v1.7.5 library, dated 09/21/2012, unmodified |
| `models/CSD18533KCS.OLB` | OrCAD symbol that came with the model; not used |

The directory was renamed from `simulation`. The files of the earlier
detailed model are still here and unchanged: `prototype1.cir`,
`plot_waveforms.py`, `simulated_circuit.svg`, `waveforms.svg` and the four
datasheet-based files in `models/`. They are described in
[`../README.md`](../README.md) and are not part of this report.

## What changed from the simple model

Only the MOSFET block. The six elements `RG`, `CGS`, `CGD`, `CDS`, `SQ1` and
`DQ1` and their two `.model` lines are replaced by the subcircuit call and the
`.include` of the vendor file. `RG` is dropped because the vendor model has
its own gate resistance. Everything else, including the operating point, the
options and the measurements, is identical.

## How to reproduce

```
cd prototype1/simulation_vendor
ngspice -b flyback_vendor.cir
```

ngspice reads `.spiceinit` from the current directory, so it must be started
from here. The start-up line `Note: Compatibility modes selected: ps a`
confirms that the compatibility mode is active.

## Result with the unmodified model

The run stops while the netlist is being read:

```
Netlist line no. 0:
Undefined parameter [pwidthp]
Netlist line no. 0:
Cannot compute substitute
Netlist line no. 0:
Undefined parameter [ptrc1]
Netlist line no. 0:
Cannot compute substitute
ERROR: fatal error in ngspice, exit(1)
```

The result is the same with `ngbehavior=psa`, with `ngbehavior=ps` and with no
compatibility mode.

## Investigation

To see what lies behind the first error, corrected copies of the vendor file
were made in a temporary directory outside the repository. Each step below
changes one thing. None of these copies is committed.

### Issue 1: `.PARAM` lines without an equals sign

Lines 439–444 of the vendor file define six parameters in the form
`.PARAM name value`:

```
 .PARAM  ptrc1    7.00e-3
 .PARAM  pwidthP  4.02
 .PARAM  perimP   {2.1*pwidthP}
```

ngspice accepts only `.PARAM name=value`, in every compatibility mode, so
none of the six parameters is defined. This is the error shown above.

| Trial | Outcome |
|---|---|
| Convert CRLF line ends to LF only | Same error |
| Add `=` to the three numeric parameters | Next error: `Undefined parameter [perimp]` |
| Add `=` to all six | This issue is gone; issue 2 appears |

### Issue 2: body diode area given as a bare brace expression

Line 454 gives the area of the body diode as an expression in braces after the
model name:

```
DBD	3	1	DBD {4.02/5.788666666666666666666666666666666666666666666667}
```

With issue 1 out of the way, ngspice evaluates the expression and then rejects
the line:

```
Error on line:
  d.x1.dbd 0 d x1.dbd   6.944604399401128e-01
could not find a valid modelname
```

| Trial | Outcome |
|---|---|
| Rename the diode model so it differs from the instance name | Same error |
| Remove `TNOM` from the diode model | Same error |
| Shorter expression, `{4.02/5.7887}` | Same error |
| A single number in braces, `{0.69446}` | Same error |
| Named form, `area={...}`, same expression | Loads |
| Plain number, `0.69446` | Loads |

So the cause is the brace expression in the unnamed area position. Its length
and the model name do not matter. This is ngspice 42 behaviour; other versions
were not tested.

### Issue 3: the model needs the PSpice compatibility mode

With issues 1 and 2 corrected in the copy, the model loads only when the
compatibility mode is on:

| Mode | Outcome |
|---|---|
| `psa` | Loads |
| `ps` | Loads |
| none | `could not find a valid modelname` for the transistor `M1` |

The transistor uses `LEVEL = 7`, which is BSIM3 in PSpice. ngspice uses a
different level number for BSIM3 and translates it only in the compatibility
mode. This is not a defect of the file, and `.spiceinit` already covers it.

### Issue 4: the transient analysis does not converge

With issues 1 and 2 corrected in the copy and `psa` active, the model loads
and the converter simulation starts, but it never finishes. It runs normally
for some switching periods and then aborts:

```
Warning: singular matrix:  check nodes xq1.xcgd.6 and e.xq1.xcgd.e2#branch
doAnalyses: TRAN:  Timestep too small; time = 0.000215474, timestep = 2.5e-20:
trouble with xq1:dbd-instance d.xq1.dbd
```

That is in the 22nd switching period, 0.47 µs after turn-off, while the drain
rings with the leakage inductance. At the last accepted point the drain is at
8.3 V and rising at about 0.7 V/ns. The simple model runs the full 100 ms in
under a minute.

Variants of the same circuit, each run for 5 ms of simulated time:

| Variant | Outcome |
|---|---|
| As in `flyback_vendor.cir` (gear) | Abort at 215 µs; in a repeat run it stalled at the same point |
| Trapezoidal integration | Abort at 6.7 µs |
| Default tolerances | Abort at 35 µs |
| Looser tolerances (`vntol=10u`, `itl4=100`) | Stalls near 195 µs |
| Lead inductances at drain, gate and source (6, 8, 4 nH) | Stalls near 190 µs |
| Lead inductances and looser tolerances | Stalls near 205 µs |
| Body diode `DBD` removed | Stalls near 240 µs |
| Maximum time step 2 ns | Stalls near 300 µs |
| 6 kΩ across the primary | Abort at 517 µs |
| 90 pF across the secondary | Abort at 185 µs |
| 25 pF across the secondary | Abort at 155 µs |
| 6 kΩ and 90 pF together | Abort at 56 µs |
| Capacitance tables made linear between 8 V and 12 V | Abort at 835 µs |

"Stalls" means the run was still alive after 10 minutes but advancing by
microseconds of simulated time per minute. These runs shared the processor
with each other, so the times are not comparable with a single run.

What these runs show:

- The failure is not caused by the settings. It appears with every integration
  method, tolerance and step limit tried, at a different moment each time.
- The device named in the error message is not the cause. The message names
  the body diode, but removing the body diode does not help, and other
  variants name the output diode `D1` instead.
- The step in the capacitance tables contributes but is not the whole cause.
  Between 9 V and 10 V of drain voltage the tabulated drain-source capacitance
  drops from 1037 pF to 607 pF and the gate-drain capacitance from 97 pF to
  34 pF. The abort in the base run happens as the drain approaches this step.
  Replacing the step by a straight line moves the abort from 215 µs to 835 µs
  but does not remove it.
- The MOSFET model alone is stable. With the transistor off, its drain was
  rung through 144 nH over four voltage ranges (0.5–8 V, 2–19 V, 14–27 V and
  9–61 V), with the gate shorted and with the gate tied to ground through
  3.4 Ω. All eight runs finished in about a second.

The root cause was not found. The failure needs the complete converter:
the model's capacitance sources together with the coupled inductors and the
output diode.

One earlier netlist did run with a corrected copy of this model: a separate
flyback netlist with more parasitic elements (damped leakage inductance, core
loss, 90 pF winding capacitance, lead inductances, lossy capacitors). It is
not in the repository. Adding some of these elements one at a time, as in the
table above, did not reproduce that.

## How the vendor model is built

Two properties of the file are relevant to issue 4 and to any later use.

**Capacitances are current sources driven by a numerical derivative.** The
gate-drain and drain-source capacitances are subcircuits. Each one looks up
the capacitance in a table of drain-source voltage, measures the current in a
1 fF capacitor connected to the drain, and multiplies the two by $10^{15}$ to
make the capacitor current. ngspice turns each table into an XSPICE element
and reports `Reducing trtol to 1 for xspice 'A' devices`, which makes every
time step smaller.

**The capacitor currents follow the drain voltage relative to node 0.** The
1 fF sensing capacitors are connected between the drain pin and the global
ground, not the source pin. The model is therefore exact only when the source
is at ground, as it is in `flyback_vendor.cir`. Also, the gate-drain
capacitor current depends on how fast the drain moves but not on how fast the
gate moves.

## Static check of the model

With issues 1 and 2 corrected in the copy, the DC and charge values of the
model were compared with the datasheet (ngspice at its default 27 °C):

| Quantity | Model | Datasheet (typ) |
|---|---|---|
| $R_{DS(on)}$ at 4.5 V, 75 A | 6.3 mΩ | 6.9 mΩ |
| $R_{DS(on)}$ at 10 V, 75 A | 4.9 mΩ | 5.0 mΩ |
| $V_{GS(th)}$ at 250 µA | 1.85 V | 1.9 V |
| Body diode drop at 75 A | 0.92 V | 0.8 V (1 V max) |
| $C_{oss}$ at 30 V | 301 pF | 300 pF |
| $Q_{oss}$ at 30 V | 24.5 nC | 31 nC |

The model matches the datasheet in these points, apart from $Q_{oss}$, which
is 21 % low. The gate charge was not measured: the test circuit written for
it did not converge.

## Summary

| # | Issue | Where | Effect | Understood |
|---|---|---|---|---|
| 1 | `.PARAM name value` without `=` | Vendor file, lines 439–444 | File does not load | Yes |
| 2 | Diode area as a bare `{expression}` | Vendor file, line 454 | File does not load | Yes |
| 3 | `LEVEL = 7` transistor | Vendor file, line 468 | Needs compatibility mode; handled by `.spiceinit` | Yes |
| 4 | Transient analysis aborts or stalls | Converter with the model | No results even after 1 and 2 are corrected | No |

Issues 1 and 2 are small syntax differences between PSpice and ngspice that
the compatibility mode does not cover. Correcting them would be enough to load
the model, but not to simulate the converter: issue 4 remains and its cause
is open.
