#!/usr/bin/env python3
"""Sample model for the library's compiled arithmetic/SVF/LUT/scratchpad subset.

Consume production programming bytes, not a second .eff parser. Reject resources
and opcodes whose behavior is not modelled instead of silently approximating them.
"""
import argparse
import array
from pathlib import Path
import sys


def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def saturate(value):
    return max(-32768, min(32767, value))


def read_program(path):
    data = Path(path).read_bytes()
    instructions, registers = {}, {}
    pos = 0
    while pos < len(data):
        command = data[pos]
        pos += 1
        if command == 39:
            if pos != len(data):
                raise ValueError('tail must end the program')
            break
        if command not in (2, 3, 4):
            raise ValueError(f'unsupported programming command {command}')
        width = 4 if command == 2 else 2
        if pos + 2 + width > len(data):
            raise ValueError('truncated programming command')
        block = int.from_bytes(data[pos:pos + 2], 'big')
        value = int.from_bytes(data[pos + 2:pos + 2 + width], 'big')
        pos += 2 + width
        if command == 2:
            if block in instructions:
                raise ValueError('duplicate instruction')
            instructions[block] = value
        else:
            registers[block, command - 3] = signed(value, 16)
    else:
        raise ValueError('missing tail')
    if not instructions or sorted(instructions) != list(range(len(instructions))):
        raise ValueError('expected contiguous instruction blocks')
    program = [(instructions[i], registers.get((i, 0), 0), registers.get((i, 1), 0))
               for i in range(len(instructions))]
    for i, (word, _, _) in enumerate(program):
        op = word & 31
        if op not in (1, 5, 6, 7, 8, 16, 19, 20, 23, 24, 25, 26):
            raise ValueError(f'unsupported opcode {op} at block {i}')
        resource = bool(word & 32)
        if resource != (op in (16, 19, 20)):
            raise ValueError('unsupported instruction format')
        handle = word >> 20
        if resource and (handle > 255 or (op == 16 and handle not in (0, 1))):
            raise ValueError('unsupported resource handle')
        dest = (word >> (16 if resource else 21)) & 15
        if op not in (20, 23) and dest == 0 and i != len(program) - 1:
            raise ValueError('library renderer requires only the final instruction to write c0')
    word = program[-1][0]
    if (word & 31) in (20, 23) or ((word >> (16 if word & 32 else 21)) & 15) != 0:
        raise ValueError('final instruction must write c0')
    return program


class DSP:
    def __init__(self, program):
        self.program = program
        self.states = {}
        self.memory = {}
        self.luts = []
        if any((word & 31) == 16 for word, _, _ in program):
            root = Path(__file__).resolve().parents[1] / 'kestrel_core' / 'luts'
            self.luts = [[signed(int(word, 16), 16) for word in (root / name).read_text().split()]
                         for name in ('sin_q15_full.hex', 'tanh_q15.hex')]
            if any(len(table) != 2048 for table in self.luts):
                raise ValueError('expected 2048-word built-in LUTs')

    def lookup(self, handle, value):
        # Use the actual ROM words and the RTL's per-bit rounded interpolation.
        word = value & 65535
        index = (word & 32767) >> 4 if handle == 0 else ((word + 32768) & 65535) >> 5
        fraction = word & 15 if handle == 0 else (word >> 1) & 15
        following = (index + 1) % 2048 if handle == 0 else min(index + 1, 2047)
        table = self.luts[handle]
        difference = signed(table[following] - table[index], 16)
        result = table[index] + ((difference >> 1) if fraction & 8 else 0)
        term = (-1 if difference < 0 else 1) * (abs(difference) >> 2)
        for bit in (2, 1, 0):
            if fraction & (1 << bit):
                result += term
            term = (-1 if term < 0 else 1) * (abs(term) >> 1)
        return signed(result, 16)

    def sample(self, audio):
        channels = {0: audio}
        outputs = None
        for block, (word, reg0, reg1) in enumerate(self.program):
            def operand(offset):
                source = (word >> offset) & 31
                if source & 16:
                    return {0: reg0, 1: reg1, 3: 16384, 4: -32768, 5: 23170}.get(source & 15, 0)
                if source not in channels:
                    raise ValueError(f'uninitialized channel c{source:x} at block {block}')
                return channels[source]

            op, shift = word & 31, (word >> 25) & 31
            dest = (word >> (16 if word & 32 else 21)) & 15
            if op == 20:
                self.memory[word >> 20] = operand(6)
                continue
            if op == 19:
                channels[dest] = self.memory.get(word >> 20, 0)
                continue
            if op == 16:
                channels[dest] = self.lookup(word >> 20, operand(6))
                continue
            if op == 23:
                a, f, damping = operand(6), max(0, operand(11)), operand(16)
                if shift > 15:
                    raise ValueError('unsupported SVF damping format')
                low, band = self.states.get(block, (0, 0))
                low = signed(low + ((f * band) >> 15), 18)
                high = signed(a - low - ((damping * band) >> (15 - shift)), 18)
                band = signed(band + ((f * high) >> 15), 18)
                self.states[block] = low, band
                outputs = (saturate(low), saturate(high), saturate(band))
                continue
            if op in (24, 25, 26):
                if outputs is None:
                    raise ValueError('SVF read before update')
                value = outputs[op - 24]
            else:
                a = operand(6)
                if op == 1:
                    product = a * operand(11)
                    if not word & (1 << 31):
                        amount = (15 - shift) & 31
                        rounding = ((product >> (amount - 1)) & 1) if amount else 0
                        product = ((product >> amount) if amount <= 15 else 0) + rounding
                    value = signed(product + operand(16), 33)
                    value = signed(value, 16) if word & (1 << 30) else saturate(value)
                elif op == 5:
                    value = signed(abs(a), 16)
                elif op == 6:
                    value = min(a, operand(11))
                elif op == 7:
                    value = max(a, operand(11))
                else:
                    low, high = sorted((operand(11), operand(16)))
                    value = max(low, min(high, a))
            channels[dest] = value
        return channels[0]


def read_pcm(path):
    data = Path(path).read_bytes()
    if len(data) % 2:
        raise ValueError('truncated PCM16')
    values = array.array('h')
    values.frombytes(data)
    if sys.byteorder != 'little':
        values.byteswap()
    return values


def write_pcm(path, values):
    values = array.array('h', values)
    if sys.byteorder != 'little':
        values.byteswap()
    Path(path).write_bytes(values.tobytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('program')
    parser.add_argument('input', help='mono signed little-endian PCM16')
    parser.add_argument('output')
    args = parser.parse_args()
    dsp = DSP(read_program(args.program))
    write_pcm(args.output, (dsp.sample(x) for x in read_pcm(args.input)))
