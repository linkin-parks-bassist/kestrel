#!/usr/bin/env python3
"""Exercise the MCU read helpers against a sticky-error SPI stub."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "kestrel_interface/components/fpga/kest_fpga_io.c").read_text()
helpers = source[source.index("int64_t kest_fpga_req_data("):source.index("uint32_t kest_fpga_get_block_instr(")]
stub = r'''
#include <stdint.h>
#include <assert.h>
#include <stddef.h>
enum {COMMAND_READ=1, COMMAND_READ32=2, COMMAND_READOUT=3,
      COMMAND_CLEAR_CMD_ERR_FLAG=37};
typedef struct {int cmd_err, data_ready;} kest_fpga_status_flags;
static int sticky, new_error, count, bytes[32];
static int kest_fpga_send_byte(uint8_t byte) {
    bytes[count++] = byte;
    if (byte == COMMAND_CLEAR_CMD_ERR_FLAG) sticky = 0;
    return 0;
}
static int kest_fpga_send_byte_get_flags(uint8_t byte, kest_fpga_status_flags *flags) {
    kest_fpga_send_byte(byte);
    if (new_error && (byte == COMMAND_READ || byte == COMMAND_READ32)) sticky=1;
    flags->cmd_err=sticky; flags->data_ready=1;
    return 0;
}
static int kest_fpga_get_status_flags(kest_fpga_status_flags *flags) {
    flags->cmd_err=sticky; flags->data_ready=1; return 0;
}
static uint8_t kest_fpga_readout(void) {return 0x42;}
static void reset(int inject) {sticky=1; new_error=inject; count=0;}
'''
checks = r'''
int main(void) {
    kest_fpga_status_flags flags;
    uint8_t address[2]={0xab,0xcd};
    reset(0);
    assert(kest_fpga_read32(0x123454, &flags)==0x42424242);
    assert(bytes[0]==37 && bytes[1]==COMMAND_READ32);
    assert(bytes[2]==0x12 && bytes[3]==0x34 && bytes[4]==0x54);
    reset(0);
    assert(kest_fpga_req_data_p(7,address,2,2,&flags)==0x4242);
    assert(bytes[0]==37 && bytes[1]==COMMAND_READ && bytes[2]==7);
    assert(bytes[3]==0xab && bytes[4]==0xcd);
    reset(0);
    assert(kest_fpga_req_data(7,2,&flags)==0x4242);
    assert(bytes[0]==37 && bytes[1]==COMMAND_READ && bytes[2]==7);
    reset(1);
    assert(kest_fpga_read32(0,&flags)==-2);
    assert(count==2); /* A fresh error is still reported. */
    reset(0);
    assert(kest_fpga_read32(3,&flags)==-1 && count==0);
    assert(kest_fpga_req_data(7,2,NULL)==-1 && count==0);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="kestrel-read-errors-") as directory:
    work = Path(directory)
    (work / "test.c").write_text(stub + helpers + checks)
    subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    str(work / "test.c"), "-o", str(work / "test")], check=True)
    subprocess.run([str(work / "test")], check=True)
print("MCU read helpers: stale error cleared before payload; fresh error retained")
