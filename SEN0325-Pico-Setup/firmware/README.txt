EE475 RX2 — FIRMWARE 0.6 (27 OCTOBER 2026)

sen0325_setup-RAM.uf2: validated RP2040 SRAM-only image. When the Pico is the RPI-RP2 drive, the launcher copies this file onto that drive. picotool remains available for a running v0.5 application when the drive is absent.
sen0325_setup-RAM.elf: matching debug symbols/executable from the same build.

48 kHz, 4096 frames, seven signed 16-bit channels; GPIO mapping and sample unpacking preserved.
USB software buffers: TX FIFO 4096 bytes, RX FIFO and endpoint transfer buffer 512 bytes. USB full-speed endpoint packet size remains 64 bytes.
CRC-32 remains zlib-compatible, now computed with a 256-entry lookup table.

Stage documentation, source backups, variant benchmarks and validation are in ../../stages/04-latency-reduction/.
Experimental and old binaries under that stage are evidence, not normal launch targets.
No flash-payload blocks are present. RAM-only code is lost when power is removed; use the normal launcher/BOOTSEL workflow again.
