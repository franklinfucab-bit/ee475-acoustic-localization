#ifndef EE475_PHASE_DOA_H
#define EE475_PHASE_DOA_H

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { DOA_OUTER = 6, DOA_MIN_HZ = 300, DOA_MAX_HZ = 2000 };
#define DOA_RADIUS_M 0.04f
#define DOA_SOUND_M_S 343.0f
#define DOA_PI 3.141592653589793f

typedef struct {
    uint32_t seq;
    unsigned freq;
    uint32_t dropped;
    int rx_stall;
    uint32_t frames;
    float phase[DOA_OUTER];
    float coherence[DOA_OUTER];
    int present[DOA_OUTER];
    int center_present;
} feat_msg;

typedef struct {
    uint32_t seq;
    uint32_t age_ms;
    int valid;
    const char *reason;
    float angle_deg;
    float quality;
} doa_msg;

typedef struct {
    uint32_t previous_dropped;
    int have_dropped;
    float smooth_x, smooth_y;
    int have_smooth;
    float last_valid_s;
} doa_state;

static const float doa_bearings_deg[DOA_OUTER] = {0.f, 60.f, 120.f, 180.f, 240.f, 300.f};

static float doa_wrap_pi(float angle) {
    float two_pi = 2.f * DOA_PI;
    float x = angle + DOA_PI;
    x -= two_pi * floorf(x / two_pi);
    return x - DOA_PI;
}

static int doa_solve3(const float matrix[3][3], const float vector[3], float out[3]) {
    float rows[3][4];
    int col, i, pivot;
    for (i = 0; i < 3; ++i) {
        rows[i][0] = matrix[i][0];
        rows[i][1] = matrix[i][1];
        rows[i][2] = matrix[i][2];
        rows[i][3] = vector[i];
    }
    for (col = 0; col < 3; ++col) {
        pivot = col;
        for (i = col + 1; i < 3; ++i)
            if (fabsf(rows[i][col]) > fabsf(rows[pivot][col])) pivot = i;
        if (fabsf(rows[pivot][col]) < 1e-12f) return 0;
        if (pivot != col)
            for (i = 0; i < 4; ++i) {
                float tmp = rows[col][i];
                rows[col][i] = rows[pivot][i];
                rows[pivot][i] = tmp;
            }
        {
            float scale = rows[col][col];
            for (i = 0; i < 4; ++i) rows[col][i] /= scale;
        }
        for (i = 0; i < 3; ++i) {
            float scale;
            if (i == col) continue;
            scale = rows[i][col];
            {
                int j;
                for (j = 0; j < 4; ++j) rows[i][j] -= scale * rows[col][j];
            }
        }
    }
    out[0] = rows[0][3];
    out[1] = rows[1][3];
    out[2] = rows[2][3];
    return 1;
}

typedef struct {
    float row[3];
    float value;
    float weight0;
    float weight;
    float coherence;
    int used;
} doa_obs;

static int doa_fit_rows(doa_obs *rows, int count, float k, float fit[3], float *rms) {
    float weights[DOA_OUTER];
    int pass, i, a, b;
    if (count < 3) return 0;
    for (i = 0; i < count; ++i) weights[i] = rows[i].weight0;
    for (pass = 0; pass < 3; ++pass) {
        float matrix[3][3] = {{0}};
        float vector[3] = {0};
        float residuals[DOA_OUTER];
        for (i = 0; i < count; ++i) {
            for (a = 0; a < 3; ++a) {
                vector[a] += weights[i] * rows[i].row[a] * rows[i].value;
                for (b = 0; b < 3; ++b)
                    matrix[a][b] += weights[i] * rows[i].row[a] * rows[i].row[b];
            }
        }
        if (!doa_solve3(matrix, vector, fit)) return 0;
        for (i = 0; i < count; ++i) {
            float pred = rows[i].row[0] * fit[0] + rows[i].row[1] * fit[1] + rows[i].row[2] * fit[2];
            residuals[i] = k * (pred - rows[i].value);
            weights[i] = rows[i].weight0 * fminf(1.f, 0.15f / fmaxf(fabsf(residuals[i]), 1e-9f));
        }
        if (pass == 2) {
            float num = 0, den = 0;
            for (i = 0; i < count; ++i) {
                num += rows[i].weight0 * residuals[i] * residuals[i];
                den += rows[i].weight0;
            }
            *rms = sqrtf(num / den);
        }
    }
    return 1;
}

