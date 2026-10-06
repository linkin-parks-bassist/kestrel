#!/usr/bin/env python3
"""Check UART parameter rejection, convergence and restoration on an active effect.

Accepted targets mark the preset dirty, including restoration. Does not save files.
"""
import argparse
import math
from pathlib import Path
import re
import time

from upload_effects import Console


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('preset', type=int)
    parser.add_argument('effect', type=int)
    parser.add_argument('parameter', type=int)
    parser.add_argument('target', type=float)
    args = parser.parse_args()
    ids = (args.preset, args.effect, args.parameter)
    if any(not 0 <= item <= 65535 for item in ids) or not math.isfinite(args.target):
        parser.error('IDs must fit uint16 and target must be finite')
    dotted = '.'.join(map(str, ids))
    command = 'parameter-target ' + ' '.join(map(str, ids))
    row = re.compile(rb'KEST dsp parameter=' + re.escape(dotted.encode()) +
                     rb' name=([^ ]*) value=([^ ]*) min=([^ ]*) max=([^ ]*) driven=([01]) override=([01])')
    with args.log.open('xb') as log:
        console = Console(args.port, log)
        try:
            console.wait_startup()

            def snapshot():
                reply = console.command('dsp', row)
                match = row.search(reply)
                return float(match[2]), float(match[3]), float(match[4]), int(match[5]), int(match[6])

            def converge(target):
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    current, *_ = snapshot()
                    if math.isclose(current, target, rel_tol=1e-6, abs_tol=1e-6):
                        return
                    time.sleep(0.05)
                raise AssertionError(f'{dotted} did not converge to {target}')

            def queue(target):
                reply = console.command(f'{command} {target:.9g}',
                    rb'KEST parameter-target id=[^\r\n]*reason=[^\r\n]+')
                assert re.search(rb'result=0 reason=queued', reply), reply

            original, lower, upper, driven, override = snapshot()
            assert all(map(math.isfinite, (original, lower, upper)))
            assert lower <= original <= upper and lower <= args.target <= upper
            assert not driven or override
            for value in ('nan', 'inf', '1e39', '0junk'):
                reply = console.command(f'{command} {value}', rb'KEST parameter-target reason=invalid-input')
            reply = console.command(f'parameter-target 65536 {args.effect} {args.parameter} 0',
                                    rb'KEST parameter-target reason=invalid-input')
            for value in (lower - max(1, abs(lower)), upper + max(1, abs(upper))):
                console.command(f'{command} {value:.9g}', rb'KEST parameter-target id=[^\r\n]*reason=out-of-range')
            current, *_ = snapshot()
            assert math.isclose(current, original, rel_tol=1e-6, abs_tol=1e-6)
            try:
                queue(args.target)
                converge(args.target)
            finally:
                queue(original)
                converge(original)
            console.command('fpga-status', rb'KEST fpga-status raw=0x01[^\r\n]*timeout=0[^\r\n]*bad=0[^\r\n]*cmd_err=0')
            print(f'{dotted}: invalid targets rejected; {original} -> {args.target} -> {original}; FPGA healthy')
        finally:
            console.uart.close()


if __name__ == '__main__':
    main()
