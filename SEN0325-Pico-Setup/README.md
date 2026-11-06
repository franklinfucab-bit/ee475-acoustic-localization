# Active firmware and Windows workspace

This is the current EE475 workspace. Desktop checkpoint **RX4**, published Pico RAM image **v0.6-RX2**. Source on branch `Pico-ESP32` also builds **v0.7-LINK** (UART0 on GP0/GP1). Use [Update-and-Start.cmd](../Update-and-Start.cmd) or [一键启动雷达.cmd](../一键启动雷达.cmd) in the project root for RX4. The ESP32 path is documented in [esp32-link/README.md](../esp32-link/README.md).

Current code is here; validated SRAM-only ELF/UF2 are in `firmware/`. Runtime logs and short raw snapshots are in `logs/`. The current phase is [stages/06-joint-delay](../stages/06-joint-delay/README.md); superseded work is in [legacy](../legacy/README.md). See the [project README](../README.md) for wiring, roles, operation and limitations.
