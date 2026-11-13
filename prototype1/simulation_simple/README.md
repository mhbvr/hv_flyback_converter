# Prototype 1 – simulation

An ngspice model of the [prototype 1](../README.md) converter. It is one flat
netlist of 12 elements with no vendor models and no subcircuits. The MOSFET,
the diode and the transformer are standard SPICE elements whose parameters
come from the datasheets in
[`docs/datasheets`](../../docs/datasheets/README.md). This README explains
each parameter, checks the models against the datasheets, and lists what the
results can and cannot be trusted for.

| File | Contents |
|---|---|
| `flyback_simple.cir` | Netlist, analysis and measurements |
| `plot_waveforms.py` | Plots the saved waveforms (needs numpy and matplotlib) |
| `waveforms.svg` | Result of the plot script |

## Running it

```
cd prototype1/simulation_simple
ngspice -b flyback_simple.cir
python3 plot_waveforms.py
```

Tested with ngspice 42; one run takes about a minute. The parameters at the
top of the netlist set the operating point: `VIN`, `FSW`, `DUTY`, `RLOAD`.
The default is the 3 W point of the ideal table: `DUTY` = 0.49 and
`RLOAD` = 9.63 kΩ.

The output capacitor starts charged to `VSTART` = 170 V, the ideal value for
this operating point, so there is no start-up transient. The run lasts 100 ms,
about five time constants of $R\,C$ = 21 ms, and the output settles to its
real value. For another operating point, set `VSTART` to the expected output
voltage and keep the run at least five time constants long.

The measurements are printed at the end of the run and are taken over the last
20 switching periods. The last two periods are written to `waveforms.txt`.

## Circuit

```
           RP      LP                  LS      RS        D1
 vin ──┬──[15m]──[10u]── drain      ┌─[1m]──[1.1]── sec ─▶|──┬────────┬── out
       │           ·       │        │   ·                    │        │
      VIN        KT = 0.99277      gnd                     COUT     RLOAD
      5 V                  │                               2.2u     9.63k
       │                   │                                 │        │
      gnd        gate ──┤ M1                                gnd      gnd
                   │       │
 drv ───[RDRV]─────┘      gnd
         3.4
```

| Element | What it is |
|---|---|
| `VIN` | 5 V supply |
| `VDRV`, `RDRV` | Gate driver: a 0–5 V pulse on node `drv` behind the driver output resistance |
| `RP`, `LP`, `LS`, `RS`, `KT` | Transformer: two coupled inductors with their winding resistances |
| `M1` | MOSFET |
| `D1` | Output diode |
| `COUT`, `RLOAD` | Output capacitor and load |

The dots mark the winding polarity: the secondary conducts when the MOSFET
turns off.

## MOSFET CSD18533KCS

The MOSFET is the ngspice `VDMOS` element, a built-in model of a vertical
power MOSFET. It contains a transistor with a square-law characteristic,
drain, source and gate resistances, three capacitances and the body diode.
All datasheet values below are typical values at 25 °C.

### Conduction

| Parameter | Value | Datasheet values used | How it is obtained |
|---|---|---|---|
| `vto` | 1.9 V | $V_{GS(th)}$ = 1.9 V | Taken directly |
| `kp` | 150 A/V² | $g_{fs}$ = 150 S at $I_D$ = 75 A | For a square-law transistor $g_{fs} = \sqrt{2 K_p I_D}$, so $K_p = g_{fs}^2 / (2 I_D)$ |
| `rd` + `rs` | 2.3 mΩ + 2.0 mΩ | $R_{DS(on)}$ = 6.9 mΩ at $V_{GS}$ = 4.5 V | The channel resistance is $1/(K_p (V_{GS} - V_{th}))$ = 2.6 mΩ. The remaining 4.3 mΩ is series resistance |
| `rg` | 1.4 Ω | Series gate resistance $R_G$ | Taken directly |
| `ksubthres` | 0.02 | $V_{GS(th)}$ is defined at $I_D$ = 250 µA | Sets how sharply the transistor turns on near the threshold. The ngspice default of 0.1 makes it conduct 250 µA at 1.5 V; 0.02 moves that to 1.85 V |
| `is`, `n`, `rb` | 0.9 nA, 1, 2 mΩ | Body diode $V_{SD}$ = 0.8 V at 75 A | Diode equation plus series resistance, solved for 0.8 V at 75 A |
| `bv`, `ibv` | 60 V, 250 µA | $BV_{DSS}$ = 60 V min at 250 µA | Taken directly |

The datasheet does not say how the 4.3 mΩ is divided between drain and
source, so the split into `rd` and `rs` is an assumption.

### Capacitances

The datasheet gives three capacitances measured between pairs of pins. The
model needs the three capacitances between the terminals:

| Model capacitance | From datasheet values |
|---|---|
| Gate-source $C_{gs}$ | $C_{iss} - C_{rss}$ |
| Gate-drain $C_{gd}$ | $C_{rss}$ |
| Drain-source $C_{ds}$ | $C_{oss} - C_{rss}$ |

