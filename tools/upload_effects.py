#!/usr/bin/env python3
"""Deploy verified .eff files over UART/USB with exact byte readback.

One persistent connection; existing differing files require --replace. Uploads
do not reload descriptors or alter presets. Reboot deliberately to discover them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

import serial


class Console:
    def __init__(self, port, log):
        self.uart = serial.Serial(port=None, baudrate=115200, timeout=0.1)
        self.uart.dtr = self.uart.rts = False
        self.uart.port = port
        self.log = log
        self.uart.open()

    def read_until(self, pattern, timeout):
        data = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self.uart.read(4096)
            if chunk:
                self.log.write(chunk)
                self.log.flush()
                data.extend(chunk)
                # IDF linenoise queries cursor position, including across reads.
                if b'\x1b[6n' in data:
                    self.uart.write(b'\x1b[1;1R')
                    data[:] = data.replace(b'\x1b[6n', b'')
                if re.search(pattern, data):
                    return bytes(data)
        raise TimeoutError(f'UART response timeout: {bytes(data[-500:])!r}')

    def command(self, command, pattern=rb'KEST eff-file result=-?\d+ errno=\d+'):
        self.uart.write(command.encode('ascii') + b'\r')
        return self.read_until(pattern, 10)

    def file(self, command):
        data = self.command('eff-file ' + command)
        result = re.search(rb'KEST eff-file result=(-?\d+) errno=(\d+)', data)
        return int(result[1]), int(result[2]), data

    def wait_startup(self):
        self.read_until(rb'kest>', 30)
        self.uart.write(b'\r')
        self.read_until(rb'kest>', 10)
        uptime = self.command('uptime', rb'KEST uptime ms=\d+[\r\n]')
        elapsed = int(re.search(rb'KEST uptime ms=(\d+)', uptime)[1])
        # The console appears before SD/codec initialization finishes.
        # Let carrier startup finish before requesting hex file dumps.
        deadline = time.monotonic() + max(0, 12 - elapsed / 1000)
        pending = bytearray()
        while time.monotonic() < deadline:
            chunk = self.uart.read(4096)
            if chunk:
                self.log.write(chunk)
                self.log.flush()
                pending.extend(chunk)
                if b'\x1b[6n' in pending:
                    self.uart.write(b'\x1b[1;1R')
                pending[:] = pending[-3:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--verified', type=Path, required=True, help='effect_library.py output directory')
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--replace', action='store_true')
    parser.add_argument('effects', type=Path, nargs='+')
    args = parser.parse_args()
    records = json.loads((args.verified / 'results.json').read_text())
    verified = {r['effect']: r for r in records if not r['parameters']}
    payloads = []
    for file in args.effects:
        if not re.fullmatch(r'[A-Z0-9_]{1,8}\.EFF', file.name):
            parser.error(f'{file.name}: requires an uppercase 8.3 .EFF filename')
        data = file.read_bytes()
        record = verified.get(file.name)
        if not record or record.get('descriptor_sha256') != hashlib.sha256(data).hexdigest():
            parser.error(f'{file.name}: current bytes have no matching default verification')
        payloads.append((file.name, data))
    with args.log.open('xb') as log:
        console = Console(args.port, log)
        try:
            console.wait_startup()
            magic = console.command('fpga-read32 0', rb'value=0x[0-9a-f]{8}')
            flags = console.command('fpga-read32 4', rb'value=0x[0-9a-f]{8}')
            if b'value=0x4b455354' not in magic or b'value=0x00000006' not in flags:
                raise RuntimeError('expected current polynomial/SVF partner image')
            for name, data in payloads:
                result, error, reply = console.file(f'read {name}')
                existed = result == 0
                existing = b''.join(bytes.fromhex(x.decode()) for x in
                                    re.findall(rb'KEST eff-file data=([0-9a-f]+)', reply))
                if result == 0 and existing == data:
                    print(f'{name}: already identical', flush=True)
                    continue
                if result == 0 and not args.replace:
                    raise RuntimeError(f'{name}: exists with different bytes; use --replace deliberately')
                if result != 0 and error != 2:
                    raise RuntimeError(f'{name}: cannot read destination: errno {error}')
                for offset in range(0, len(data), 96):
                    result, error, _ = console.file(f'write {name} {offset} {data[offset:offset + 96].hex()}')
                    if result:
                        raise RuntimeError(f'{name}: write failed: errno {error}')
                if existed:
                    result, error, _ = console.file(f'delete {name}')
                    if result:
                        raise RuntimeError(f'{name}: delete failed: errno {error}')
                result, error, _ = console.file(f'publish {name}')
                if result:
                    raise RuntimeError(f'{name}: publish failed: errno {error}')
                result, error, reply = console.file(f'read {name}')
                actual = b''.join(bytes.fromhex(x.decode()) for x in
                                  re.findall(rb'KEST eff-file data=([0-9a-f]+)', reply))
                if result or actual != data:
                    raise RuntimeError(f'{name}: byte readback mismatch')
                print(f'{name}: published and verified {len(data)} bytes', flush=True)
        finally:
            console.uart.close()


if __name__ == '__main__':
    main()
