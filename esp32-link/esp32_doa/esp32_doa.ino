#include "phase_doa.h"

#ifndef PIC_RX
#define PIC_RX 16
#endif
#ifndef PIC_TX
#define PIC_TX 17
#endif

static doa_state estimator;
static char line[240];
static size_t used;

static void handle_line(const char *text) {
    feat_msg feat;
    doa_msg doa;
    char out[96];
    if (!parse_feat(text, &feat)) return;
    estimate_doa(&estimator, &feat, millis() * 0.001f, &doa);
    format_doa(&doa, out, sizeof out);
    Serial2.print(out);
    Serial.print(out);
}

void setup() {
    memset(&estimator, 0, sizeof estimator);
    Serial.begin(115200);
    Serial2.begin(115200, SERIAL_8N1, PIC_RX, PIC_TX);
    Serial.println("EE475 ESP32 DOA display; no motor output");
}

void loop() {
    while (Serial2.available() > 0) {
        char c = (char)Serial2.read();
        if (c == '\r' || c == '\n') {
            if (used) {
                line[used] = 0;
                handle_line(line);
                used = 0;
            }
        } else if (c >= 32 && c < 127 && used + 1 < sizeof line) {
            line[used++] = c;
        }
    }
}