$C_{gs}$ is almost constant. The other two fall steeply as the drain voltage
rises (datasheet Figure 4-5), so each is described by a curve with a few
parameters. These parameters cannot be read from the datasheet directly. They
were adjusted until the model reproduced the datasheet capacitances and
charges listed in the next section.

| Parameter | Value | Meaning | Fitted to |
|---|---|---|---|
| `cgs` | 2413 pF | Constant $C_{gs}$ | $C_{iss} - C_{rss}$ = 2420 pF − 7 pF |
| `cgdmax` | 450 pF | $C_{gd}$ when the MOSFET is fully on | $C_{rss}$ near 0 V (Figure 4-5) and the total gate charge |
| `cgdmin` | 4 pF | $C_{gd}$ at high drain voltage | $C_{rss}$ at 30 V (Figure 4-5) |
| `a` | 0.3 | How fast $C_{gd}$ falls with drain voltage | Shape of the $C_{rss}$ curve |
| `cjo` | 8.9 nF | $C_{ds}$ at 0 V | $C_{oss}$ at 30 V and $Q_{oss}$ |
| `vj` | 0.8 V | Junction potential in $C_{ds} = C_{jo}/(1 + V/V_j)^m$ | Same |
| `m` | 0.95 | Exponent in the same formula | Same |

The datasheet is not consistent about $C_{rss}$ at 30 V: the table says 7 pF
and Figure 4-5 shows about 20 pF. The model follows the figure, because the
rest of the curve is also taken from it.

### Check of the MOSFET model against the datasheet

The finished model was put into small test circuits that repeat the datasheet
measurements. The test circuits are not in the repository.

| Quantity | Model | Datasheet (typ) |
|---|---|---|
| $R_{DS(on)}$ at $V_{GS}$ = 4.5 V | 6.9 mΩ at 6 A, 7.1 mΩ at 58 A | 6.9 mΩ at 75 A |
| $R_{DS(on)}$ at $V_{GS}$ = 10 V | 5.1 mΩ | 5.0 mΩ |
| $V_{GS}$ at $I_D$ = 250 µA | 1.85 V | 1.9 V |
| Body diode drop at 75 A | 0.80 V | 0.8 V |
| Breakdown voltage at 250 µA | 60.0 V | 60 V min |
| $C_{oss}$ at 30 V | 302 pF | 300 pF |
| $Q_{oss}$ at 30 V | 30.5 nC | 31 nC |
| $Q_{g(th)}$, gate charge at threshold | 4.6 nC | 4.6 nC |
| $Q_g$ at 4.5 V | 14.0 nC | 14 nC |
| $Q_g$ at 10 V | 29.7 nC | 28 nC |
| $Q_{gs}$, gate charge up to the plateau | 7.1 nC | 9.4 nC |
| $Q_{gd}$, gate charge along the plateau | 2.4 nC | 3.9 nC |
| Plateau voltage at 75 A | 3.05 V | about 3.6 V to 4.3 V (Figure 4-4) |

Capacitance against drain voltage, compared with values read from Figure 4-5:

| $V_{DS}$ | $C_{oss}$ model | $C_{oss}$ figure | $C_{rss}$ model | $C_{rss}$ figure |
|---|---|---|---|---|
| 0 V | 8700 pF | about 2700 pF | 275 pF | about 280 pF |
| 2 V | 2900 pF | about 2000 pF | 183 pF | about 210 pF |
| 5 V | 1460 pF | about 1550 pF | 106 pF | about 175 pF |
| 10 V | 810 pF | about 640 pF | 60 pF | about 35 pF |
| 20 V | 436 pF | about 380 pF | 33 pF | about 24 pF |
| 30 V | 302 pF | 300 pF | 23 pF | about 20 pF |

The figure values are read from a logarithmic plot and are accurate to about
10 %.

Where the model is good and where it is not:

- **On-resistance, total gate charge, output charge and output capacitance at
  30 V match within a few percent.** These set the conduction loss, the gate
  drive power and the energy stored on the drain, which are what this
  converter depends on.
- **The output capacitance below 2 V is too large.** The real curve has a
  plateau up to 9 V and then drops by about 40 % within one volt. The smooth
  formula cannot follow that, so it was fitted to the charge at 30 V instead.
  The price is too much capacitance near 0 V.
- **The plateau is too low and too short at 75 A.** A square-law transistor
  that matches $g_{fs}$ at 75 A carries more current at a given gate voltage
  than the real device (datasheet Figure 4-3). This converter switches at
  most 2.4 A, where the plateau is close to the threshold voltage, so the
  error should matter much less than the 75 A test suggests. This was not
  checked separately.

## Output diode QH05TZ600

A standard SPICE diode.

| Parameter | Value | Datasheet values used |
|---|---|---|
| `is`, `n`, `rs` | 8.4 pA, 2, 0.24 Ω | $V_F$ = 2.6 V at 5 A (table); knee near 1.2 V (Figure 3) |
| `cjo`, `vj`, `m` | 41 pF, 1 V, 0.37 | $C_J$ = 17 pF at 10 V (table); about 6 pF at 180 V (Figure 4) |
| `tt` | 1.3 ns | $Q_{RR}$ = 6.5 nC at $I_F$ = 5 A: $t_t = Q_{RR}/I_F$ |
| `bv`, `ibv` | 600 V, 250 µA | $V_{RRM}$ and maximum reverse current |