static void doa_invalid(doa_msg *out, uint32_t seq, const char *reason) {
    out->seq = seq;
    out->age_ms = 0;
    out->valid = 0;
    out->reason = reason;
    out->angle_deg = 0.f;
    out->quality = 0.f;
}

static void estimate_doa(doa_state *st, const feat_msg *feat, float now_s, doa_msg *out) {
    doa_obs obs[DOA_OUTER];
    doa_obs kept[DOA_OUTER];
    float k, fit[3], residual, magnitude, coherence, quality, raw_angle, angle;
    int n = 0, i, count;
    int gap = st->have_dropped && feat->dropped > st->previous_dropped;
    st->previous_dropped = feat->dropped;
    st->have_dropped = 1;
    if (feat->freq < DOA_MIN_HZ || feat->freq > DOA_MAX_HZ) {
        doa_invalid(out, feat->seq, "frequency_outside_doa_range");
        return;
    }
    if (gap || feat->rx_stall || feat->frames == 0) {
        doa_invalid(out, feat->seq, "capture_gap");
        return;
    }
    if (!feat->center_present) {
        doa_invalid(out, feat->seq, "no_reference_tone");
        return;
    }
    k = 2.f * DOA_PI * (float)feat->freq / DOA_SOUND_M_S;
    for (i = 0; i < DOA_OUTER; ++i) {
        float bearing, phi;
        if (!feat->present[i] || feat->coherence[i] < 0.7f) continue;
        bearing = doa_bearings_deg[i] * DOA_PI / 180.f;
        phi = doa_wrap_pi(feat->phase[i]);
        obs[n].row[0] = DOA_RADIUS_M * sinf(bearing);
        obs[n].row[1] = DOA_RADIUS_M * cosf(bearing);
        obs[n].row[2] = 1.f;
        obs[n].value = -phi / k;
        obs[n].weight0 = feat->coherence[i] * feat->coherence[i];
        obs[n].coherence = feat->coherence[i];
        obs[n].used = 1;
        ++n;
    }
    if (n < 4) {
        doa_invalid(out, feat->seq, "insufficient_coherent_channels");
        return;
    }
    if (!doa_fit_rows(obs, n, k, fit, &residual)) {
        doa_invalid(out, feat->seq, "degenerate_geometry");
        return;
    }
    count = n;
    memcpy(kept, obs, sizeof obs);
    if (n == 6 && residual > 0.15f) {
        int best_omit = -1;
        float best_err = 0, best_fit[3];
        for (i = 0; i < 6; ++i) {
            doa_obs remain[5];
            float cand[3], err, held, mag;
            int j, m = 0;
            for (j = 0; j < 6; ++j) if (j != i) remain[m++] = obs[j];
            if (!doa_fit_rows(remain, 5, k, cand, &err)) continue;
            held = fabsf(k * (obs[i].row[0] * cand[0] + obs[i].row[1] * cand[1] + obs[i].row[2] * cand[2] - obs[i].value));
            mag = hypotf(cand[0], cand[1]);
            if (mag >= 0.25f && mag <= 1.35f && err <= 0.12f && err < residual / 2.f && held > fmaxf(0.35f, 4.f * err)) {
                if (best_omit < 0 || err < best_err) {
                    best_omit = i;
                    best_err = err;
                    memcpy(best_fit, cand, sizeof best_fit);
                }
            }
        }
        if (best_omit >= 0) {
            int m = 0;
            residual = best_err;
            memcpy(fit, best_fit, sizeof fit);
            for (i = 0; i < 6; ++i) if (i != best_omit) kept[m++] = obs[i];
            count = 5;
        }
    }
    magnitude = hypotf(fit[0], fit[1]);
    coherence = 0.f;
    for (i = 0; i < count; ++i) coherence += kept[i].coherence;
    coherence /= (float)count;
    quality = coherence * expf(-0.5f * (residual / 0.20f) * (residual / 0.20f)) *
              fminf(1.f, magnitude / 0.55f) * (float)count / 6.f;
    if (magnitude < 0.25f) {
        doa_invalid(out, feat->seq, "weak_horizontal_direction");
        return;
    }
    if (magnitude > 1.35f || residual > 0.25f || quality < 0.45f) {
        doa_invalid(out, feat->seq, "phase_model_mismatch");
        return;
    }
    raw_angle = fmodf(atan2f(fit[0], fit[1]) * 180.f / DOA_PI + 360.f, 360.f);
    angle = raw_angle;
    {
        float vx = sinf(angle * DOA_PI / 180.f);
        float vy = cosf(angle * DOA_PI / 180.f);
        if (st->have_smooth && (now_s - st->last_valid_s) < 0.8f) {
            float dt = fmaxf(0.001f, now_s - st->last_valid_s);
            float alpha = 1.f - expf(-dt / 0.35f);
            vx = st->smooth_x * (1.f - alpha) + vx * alpha;
            vy = st->smooth_y * (1.f - alpha) + vy * alpha;
        }
        {
            float mag = hypotf(vx, vy);
            if (mag > 1e-8f) { vx /= mag; vy /= mag; }
        }
        st->smooth_x = vx;
        st->smooth_y = vy;
        st->have_smooth = 1;
        st->last_valid_s = now_s;
        angle = fmodf(atan2f(vx, vy) * 180.f / DOA_PI + 360.f, 360.f);
    }
    out->seq = feat->seq;
    out->age_ms = 0;
    out->valid = 1;
    out->reason = "estimated";
    out->angle_deg = angle;
    out->quality = fminf(1.f, quality);
}

