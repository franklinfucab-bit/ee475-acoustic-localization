#include <ctype.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/pio.h"
#include "hardware/sync.h"
#include "hardware/uart.h"
#include "sen0325_i2s.pio.h"
#include "tone_filter.h"
#include "crc32_fast.h"

enum { DATA_BASE = 6, BCLK_PIN = 10, WS_PIN = 11, LED_CLK = 12, LED_DAT = 13 };
enum { LINK_TX_PIN = 0, LINK_RX_PIN = 1, LINK_BAUD = 115200, LED_COUNT = 12, LED_BRIGHT = 2, LED_STALE_US = 400000 };
enum { SAMPLE_RATE = 48000, FRAMES = 1024, WORDS_PER_FRAME = 8, WORDS = FRAMES * WORDS_PER_FRAME };
static const char *names[8] = {"D0L", "D0R", "D1L", "D1R", "D2L", "D2R", "D3L_UNUSED", "D3R_CENTER"};
static PIO capture_pio = pio0;
static uint sm, program_offset;
static int channels[2];
static uint32_t buffers[2][WORDS];
static volatile bool running, ready[2], processing_corrupted;
static volatile int processing_buffer = -1;
static volatile uint32_t dropped_buffers;
static absolute_time_t warm_until, report_at;

typedef struct {
    int64_t sum;
    uint64_t sum_sq;
    int32_t minimum, maximum;
    uint32_t zeros, clips;
    float tone_power;
    float tone_reference;
    float cross_re, cross_im;
} channel_stats;
static channel_stats accumulated[8];
static uint32_t accumulated_frames;
static uint32_t maximum_process_us;
static uint32_t report_sequence;
enum { RAW_FRAMES = 4096, RAW_CHANNELS = 7 };
static int16_t raw_audio[RAW_FRAMES][RAW_CHANNELS];
static bool raw_recording,raw_stream;
static uint32_t raw_frames, raw_sequence;
static uint32_t raw_request_started_us;
static char link_line[96];
static size_t link_used;
static uint32_t last_valid_doa_us;
static bool led_bearing_on;

static void reset_stats(channel_stats *stats) {
    memset(stats, 0, sizeof(channel_stats) * 8);
    for (uint ch = 0; ch < 8; ++ch) {
        stats[ch].minimum = INT32_MAX;
        stats[ch].maximum = INT32_MIN;
    }
}

// The LED ring is deliberately kept black; no high-current light test here.
static void led_byte(uint8_t value) {
    for (int bit = 7; bit >= 0; --bit) {
        gpio_put(LED_CLK, 0);
        gpio_put(LED_DAT, (value >> bit) & 1u);
        sleep_us(1);
        gpio_put(LED_CLK, 1);
        sleep_us(1);
    }
}
static void led_ring_off(void) {
    for (uint i = 0; i < 4; ++i) led_byte(0);
    for (uint led = 0; led < 12; ++led) {
        led_byte(0xe0); // Global brightness 0, B/G/R all 0.
        led_byte(0); led_byte(0); led_byte(0);
    }
    for (uint i = 0; i < 8; ++i) led_byte(0xff);
    gpio_put(LED_CLK, 0);
    gpio_put(LED_DAT, 0);
    led_bearing_on = false;
}

static void led_show_bearing(float angle_deg) {
    unsigned on = (unsigned)lroundf(fmodf(angle_deg + 360.f, 360.f) / 30.f) % LED_COUNT;
    for (uint i = 0; i < 4; ++i) led_byte(0);
    for (uint led = 0; led < LED_COUNT; ++led) {
        uint8_t bright = (led == on) ? (uint8_t)(0xe0u | LED_BRIGHT) : 0xe0u;
        led_byte(bright);
        led_byte(led == on ? 16 : 0);
        led_byte(0);
        led_byte(led == on ? 16 : 0);
    }
    for (uint i = 0; i < 8; ++i) led_byte(0xff);
    gpio_put(LED_CLK, 0);
    gpio_put(LED_DAT, 0);
    led_bearing_on = true;
}

