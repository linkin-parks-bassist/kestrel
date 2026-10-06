#!/usr/bin/env python3
"""Reset the probe over MCU UART, save its output and require successful cleanup."""
import argparse
from pathlib import Path
import time
import serial

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("port")
parser.add_argument("log", type=Path)
parser.add_argument("--timeout", type=float, default=120)
args = parser.parse_args()
data = bytearray()
with serial.Serial(args.port, 115200, timeout=0.2) as uart:
    uart.dtr = False
    uart.rts = True
    time.sleep(0.1)
    uart.rts = False
    deadline = time.monotonic() + args.timeout
    started = False
    while time.monotonic() < deadline:
        data.extend(uart.read(4096))
        if not started and b"PROBE ready" in data:
            uart.write(b"g\n")
            started = True
        if b"PROBE rc=" in data or b"Guru Meditation" in data or b"PROBE mount failed" in data:
            data.extend(uart.read(4096))
            break
output = data.decode(errors="replace")
args.log.write_text(output)
for line in output.splitlines():
    if any(marker in line for marker in ("COVERING ", "COMPOSED ", "HOTFIRST ", "NAV ", "PAGE ", "CANCEL ", "IO ", "WALK ", "PROBE ", "SD fixture", "Guru Meditation")):
        print(line)
if "PROBE rc=0 cleanup=0" not in output:
    raise SystemExit("Probe did not report success; inspect the saved log")
