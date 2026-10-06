#!/usr/bin/env python3
"""Run UART HIL steps over one connection using the upload console transport.

A JSON array contains {"command": "info", "expect": "KEST info", "wait_ms": 0}
steps. Expectations are ASCII regular expressions; waits follow matched replies.
Optional "page" checks the screen header before sending the command.
Commands may change the device: review the supplied script before running it.
"""
import argparse
import json
from pathlib import Path
import re
import time

from upload_effects import Console


def page_matches(reply, title):
    """Match a title inside the first screen's full-width top panel, not a row."""
    rows = re.findall(rb'KEST obj depth=(\d+) x=(-?\d+) y=(-?\d+) w=(\d+) h=(\d+) clickable=\d+ text=([^\r\n]*)', reply)
    if not rows or rows[0][0] != b'0':
        return False
    root = rows[0]
    for i, row in enumerate(rows[1:], 1):
        if row[0] == b'0':
            break
        if row[0] == b'1' and row[1:4] == root[1:4]:
            for child in rows[i + 1:]:
                if int(child[0]) <= 1:
                    break
                if child[5] == title.encode('utf-8'):
                    return True
            break
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('script', type=Path)
    args = parser.parse_args()
    steps = json.loads(args.script.read_text())
    if not isinstance(steps, list) or not steps:
        parser.error('script must contain a nonempty array of steps')
    prepared = []
    for i, step in enumerate(steps, 1):
        try:
            command = step['command'].encode('ascii')
            pattern = re.compile(step['expect'].encode('ascii'))
            wait_ms = step.get('wait_ms', 0)
            page = step.get('page')
            if not command or b'\r' in command or b'\n' in command:
                raise ValueError('command must be one nonempty line')
            if not isinstance(wait_ms, (int, float)) or not 0 <= wait_ms <= 60000:
                raise ValueError('wait_ms must be between 0 and 60000')
            if page is not None and (not isinstance(page, str) or not page or '\r' in page or '\n' in page):
                raise ValueError('page must be a nonempty single-line title')
        except (KeyError, TypeError, AttributeError, ValueError, re.error) as error:
            parser.error(f'step {i}: {error}')
        prepared.append((command.decode('ascii'), pattern, wait_ms, page))
    with args.log.open('xb') as log:
        console = Console(args.port, log)
        try:
            console.wait_startup()
            for i, (command, pattern, wait_ms, page) in enumerate(prepared, 1):
                if page is not None:
                    reply = console.command('ui-tree', rb'KEST tree end')
                    if not page_matches(reply, page):
                        raise RuntimeError(f'step {i}: expected page {page!r}; command {command!r} was not sent')
                reply = console.command(command, pattern)
                print(f'{i}: {command}\n{reply.decode("ascii", errors="replace")}', flush=True)
                time.sleep(wait_ms / 1000)
        finally:
            console.uart.close()


if __name__ == '__main__':
    main()
