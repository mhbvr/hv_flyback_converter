# Prototype 1

First bench prototype of the flyback converter. It runs open-loop: a Flipper
Zero generates the PWM signal and the duty cycle is set by hand.

## Components

| Function | Part | Notes |
|---|---|---|
| Flyback transformer | Coilcraft DA2033-AL | $L_p$ = 10 µH, turns ratio 1 : 10 |
| Output diode | Power Integrations QH05TZ600 | Qspeed H-series, 600 V, 5 A, TO-220AC |
| Switch | Texas Instruments CSD18533KCS | N-channel MOSFET, 60 V, TO-220 |
| Gate driver | Microchip MCP1407 | Non-inverting low-side driver |
| Output capacitor | WIMA MKS4, 2.2 µF, 400 V | Metallized polyester film |
| Input capacitor | Nichicon, 1000 µF, 50 V | Aluminium electrolytic |
| Bypass capacitor | 1 µF ceramic | |
| PWM source | Flipper Zero | 3.3 V logic output, drives the MCP1407 input |

Datasheets: see [`docs/datasheets`](../docs/datasheets/README.md).

## Ideal characteristics

Calculated with the lossless DCM formulas from
[`docs/theory.md`](../docs/theory.md) ($\eta = 1$). Parasitics and datasheet
limits are not included yet.

### Operating conditions

| Quantity | Value |
|---|---|
| Input voltage $V_{in}$ | 5 V |
| Output voltage $V_{out}$ | 170 V |
| Switching frequency $f$ | 100 kHz ($T$ = 10 µs) |
| Primary inductance $L_p$ | 10 µH |
| Turns ratio $N$ | 10 |
| Output capacitor $C$ | 2.2 µF |
| Input power limit of the 5 V supply | 3 W |

### Fixed values

| Quantity | Formula | Value |
|---|---|---|
| Secondary inductance | $L_s = N^2 L_p$ | 1 mH |
| Maximum DCM duty cycle | $D_{max} = \dfrac{V_{out}}{V_{out} + N V_{in}}$ | 0.773 |
| Maximum DCM output current | $\dfrac{V_{in}^2 D_{max}^2}{2 f L_p V_{out}}$ | 43.9 mA (7.46 W) |
| MOSFET voltage | $V_{in} + V_{out}/N$ | 22 V |
| Diode reverse voltage | $V_{out} + N V_{in}$ | 220 V |
| Input power vs. duty cycle | $P_{in} = \dfrac{V_{in}^2 D^2}{2 f L_p}$ | $12.5\,D^2$ W |

The 3 W supply limits the converter well before the DCM boundary:

| Quantity | Formula | Value |
|---|---|---|
| Duty cycle at 3 W | $D = \sqrt{2 f L_p P_{in}}/V_{in}$ | 0.49 |
| Output current at 3 W | $P_{in}/V_{out}$ | 17.6 mA |

### Operating points at $V_{out}$ = 170 V

Each row is the duty cycle that holds 170 V at the given load.

| $D$ | $t_{on}$, µs | $I_{p\,max}$, A | $I_{s\,max}$, mA | $t_{off}$, µs | Idle, µs | $I_{in,avg}$, A | $P_{in}$, W | $I_{out}$, mA | Load $R$, kΩ | Ripple $\Delta V_{out}$, mV |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.10 | 1.00 | 0.50 | 50 | 0.29 | 8.71 | 0.025 | 0.125 | 0.74 | 231 | 3 |
| 0.20 | 2.00 | 1.00 | 100 | 0.59 | 7.41 | 0.10 | 0.50 | 2.94 | 57.8 | 13 |
| 0.30 | 3.00 | 1.50 | 150 | 0.88 | 6.12 | 0.225 | 1.125 | 6.62 | 25.7 | 27 |
| 0.40 | 4.00 | 2.00 | 200 | 1.18 | 4.82 | 0.40 | 2.00 | 11.8 | 14.5 | 47 |
| **0.49** | **4.90** | **2.45** | **245** | **1.44** | **3.66** | **0.60** | **3.00** | **17.6** | **9.63** | **69** |
| 0.50 | 5.00 | 2.50 | 250 | 1.47 | 3.53 | 0.625 | 3.125 | 18.4 | 9.25 | 72 |
| 0.60 | 6.00 | 3.00 | 300 | 1.76 | 2.24 | 0.90 | 4.50 | 26.5 | 6.42 | 100 |
| 0.70 | 7.00 | 3.50 | 350 | 2.06 | 0.94 | 1.225 | 6.125 | 36.0 | 4.72 | 132 |
| 0.773 | 7.73 | 3.86 | 386 | 2.27 | 0 | 1.49 | 7.46 | 43.9 | 3.87 | 157 |

The bold row is the 3 W supply limit. Rows below it need more input power
than the supply can deliver. The last row is the DCM/CCM boundary.

### Open-loop warning

There is no feedback, so the output voltage follows the load:

$$
V_{out} = V_{in}\, D\,\sqrt{\frac{R\,T}{2L_p}} = 3.54\; D\,\sqrt{R}\ \text{V} \quad (R \text{ in } \Omega).
$$

For a given load, use the table to find the duty cycle for 170 V and do not
exceed it. With a light or missing load the output rises far above 170 V and
past the 400 V rating of the output capacitor. Always connect the load before
enabling the PWM, and start from a low duty cycle.
