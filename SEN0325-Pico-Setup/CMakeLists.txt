cmake_minimum_required(VERSION 3.13)
if(NOT PICO_SDK_PATH)
    if(DEFINED ENV{PICO_SDK_PATH})
        set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
    else()
        set(PICO_SDK_PATH "C:/Tools/Embedded/pico-sdk")
    endif()
endif()
include("${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
project(sen0325_setup C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
add_executable(sen0325_setup main.c)
# Aggregate full-speed USB packets without changing the 64-byte USB descriptor.
# The endpoint buffer is a software transfer buffer, not an endpoint packet size.
set(RX2_USB_TX_FIFO_BYTES 4096 CACHE STRING "CDC software TX FIFO bytes")
set(RX2_USB_EP_BUFFER_BYTES 512 CACHE STRING "CDC software endpoint transfer buffer bytes")
if(NOT RX2_USB_TX_FIFO_BYTES MATCHES "^(64|128|256|512|1024|2048|4096)$" OR
   NOT RX2_USB_EP_BUFFER_BYTES MATCHES "^(64|128|256|512|1024)$" OR
   RX2_USB_TX_FIFO_BYTES LESS RX2_USB_EP_BUFFER_BYTES)
    message(FATAL_ERROR "Use supported power-of-two USB buffers with TX FIFO >= endpoint buffer")
endif()
target_compile_definitions(sen0325_setup PRIVATE
    CFG_TUD_CDC_TX_BUFSIZE=${RX2_USB_TX_FIFO_BYTES}
    # TinyUSB only arms OUT when RX FIFO space can hold one transfer buffer.
    CFG_TUD_CDC_RX_BUFSIZE=${RX2_USB_EP_BUFFER_BYTES}
    CFG_TUD_CDC_EP_BUFSIZE=${RX2_USB_EP_BUFFER_BYTES})
pico_set_program_version(sen0325_setup "0.7-LINK")
# The 48 kHz unpacking and three-bin detector must finish within each DMA block.
# Keep debug symbols while optimizing this application source for real-time use.
set_source_files_properties(main.c PROPERTIES COMPILE_OPTIONS "-O3")
pico_generate_pio_header(sen0325_setup ${CMAKE_CURRENT_LIST_DIR}/sen0325_i2s.pio)
target_link_libraries(sen0325_setup pico_stdlib hardware_pio hardware_dma hardware_irq hardware_clocks hardware_uart m)
pico_enable_stdio_usb(sen0325_setup 1)
pico_enable_stdio_uart(sen0325_setup 0)
pico_add_extra_outputs(sen0325_setup)