static void link_init(void) {
    uart_init(uart0, LINK_BAUD);
    gpio_set_function(LINK_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(LINK_RX_PIN, GPIO_FUNC_UART);
    uart_set_hw_flow(uart0, false, false);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
}

static int channel_present(uint ch) {
    if (!accumulated_frames) return 0;
    float power = accumulated[ch].tone_power / (accumulated_frames / FRAMES);
    float reference = accumulated[ch].tone_reference / (accumulated_frames / FRAMES);
    return tone_is_present(power, reference, accumulated[ch].clips);
}

static void link_send_feat(int rx_stall) {
    char line[240];
    float phase[6] = {0}, coherence[6] = {0};
    int present[6] = {0}, center = 0;
    if (accumulated_frames) {
        center = channel_present(7);
        for (uint ch = 0; ch < 6; ++ch) {
            float re = accumulated[ch].cross_re, im = accumulated[ch].cross_im;
            float den = sqrtf(accumulated[ch].tone_power * accumulated[7].tone_power);
            coherence[ch] = den > 0 ? fminf(1, sqrtf(re * re + im * im) / den) : 0;
            phase[ch] = atan2f(im, re);
            present[ch] = channel_present(ch);
        }
    }
    snprintf(line, sizeof line,
        "FEAT,v1,%" PRIu32 ",%u,%" PRIu32 ",%d,%" PRIu32
        ",%.6f,%.4f,%d,%.6f,%.4f,%d,%.6f,%.4f,%d,%.6f,%.4f,%d,%.6f,%.4f,%d,%.6f,%.4f,%d,%d\n",
        report_sequence, tone_frequency, dropped_buffers, rx_stall, accumulated_frames,
        phase[0], coherence[0], present[0], phase[1], coherence[1], present[1],
        phase[2], coherence[2], present[2], phase[3], coherence[3], present[3],
        phase[4], coherence[4], present[4], phase[5], coherence[5], present[5], center);
    uart_puts(uart0, line);
}

static void apply_doa_line(const char *line) {
    unsigned long seq = 0, age = 0;
    int valid = 0;
    char reason[32];
    float angle = 0, quality = 0;
    if (sscanf(line, "DOA,v1,%lu,%lu,%d,%31[^,],%f,%f", &seq, &age, &valid, reason, &angle, &quality) != 6)
        return;
    if (valid == 1 && isfinite(angle) && isfinite(quality) && quality >= 0 && quality <= 1 && age <= 400) {
        last_valid_doa_us = time_us_32();
        led_show_bearing(angle);
        return;
    }
    led_ring_off();
}

static void link_poll(void) {
    while (uart_is_readable(uart0)) {
        char c = (char)uart_getc(uart0);
        if (c == '\r' || c == '\n') {
            if (link_used) {
                link_line[link_used] = 0;
                apply_doa_line(link_line);
                link_used = 0;
            }
        } else if (c >= 32 && c < 127 && link_used + 1 < sizeof link_line) {
            link_line[link_used++] = c;
        }
    }
    if (led_bearing_on && (uint32_t)(time_us_32() - last_valid_doa_us) > LED_STALE_US)
        led_ring_off();
}

static void capture_irq(void) {
    const uint32_t mask = (1u << channels[0]) | (1u << channels[1]);
    uint32_t completed = dma_hw->ints0 & mask;
    dma_hw->ints0 = completed;
    if (!running) return;
    for (int done = 0; done < 2; ++done) {
        if (!(completed & (1u << channels[done]))) continue;
        int other = done ^ 1; // Hardware has already chained to this buffer.
        if (ready[other]) { ready[other] = false; ++dropped_buffers; }
        if (processing_buffer == other) { processing_corrupted = true; ++dropped_buffers; }
        ready[done] = true;
        dma_channel_set_write_addr(channels[done], buffers[done], false);
        dma_channel_set_trans_count(channels[done], WORDS, false);
    }
    // Recover if IRQ service was delayed beyond both buffers and a chain found
    // a channel that had not yet been rearmed. Report the gap, never hide it.
    if (!dma_channel_is_busy(channels[0]) && !dma_channel_is_busy(channels[1])) {
        ready[0] = false;
        if (processing_buffer == 0) processing_corrupted = true;
        ++dropped_buffers;
        dma_start_channel_mask(1u << channels[0]);
    }
}

static void stop_capture(void) {
    running = false;
    pio_sm_set_enabled(capture_pio, sm, false);
    for (int i = 0; i < 2; ++i) dma_channel_set_irq0_enabled(channels[i], false);
    for (int i = 0; i < 2; ++i) dma_channel_abort(channels[i]);
    dma_hw->ints0 = (1u << channels[0]) | (1u << channels[1]);
    capture_pio->fdebug = 1u << sm; // RXSTALL is write-one-to-clear.
    ready[0] = ready[1] = false;
    processing_buffer = -1;
    pio_sm_clear_fifos(capture_pio, sm);
    pio_sm_set_pins_with_mask(capture_pio, sm, 0, (1u << BCLK_PIN) | (1u << WS_PIN));
}

static void start_capture(void) {
    if (running) { puts("ALREADY_RUNNING"); return; }
    led_ring_off();
    dropped_buffers = accumulated_frames = 0;
    maximum_process_us = 0;
    report_sequence = 0;
    ready[0] = ready[1] = false;
    processing_buffer = -1;
    reset_stats(accumulated);
    pio_sm_clear_fifos(capture_pio, sm);
    pio_sm_restart(capture_pio, sm);
    pio_sm_clkdiv_restart(capture_pio, sm);
    pio_sm_exec(capture_pio, sm, pio_encode_jmp(program_offset));
    for (int i = 0; i < 2; ++i) {
        dma_channel_config config = dma_channel_get_default_config(channels[i]);
        channel_config_set_transfer_data_size(&config, DMA_SIZE_32);
        channel_config_set_read_increment(&config, false);
        channel_config_set_write_increment(&config, true);
        channel_config_set_dreq(&config, pio_get_dreq(capture_pio, sm, false));
        channel_config_set_chain_to(&config, channels[i ^ 1]);
        dma_channel_configure(channels[i], &config, buffers[i], &capture_pio->rxf[sm], WORDS, false);
        dma_channel_set_irq0_enabled(channels[i], true);
    }
    dma_hw->ints0 = (1u << channels[0]) | (1u << channels[1]);
    capture_pio->fdebug = 1u << sm;
    warm_until = make_timeout_time_ms(100);
    report_at = make_timeout_time_ms(350);
    running = true;
    dma_start_channel_mask(1u << channels[0]);
    pio_sm_set_enabled(capture_pio, sm, true);
    puts("STARTED fs=48000 BCLK=3072000; warming_up=100ms; synchronous_phase_output");
}

// Gather one lane from eight MSB-first four-bit samples packed by PIO.
static inline uint32_t gather_byte(uint32_t word, uint lane) {
    uint32_t x = (word >> lane) & 0x11111111u;
    x = (x | (x >> 3)) & 0x03030303u;
    x = (x | (x >> 6)) & 0x000f000fu;
    return (x | (x >> 12)) & 0xffu;
}
static inline int32_t sample16(const volatile uint32_t *slot, uint lane) {
    uint32_t raw = (gather_byte(slot[0], lane) << 16) |
                   (gather_byte(slot[1], lane) << 8) | gather_byte(slot[2], lane);
    int32_t signed24 = (int32_t)(raw << 8) >> 8;
    return signed24 >> 8; // Keep 16 significant bits for lightweight diagnostics.
}

static void unpack_raw_buffer(int index) {
    const volatile uint32_t *data=buffers[index];
    for(uint frame=0;frame<FRAMES;++frame) {
        for(uint ch=0;ch<RAW_CHANNELS;++ch) {
            uint slot=ch==6?7:ch;
            raw_audio[raw_frames+frame][ch]=(int16_t)sample16(data+frame*8+(slot%2)*4,slot/2);
        }
    }
}
static void send_raw_audio(void) {
    bool stall=(capture_pio->fdebug&(1u<<sm))!=0;
    raw_recording=false;
    uint32_t capture_us=time_us_32()-raw_request_started_us;
    uint32_t crc_started_us=time_us_32();
    uint32_t crc=raw_crc32(raw_audio,sizeof(raw_audio));
    uint32_t crc_us=time_us_32()-crc_started_us;
    ++raw_sequence;
    printf("AUDIO frames=%u fs=48000 channels=7 bytes=%u seq=%" PRIu32 " dropped=%" PRIu32 " rx_stall=%d process_us=%" PRIu32 " crc32=%08" PRIx32 " capture_us=%" PRIu32 " crc_us=%" PRIu32 "\n",
        RAW_FRAMES,(unsigned)sizeof(raw_audio),raw_sequence,dropped_buffers,stall,maximum_process_us,crc,capture_us,crc_us);
    uint32_t tx_started_us=time_us_32();
    fwrite(raw_audio,1,sizeof(raw_audio),stdout);
    // SDK printf bypasses newlib's FILE buffer. Flush the final binary bytes
    // before emitting the textual trailer, otherwise its order can be reversed.
    fflush(stdout);
    uint32_t tx_us=time_us_32()-tx_started_us;
    printf("\nAUDIO_END seq=%" PRIu32 "\n",raw_sequence);
    fflush(stdout);
    printf("AUDIO_TIMING seq=%" PRIu32 " capture_us=%" PRIu32 " crc_us=%" PRIu32 " tx_us=%" PRIu32 " fifo=%u ep=%u\n",
        raw_sequence,capture_us,crc_us,tx_us,CFG_TUD_CDC_TX_BUFSIZE,CFG_TUD_CDC_EP_BUFSIZE);
}

static void process_one_buffer(int index, channel_stats *stats) {
    reset_stats(stats);
    tone_accumulator tones[8] = {0};
    const volatile uint32_t *data = buffers[index];
    for (uint frame = 0; frame < FRAMES; ++frame) {
        for (uint lane = 0; lane < 4; ++lane) {
            for (uint lr = 0; lr < 2; ++lr) {
                uint ch = lane * 2 + lr;
                int32_t value = sample16(data + frame * 8 + lr * 4, lane);
                stats[ch].sum += value;
                stats[ch].sum_sq += (uint32_t)(value * value);
                if (value < stats[ch].minimum) stats[ch].minimum = value;
                if (value > stats[ch].maximum) stats[ch].maximum = value;
                stats[ch].zeros += value == 0;
                stats[ch].clips += value >= 32760 || value <= -32760;
                if (ch != 6) tone_push(&tones[ch], value, frame);
            }
        }
    }
    for (uint ch = 0; ch < 8; ++ch) {
        stats[ch].tone_power = tone_power(&tones[ch], stats[ch].sum);
        stats[ch].tone_reference = tone_reference_power(&tones[ch], stats[ch].sum);
    }
    // Cross spectra share exactly the same captured frames; common tone phase
    // cancels before blocks are averaged. Channel 7 is the central microphone.
    float ref_re,ref_im;
    tone_complex(&tones[7],stats[7].sum,&ref_re,&ref_im);
    for(uint ch=0;ch<6;++ch) {
        float re,im;
        tone_complex(&tones[ch],stats[ch].sum,&re,&im);
        stats[ch].cross_re=2*(re*ref_re+im*ref_im);
        stats[ch].cross_im=2*(im*ref_re-re*ref_im);
    }
}
static void merge_stats(const channel_stats *stats) {
    for (uint ch = 0; ch < 8; ++ch) {
        accumulated[ch].sum += stats[ch].sum;
        accumulated[ch].sum_sq += stats[ch].sum_sq;
        accumulated[ch].zeros += stats[ch].zeros;
        accumulated[ch].clips += stats[ch].clips;
        accumulated[ch].tone_power += stats[ch].tone_power;
        accumulated[ch].tone_reference += stats[ch].tone_reference;
        accumulated[ch].cross_re += stats[ch].cross_re;
        accumulated[ch].cross_im += stats[ch].cross_im;
        if (stats[ch].minimum < accumulated[ch].minimum) accumulated[ch].minimum = stats[ch].minimum;
        if (stats[ch].maximum > accumulated[ch].maximum) accumulated[ch].maximum = stats[ch].maximum;
    }
    accumulated_frames += FRAMES;
}
static void print_stats(int rx_stall) {
    printf("FRAME frames=%" PRIu32 " fs=48000 dropped=%" PRIu32 " rx_stall=%d end_us=%" PRIu64 " process_us=%" PRIu32 " seq=%" PRIu32 "\n", accumulated_frames, dropped_buffers, rx_stall, time_us_64(),maximum_process_us,report_sequence);
    capture_pio->fdebug = 1u << sm;
    maximum_process_us = 0;
    if (!accumulated_frames) {
        printf("PHASE_END seq=%" PRIu32 " freq=%u\n",report_sequence,tone_frequency);
        return;
    }
    puts("CH,label,rms16,dBFS,min,max,zero_pct,clips");
    for (uint ch = 0; ch < 8; ++ch) {
        float mean = (float)accumulated[ch].sum / accumulated_frames;
        float variance = (float)accumulated[ch].sum_sq / accumulated_frames - mean * mean;
        float rms = sqrtf(variance > 0 ? variance : 0);
        float dbfs = rms > 0 ? 20.0f * log10f(rms / 32768.0f) : -120.0f;
        printf("CH,%s,%.1f,%.1f,%" PRId32 ",%" PRId32 ",%.1f,%" PRIu32 "\n",
               names[ch], rms, dbfs, accumulated[ch].minimum, accumulated[ch].maximum,
               100.0f * accumulated[ch].zeros / accumulated_frames, accumulated[ch].clips);
        if (ch != 6) {
            float power = accumulated[ch].tone_power / (accumulated_frames / FRAMES);
            float ratio = variance > 0 ? fminf(1, power / variance) : 0;
            float reference = accumulated[ch].tone_reference / (accumulated_frames / FRAMES);
            float snr = 10.0f*log10f(fmaxf(power,0.000001f)/fmaxf(reference,0.000001f));
            printf("TONE,%s,%u,%.1f,%.3f,%.1f,%d\n", names[ch], tone_frequency,
                   sqrtf(power), ratio, snr, tone_is_present(power, reference, accumulated[ch].clips));
        }
        if(ch<6) {
            float re=accumulated[ch].cross_re,im=accumulated[ch].cross_im;
            float denominator=sqrtf(accumulated[ch].tone_power*accumulated[7].tone_power);
            float coherence=denominator>0?fminf(1,sqrtf(re*re+im*im)/denominator):0;
            printf("PHASE,%s,%u,%" PRIu32 ",%.6f,%.4f\n",names[ch],tone_frequency,report_sequence,
                   atan2f(im,re),coherence);
        }
    }
    printf("PHASE_END seq=%" PRIu32 " freq=%u\n",report_sequence,tone_frequency);
    reset_stats(accumulated);
    accumulated_frames = 0;
}

static void report_features(bool usb) {
    bool rx_stall = (capture_pio->fdebug & (1u << sm)) != 0;
    ++report_sequence;
    link_send_feat(rx_stall ? 1 : 0);
    if (usb) print_stats(rx_stall ? 1 : 0);
    else {
        capture_pio->fdebug = 1u << sm;
        maximum_process_us = 0;
        reset_stats(accumulated);
        accumulated_frames = 0;
    }
}

static void banner(void) {
    printf("SEN0325_SETUP v0.7-LINK; state=%s; GPIO logic=3.3V; tone_hz=%u; phase_reference=D3R_CENTER; transport=RX2; usb_fifo=%u; usb_ep_buffer=%u\n", running ? "RUNNING" : "IDLE", tone_frequency,CFG_TUD_CDC_TX_BUFSIZE,CFG_TUD_CDC_EP_BUFSIZE);
    puts("D0=GP6 D1=GP7 D2=GP8 D3=GP9 BCLK=GP10 WS=GP11 LED_CK=GP12 LED_DA=GP13 LINK_TX=GP0 LINK_RX=GP1");
    puts("Commands: START STOP RECORD STATUS LEDOFF HELP FREQ <300..22000> TONECHECK DOACHECK CRC32CHECK");
    puts("START only after wiring/power checks. UART0 FEAT goes to ESP32; USB RECORD path is unchanged. No motor commands.");
}
static void tone_check(void) {
    if (running) { puts("TONECHECK STOP_FIRST"); return; }
    unsigned saved = tone_frequency;
    tone_configure(1000);
    const unsigned sources[] = {0, 500, 850, 1000, 1150, 2000};
    for (unsigned test = 0; test < 6; ++test) {
        tone_accumulator state = {0};
        int64_t sum = 0, sum_sq = 0;
        for (unsigned i = 0; i < TONE_N; ++i) {
            int32_t value = 6000 + (sources[test] ? (int32_t)lround(1000 * sin(6.283185307179586 * sources[test] * i / TONE_FS)) : 0);
            sum += value;
            sum_sq += value * value;
            tone_push(&state, value, i);
        }
        float mean = (float)sum / TONE_N;
        float total = (float)sum_sq / TONE_N - mean * mean;
        float power = tone_power(&state, sum);
        bool detected = tone_is_present(power, tone_reference_power(&state,sum), 0);
        bool expected = sources[test] == 1000;
        printf("TONECHECK source=%u target=1000 rms=%.2f ratio=%.3f detected=%d pass=%d\n",
               sources[test], sqrtf(power), total > 0 ? power / total : 0, detected, detected == expected);
    }
    tone_configure(saved);
    puts("TONECHECK DONE");
}
static void command(char *line) {
    for (char *p = line; *p; ++p) *p = (char)toupper((unsigned char)*p);
    if (!strcmp(line, "START")) { raw_recording=raw_stream=false; start_capture(); }
    else if (!strcmp(line, "STOP")) { stop_capture(); raw_recording=raw_stream=false; led_ring_off(); puts("STOPPED; clocks LOW"); }
    else if (!strcmp(line, "RECORD")) {
        if(running && !raw_stream) {puts("RECORD STOP_FIRST");return;}
        raw_request_started_us=time_us_32();
        raw_frames=0;
        if(!running) {
            start_capture();
            warm_until=make_timeout_time_ms(500);
        } else {
            uint32_t irq_state=save_and_disable_interrupts();
            ready[0]=ready[1]=false;
            dropped_buffers=maximum_process_us=0;
            capture_pio->fdebug=1u<<sm;
            restore_interrupts(irq_state);
        }
        raw_stream=true;
        raw_recording=true;
        puts("RAW_STARTED frames=4096 channels=7");
    }
    else if (!strcmp(line, "CRC32CHECK")) {
        if(running) {puts("CRC32CHECK STOP_FIRST");return;}
        uint8_t ramp[256];
        for(uint i=0;i<sizeof(ramp);++i) ramp[i]=(uint8_t)i;
        printf("CRC32CHECK standard=%08" PRIx32 " empty=%08" PRIx32 " ramp=%08" PRIx32 "\n",
            raw_crc32("123456789",9),raw_crc32("",0),raw_crc32(ramp,sizeof(ramp)));
    }
    else if (!strcmp(line, "STATUS")) printf("STATUS running=%d dropped=%" PRIu32 "\n", running, dropped_buffers);
    else if (!strcmp(line, "LEDOFF")) { led_ring_off(); puts("LED_RING_OFF"); }
    else if (!strcmp(line, "HELP")) banner();
    else if (!strcmp(line, "TONECHECK")) tone_check();
    else if (!strcmp(line, "DOACHECK")) {
        if(running) {puts("DOACHECK STOP_FIRST");return;}
        unsigned saved=tone_frequency;
        tone_configure(1000);
        const unsigned directions[]={0,45,90,180,270};
        for(unsigned test=0;test<5;++test) {
            tone_accumulator synthetic[7]={0};
            int64_t sums[7]={0};
            for(unsigned frame=0;frame<FRAMES;++frame) {
                double clock_phase=6.283185307179586*1000*frame/SAMPLE_RATE;
                for(unsigned ch=0;ch<7;++ch) {
                    double delta=ch==6?0:6.283185307179586*1000/343*.04*cos((directions[test]-ch*60.0)*3.141592653589793/180);
                    int32_t value=6000+(int32_t)lround(1000*cos(clock_phase+delta));
                    sums[ch]+=value;
                    tone_push(&synthetic[ch],value,frame);
                }
            }
            float ref_re,ref_im;
            tone_complex(&synthetic[6],sums[6],&ref_re,&ref_im);
            for(unsigned ch=0;ch<6;++ch) {
                float re,im;
                tone_complex(&synthetic[ch],sums[ch],&re,&im);
                printf("PHASECHECK,%u,%s,%.6f\n",directions[test],names[ch],atan2f(im*ref_re-re*ref_im,re*ref_re+im*ref_im));
            }
        }
        tone_configure(saved);
        puts("PHASECHECK DONE");
    }
    else if (!strncmp(line, "FREQ ", 5)) {
        unsigned value; char extra;
        if (running) puts("FREQ ERROR STOP_FIRST");
        else if (sscanf(line + 5, "%u %c", &value, &extra) != 1 || !tone_configure(value)) puts("FREQ ERROR RANGE=300..22000");
        else printf("FREQ OK hz=%u\n", tone_frequency);
    }
    else if (*line) puts("UNKNOWN_COMMAND; use HELP");
}

int main(void) {
    set_sys_clock_khz(120000, true); // Gives an exact 48 kHz divider (19 + 136/256).
    for (uint pin = LED_CLK; pin <= LED_DAT; ++pin) { gpio_init(pin); gpio_put(pin, 0); gpio_set_dir(pin, GPIO_OUT); }
    for (uint pin = DATA_BASE; pin < DATA_BASE + 4; ++pin) {
        pio_gpio_init(capture_pio, pin);
        gpio_pull_down(pin); // Discharge the shared I2S line during its tri-state padding.
    }
    for (uint pin = BCLK_PIN; pin <= WS_PIN; ++pin) pio_gpio_init(capture_pio, pin);
    sm = pio_claim_unused_sm(capture_pio, true);
    program_offset = pio_add_program(capture_pio, &sen0325_i2s_program);
    pio_sm_config config = sen0325_i2s_program_get_default_config(program_offset);
    sm_config_set_in_pins(&config, DATA_BASE);
    sm_config_set_sideset_pins(&config, BCLK_PIN);
    sm_config_set_in_shift(&config, false, true, 32);
    sm_config_set_fifo_join(&config, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&config, (float)clock_get_hz(clk_sys) / (SAMPLE_RATE * 128.0f));
    pio_sm_set_consecutive_pindirs(capture_pio, sm, DATA_BASE, 4, false);
    pio_sm_set_consecutive_pindirs(capture_pio, sm, BCLK_PIN, 2, true);
    pio_sm_init(capture_pio, sm, program_offset, &config);
    pio_sm_set_pins_with_mask(capture_pio, sm, 0, (1u << BCLK_PIN) | (1u << WS_PIN));
    channels[0] = dma_claim_unused_channel(true);
    channels[1] = dma_claim_unused_channel(true);
    irq_set_exclusive_handler(DMA_IRQ_0, capture_irq);
    irq_set_priority(DMA_IRQ_0, PICO_HIGHEST_IRQ_PRIORITY);
    irq_set_enabled(DMA_IRQ_0, true);
    stdio_init_all();
    // Binary audio must never have LF bytes translated to CRLF.
    stdio_set_translate_crlf(&stdio_usb,false);
    link_init();
    tone_configure(1000);
    led_ring_off();
    reset_stats(accumulated);
    bool was_connected = false;
    char line[40];
    size_t used = 0;
    while (true) {
        bool connected = stdio_usb_connected();
        if (connected && !was_connected) banner();
        was_connected = connected;
        int ch;
        while ((ch = getchar_timeout_us(0)) >= 0) {
            if (ch == '\r' || ch == '\n') { line[used] = 0; command(line); used = 0; }
            else if (ch == 8 || ch == 127) { if (used) --used; }
            else if (ch >= 32 && ch < 127 && used + 1 < sizeof(line)) line[used++] = (char)ch;
        }
        link_poll();
        if (running) {
            for (int i = 0; i < 2; ++i) {
                uint32_t irq_state = save_and_disable_interrupts();
                bool take = ready[i] && !dma_channel_is_busy(channels[i]);
                if (take) { ready[i] = false; processing_buffer = i; processing_corrupted = false; }
                restore_interrupts(irq_state);
                if (!take) continue;
                if (time_reached(warm_until)) {
                    channel_stats local[8];
                    uint32_t process_started = time_us_32();
                    if(raw_recording) unpack_raw_buffer(i);
                    else if(!raw_stream) process_one_buffer(i, local);
                    uint32_t elapsed = time_us_32()-process_started;
                    if (elapsed > maximum_process_us) maximum_process_us = elapsed;
                    irq_state = save_and_disable_interrupts();
                    bool valid = !processing_corrupted && !dma_channel_is_busy(channels[i]);
                    processing_buffer = -1;
                    restore_interrupts(irq_state);
                    if (valid) {
                        if(raw_recording) {
                            raw_frames+=FRAMES;
                            if(raw_frames>=RAW_FRAMES) {send_raw_audio();break;}
                        } else if(!raw_stream) merge_stats(local);
                    }
                } else processing_buffer = -1;
            }
            if (running && !raw_stream && time_reached(report_at)) {
                report_features(connected);
                report_at = make_timeout_time_ms(250);
            }
        }
        sleep_us(50);
    }
}
