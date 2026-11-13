# HV Flyback Converter

A flyback boost converter that generates the high-voltage DC anode supply for
**nixie tubes** from a low-voltage input. The target is about 170 V from a 5 V
supply with a limited power budget.

The converter is a flyback (an isolated buck-boost with a coupled
"flyback transformer"). It runs in **discontinuous conduction mode (DCM)**
under closed-loop voltage regulation.

## Repository layout

| Path | Contents |
|---|---|
| `docs/theory.md` | Derivation of the DCM design equations: peak currents, demagnetization time, DCM limit, maximum output current, voltage stresses and output ripple |
| `docs/img/` | Circuit diagram and the original hand-written derivation sheets |

## Status

Early stage: theory and design equations. Schematic, transformer design and
firmware/controller selection will follow.
