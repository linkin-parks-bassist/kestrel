<p align="center">
  <img src="docs/resources/image.jpg" alt="Image" width="80%">
</p>
<p align="center"><i>(Todo: replace with better photo)</i></p>

# Kestrel

**Kestrel** is a programmable digital effects pedal.

It is designed to be:

- **Easy to use** — drag-and-drop effects, turn knobs, press buttons.
- **Extremely powerful** — a real-time programmable DSP platform capable of complex audio processing pipelines.

Under the hood, Kestrel combines Kestrel Core, Kestrel Interface, and a flexible, modular effect description system.

---

# System Architecture

Kestrel consists of three major components:

- **MCU control system** running [Kestrel Interface](https://github.com/linkin-parks-bassist/kestrel-interface)  
  (UI, control logic, effect compiler)

- **FPGA DSP engine** running [Kestrel Core](https://github.com/linkin-parks-bassist/kestrel-core)  
  (high-performance programmable audio processing)

- **Hardware platform** on [Kestrel PCB](https://github.com/linkin-parks-bassist/kestrel-pcb)
  including the touchscreen interface, power system, and audio I/O.

### Hardware stack

The current prototype uses the following hardware modules:

- **Sipeed Tang Nano 20K** — FPGA DSP core  
- **Waveshare ESP32-P4-Pico** — UI and control processor  
- **Waveshare DSI-TOUCH-5A** — 5" MIPI-DSI touchscreen display  
- **Kestrel PCB** — carrier board integrating audio codec (SGTL5000), power, audio I/O and module interconnects

---

# Features

<p align="center">
  <img src="docs/resources/image.png" alt="Image" width="100%">
</p>

- Create pipelines with any effects in any order
- Real-time reconfiguration
- Drag-and-drop effect ordering
- Smoothed parameter control
- Click/pop-less transitions
- Effects stored as text files on SD card
- Latency under 60μs
- Performs >100 million multiply-accumulate operations per second
- Powerful programmable filter engine supporting arbitrary FIR/IIR filters

---

# Effect Descriptors

Effects are defined using **effect descriptor (`.eff`) files**, a small DSL that combines metadata, parameter definitions, and inline DSP assembly.

Example:

```text
v1.0

.INFO

name: "Low Pass Filter"
cname: "example_low_pass_filter"

.PARAMETERS

cutoff: (name: "Cutoff",
         default: 1000,
         min: 60,
         max: sample_rate / 2 - 1,
         units: "Hz",
         scale = "logarithmic")
Q: (name: "Resonance", default: 1 / sqrt(2), min: 0.1, max: 3)

.DEFS

omega: 2 * pi * cutoff / sample_rate
alpha: sin(omega) / (2 * Q)

.RESOURCES

x1: (type: "mem")
x2: (type: "mem")
y1: (type: "mem")
y2: (type: "mem")

.CODE

mem_read c1 $x1
mem_read c2 $x2
mem_read c3 $y1
mem_read c4 $y2

macz [(1/2) * (1 - cos(omega)) / (1 + alpha)] c0
mac  [        (1 - cos(omega)) / (1 + alpha)] c1
mac  [(1/2) * (1 - cos(omega)) / (1 + alpha)] c2
mac  [        (2 * cos(omega)) / (1 + alpha)] c3
mac  [             (alpha - 1) / (1 + alpha)] c4

mem_write $x2 c1
mem_write $x1 c0
mem_write $y2 c3

mov_acc c0

mem_write $y1 c0
```

The UI is generated automatically from these files.

### Descriptor Features

- Simple assembly syntax
- Inline math expressions
- Parameter-dependent register computation
- Delay buffers and scratch memory
- Continuous and discrete parameters
- Automatic UI generation
- Customizable parameter widgets

---

# System Overview

<p align="center">
  <img src="docs/resources/M-stack.svg" alt="Image" width="50%">
</p>

Audio flows through the system as follows:

1. Audio enters via the codec over **I2S**
2. Kestrel Core executes DSP instructions on each sample
3. Kestrel Interface configures and updates the DSP engine via **SPI**
4. The UI allows users to create and control processing pipelines in real time

---

# [Kestrel Interface](https://github.com/linkin-parks-bassist/kestrel-interface)

Kestrel Interface is the control system and compiler for **Kestrel**.

It uses **FreeRTOS** and **LVGL** to provide the touchscreen UI used to create, edit and manage effect chains.

### Components

- Effect compiler
- FPGA control system
- Symbolic math engine
- Effect/profile/sequence management
- Parameter control subsystem
- LVGL-based GUI framework
- State capture system
- File system

---

# Getting Started

### ESP32 build

The display subsystem uses the Waveshare board support package for **ESP32-P4-Nano / Pico**.

Build:

```bash
idf.py build
```

Flash:

```bash
idf.py flash
```

---

### Desktop demo

A demo interface runs on POSIX systems.

Build:

```bash
make
```

Run:

```bash
./kest
```

Build shared library:

```bash
make lib
```

Install:

```bash
sudo make lib_install
```

Include:

```c
#include <libkest/kest_lib.h>
```

and link with `-lkest`.

---

# [Kestrel Core](https://github.com/linkin-parks-bassist/kestrel-core)

<p align="center">
  <img src="docs/resources/M-fpga.svg" alt="Global schematic" width="60%">
</p>

Implements a fixed-point, pipelined, programmable audio processing core targeting Gowin GW2AR devices.

### Features

- Single cycle throughput for MAC instructions
- Dual DSP pipelines with smoothed crossover and warmup
- Out-of-order execution with scoreboard hazard prevention
- Order enforced at commit boundary
- Delay buffer controller
- Arbitrary IIR filter engine
- Simple instruction set
- Variable fixed-point format controlled by instruction field

Timing closure achieved at 112.5 MHz on Gowin GW2AR-18.

---

# License

GNU GPL 3.0

---

# Contact

I'd love to hear from you.

email: davidjfarrell96@gmail.com