static int parse_feat(const char *line, feat_msg *out) {
    unsigned long seq = 0, dropped = 0, frames = 0;
    int n;
    memset(out, 0, sizeof *out);
    n = sscanf(line,
        "FEAT,v1,%lu,%u,%lu,%d,%lu,"
        "%f,%f,%d,%f,%f,%d,%f,%f,%d,%f,%f,%d,%f,%f,%d,%f,%f,%d,%d",
        &seq, &out->freq, &dropped, &out->rx_stall, &frames,
        &out->phase[0], &out->coherence[0], &out->present[0],
        &out->phase[1], &out->coherence[1], &out->present[1],
        &out->phase[2], &out->coherence[2], &out->present[2],
        &out->phase[3], &out->coherence[3], &out->present[3],
        &out->phase[4], &out->coherence[4], &out->present[4],
        &out->phase[5], &out->coherence[5], &out->present[5],
        &out->center_present);
    out->seq = (uint32_t)seq;
    out->dropped = (uint32_t)dropped;
    out->frames = (uint32_t)frames;
    return n == 24;
}

static int parse_doa(const char *line, uint32_t *seq, uint32_t *age_ms, int *valid,
                     char *reason, size_t reason_n, float *angle, float *quality) {
    unsigned long s = 0, age = 0;
    if (sscanf(line, "DOA,v1,%lu,%lu,%d,%31[^,],%f,%f", &s, &age, valid, reason, angle, quality) != 6)
        return 0;
    if (reason_n) reason[reason_n - 1] = 0;
    *seq = (uint32_t)s;
    *age_ms = (uint32_t)age;
    return 1;
}

static int format_doa(const doa_msg *msg, char *buf, size_t n) {
    return snprintf(buf, n, "DOA,v1,%lu,%lu,%d,%s,%.1f,%.2f\n",
                    (unsigned long)msg->seq, (unsigned long)msg->age_ms, msg->valid,
                    msg->reason ? msg->reason : "unknown",
                    msg->valid ? msg->angle_deg : 0.f, msg->valid ? msg->quality : 0.f);
}

#endif