The forward voltage of the model is $V_F = n V_T \ln(I/I_s) + I R_s$ with
$V_T$ = 25.9 mV. It gives 1.22 V at 0.1 A, 1.31 V at 0.25 A and 2.60 V at
5 A. The junction capacitance formula gives 16.9 pF at 10 V and 6.0 pF at
180 V.

The converter works below 0.4 A, where Figure 3 cannot be read accurately, so
the forward drop in this range is an estimate. It is fixed by the table point
at 5 A and the knee voltage only; the curve between 1 A and 20 A is not
fitted.

## Transformer DA2033-AL

Two coupled inductors with their winding resistances.

| Element | Value | Source |
|---|---|---|
| `LP` | 10 µH | Primary inductance |
| `LS` | 1 mH | $L_s = N^2 L_p$, $N$ = 10 |
| `KT` | 0.99277 | Leakage inductance 0.144 µH max, measured at the primary with the secondary shorted: $L_{lk} = L_p(1 - k^2)$, so $k = \sqrt{1 - L_{lk}/L_p}$ |
| `RP` | 15 mΩ | Primary DCR max |
| `RS` | 1.1 Ω | Secondary DCR max |

## Everything else

| Element | Value | Source |
|---|---|---|
| `VIN` | 5 V | Ideal source |
| `VDRV` | 0–5 V pulse, 10 ns edges | Ideal gate driver; the edge time is assumed |
| `RDRV` | 3.4 Ω | MCP1407 output resistance at 5 V: mean of 4.0 Ω pull-up and 2.7 Ω pull-down (datasheet Figures 2-19, 2-20) |
| `COUT` | 2.2 µF | Ideal capacitor |
| `RLOAD` | 9.63 kΩ | Load |

## What is left out

- Gate driver delay, input thresholds and separate pull-up and pull-down
  resistances.
- Transformer winding capacitance, core loss and saturation.
- Series resistance and inductance of the output capacitor.
- Input and bypass capacitors. With an ideal supply they carry no current.
- Wiring, PCB and package inductance.
- Start-up from a discharged output.
- Tolerances and temperature: all values are typical at 25 °C.

## Results

At `DUTY` = 0.49 and `RLOAD` = 9.63 kΩ, steady state:

| Quantity | Simulation | Ideal theory |
|---|---|---|
| Output voltage | 164.8 V | 170 V |
| Output current | 17.1 mA | 17.6 mA |
| Input power | 2.89 W | 3.00 W |
| Output power | 2.82 W | 3.00 W |
| Efficiency $P_{out}/P_{in}$ | 97.7 % | 100 % |
| Average supply current | 0.58 A | 0.60 A |
| Peak primary current | 2.40 A | 2.45 A |
| Peak secondary current | 0.36 A | 0.245 A |
| Peak drain voltage | 52 V | 22 V |
| Peak diode reverse voltage | 220 V | 220 V |
| Output ripple | 68 mV | 69 mV |
| Gate drive power | 5.6 mW | – |

The ideal values are from the table in [`../README.md`](../README.md). The
gate drive power is taken from the `VDRV` source and is not part of the input
power.

![Simulated waveforms](waveforms.svg)

What the simulation shows beyond the ideal theory:

- **Less power than ideal.** The peak primary current is 2.40 A instead of
  2.45 A, because the gate takes time to charge and the MOSFET and winding
  resistances reduce the voltage across the primary. Less energy is stored
  per cycle, so the output is 165 V instead of 170 V.
- **Drain spike at turn-off.** The energy in the leakage inductance has
  nowhere to go except the MOSFET capacitance. The drain rings at about
  19 MHz and reaches 52 V, against a 60 V rating. The same ring appears on
  the primary and secondary currents, which is why the secondary peak is
  0.36 A instead of 0.245 A.
- **Ringing after demagnetization.** The secondary current reaches zero
  about 1.5 µs after turn-off. The primary inductance then rings with the
  MOSFET capacitance at about 0.9 MHz until the next turn-on. The drain
  swings between 0 V, where the body diode clips it, and 16 V. The pulses are
  narrow at the top and flat at the bottom because the capacitance is small at
  high voltage and large near zero.
- **Turn-on near zero drain voltage.** At this operating point the next
  turn-on happens to fall at the bottom of that ring, so there is no ringing
  at turn-on.

## Limits of the results

- Nothing in the model damps the ringing except the winding, MOSFET and diode
  resistances, so every ring lasts longer than it will on the bench.
- The 52 V drain spike depends on the maximum leakage inductance from the
  datasheet and on the fitted output capacitance, and no wiring inductance is
  included. Treat it as an indication that the margin to 60 V is small, not
  as a prediction.
- The energy taken in each cycle depends on where in the 0.9 MHz ring the
  MOSFET turns on. A different frequency, duty cycle or capacitance moves
  that point and can shift the output by several volts.
- The transformer has no winding capacitance. The real one adds to the
  capacitance on the drain and will lower both ring frequencies.
- The model has not been compared with measurements.
