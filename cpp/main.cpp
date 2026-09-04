#include <SDL2/SDL.h>
#include <ft2build.h>
#include FT_FREETYPE_H

#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <cmath>
#include <algorithm>
#include <map>
#include <mutex>
#include <cstdint>

// --- 16:10 Screen & Gameplay Viewport Constants ---
constexpr int INTERNAL_WIDTH = 1280;
constexpr int INTERNAL_HEIGHT = 800;

// Central Highway Gameplay Viewport
constexpr int GAME_X = 220;
constexpr int GAME_W = 600;
constexpr int ROAD_WIDTH = 420;
constexpr int ROAD_MARGIN = (GAME_W - ROAD_WIDTH) / 2; // 90px verges on left & right
constexpr int CAR_WIDTH = 40;
constexpr int CAR_HEIGHT = 70;
constexpr int TARGET_FPS = 60;
constexpr float STAGE_TRACK_LENGTH = 16000.0f;
constexpr float BASE_SCROLL_SPEED = 4.0f;
constexpr float FUEL_DEPLETION_RATE = 0.06f;
constexpr float FUEL_REWARD = 20.0f;
constexpr float FUEL_PENALTY = 15.0f;
constexpr float MAX_FUEL = 100.0f;

// Colors
const SDL_Color COLOR_BG             = {15, 18, 24, 255};   // Dark arcade bezel chassis
const SDL_Color COLOR_PANEL_BG       = {20, 25, 34, 255};   // Side panel card background
const SDL_Color COLOR_PANEL_BORDER   = {45, 56, 75, 255};   // Side panel border
const SDL_Color COLOR_GRASS_1        = {30, 117, 30, 255};
const SDL_Color COLOR_GRASS_2        = {38, 140, 38, 255};
const SDL_Color COLOR_WATER_DEEP     = {12, 42, 75, 255};   // Deep sea background
const SDL_Color COLOR_WATER_MID      = {22, 72, 122, 255};  // Main ocean body
const SDL_Color COLOR_WATER_SWELL    = {35, 102, 164, 255}; // Rolling wave swell
const SDL_Color COLOR_WATER_FOAM     = {200, 235, 255, 255};// Foam crests & sea spray
const SDL_Color COLOR_BRIDGE_SHADOW  = {7, 24, 44, 255};    // Ambient bridge deck shadow
const SDL_Color COLOR_WALKWAY        = {155, 160, 165, 255};// Concrete catwalk / walkway
const SDL_Color COLOR_WALKWAY_DARK   = {110, 115, 120, 255};// Walkway edge & joints
const SDL_Color COLOR_RAILING        = {65, 70, 75, 255};   // Steel railing & stanchions
const SDL_Color COLOR_BARRIER_RED    = {225, 40, 40, 255};
const SDL_Color COLOR_ROAD           = {85, 85, 85, 255};
const SDL_Color COLOR_LINE           = {255, 255, 255, 255};
const SDL_Color COLOR_EDGE           = {204, 204, 204, 255};
const SDL_Color COLOR_PLAYER         = {255, 51, 51, 255};
const SDL_Color COLOR_SAND           = {238, 208, 148, 255}; // Sunny golden beach sand
const SDL_Color COLOR_SAND_DUNE      = {220, 188, 128, 255}; // Sand dune ripple shadow
const SDL_Color COLOR_SAND_WET       = {196, 164, 112, 255}; // Wet sand along surf line
const SDL_Color COLOR_TROPICAL_DEEP  = {14, 86, 154, 255};   // Deep tropical azure sea
const SDL_Color COLOR_TROPICAL_MID   = {26, 146, 196, 255};  // Tropical turquoise sea
const SDL_Color COLOR_TROPICAL_SURF  = {60, 200, 225, 255};  // Shallow turquoise surf
const SDL_Color COLOR_TROPICAL_FOAM  = {240, 250, 255, 255}; // Foaming white wave crests
const SDL_Color COLOR_PALM_TRUNK     = {118, 76, 42, 255};   // Textured palm tree trunk
const SDL_Color COLOR_PALM_LEAF_1    = {26, 128, 38, 255};   // Vibrant tropical palm green
const SDL_Color COLOR_PALM_LEAF_2    = {45, 168, 52, 255};   // Bright sunlit palm frond

struct KanaData {
    std::string kana;
    std::string romaji;
    SDL_Color color;
};

// Stage 1: Vowels
const std::vector<KanaData> STAGE_1_KANA = {
    {"あ", "a", {51, 102, 255, 255}},   // Blue
    {"い", "i", {46, 204, 113, 255}},   // Green
    {"う", "u", {241, 196, 15, 255}},   // Yellow
    {"え", "e", {155, 89, 182, 255}},   // Purple
    {"お", "o", {230, 126, 34, 255}}    // Orange
};

// Stage 2: Ka-column
const std::vector<KanaData> STAGE_2_KANA = {
    {"か", "ka", {51, 102, 255, 255}},  // Blue
    {"き", "ki", {46, 204, 113, 255}},  // Green
    {"く", "ku", {241, 196, 15, 255}},  // Yellow
    {"け", "ke", {155, 89, 182, 255}},  // Purple
    {"こ", "ko", {230, 126, 34, 255}}   // Orange
};

// Stage 3: Sa-column
const std::vector<KanaData> STAGE_3_KANA = {
    {"さ", "sa",  {51, 102, 255, 255}},  // Blue
    {"し", "shi", {46, 204, 113, 255}},  // Green
    {"す", "su",  {241, 196, 15, 255}},  // Yellow
    {"せ", "se",  {155, 89, 182, 255}},  // Purple
    {"そ", "so",  {230, 126, 34, 255}}   // Orange
};

inline const std::vector<KanaData>& getStageKana(int stage) {
    if (stage == 1) return STAGE_1_KANA;
    if (stage == 2) return STAGE_2_KANA;
    return STAGE_3_KANA;
}

// Compute road boundaries for any world position within the gameplay viewport
inline void getRoadEdges(int stage, float worldY, float trackDist, float& outLeft, float& outRight) {
    constexpr float normalLeft = static_cast<float>(GAME_X + ROAD_MARGIN);
    constexpr float normalRight = static_cast<float>(GAME_X + GAME_W - ROAD_MARGIN);

    if (stage == 1 || trackDist >= STAGE_TRACK_LENGTH - 1200.0f) {
        outLeft = normalLeft;
        outRight = normalRight;
        return;
    }

    if (stage == 3) {
        // Stage 3: High-Speed Winding Curves & Chicanes
        constexpr float SEGMENT_LEN = 2400.0f;
        int segIdx = static_cast<int>(worldY / SEGMENT_LEN);
        float segPos = std::fmod(worldY, SEGMENT_LEN);
        if (segPos < 0.0f) segPos += SEGMENT_LEN;

        int pattern = std::abs(segIdx) % 4;
        float curveShift = 0.0f;
        float widthNarrow = 0.0f;

        if (pattern == 0) {
            // Sweeping long left turn
            if (segPos >= 400.0f && segPos < 800.0f) {
                float t = (segPos - 400.0f) / 400.0f;
                curveShift = -65.0f * (0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI)));
            } else if (segPos >= 800.0f && segPos < 1600.0f) {
                curveShift = -65.0f;
            } else if (segPos >= 1600.0f && segPos < 2000.0f) {
                float t = (segPos - 1600.0f) / 400.0f;
                curveShift = -65.0f * (0.5f + 0.5f * std::cos(t * static_cast<float>(M_PI)));
            }
        } else if (pattern == 1) {
            // Sweeping long right turn
            if (segPos >= 400.0f && segPos < 800.0f) {
                float t = (segPos - 400.0f) / 400.0f;
                curveShift = 70.0f * (0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI)));
            } else if (segPos >= 800.0f && segPos < 1600.0f) {
                curveShift = 70.0f;
            } else if (segPos >= 1600.0f && segPos < 2000.0f) {
                float t = (segPos - 1600.0f) / 400.0f;
                curveShift = 70.0f * (0.5f + 0.5f * std::cos(t * static_cast<float>(M_PI)));
            }
        } else if (pattern == 2) {
            // S-Chicane (rapid left then right)
            if (segPos >= 300.0f && segPos < 800.0f) {
                float t = (segPos - 300.0f) / 500.0f;
                curveShift = -60.0f * (0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI)));
            } else if (segPos >= 800.0f && segPos < 1300.0f) {
                float t = (segPos - 800.0f) / 500.0f;
                curveShift = -60.0f + 120.0f * (0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI)));
            } else if (segPos >= 1300.0f && segPos < 1800.0f) {
                float t = (segPos - 1300.0f) / 500.0f;
                curveShift = 60.0f * (0.5f + 0.5f * std::cos(t * static_cast<float>(M_PI)));
            }
            widthNarrow = 20.0f;
        } else {
            // Express Straightaway with elevated expressway narrows
            if (segPos >= 500.0f && segPos < 900.0f) {
                float t = (segPos - 500.0f) / 400.0f;
                widthNarrow = 30.0f * (0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI)));
            } else if (segPos >= 900.0f && segPos < 1700.0f) {
                widthNarrow = 30.0f;
            } else if (segPos >= 1700.0f && segPos < 2100.0f) {
                float t = (segPos - 1700.0f) / 400.0f;
                widthNarrow = 30.0f * (0.5f + 0.5f * std::cos(t * static_cast<float>(M_PI)));
            }
        }

        outLeft = normalLeft + curveShift + widthNarrow;
        outRight = normalRight + curveShift - widthNarrow;
        return;
    }

    // Stage 2: Elevated Coastal Highway Bridge
    constexpr float SEGMENT_LEN = 1600.0f;
    int segIdx = static_cast<int>(worldY / SEGMENT_LEN);
    float segPos = std::fmod(worldY, SEGMENT_LEN);
    if (segPos < 0.0f) segPos += SEGMENT_LEN;

    // Target narrow bounds for this segment
    float targetLeft = normalLeft;
    float targetRight = normalRight;

    int type = std::abs(segIdx) % 3;
    if (type == 0) {
        // Left pinch (curb narrows from left, width = 320)
        targetLeft = normalLeft + 100.0f;
    } else if (type == 1) {
        // Right pinch (curb narrows from right, width = 320)
        targetRight = normalRight - 100.0f;
    } else {
        // Center bottleneck bridge (width = 280)
        targetLeft = normalLeft + 70.0f;
        targetRight = normalRight - 70.0f;
    }

    // 0 - 450: Normal
    // 450 - 650: Taper in
    // 650 - 1250: Narrow street
    // 1250 - 1450: Taper out
    // 1450 - 1600: Normal
    if (segPos < 450.0f) {
        outLeft = normalLeft;
        outRight = normalRight;
    } else if (segPos < 650.0f) {
        float t = (segPos - 450.0f) / 200.0f;
        float smoothT = 0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI));
        outLeft = normalLeft + (targetLeft - normalLeft) * smoothT;
        outRight = normalRight + (targetRight - normalRight) * smoothT;
    } else if (segPos < 1250.0f) {
        outLeft = targetLeft;
        outRight = targetRight;
    } else if (segPos < 1450.0f) {
        float t = (segPos - 1250.0f) / 200.0f;
        float smoothT = 0.5f - 0.5f * std::cos(t * static_cast<float>(M_PI));
        outLeft = targetLeft + (normalLeft - targetLeft) * smoothT;
        outRight = targetRight + (normalRight - targetRight) * smoothT;
    } else {
        outLeft = normalLeft;
        outRight = normalRight;
    }
}

// --- Audio Synthesizer ---
class AudioEngine {
public:
    enum EngineState { ENG_OFF, ENG_LOW, ENG_MID, ENG_HIGH };

    AudioEngine() = default;
    ~AudioEngine() {
        if (deviceId) {
            SDL_CloseAudioDevice(deviceId);
        }
    }

    bool init() {
        SDL_AudioSpec desired, obtained;
        SDL_zero(desired);
        desired.freq = 44100;
        desired.format = AUDIO_S16SYS;
        desired.channels = 2;
        desired.samples = 512;
        desired.callback = audioCallback;
        desired.userdata = this;

        deviceId = SDL_OpenAudioDevice(nullptr, 0, &desired, &obtained, 0);
        if (!deviceId) {
            std::cerr << "Failed to open audio: " << SDL_GetError() << std::endl;
            return false;
        }

        // Pre-generate sound effects
        generateOneShots();
        SDL_PauseAudioDevice(deviceId, 0);
        return true;
    }

    void setEngine(EngineState state) {
        std::lock_guard<std::mutex> lock(audioMutex);
        engineState = state;
    }

    void playGas() {
        std::lock_guard<std::mutex> lock(audioMutex);
        activeSounds.push_back({sndGas, 0});
    }

    void playCrash() {
        std::lock_guard<std::mutex> lock(audioMutex);
        activeSounds.push_back({sndCrash, 0});
    }

    void playClear() {
        std::lock_guard<std::mutex> lock(audioMutex);
        activeSounds.push_back({sndClear, 0});
    }

    void playGameOver() {
        std::lock_guard<std::mutex> lock(audioMutex);
        activeSounds.push_back({sndGameOver, 0});
    }

    void playSkid() {
        std::lock_guard<std::mutex> lock(audioMutex);
        activeSounds.push_back({sndSkid, 0});
    }

private:
    struct SoundInstance {
        std::vector<int16_t> samples;
        size_t cursor;
    };

    SDL_AudioDeviceID deviceId = 0;
    std::mutex audioMutex;
    EngineState engineState = ENG_OFF;
    float enginePhase = 0.0f;

    std::vector<int16_t> sndGas;
    std::vector<int16_t> sndCrash;
    std::vector<int16_t> sndClear;
    std::vector<int16_t> sndGameOver;
    std::vector<int16_t> sndSkid;
    std::vector<SoundInstance> activeSounds;

    static void audioCallback(void* userdata, Uint8* stream, int len) {
        auto* self = static_cast<AudioEngine*>(userdata);
        self->fillBuffer(reinterpret_cast<int16_t*>(stream), len / sizeof(int16_t));
    }

    void fillBuffer(int16_t* buffer, int numSamples) {
        std::lock_guard<std::mutex> lock(audioMutex);
        std::fill(buffer, buffer + numSamples, 0);

        // 1. Synthesize Engine Tone (sawtooth)
        float freq = 0.0f;
        if (engineState == ENG_LOW) freq = 50.0f;
        else if (engineState == ENG_MID) freq = 75.0f;
        else if (engineState == ENG_HIGH) freq = 100.0f;

        if (freq > 0.0f) {
            float phaseStep = freq / 44100.0f;
            float volume = 0.04f * 32767.0f;
            for (int i = 0; i < numSamples; i += 2) {
                float sampleVal = 2.0f * (enginePhase - std::floor(enginePhase + 0.5f));
                int16_t val = static_cast<int16_t>(sampleVal * volume);
                buffer[i] = clampAdd(buffer[i], val);
                buffer[i + 1] = clampAdd(buffer[i + 1], val);

                enginePhase += phaseStep;
                if (enginePhase >= 1.0f) enginePhase -= 1.0f;
            }
        }

        // 2. Mix active one-shot sound effects
        for (auto it = activeSounds.begin(); it != activeSounds.end();) {
            for (int i = 0; i < numSamples; i += 2) {
                if (it->cursor < it->samples.size()) {
                    int16_t val = it->samples[it->cursor++];
                    buffer[i] = clampAdd(buffer[i], val);
                    buffer[i + 1] = clampAdd(buffer[i + 1], val);
                } else {
                    break;
                }
            }
            if (it->cursor >= it->samples.size()) {
                it = activeSounds.erase(it);
            } else {
                ++it;
            }
        }
    }

    static int16_t clampAdd(int16_t a, int16_t b) {
        int32_t res = static_cast<int32_t>(a) + static_cast<int32_t>(b);
        if (res > 32767) return 32767;
        if (res < -32768) return -32768;
        return static_cast<int16_t>(res);
    }

    void generateOneShots() {
        constexpr int sampleRate = 44100;

        // Gas Sound: Two cheerful square beeps (880Hz & 1108Hz)
        {
            float dur = 0.16f;
            int total = static_cast<int>(dur * sampleRate);
            sndGas.resize(total);
            for (int i = 0; i < total; ++i) {
                float t = (float)i / sampleRate;
                float f = (t < 0.08f) ? 880.0f : 1108.0f;
                float w = std::sin(2.0f * M_PI * f * t) >= 0.0f ? 1.0f : -1.0f;
                float env = 1.0f - (t / dur) * 0.4f;
                sndGas[i] = static_cast<int16_t>(w * 0.25f * 32767.0f * env);
            }
        }

        // Crash Sound: White noise with exponential decay
        {
            float dur = 0.35f;
            int total = static_cast<int>(dur * sampleRate);
            sndCrash.resize(total);
            std::mt19937 rng(1337);
            std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
            for (int i = 0; i < total; ++i) {
                float t = (float)i / sampleRate;
                float env = std::exp(-7.0f * (t / dur));
                sndCrash[i] = static_cast<int16_t>(dist(rng) * 0.35f * 32767.0f * env);
            }
        }

        // Clear Fanfare: Ascending arpeggio (C5 - E5 - G5 - C6)
        {
            float dur = 0.6f;
            int total = static_cast<int>(dur * sampleRate);
            sndClear.resize(total);
            float notes[] = {523.25f, 659.25f, 783.99f, 1046.50f};
            for (int i = 0; i < total; ++i) {
                float t = (float)i / sampleRate;
                int noteIdx = std::min(3, static_cast<int>(t / (dur / 4.0f)));
                float f = notes[noteIdx];
                float w = std::sin(2.0f * M_PI * f * t);
                sndClear[i] = static_cast<int16_t>(w * 0.3f * 32767.0f);
            }
        }

        // Game Over: Low descending buzz
        {
            float dur = 0.5f;
            int total = static_cast<int>(dur * sampleRate);
            sndGameOver.resize(total);
            for (int i = 0; i < total; ++i) {
                float t = (float)i / sampleRate;
                float f = 220.0f - 80.0f * (t / dur);
                float w = std::sin(2.0f * M_PI * f * t) >= 0.0f ? 1.0f : -1.0f;
                float env = 1.0f - (t / dur);
                sndGameOver[i] = static_cast<int16_t>(w * 0.3f * 32767.0f * env);
            }
        }

        // Skid / Tire Screech Sound
        {
            float dur = 0.5f;
            int total = static_cast<int>(dur * sampleRate);
            sndSkid.resize(total);
            std::mt19937 rng(42);
            std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
            for (int i = 0; i < total; ++i) {
                float t = (float)i / sampleRate;
                float f = 2100.0f + 350.0f * std::sin(2.0f * M_PI * 30.0f * t);
                float sq = (std::sin(2.0f * M_PI * f * t) >= 0.0f ? 1.0f : -1.0f);
                float noise = dist(rng) * 0.4f;
                float env = 1.0f - (t / dur);
                sndSkid[i] = static_cast<int16_t>((sq * 0.6f + noise) * 0.28f * 32767.0f * env);
            }
        }
    }
};

// --- FreeType Japanese & Text Renderer ---
class TextRenderer {
public:
    TextRenderer() = default;
    ~TextRenderer() {
        for (auto& pair : textureCache) {
            if (pair.second) SDL_DestroyTexture(pair.second);
        }
        if (face) FT_Done_Face(face);
        if (ft) FT_Done_FreeType(ft);
    }

    bool init() {
        if (FT_Init_FreeType(&ft)) {
            std::cerr << "ERROR: Could not initialize FreeType library\n";
            return false;
        }

        std::string base = "";
        char* basePath = SDL_GetBasePath();
        if (basePath) {
            base = basePath;
            SDL_free(basePath);
        }

        // Try local bundled font, AppImage bundled font, or standard Linux Japanese Noto font locations
        // Try bold fonts first for maximum clarity, then medium/regular fallback
        std::vector<std::string> fontPaths;
        if (!base.empty()) {
            fontPaths.push_back(base + "assets/fonts/NotoSansCJK-Bold.ttc");
            fontPaths.push_back(base + "fonts/NotoSansCJK-Bold.ttc");
            fontPaths.push_back(base + "NotoSansCJK-Bold.ttc");
            fontPaths.push_back(base + "../share/fonts/NotoSansCJK-Bold.ttc");
            fontPaths.push_back(base + "assets/fonts/NotoSansCJK-Regular.ttc");
            fontPaths.push_back(base + "fonts/NotoSansCJK-Regular.ttc");
            fontPaths.push_back(base + "NotoSansCJK-Regular.ttc");
            fontPaths.push_back(base + "../share/fonts/NotoSansCJK-Regular.ttc");
        }
        fontPaths.push_back("assets/fonts/NotoSansCJK-Bold.ttc");
        fontPaths.push_back("fonts/NotoSansCJK-Bold.ttc");
        fontPaths.push_back("NotoSansCJK-Bold.ttc");
        fontPaths.push_back("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc");
        fontPaths.push_back("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc");
        fontPaths.push_back("/usr/share/fonts/noto/NotoSans-Bold.ttf");
        fontPaths.push_back("/usr/share/fonts/noto-cjk/NotoSansCJK-Medium.ttc");
        fontPaths.push_back("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc");
        fontPaths.push_back("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc");
        fontPaths.push_back("/usr/share/fonts/noto/NotoSans-Regular.ttf");

        for (const auto& path : fontPaths) {
            if (FT_New_Face(ft, path.c_str(), 0, &face) == 0) {
                std::cout << "Loaded font: " << path << std::endl;
                return true;
            }
        }

        std::cerr << "Warning: Could not load Japanese Noto font face. Text may be missing.\n";
        return false;
    }

    SDL_Texture* getTextTexture(SDL_Renderer* renderer, const std::string& text, int pixelSize, SDL_Color color, int* outW = nullptr, int* outH = nullptr) {
        std::string key = text + "_" + std::to_string(pixelSize) + "_" + std::to_string(color.r) + "," + std::to_string(color.g) + "," + std::to_string(color.b) + "," + std::to_string(color.a);
        auto it = textureCache.find(key);
        if (it != textureCache.end()) {
            if (outW && outH) {
                *outW = sizeCache[key].first;
                *outH = sizeCache[key].second;
            }
            return it->second;
        }

        if (!face) return nullptr;

        FT_Set_Pixel_Sizes(face, 0, pixelSize);
        auto codepoints = utf8ToCodepoints(text);

        // Measure dimensions
        int totalWidth = 0;
        int maxAscent = 0;
        int maxDescent = 0;

        for (uint32_t cp : codepoints) {
            if (FT_Load_Char(face, cp, FT_LOAD_RENDER | FT_LOAD_TARGET_LIGHT)) continue;
            FT_GlyphSlot g = face->glyph;
            totalWidth += (g->advance.x >> 6);
            if (g->bitmap_top > maxAscent) maxAscent = g->bitmap_top;
            int descent = g->bitmap.rows - g->bitmap_top;
            if (descent > maxDescent) maxDescent = descent;
        }

        int height = maxAscent + maxDescent + 2;
        if (totalWidth <= 0 || height <= 0) return nullptr;

        SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(0, totalWidth + 2, height, 32, SDL_PIXELFORMAT_RGBA32);
        if (!surface) return nullptr;
        SDL_FillRect(surface, nullptr, SDL_MapRGBA(surface->format, 0, 0, 0, 0));

        // Render characters onto surface
        int penX = 1;
        int baseline = maxAscent + 1;

        for (uint32_t cp : codepoints) {
            if (FT_Load_Char(face, cp, FT_LOAD_RENDER | FT_LOAD_TARGET_LIGHT)) continue;
            FT_GlyphSlot g = face->glyph;

            int dstX = penX + g->bitmap_left;
            int dstY = baseline - g->bitmap_top;

            for (unsigned int r = 0; r < g->bitmap.rows; ++r) {
                for (unsigned int c = 0; c < g->bitmap.width; ++c) {
                    int px = dstX + c;
                    int py = dstY + r;
                    if (px >= 0 && px < surface->w && py >= 0 && py < surface->h) {
                        uint8_t alpha = g->bitmap.buffer[r * g->bitmap.pitch + c];
                        if (alpha > 0) {
                            uint32_t* pixel = reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(surface->pixels) + py * surface->pitch + px * 4);
                            uint8_t finalAlpha = static_cast<uint8_t>((alpha * color.a) / 255);
                            *pixel = SDL_MapRGBA(surface->format, color.r, color.g, color.b, finalAlpha);
                        }
                    }
                }
            }
            penX += (g->advance.x >> 6);
        }

        SDL_Texture* texture = SDL_CreateTextureFromSurface(renderer, surface);
        int finalW = surface->w;
        int finalH = surface->h;
        SDL_FreeSurface(surface);

        textureCache[key] = texture;
        sizeCache[key] = {finalW, finalH};

        if (outW && outH) {
            *outW = finalW;
            *outH = finalH;
        }
        return texture;
    }

    void drawText(SDL_Renderer* renderer, const std::string& text, int x, int y, int pixelSize, SDL_Color color, bool center = false) {
        int w = 0, h = 0;
        SDL_Texture* tex = getTextTexture(renderer, text, pixelSize, color, &w, &h);
        if (!tex) return;

        SDL_Rect dst = {center ? (x - w / 2) : x, center ? (y - h / 2) : y, w, h};
        SDL_RenderCopy(renderer, tex, nullptr, &dst);
    }

    void drawTextWithOutline(SDL_Renderer* renderer, const std::string& text, int x, int y, int pixelSize, SDL_Color color, SDL_Color outlineColor = {0, 0, 0, 255}, int outlineThickness = 1, bool center = false) {
        if (outlineThickness <= 1) {
            drawText(renderer, text, x - 1, y, pixelSize, outlineColor, center);
            drawText(renderer, text, x + 1, y, pixelSize, outlineColor, center);
            drawText(renderer, text, x, y - 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x, y + 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x - 1, y - 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x + 1, y - 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x - 1, y + 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x + 1, y + 1, pixelSize, outlineColor, center);
            drawText(renderer, text, x, y + 2, pixelSize, outlineColor, center);
        } else {
            for (int ox = -2; ox <= 2; ++ox) {
                for (int oy = -2; oy <= 2; ++oy) {
                    if (ox == 0 && oy == 0) continue;
                    drawText(renderer, text, x + ox, y + oy, pixelSize, outlineColor, center);
                }
            }
        }
        drawText(renderer, text, x, y, pixelSize, color, center);
    }

    void drawTextWithShadow(SDL_Renderer* renderer, const std::string& text, int x, int y, int pixelSize, SDL_Color color, bool center = false) {
        drawTextWithOutline(renderer, text, x, y, pixelSize, color, {0, 0, 0, 255}, (pixelSize >= 24 ? 2 : 1), center);
    }

    void drawTextRight(SDL_Renderer* renderer, const std::string& text, int x, int y, int pixelSize, SDL_Color color, bool centerVertically = false) {
        int w = 0, h = 0;
        SDL_Texture* tex = getTextTexture(renderer, text, pixelSize, color, &w, &h);
        if (!tex) return;
        SDL_Rect dst = {x - w, centerVertically ? (y - h / 2) : y, w, h};
        SDL_RenderCopy(renderer, tex, nullptr, &dst);
    }

    void drawTextRightWithShadow(SDL_Renderer* renderer, const std::string& text, int x, int y, int pixelSize, SDL_Color color, bool centerVertically = false) {
        int t = (pixelSize >= 24 ? 2 : 1);
        if (t <= 1) {
            drawTextRight(renderer, text, x - 1, y, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x + 1, y, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x, y - 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x, y + 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x - 1, y - 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x + 1, y - 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x - 1, y + 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x + 1, y + 1, pixelSize, {0, 0, 0, 255}, centerVertically);
            drawTextRight(renderer, text, x, y + 2, pixelSize, {0, 0, 0, 255}, centerVertically);
        } else {
            for (int ox = -2; ox <= 2; ++ox) {
                for (int oy = -2; oy <= 2; ++oy) {
                    if (ox == 0 && oy == 0) continue;
                    drawTextRight(renderer, text, x + ox, y + oy, pixelSize, {0, 0, 0, 255}, centerVertically);
                }
            }
        }
        drawTextRight(renderer, text, x, y, pixelSize, color, centerVertically);
    }

private:
    FT_Library ft = nullptr;
    FT_Face face = nullptr;
    std::map<std::string, SDL_Texture*> textureCache;
    std::map<std::string, std::pair<int, int>> sizeCache;

    static std::vector<uint32_t> utf8ToCodepoints(const std::string& s) {
        std::vector<uint32_t> res;
        size_t i = 0;
        while (i < s.size()) {
            uint8_t c = s[i];
            uint32_t cp = 0;
            if ((c & 0x80) == 0) { cp = c; i += 1; }
            else if ((c & 0xE0) == 0xC0 && i + 1 < s.size()) { cp = ((c & 0x1F) << 6) | (s[i + 1] & 0x3F); i += 2; }
            else if ((c & 0xF0) == 0xE0 && i + 2 < s.size()) { cp = ((c & 0x0F) << 12) | ((s[i + 1] & 0x3F) << 6) | (s[i + 2] & 0x3F); i += 3; }
            else if ((c & 0xF8) == 0xF0 && i + 3 < s.size()) { cp = ((c & 0x07) << 18) | ((s[i + 1] & 0x3F) << 12) | ((s[i + 2] & 0x3F) << 6) | (s[i + 3] & 0x3F); i += 4; }
            else { i += 1; }
            res.push_back(cp);
        }
        return res;
    }
};

// --- Car Entity ---
struct Car {
    float x = 0;
    float y = 0;
    float speed = 0;
    bool isPlayer = false;
    bool isSpinning = false;
    float spinAngle = 0.0f;
    int spinStartFrame = 0;
    KanaData data;
    SDL_Color color = {255, 51, 51, 255};

    SDL_FRect getBounds() const {
        return {x, y, (float)CAR_WIDTH, (float)CAR_HEIGHT};
    }

    void draw(SDL_Renderer* renderer, TextRenderer& textRenderer, SDL_Texture* targetTexture, SDL_Texture* carTexture, bool isBraking = false, bool isTurbo = false, int frames = 0) {
        constexpr int texW = CAR_WIDTH + 20;
        constexpr int texH = CAR_HEIGHT + 28;
        constexpr int ox = 10;
        constexpr int oy = 6;

        // Render car components onto reusable transparent carTexture
        SDL_SetRenderTarget(renderer, carTexture);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0);
        SDL_RenderClear(renderer);

        // 1. Ambient Ground Drop Shadow
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 110);
        SDL_Rect sh1 = {ox - 3, oy + 4, CAR_WIDTH + 6, CAR_HEIGHT};
        SDL_RenderFillRect(renderer, &sh1);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 50);
        SDL_Rect sh2 = {ox - 5, oy + 6, CAR_WIDTH + 10, CAR_HEIGHT + 2};
        SDL_RenderFillRect(renderer, &sh2);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // 2. Wheels with Alloy Rims & Rubber Tread
        SDL_SetRenderDrawColor(renderer, 22, 22, 24, 255);
        SDL_Rect wFL = {ox - 3, oy + 8, 4, 15};
        SDL_Rect wFR = {ox + CAR_WIDTH - 1, oy + 8, 4, 15};
        SDL_Rect wRL = {ox - 3, oy + CAR_HEIGHT - 23, 4, 15};
        SDL_Rect wRR = {ox + CAR_WIDTH - 1, oy + CAR_HEIGHT - 23, 4, 15};
        SDL_RenderFillRect(renderer, &wFL);
        SDL_RenderFillRect(renderer, &wFR);
        SDL_RenderFillRect(renderer, &wRL);
        SDL_RenderFillRect(renderer, &wRR);

        // Silver metallic alloy rims
        SDL_SetRenderDrawColor(renderer, 195, 202, 215, 255);
        SDL_Rect rFL = {ox - 2, oy + 11, 2, 9};
        SDL_Rect rFR = {ox + CAR_WIDTH, oy + 11, 2, 9};
        SDL_Rect rRL = {ox - 2, oy + CAR_HEIGHT - 20, 2, 9};
        SDL_Rect rRR = {ox + CAR_WIDTH, oy + CAR_HEIGHT - 20, 2, 9};
        SDL_RenderFillRect(renderer, &rFL);
        SDL_RenderFillRect(renderer, &rFR);
        SDL_RenderFillRect(renderer, &rRL);
        SDL_RenderFillRect(renderer, &rRR);

        // Center axle hubcap
        SDL_SetRenderDrawColor(renderer, 45, 48, 55, 255);
        SDL_Rect hFL = {ox - 2, oy + 14, 2, 3};
        SDL_Rect hFR = {ox + CAR_WIDTH, oy + 14, 2, 3};
        SDL_Rect hRL = {ox - 2, oy + CAR_HEIGHT - 17, 2, 3};
        SDL_Rect hRR = {ox + CAR_WIDTH, oy + CAR_HEIGHT - 17, 2, 3};
        SDL_RenderFillRect(renderer, &hFL);
        SDL_RenderFillRect(renderer, &hFR);
        SDL_RenderFillRect(renderer, &hRL);
        SDL_RenderFillRect(renderer, &hRR);

        // 3. Exhaust Pipes & Turbo Flame VFX
        SDL_SetRenderDrawColor(renderer, 175, 180, 190, 255);
        SDL_Rect exL = {ox + 7, oy + CAR_HEIGHT - 2, 4, 4};
        SDL_Rect exR = {ox + CAR_WIDTH - 11, oy + CAR_HEIGHT - 2, 4, 4};
        SDL_RenderFillRect(renderer, &exL);
        SDL_RenderFillRect(renderer, &exR);
        SDL_SetRenderDrawColor(renderer, 20, 20, 25, 255);
        SDL_Rect exHL = {ox + 8, oy + CAR_HEIGHT, 2, 2};
        SDL_Rect exHR = {ox + CAR_WIDTH - 10, oy + CAR_HEIGHT, 2, 2};
        SDL_RenderFillRect(renderer, &exHL);
        SDL_RenderFillRect(renderer, &exHR);

        // Animated Nitro Turbo Boost Flames
        if (isTurbo) {
            int flH = 8 + (frames % 4) * 3;
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 255, 110, 20, 220);
            SDL_Rect flO1 = {ox + 6, oy + CAR_HEIGHT + 2, 6, flH};
            SDL_Rect flO2 = {ox + CAR_WIDTH - 12, oy + CAR_HEIGHT + 2, 6, flH};
            SDL_RenderFillRect(renderer, &flO1);
            SDL_RenderFillRect(renderer, &flO2);
            SDL_SetRenderDrawColor(renderer, 130, 230, 255, 255);
            SDL_Rect flI1 = {ox + 8, oy + CAR_HEIGHT + 2, 2, flH - 3};
            SDL_Rect flI2 = {ox + CAR_WIDTH - 10, oy + CAR_HEIGHT + 2, 2, flH - 3};
            SDL_RenderFillRect(renderer, &flI1);
            SDL_RenderFillRect(renderer, &flI2);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
        }

        // 4. Aerodynamic Sculpted Chassis
        SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, 255);
        SDL_Rect carBody = {ox, oy + 3, CAR_WIDTH, CAR_HEIGHT - 6};
        SDL_RenderFillRect(renderer, &carBody);

        // Aerodynamic front nose taper
        SDL_Rect nose1 = {ox + 2, oy + 1, CAR_WIDTH - 4, 3};
        SDL_Rect nose2 = {ox + 4, oy, CAR_WIDTH - 8, 2};
        SDL_RenderFillRect(renderer, &nose1);
        SDL_RenderFillRect(renderer, &nose2);

        // Front splitter / chin spoiler (dark carbon fiber)
        SDL_SetRenderDrawColor(renderer, 32, 35, 42, 255);
        SDL_Rect splitter = {ox + 1, oy, CAR_WIDTH - 2, 2};
        SDL_RenderFillRect(renderer, &splitter);

        // Body lighting: left sunlight highlight & right ambient shadow
        Uint8 hlR = static_cast<Uint8>(std::min(255, (int)color.r + 45));
        Uint8 hlG = static_cast<Uint8>(std::min(255, (int)color.g + 45));
        Uint8 hlB = static_cast<Uint8>(std::min(255, (int)color.b + 45));
        SDL_SetRenderDrawColor(renderer, hlR, hlG, hlB, 255);
        SDL_Rect bodyHL = {ox, oy + 4, 2, CAR_HEIGHT - 8};
        SDL_RenderFillRect(renderer, &bodyHL);

        Uint8 shR = static_cast<Uint8>(std::max(0, (int)color.r - 45));
        Uint8 shG = static_cast<Uint8>(std::max(0, (int)color.g - 45));
        Uint8 shB = static_cast<Uint8>(std::max(0, (int)color.b - 45));
        SDL_SetRenderDrawColor(renderer, shR, shG, shB, 255);
        SDL_Rect bodySH = {ox + CAR_WIDTH - 2, oy + 4, 2, CAR_HEIGHT - 8};
        SDL_RenderFillRect(renderer, &bodySH);

        // Hood detail: twin cooling vents & nose badge
        SDL_SetRenderDrawColor(renderer, 28, 30, 36, 255);
        SDL_Rect vent1 = {ox + 10, oy + 5, 5, 2};
        SDL_Rect vent2 = {ox + CAR_WIDTH - 15, oy + 5, 5, 2};
        SDL_RenderFillRect(renderer, &vent1);
        SDL_RenderFillRect(renderer, &vent2);
        SDL_SetRenderDrawColor(renderer, 240, 245, 255, 255);
        SDL_Rect emblem = {ox + CAR_WIDTH / 2 - 2, oy + 2, 4, 2};
        SDL_RenderFillRect(renderer, &emblem);

        // Rear aerodynamic spoiler / wing
        SDL_SetRenderDrawColor(renderer, 38, 42, 50, 255);
        SDL_Rect spMountL = {ox + 6, oy + CAR_HEIGHT - 6, 2, 4};
        SDL_Rect spMountR = {ox + CAR_WIDTH - 8, oy + CAR_HEIGHT - 6, 2, 4};
        SDL_RenderFillRect(renderer, &spMountL);
        SDL_RenderFillRect(renderer, &spMountR);

        SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, 255);
        SDL_Rect spoilerWing = {ox + 1, oy + CAR_HEIGHT - 5, CAR_WIDTH - 2, 3};
        SDL_RenderFillRect(renderer, &spoilerWing);
        SDL_SetRenderDrawColor(renderer, hlR, hlG, hlB, 255);
        SDL_Rect spoilerLip = {ox + 1, oy + CAR_HEIGHT - 5, CAR_WIDTH - 2, 1};
        SDL_RenderFillRect(renderer, &spoilerLip);

        // 5. Headlights & Taillights
        SDL_SetRenderDrawColor(renderer, 255, 255, 225, 255);
        SDL_Rect hlL = {ox + 3, oy + 1, 6, 3};
        SDL_Rect hlR_rect = {ox + CAR_WIDTH - 9, oy + 1, 6, 3};
        SDL_RenderFillRect(renderer, &hlL);
        SDL_RenderFillRect(renderer, &hlR_rect);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_Rect hlDotL = {ox + 5, oy + 1, 2, 2};
        SDL_Rect hlDotR = {ox + CAR_WIDTH - 7, oy + 1, 2, 2};
        SDL_RenderFillRect(renderer, &hlDotL);
        SDL_RenderFillRect(renderer, &hlDotR);
        SDL_SetRenderDrawColor(renderer, 255, 160, 0, 255);
        SDL_Rect indL = {ox + 1, oy + 2, 2, 2};
        SDL_Rect indR = {ox + CAR_WIDTH - 3, oy + 2, 2, 2};
        SDL_RenderFillRect(renderer, &indL);
        SDL_RenderFillRect(renderer, &indR);

        // Taillights
        if (isBraking) {
            SDL_SetRenderDrawColor(renderer, 255, 60, 60, 255);
            SDL_Rect brkL = {ox + 2, oy + CAR_HEIGHT - 4, 8, 3};
            SDL_Rect brkR = {ox + CAR_WIDTH - 10, oy + CAR_HEIGHT - 4, 8, 3};
            SDL_Rect brkC = {ox + CAR_WIDTH / 2 - 6, oy + CAR_HEIGHT - 4, 12, 2};
            SDL_RenderFillRect(renderer, &brkL);
            SDL_RenderFillRect(renderer, &brkR);
            SDL_RenderFillRect(renderer, &brkC);
        } else {
            SDL_SetRenderDrawColor(renderer, 210, 25, 25, 255);
            SDL_Rect tlL = {ox + 3, oy + CAR_HEIGHT - 4, 7, 3};
            SDL_Rect tlR = {ox + CAR_WIDTH - 10, oy + CAR_HEIGHT - 4, 7, 3};
            SDL_RenderFillRect(renderer, &tlL);
            SDL_RenderFillRect(renderer, &tlR);
            SDL_SetRenderDrawColor(renderer, 240, 240, 245, 255);
            SDL_Rect revL = {ox + 7, oy + CAR_HEIGHT - 3, 2, 1};
            SDL_Rect revR = {ox + CAR_WIDTH - 7, oy + CAR_HEIGHT - 3, 2, 1};
            SDL_RenderFillRect(renderer, &revL);
            SDL_RenderFillRect(renderer, &revR);
            SDL_SetRenderDrawColor(renderer, 240, 35, 35, 255);
            SDL_Rect chmsl = {ox + CAR_WIDTH / 2 - 4, oy + CAR_HEIGHT - 4, 8, 2};
            SDL_RenderFillRect(renderer, &chmsl);
        }

        // 6. Cockpit Glass & Glare Reflections
        SDL_SetRenderDrawColor(renderer, 28, 48, 72, 255);
        SDL_Rect windshield = {ox + 4, oy + 9, CAR_WIDTH - 8, 8};
        SDL_RenderFillRect(renderer, &windshield);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 195, 230, 255, 170);
        SDL_RenderDrawLine(renderer, ox + 8, oy + 15, ox + 18, oy + 10);
        SDL_RenderDrawLine(renderer, ox + 9, oy + 15, ox + 19, oy + 10);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        SDL_SetRenderDrawColor(renderer, 24, 40, 60, 255);
        SDL_Rect rearWin = {ox + 4, oy + CAR_HEIGHT - 17, CAR_WIDTH - 8, 7};
        SDL_RenderFillRect(renderer, &rearWin);
        SDL_SetRenderDrawColor(renderer, 130, 80, 50, 200);
        SDL_RenderDrawLine(renderer, ox + 6, oy + CAR_HEIGHT - 14, ox + CAR_WIDTH - 6, oy + CAR_HEIGHT - 14);

        // 7. Side Mirrors
        SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, 255);
        SDL_Rect mirL = {ox - 4, oy + 15, 4, 5};
        SDL_Rect mirR = {ox + CAR_WIDTH, oy + 15, 4, 5};
        SDL_RenderFillRect(renderer, &mirL);
        SDL_RenderFillRect(renderer, &mirR);
        SDL_SetRenderDrawColor(renderer, 210, 225, 240, 255);
        SDL_Rect mirGlassL = {ox - 4, oy + 16, 1, 3};
        SDL_Rect mirGlassR = {ox + CAR_WIDTH + 3, oy + 16, 1, 3};
        SDL_RenderFillRect(renderer, &mirGlassL);
        SDL_RenderFillRect(renderer, &mirGlassR);

        // 8. High-Contrast Illuminated Racing Roof Decal & Character Display
        if (isPlayer) {
            // Player Car: Illuminated pearl-white racing plate with metallic gold trim
            SDL_SetRenderDrawColor(renderer, 20, 25, 35, 255); // Outer dark frame
            SDL_Rect plateBezel = {ox + 3, oy + 16, CAR_WIDTH - 6, CAR_HEIGHT - 32};
            SDL_RenderFillRect(renderer, &plateBezel);

            SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255); // Metallic gold border
            SDL_Rect plateGold = {ox + 4, oy + 17, CAR_WIDTH - 8, CAR_HEIGHT - 34};
            SDL_RenderDrawRect(renderer, &plateGold);

            SDL_SetRenderDrawColor(renderer, 250, 252, 255, 255); // Brilliant pearl white plate
            SDL_Rect plateInner = {ox + 5, oy + 18, CAR_WIDTH - 10, CAR_HEIGHT - 36};
            SDL_RenderFillRect(renderer, &plateInner);

            int cx = ox + CAR_WIDTH / 2;
            int cy = oy + CAR_HEIGHT / 2;
            // Bold rich crimson Hiragana glyph on crisp pearl plate for instant identification
            textRenderer.drawText(renderer, data.kana, cx, cy, 26, {190, 15, 20, 255}, true);
        } else {
            // Traffic Vehicle: High-contrast illuminated white decal plate with dark racing bezel
            SDL_SetRenderDrawColor(renderer, 15, 20, 30, 255); // Outer dark bezel
            SDL_Rect plateBezel = {ox + 3, oy + 16, CAR_WIDTH - 6, CAR_HEIGHT - 32};
            SDL_RenderFillRect(renderer, &plateBezel);

            SDL_SetRenderDrawColor(renderer, 75, 90, 115, 255); // Steel frame
            SDL_Rect plateFrame = {ox + 4, oy + 17, CAR_WIDTH - 8, CAR_HEIGHT - 34};
            SDL_RenderDrawRect(renderer, &plateFrame);

            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255); // Crisp pure white backing
            SDL_Rect plateInner = {ox + 5, oy + 18, CAR_WIDTH - 10, CAR_HEIGHT - 36};
            SDL_RenderFillRect(renderer, &plateInner);

            int cx = ox + CAR_WIDTH / 2;
            int cy = oy + CAR_HEIGHT / 2;
            // Dynamic font sizing for Romaji to guarantee perfect fit within decal plate
            int fSize = 22;
            if (data.romaji.length() == 1) fSize = 24;
            else if (data.romaji.length() == 2) fSize = 20;
            else fSize = 17;

            // Deep charcoal/navy Romaji on pure white plate for razor-sharp legibility at high speed
            textRenderer.drawText(renderer, data.romaji, cx, cy, fSize, {10, 15, 25, 255}, true);
        }

        // Switch back to targetTexture and render rotated car with exact pivot
        SDL_SetRenderTarget(renderer, targetTexture);
        SDL_Rect dst = {static_cast<int>(x) - ox, static_cast<int>(y) - oy, texW, texH};
        SDL_Point center = {ox + CAR_WIDTH / 2, oy + CAR_HEIGHT / 2};
        SDL_RenderCopyEx(renderer, carTexture, nullptr, &dst, spinAngle, &center, SDL_FLIP_NONE);
    }
};

// --- Drawing Helpers ---
void drawCircle(SDL_Renderer* renderer, int centerX, int centerY, int radius, SDL_Color color) {
    SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, color.a);
    for (int w = 0; w < radius * 2; w++) {
        for (int h = 0; h < radius * 2; h++) {
            int dx = radius - w;
            int dy = radius - h;
            if ((dx * dx + dy * dy) <= (radius * radius)) {
                SDL_RenderDrawPoint(renderer, centerX + dx, centerY + dy);
            }
        }
    }
}

void drawTree(SDL_Renderer* renderer, int x, int y, int treeType = 0) {
    // 1. Soft Ground Shadow
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    drawCircle(renderer, x + 3, y + 8, 14, {0, 0, 0, 45});
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

    // 2. Trunk with Bark Texture
    SDL_SetRenderDrawColor(renderer, 85, 50, 22, 255);
    SDL_Rect trunk = {x - 3, y + 4, 6, 14};
    SDL_RenderFillRect(renderer, &trunk);
    SDL_SetRenderDrawColor(renderer, 115, 68, 30, 255);
    SDL_Rect trunkHL = {x - 3, y + 4, 2, 14};
    SDL_RenderFillRect(renderer, &trunkHL);
    SDL_SetRenderDrawColor(renderer, 60, 35, 15, 255);
    SDL_Rect rootFlare = {x - 5, y + 15, 10, 3};
    SDL_RenderFillRect(renderer, &rootFlare);

    // 3. Multi-Layered Shaded Foliage
    if (treeType == 0) {
        // Broadleaf Canopy (Lush Deciduous Oak)
        drawCircle(renderer, x, y + 3, 13, {18, 75, 24, 255});
        drawCircle(renderer, x - 3, y - 1, 11, {28, 125, 36, 255});
        drawCircle(renderer, x + 3, y - 2, 10, {35, 140, 42, 255});
        drawCircle(renderer, x - 1, y - 6, 8, {55, 185, 58, 255});
        drawCircle(renderer, x - 2, y - 8, 4, {85, 220, 80, 255});
    } else {
        // Conifer Pine Tree (Layered Needle Cones)
        SDL_SetRenderDrawColor(renderer, 16, 68, 32, 255);
        for (int i = 0; i < 9; ++i) {
            SDL_Rect tier = {x - 14 + i, y + 5 - i, (14 - i) * 2, 1};
            SDL_RenderFillRect(renderer, &tier);
        }
        SDL_SetRenderDrawColor(renderer, 24, 105, 45, 255);
        for (int i = 0; i < 8; ++i) {
            SDL_Rect tier = {x - 11 + i, y - 2 - i, (11 - i) * 2, 1};
            SDL_RenderFillRect(renderer, &tier);
        }
        SDL_SetRenderDrawColor(renderer, 38, 145, 60, 255);
        for (int i = 0; i < 7; ++i) {
            SDL_Rect tier = {x - 7 + i, y - 9 - i, (7 - i) * 2, 1};
            SDL_RenderFillRect(renderer, &tier);
        }
    }
}

void drawPalmTree(SDL_Renderer* renderer, int x, int y, int frames, int seed) {
    // 1. Soft Circular Ground Shadow on Sand
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    drawCircle(renderer, x + 4, y + 16, 16, {150, 120, 80, 75});
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

    // 2. Curved Coconut Palm Trunk with segmented bark rings
    float lean = (seed % 2 == 0 ? 1.0f : -1.0f) * 12.0f;
    int trunkSteps = 10;
    int topX = x;
    int topY = y - 36;

    for (int s = 0; s < trunkSteps; ++s) {
        float t0 = static_cast<float>(s) / trunkSteps;
        float t1 = static_cast<float>(s + 1) / trunkSteps;
        int sx0 = x + static_cast<int>(std::sin(t0 * 1.57f) * lean);
        int sy0 = y + 16 - static_cast<int>(t0 * 52.0f);
        int sx1 = x + static_cast<int>(std::sin(t1 * 1.57f) * lean);
        int sy1 = y + 16 - static_cast<int>(t1 * 52.0f);
        int w = 7 - (s * 3) / trunkSteps;

        SDL_SetRenderDrawColor(renderer, COLOR_PALM_TRUNK.r, COLOR_PALM_TRUNK.g, COLOR_PALM_TRUNK.b, 255);
        SDL_Rect seg = {sx0 - w / 2, sy1, w, std::max(2, sy0 - sy1)};
        SDL_RenderFillRect(renderer, &seg);

        if (s % 2 == 0) {
            SDL_SetRenderDrawColor(renderer, 85, 52, 28, 255);
            SDL_RenderDrawLine(renderer, sx0 - w / 2, sy1, sx0 + w / 2, sy1);
        }
        if (s == trunkSteps - 1) {
            topX = sx1;
            topY = sy1;
        }
    }

    // 3. Cluster of Coconuts under the crown
    drawCircle(renderer, topX - 3, topY + 2, 3, {95, 58, 25, 255});
    drawCircle(renderer, topX + 2, topY + 1, 3, {82, 48, 20, 255});
    drawCircle(renderer, topX, topY + 4, 3, {110, 68, 30, 255});

    // 4. Layered Tropical Palm Fronds (Arching and swaying in ocean breeze)
    float sway = std::sin(frames * 0.05f + seed) * 3.5f;

    struct Frond { float angle; int length; int curve; };
    const Frond FRONDS[6] = {
        {-2.5f, 26, 8},  // Far Left
        {-1.8f, 30, 10}, // Up Left
        {-0.9f, 28, 9},  // Up Right
        {-0.3f, 26, 8},  // Far Right
        {-2.9f, 22, 6},  // Low Left
        {0.1f, 22, 6}    // Low Right
    };

    for (int f = 0; f < 6; ++f) {
        float baseAng = FRONDS[f].angle;
        int len = FRONDS[f].length;
        SDL_Color fCol = (f % 2 == 0) ? COLOR_PALM_LEAF_1 : COLOR_PALM_LEAF_2;

        int prevFx = topX;
        int prevFy = topY;
        for (int step = 1; step <= 5; ++step) {
            float frac = static_cast<float>(step) / 5.0f;
            float curAng = baseAng + (frac * frac * 0.35f) + (sway * 0.04f * frac);
            int fx = topX + static_cast<int>(std::cos(curAng) * len * frac);
            int fy = topY + static_cast<int>(std::sin(curAng) * len * frac + (frac * frac * FRONDS[f].curve));

            SDL_SetRenderDrawColor(renderer, fCol.r, fCol.g, fCol.b, 255);
            SDL_RenderDrawLine(renderer, prevFx, prevFy, fx, fy);
            SDL_RenderDrawLine(renderer, prevFx + 1, prevFy, fx + 1, fy);
            SDL_RenderDrawLine(renderer, prevFx, prevFy + 1, fx, fy + 1);

            if (step >= 2) {
                SDL_SetRenderDrawColor(renderer, COLOR_PALM_LEAF_2.r, COLOR_PALM_LEAF_2.g, COLOR_PALM_LEAF_2.b, 255);
                SDL_RenderDrawLine(renderer, fx, fy, fx - 2, fy + 3);
                SDL_RenderDrawLine(renderer, fx, fy, fx + 2, fy + 3);
            }
            prevFx = fx;
            prevFy = fy;
        }
    }
}

void drawBeachProp(SDL_Renderer* renderer, int x, int y, int propType) {
    if (propType == 0) {
        // Striped Beach Parasol / Umbrella
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        drawCircle(renderer, x + 6, y + 10, 12, {140, 110, 70, 70});
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Mast
        SDL_SetRenderDrawColor(renderer, 220, 225, 230, 255);
        SDL_RenderDrawLine(renderer, x + 4, y + 8, x - 2, y - 8);
        SDL_RenderDrawLine(renderer, x + 5, y + 8, x - 1, y - 8);

        // Striped Canopy
        int cx = x - 2;
        int cy = y - 10;
        int uRad = 16;
        for (int dy = -6; dy <= 6; ++dy) {
            int span = static_cast<int>(std::sqrt(std::max(0, uRad * uRad - (dy * 3) * (dy * 3))));
            for (int dx = -span; dx <= span; ++dx) {
                bool stripe = (((dx + dy + 32) / 5) % 2 == 0);
                if (stripe) SDL_SetRenderDrawColor(renderer, 235, 45, 45, 255); // Vibrant Red
                else SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);       // Pure White
                SDL_RenderDrawPoint(renderer, cx + dx, cy + dy);
            }
        }
        SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
        SDL_Rect finial = {cx - 1, cy - 8, 3, 3};
        SDL_RenderFillRect(renderer, &finial);
    } else if (propType == 1) {
        // Surfboard planted in the sand
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        drawCircle(renderer, x + 4, y + 8, 8, {140, 110, 70, 70});
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        SDL_SetRenderDrawColor(renderer, 0, 195, 235, 255); // Cyan board
        SDL_Rect b1 = {x - 2, y - 16, 6, 22};
        SDL_RenderFillRect(renderer, &b1);

        SDL_SetRenderDrawColor(renderer, 255, 220, 30, 255);
        SDL_Rect bStripe = {x, y - 16, 2, 22};
        SDL_RenderFillRect(renderer, &bStripe);

        SDL_SetRenderDrawColor(renderer, 0, 195, 235, 255);
        SDL_RenderDrawPoint(renderer, x - 1, y - 17);
        SDL_RenderDrawPoint(renderer, x + 1, y - 17);
        SDL_RenderDrawPoint(renderer, x, y - 18);
    } else {
        // Beach Towel laid on sand
        SDL_SetRenderDrawColor(renderer, 255, 140, 30, 255); // Orange towel
        SDL_Rect towel = {x - 8, y - 4, 16, 24};
        SDL_RenderFillRect(renderer, &towel);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDrawLine(renderer, x - 8, y + 2, x + 7, y + 2);
        SDL_RenderDrawLine(renderer, x - 8, y + 14, x + 7, y + 14);

        // Mini cooler box
        SDL_SetRenderDrawColor(renderer, 45, 120, 225, 255);
        SDL_Rect cooler = {x + 10, y + 2, 8, 8};
        SDL_RenderFillRect(renderer, &cooler);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_Rect lid = {x + 9, y + 1, 10, 2};
        SDL_RenderFillRect(renderer, &lid);
    }
}

void drawFinishLine(SDL_Renderer* renderer, TextRenderer& textRenderer, int y) {
    constexpr int roadLeft = GAME_X + ROAD_MARGIN;
    constexpr int squareSize = 15;
    constexpr int numCols = ROAD_WIDTH / squareSize;
    constexpr int numRows = 2;

    // White base border
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect bg = {roadLeft, y - 2, ROAD_WIDTH, numRows * squareSize + 4};
    SDL_RenderFillRect(renderer, &bg);

    // Checkered pattern
    for (int r = 0; r < numRows; ++r) {
        for (int c = 0; c < numCols; ++c) {
            bool isBlack = ((r + c) % 2 == 0);
            if (isBlack) SDL_SetRenderDrawColor(renderer, 20, 20, 20, 255);
            else SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
            SDL_Rect sq = {roadLeft + c * squareSize, y + r * squareSize, squareSize, squareSize};
            SDL_RenderFillRect(renderer, &sq);
        }
    }

    // Red-and-white goal posts on the road sides
    int postXs[2] = {roadLeft - 14, roadLeft + ROAD_WIDTH + 2};
    for (int sideX : postXs) {
        for (int pr = 0; pr < 4; ++pr) {
            if (pr % 2 == 0) SDL_SetRenderDrawColor(renderer, 230, 40, 40, 255);
            else SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
            SDL_Rect prt = {sideX, y - 8 + pr * 10, 12, 10};
            SDL_RenderFillRect(renderer, &prt);
            SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
            SDL_RenderDrawRect(renderer, &prt);
        }
    }

    // Overhead GOAL banner
    int bx = roadLeft + ROAD_WIDTH / 2;
    int by = y - 24;
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_Rect bannerBg = {bx - 60, by - 12, 120, 24};
    SDL_RenderFillRect(renderer, &bannerBg);
    SDL_SetRenderDrawColor(renderer, 255, 235, 59, 255);
    SDL_RenderDrawRect(renderer, &bannerBg);

    textRenderer.drawTextWithShadow(renderer, "★ GOAL ★", bx, by, 16, {255, 235, 59, 255}, true);
}

// --- Procedural Game Textures ---
struct GameTextures {
    SDL_Texture* asphaltTex = nullptr;
    SDL_Texture* grassTex = nullptr;
    SDL_Texture* concreteTex = nullptr;
    SDL_Texture* carbonTex = nullptr;
    SDL_Texture* waterTex = nullptr;
    SDL_Texture* sandTex = nullptr;

    void init(SDL_Renderer* renderer) {
        // 1. Asphalt Road Surface Texture (256 x 256)
        {
            constexpr int W = 256, H = 256;
            std::vector<Uint32> pixels(W * H);
            std::mt19937 prng(42);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    int base = 65 + (prng() % 13) - 6;
                    int r = base - 2;
                    int g = base - 1;
                    int b = base + 3;

                    int speckle = prng() % 100;
                    if (speckle < 8) {
                        int stone = 90 + (prng() % 35);
                        r = stone - 4; g = stone - 2; b = stone + 6;
                    } else if (speckle > 92) {
                        int tar = 40 + (prng() % 15);
                        r = tar; g = tar; b = tar + 2;
                    }

                    float wave = std::sin(x * 0.08f) * 4.0f + std::cos(y * 0.05f) * 3.0f;
                    r = std::clamp(r + static_cast<int>(wave), 25, 240);
                    g = std::clamp(g + static_cast<int>(wave), 25, 240);
                    b = std::clamp(b + static_cast<int>(wave), 25, 240);

                    pixels[y * W + x] = (static_cast<Uint32>(r) << 24) |
                                        (static_cast<Uint32>(g) << 16) |
                                        (static_cast<Uint32>(b) << 8)  | 255;
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            asphaltTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
        }

        // 2. Lush Grass Turf Texture (256 x 256)
        {
            constexpr int W = 256, H = 256;
            std::vector<Uint32> pixels(W * H);
            std::mt19937 prng(101);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    int baseG = 112 + (prng() % 21) - 10;
                    int baseR = static_cast<int>(baseG * 0.28f) + (prng() % 9) - 4;
                    int baseB = static_cast<int>(baseG * 0.32f) + (prng() % 9) - 4;

                    int patch = prng() % 100;
                    if (patch < 6) {
                        baseG -= 22; baseR -= 8; baseB -= 8;
                    } else if (patch > 90) {
                        baseG += 26; baseR += 10; baseB += 6;
                    }

                    baseR = std::clamp(baseR, 12, 220);
                    baseG = std::clamp(baseG, 40, 240);
                    baseB = std::clamp(baseB, 15, 220);

                    pixels[y * W + x] = (static_cast<Uint32>(baseR) << 24) |
                                        (static_cast<Uint32>(baseG) << 16) |
                                        (static_cast<Uint32>(baseB) << 8)  | 255;
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            grassTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
        }

        // 3. Concrete Catwalk & Pylon Texture (256 x 256)
        {
            constexpr int W = 256, H = 256;
            std::vector<Uint32> pixels(W * H);
            std::mt19937 prng(202);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    int val = 145 + (prng() % 17) - 8;
                    int r = val;
                    int g = val + 2;
                    int b = val + 5;

                    int p = prng() % 100;
                    if (p < 5) {
                        r -= 25; g -= 25; b -= 22;
                    } else if (p > 94) {
                        r += 22; g += 22; b += 25;
                    }

                    r = std::clamp(r, 0, 255);
                    g = std::clamp(g, 0, 255);
                    b = std::clamp(b, 0, 255);

                    pixels[y * W + x] = (static_cast<Uint32>(r) << 24) |
                                        (static_cast<Uint32>(g) << 16) |
                                        (static_cast<Uint32>(b) << 8)  | 255;
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            concreteTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
        }

        // 4. Carbon Fiber Twill Composite Texture (64 x 64)
        {
            constexpr int W = 64, H = 64;
            std::vector<Uint32> pixels(W * H);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    bool diag1 = ((x + y) / 4) % 2 == 0;
                    bool diag2 = ((x - y + 64) / 4) % 2 == 0;
                    int tone = 26;
                    if (diag1 ^ diag2) tone = 38;
                    if ((x % 4 == 0) || (y % 4 == 0)) tone -= 8;

                    int r = tone;
                    int g = tone + 4;
                    int b = tone + 12;
                    pixels[y * W + x] = (static_cast<Uint32>(r) << 24) |
                                        (static_cast<Uint32>(g) << 16) |
                                        (static_cast<Uint32>(b) << 8)  | 255;
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            carbonTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
        }

        // 5. Ocean Caustics & Water Ripple Texture (256 x 256)
        {
            constexpr int W = 256, H = 256;
            std::vector<Uint32> pixels(W * H);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    float v1 = std::sin(x * 0.12f + y * 0.08f);
                    float v2 = std::sin(x * 0.09f - y * 0.14f);
                    float v3 = std::cos((x + y) * 0.07f);
                    float ripple = (v1 + v2 + v3) / 3.0f;

                    int alpha = static_cast<int>(std::clamp((ripple * 0.5f + 0.5f) * 65.0f, 0.0f, 255.0f));
                    pixels[y * W + x] = (static_cast<Uint32>(190) << 24) |
                                        (static_cast<Uint32>(230) << 16) |
                                        (static_cast<Uint32>(255) << 8)  |
                                        static_cast<Uint32>(alpha);
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            waterTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_SetTextureBlendMode(waterTex, SDL_BLENDMODE_BLEND);
            SDL_FreeSurface(surf);
        }

        // 6. Warm Golden Beach Sand Texture (256 x 256)
        {
            constexpr int W = 256, H = 256;
            std::vector<Uint32> pixels(W * H);
            std::mt19937 prng(404);
            for (int y = 0; y < H; ++y) {
                for (int x = 0; x < W; ++x) {
                    int base = 212 + (prng() % 15) - 7;
                    int r = base + 22;
                    int g = base - 6;
                    int b = base - 68;

                    float ripple = std::sin(x * 0.05f + y * 0.03f) * 6.0f + std::cos(y * 0.06f) * 4.0f;
                    r = std::clamp(r + static_cast<int>(ripple), 180, 255);
                    g = std::clamp(g + static_cast<int>(ripple * 0.85f), 150, 240);
                    b = std::clamp(b + static_cast<int>(ripple * 0.6f), 100, 200);

                    int speckle = prng() % 100;
                    if (speckle < 4) {
                        r = 255; g = 250; b = 230;
                    } else if (speckle > 95) {
                        r -= 28; g -= 26; b -= 20;
                    }

                    pixels[y * W + x] = (static_cast<Uint32>(r) << 24) |
                                        (static_cast<Uint32>(g) << 16) |
                                        (static_cast<Uint32>(b) << 8)  | 255;
                }
            }
            SDL_Surface* surf = SDL_CreateRGBSurfaceFrom(pixels.data(), W, H, 32, W * 4, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF);
            sandTex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
        }
    }

    void destroy() {
        if (asphaltTex) { SDL_DestroyTexture(asphaltTex); asphaltTex = nullptr; }
        if (grassTex) { SDL_DestroyTexture(grassTex); grassTex = nullptr; }
        if (concreteTex) { SDL_DestroyTexture(concreteTex); concreteTex = nullptr; }
        if (carbonTex) { SDL_DestroyTexture(carbonTex); carbonTex = nullptr; }
        if (waterTex) { SDL_DestroyTexture(waterTex); waterTex = nullptr; }
        if (sandTex) { SDL_DestroyTexture(sandTex); sandTex = nullptr; }
    }

    static void drawTiled(SDL_Renderer* renderer, SDL_Texture* tex, int dstX, int dstY, int dstW, int dstH, int scrollX, int scrollY, int tileW, int tileH) {
        if (!tex || dstW <= 0 || dstH <= 0) return;
        SDL_Rect prevClip;
        SDL_bool hasClip = SDL_RenderIsClipEnabled(renderer);
        if (hasClip) SDL_RenderGetClipRect(renderer, &prevClip);

        SDL_Rect clipRect = {dstX, dstY, dstW, dstH};
        SDL_RenderSetClipRect(renderer, &clipRect);

        int startX = dstX - ((scrollX % tileW + tileW) % tileW);
        int startY = dstY - ((scrollY % tileH + tileH) % tileH);

        for (int y = startY; y < dstY + dstH; y += tileH) {
            for (int x = startX; x < dstX + dstW; x += tileW) {
                SDL_Rect d = {x, y, tileW, tileH};
                SDL_RenderCopy(renderer, tex, nullptr, &d);
            }
        }

        if (hasClip) SDL_RenderSetClipRect(renderer, &prevClip);
        else SDL_RenderSetClipRect(renderer, nullptr);
    }
};

// --- Main Application ---
int main(int argc, char* argv[]) {
    std::string screenshotPath = "";
    int screenshotTargetFrame = 90;
    int screenshotStage = 1;
    bool screenshotPause = false;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--screenshot" && i + 1 < argc) {
            screenshotPath = argv[++i];
            if (i + 1 < argc && argv[i + 1][0] != '-') screenshotTargetFrame = std::stoi(argv[++i]);
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                std::string sArg = argv[++i];
                if (sArg == "pause") {
                    screenshotPause = true;
                } else {
                    screenshotStage = std::stoi(sArg);
                }
            }
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                if (std::string(argv[++i]) == "pause") screenshotPause = true;
            }
        }
    }

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMECONTROLLER | SDL_INIT_JOYSTICK | SDL_INIT_HAPTIC) != 0) {
        std::cerr << "SDL_Init Error: " << SDL_GetError() << std::endl;
        return 1;
    }

    // Auto-detect maximum display resolution and optimal aspect ratio
    int autoResW = INTERNAL_WIDTH;  // Default fallback
    int autoResH = INTERNAL_HEIGHT;

    SDL_DisplayMode desktopMode;
    if (SDL_GetDesktopDisplayMode(0, &desktopMode) == 0 && desktopMode.w > 0 && desktopMode.h > 0) {
        autoResW = desktopMode.w;
        autoResH = desktopMode.h;
    }

    int numDisplayModes = SDL_GetNumDisplayModes(0);
    for (int i = 0; i < numDisplayModes; ++i) {
        SDL_DisplayMode mode;
        if (SDL_GetDisplayMode(0, i, &mode) == 0) {
            if (mode.w * mode.h > autoResW * autoResH) {
                autoResW = mode.w;
                autoResH = mode.h;
            }
        }
    }

    // Automatically determine the optimal aspect ratio based on detected resolution
    float dispRatio = static_cast<float>(autoResW) / static_cast<float>(autoResH);
    float autoAspectRatio = 16.0f / 10.0f;
    std::string autoAspectLabel = "16:10 (Deck Native Widescreen)";

    if (std::abs(dispRatio - (16.0f / 10.0f)) < 0.05f) {
        autoAspectRatio = 16.0f / 10.0f;
        autoAspectLabel = "16:10 (Deck Native Widescreen)";
    } else if (std::abs(dispRatio - (16.0f / 9.0f)) < 0.05f) {
        autoAspectRatio = 16.0f / 9.0f;
        autoAspectLabel = "16:9 (Standard HDTV / Monitor)";
    } else if (std::abs(dispRatio - (4.0f / 3.0f)) < 0.05f) {
        autoAspectRatio = 4.0f / 3.0f;
        autoAspectLabel = "4:3 (Classic CRT Arcade)";
    } else if (std::abs(dispRatio - (21.0f / 9.0f)) < 0.15f) {
        autoAspectRatio = 21.0f / 9.0f;
        autoAspectLabel = "21:9 (Ultrawide)";
    } else {
        autoAspectRatio = dispRatio;
        autoAspectLabel = "Custom (" + std::to_string(autoResW) + "x" + std::to_string(autoResH) + ")";
    }

    std::cout << "[Display] Detected Maximum Resolution: " << autoResW << "x" << autoResH << std::endl;
    std::cout << "[Display] Auto Aspect Ratio: " << autoAspectLabel << " (" << autoAspectRatio << ")" << std::endl;

    Uint32 winFlags = screenshotPath.empty() ? (SDL_WINDOW_FULLSCREEN_DESKTOP | SDL_WINDOW_SHOWN) : SDL_WINDOW_HIDDEN;
    SDL_Window* window = SDL_CreateWindow(
        "Hiragana Road Fighter (C++)",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        screenshotPath.empty() ? autoResW : INTERNAL_WIDTH,
        screenshotPath.empty() ? autoResH : INTERNAL_HEIGHT,
        winFlags
    );

    if (!window) {
        std::cerr << "Window creation failed: " << SDL_GetError() << std::endl;
        SDL_Quit();
        return 1;
    }

    if (screenshotPath.empty()) {
        SDL_SetWindowFullscreen(window, SDL_WINDOW_FULLSCREEN_DESKTOP);
    }

    // Initially hide mouse cursor
    SDL_ShowCursor(SDL_DISABLE);
    bool cursorVisible = false;
    Uint32 lastMouseMoveTime = 0;

    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!renderer) {
        renderer = SDL_CreateRenderer(window, -1, 0);
    }

    SDL_Texture* targetTexture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_RGBA8888,
        SDL_TEXTUREACCESS_TARGET,
        INTERNAL_WIDTH, INTERNAL_HEIGHT
    );

    SDL_Texture* carTexture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_RGBA8888,
        SDL_TEXTUREACCESS_TARGET,
        CAR_WIDTH + 20, CAR_HEIGHT + 28
    );
    SDL_SetTextureBlendMode(carTexture, SDL_BLENDMODE_BLEND);

    AudioEngine audio;
    audio.init();

    TextRenderer textRenderer;
    textRenderer.init();

    GameTextures textures;
    textures.init(renderer);

    std::mt19937 rng(std::random_device{}());

    // Skid marks & smoke particle effects
    struct SkidMark {
        float x1, y1, x2, y2;
        float alpha;
    };
    std::vector<SkidMark> skidMarks;

    struct SmokeParticle {
        float x, y;
        float vx, vy;
        float size;
        float alpha;
    };
    std::vector<SmokeParticle> smokeParticles;

    // Game State
    enum GameState { PLAYING, PAUSED, OVER, CLEAR };
    GameState gameState = PLAYING;
    int currentStage = 1;

    bool isFullscreen = screenshotPath.empty();
    int pauseMenuIndex = 0; // 0: Resume, 1: Screen Mode, 2: Restart Stage, 3: Quit
    std::string statusMessage = "";
    Uint32 statusMessageTime = 0;

    auto applyFullscreenMode = [&](bool fullscreen) {
        isFullscreen = fullscreen;
        if (isFullscreen) {
            SDL_SetWindowFullscreen(window, 0);
            SDL_SetWindowSize(window, autoResW, autoResH);
            SDL_SetWindowPosition(window, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED);

            SDL_DisplayMode mode;
            if (SDL_GetWindowDisplayMode(window, &mode) == 0) {
                mode.w = autoResW;
                mode.h = autoResH;
                SDL_SetWindowDisplayMode(window, &mode);
            }
            SDL_SetWindowFullscreen(window, SDL_WINDOW_FULLSCREEN_DESKTOP);
            statusMessage = "SCREEN MODE: Fullscreen (Native " + std::to_string(autoResW) + "x" + std::to_string(autoResH) + ")";
        } else {
            SDL_SetWindowFullscreen(window, 0);
            int winW = std::min(autoResW, (autoResW > 1280 ? 1280 : static_cast<int>(autoResW * 0.85f)));
            int winH = static_cast<int>(winW / autoAspectRatio);
            SDL_SetWindowSize(window, winW, winH);
            SDL_SetWindowPosition(window, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED);
            statusMessage = "SCREEN MODE: Windowed (" + std::to_string(winW) + "x" + std::to_string(winH) + ")";
        }
        statusMessageTime = SDL_GetTicks();
        std::cout << "[Video] " << statusMessage << std::endl;
    };

    Car player;
    std::vector<Car> enemies;
    float score = 0.0f;
    float trackDistance = 0.0f;
    float fuel = MAX_FUEL;
    float roadOffset = 0.0f;
    float speedMultiplier = 1.0f;
    int frames = 0;
    bool isPlayerBraking = false;
    AudioEngine::EngineState curEngState = AudioEngine::ENG_OFF;
    int matchFeedbackTimer = 0;
    bool lastMatchSuccess = false;
    int matchStreak = 0;

    auto startStage = [&](int stage, bool keepFuel = false) {
        currentStage = stage;
        player.x = GAME_X + GAME_W / 2.0f - CAR_WIDTH / 2.0f;
        player.y = INTERNAL_HEIGHT - CAR_HEIGHT - 40.0f;
        player.isPlayer = true;
        player.isSpinning = false;
        player.spinAngle = 0.0f;
        player.color = COLOR_PLAYER;
        isPlayerBraking = false;
        matchFeedbackTimer = 0;
        lastMatchSuccess = false;
        matchStreak = 0;

        const auto& stageKana = getStageKana(currentStage);
        player.data = stageKana[std::uniform_int_distribution<size_t>(0, stageKana.size() - 1)(rng)];

        enemies.clear();
        skidMarks.clear();
        smokeParticles.clear();
        if (!keepFuel) {
            score = 0.0f;
            fuel = MAX_FUEL;
        } else {
            fuel = std::min(MAX_FUEL, fuel + 35.0f);
        }
        trackDistance = 0.0f;
        roadOffset = 0.0f;
        speedMultiplier = 1.0f;
        frames = 0;
        gameState = PLAYING;
        curEngState = AudioEngine::ENG_OFF;
        audio.setEngine(AudioEngine::ENG_OFF);
    };

    // Game Controllers & Joysticks
    std::vector<SDL_GameController*> controllers;
    std::vector<SDL_Joystick*> joysticks;

    auto openControllers = [&]() {
        for (auto* c : controllers) SDL_GameControllerClose(c);
        controllers.clear();
        for (auto* j : joysticks) SDL_JoystickClose(j);
        joysticks.clear();

        int numJoy = SDL_NumJoysticks();
        for (int i = 0; i < numJoy; ++i) {
            if (SDL_IsGameController(i)) {
                SDL_GameController* c = SDL_GameControllerOpen(i);
                if (c) {
                    controllers.push_back(c);
                    std::cout << "[Controller] Connected: " << SDL_GameControllerName(c) << std::endl;
                }
            } else {
                SDL_Joystick* j = SDL_JoystickOpen(i);
                if (j) {
                    joysticks.push_back(j);
                    std::cout << "[Joystick] Connected: " << SDL_JoystickName(j) << std::endl;
                }
            }
        }
    };

    openControllers();

    auto rumble = [&](Uint16 low, Uint16 high, Uint32 ms) {
        for (auto* c : controllers) {
            SDL_GameControllerRumble(c, low, high, ms);
        }
    };

    auto resetGame = [&]() {
        startStage(screenshotStage, false);
        if (screenshotPause) {
            gameState = PAUSED;
        }
    };

    resetGame();

    bool running = true;
    Uint32 frameStart = 0;
    int loopFrames = 0;

    while (running) {
        frameStart = SDL_GetTicks();
        loopFrames++;

        // 1. Process Events
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                running = false;
            } else if (event.type == SDL_CONTROLLERDEVICEADDED || event.type == SDL_JOYDEVICEADDED ||
                       event.type == SDL_CONTROLLERDEVICEREMOVED || event.type == SDL_JOYDEVICEREMOVED) {
                openControllers();
            } else if (event.type == SDL_CONTROLLERBUTTONDOWN) {
                Uint8 btn = event.cbutton.button;
                if (btn == SDL_CONTROLLER_BUTTON_BACK) {
                    running = false;
                } else if (btn == SDL_CONTROLLER_BUTTON_START) {
                    if (gameState == PLAYING) {
                        gameState = PAUSED;
                        audio.setEngine(AudioEngine::ENG_OFF);
                    } else if (gameState == PAUSED) {
                        gameState = PLAYING;
                    } else if (gameState == CLEAR) {
                        if (currentStage == 1) startStage(2, true);
                        else if (currentStage == 2) startStage(3, true);
                        else startStage(1, false);
                    } else if (gameState == OVER) {
                        startStage(currentStage, false);
                    }
                } else if (gameState == PAUSED) {
                    if (btn == SDL_CONTROLLER_BUTTON_DPAD_UP) {
                        pauseMenuIndex = (pauseMenuIndex == 0 ? 3 : pauseMenuIndex - 1);
                    } else if (btn == SDL_CONTROLLER_BUTTON_DPAD_DOWN) {
                        pauseMenuIndex = (pauseMenuIndex == 3 ? 0 : pauseMenuIndex + 1);
                    } else if (btn == SDL_CONTROLLER_BUTTON_DPAD_LEFT || btn == SDL_CONTROLLER_BUTTON_DPAD_RIGHT) {
                        if (pauseMenuIndex == 1) {
                            applyFullscreenMode(!isFullscreen);
                        }
                    } else if (btn == SDL_CONTROLLER_BUTTON_A || btn == SDL_CONTROLLER_BUTTON_X) {
                        if (pauseMenuIndex == 0) {
                            gameState = PLAYING;
                        } else if (pauseMenuIndex == 1) {
                            applyFullscreenMode(!isFullscreen);
                        } else if (pauseMenuIndex == 2) {
                            startStage(currentStage, false);
                        } else if (pauseMenuIndex == 3) {
                            running = false;
                        }
                    } else if (btn == SDL_CONTROLLER_BUTTON_B) {
                        gameState = PLAYING;
                    }
                } else if (gameState != PLAYING) {
                    if (btn == SDL_CONTROLLER_BUTTON_A || btn == SDL_CONTROLLER_BUTTON_B || btn == SDL_CONTROLLER_BUTTON_X) {
                        if (gameState == CLEAR) {
                            if (currentStage == 1) {
                                startStage(2, true); // Advance to Stage 2 with bonus fuel
                            } else if (currentStage == 2) {
                                startStage(3, true); // Advance to Stage 3 with bonus fuel
                            } else {
                                startStage(1, false); // All stages clear, restart
                            }
                        } else {
                            // Game Over -> retry current stage
                            startStage(currentStage, false);
                        }
                    }
                }
            } else if (event.type == SDL_JOYBUTTONDOWN) {
                if (gameState == PAUSED) {
                    if (event.jbutton.button == 0 || event.jbutton.button == 1) {
                        if (pauseMenuIndex == 0) gameState = PLAYING;
                        else if (pauseMenuIndex == 1) applyFullscreenMode(!isFullscreen);
                        else if (pauseMenuIndex == 2) startStage(currentStage, false);
                        else if (pauseMenuIndex == 3) running = false;
                    }
                } else if (gameState != PLAYING) {
                    if (gameState == CLEAR) {
                        if (currentStage == 1) startStage(2, true);
                        else if (currentStage == 2) startStage(3, true);
                        else startStage(1, false);
                    } else {
                        startStage(currentStage, false);
                    }
                }
            } else if (event.type == SDL_MOUSEMOTION) {
                if (SDL_GetTicks() > 300 && (event.motion.xrel != 0 || event.motion.yrel != 0)) {
                    if (!cursorVisible) {
                        SDL_ShowCursor(SDL_ENABLE);
                        cursorVisible = true;
                    }
                    lastMouseMoveTime = SDL_GetTicks();
                }
            } else if (event.type == SDL_KEYDOWN) {
                SDL_Keycode sym = event.key.keysym.sym;
                if (sym == SDLK_q) {
                    running = false;
                } else if (sym == SDLK_ESCAPE || sym == SDLK_p || sym == SDLK_TAB) {
                    if (gameState == PLAYING) {
                        gameState = PAUSED;
                        audio.setEngine(AudioEngine::ENG_OFF);
                    } else if (gameState == PAUSED) {
                        gameState = PLAYING;
                    }
                } else if (gameState == PAUSED) {
                    if (sym == SDLK_UP || sym == SDLK_w) {
                        pauseMenuIndex = (pauseMenuIndex == 0 ? 3 : pauseMenuIndex - 1);
                    } else if (sym == SDLK_DOWN || sym == SDLK_s) {
                        pauseMenuIndex = (pauseMenuIndex == 3 ? 0 : pauseMenuIndex + 1);
                    } else if (sym == SDLK_LEFT || sym == SDLK_a || sym == SDLK_RIGHT || sym == SDLK_d) {
                        if (pauseMenuIndex == 1) {
                            applyFullscreenMode(!isFullscreen);
                        }
                    } else if (sym == SDLK_RETURN || sym == SDLK_SPACE) {
                        if (pauseMenuIndex == 0) {
                            gameState = PLAYING;
                        } else if (pauseMenuIndex == 1) {
                            applyFullscreenMode(!isFullscreen);
                        } else if (pauseMenuIndex == 2) {
                            startStage(currentStage, false);
                        } else if (pauseMenuIndex == 3) {
                            running = false;
                        }
                    }
                } else if (gameState != PLAYING) {
                    if (sym == SDLK_SPACE || sym == SDLK_RETURN) {
                        if (gameState == CLEAR) {
                            if (currentStage == 1) {
                                startStage(2, true); // Advance to Stage 2 with bonus fuel
                            } else if (currentStage == 2) {
                                startStage(3, true); // Advance to Stage 3 with bonus fuel
                            } else {
                                startStage(1, false); // All stages clear, restart
                            }
                        } else {
                            // Game Over -> retry current stage
                            startStage(currentStage, false);
                        }
                    }
                }
            }
        }

        // Auto-hide mouse cursor after 2 seconds of inactivity
        if (cursorVisible && (SDL_GetTicks() - lastMouseMoveTime >= 2000)) {
            SDL_ShowCursor(SDL_DISABLE);
            cursorVisible = false;
        }

        const Uint8* keys = SDL_GetKeyboardState(nullptr);

        // 2. Game Update Logic
        if (gameState == PLAYING) {
            frames++;
            if (matchFeedbackTimer > 0) matchFeedbackTimer--;

            // Determine road limits at player's current vertical position
            float pRoadLeft = 0.0f, pRoadRight = 0.0f;
            getRoadEdges(currentStage, roadOffset + (INTERNAL_HEIGHT - (player.y + CAR_HEIGHT / 2.0f)), trackDistance, pRoadLeft, pRoadRight);

            // Driving input flags (merged keyboard & controller)
            bool moveLeft = keys[SDL_SCANCODE_LEFT] || keys[SDL_SCANCODE_A];
            bool moveRight = keys[SDL_SCANCODE_RIGHT] || keys[SDL_SCANCODE_D];
            bool accel = keys[SDL_SCANCODE_UP] || keys[SDL_SCANCODE_W];
            bool brake = keys[SDL_SCANCODE_DOWN] || keys[SDL_SCANCODE_S];

            // Poll GameControllers
            for (auto* c : controllers) {
                // D-Pad
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_LEFT)) moveLeft = true;
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_RIGHT)) moveRight = true;
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_UP)) accel = true;
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_DPAD_DOWN)) brake = true;

                // Left Analog Stick
                Sint16 stickX = SDL_GameControllerGetAxis(c, SDL_CONTROLLER_AXIS_LEFTX);
                Sint16 stickY = SDL_GameControllerGetAxis(c, SDL_CONTROLLER_AXIS_LEFTY);
                if (stickX < -10000) moveLeft = true;
                if (stickX > 10000) moveRight = true;
                if (stickY < -10000) accel = true;
                if (stickY > 10000) brake = true;

                // Face Buttons & Triggers (Classic Road Fighter feel)
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_A) ||
                    SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_B) ||
                    SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_RIGHTSHOULDER) ||
                    SDL_GameControllerGetAxis(c, SDL_CONTROLLER_AXIS_TRIGGERRIGHT) > 8000) {
                    accel = true;
                }
                if (SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_X) ||
                    SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_Y) ||
                    SDL_GameControllerGetButton(c, SDL_CONTROLLER_BUTTON_LEFTSHOULDER) ||
                    SDL_GameControllerGetAxis(c, SDL_CONTROLLER_AXIS_TRIGGERLEFT) > 8000) {
                    brake = true;
                }
            }

            // Fallback for raw Joysticks
            for (auto* j : joysticks) {
                Sint16 jX = SDL_JoystickGetAxis(j, 0);
                Sint16 jY = SDL_JoystickGetAxis(j, 1);
                if (jX < -10000) moveLeft = true;
                if (jX > 10000) moveRight = true;
                if (jY < -10000) accel = true;
                if (jY > 10000) brake = true;

                Uint8 hat = SDL_JoystickGetHat(j, 0);
                if (hat & SDL_HAT_LEFT) moveLeft = true;
                if (hat & SDL_HAT_RIGHT) moveRight = true;
                if (hat & SDL_HAT_UP) accel = true;
                if (hat & SDL_HAT_DOWN) brake = true;

                if (SDL_JoystickGetButton(j, 0) || SDL_JoystickGetButton(j, 1)) accel = true;
                if (SDL_JoystickGetButton(j, 2) || SDL_JoystickGetButton(j, 3)) brake = true;
            }

            // Steering & speed inputs
            if (!player.isSpinning) {
                if (moveLeft && player.x > pRoadLeft + 3.0f) {
                    player.x -= 5.0f;
                }
                if (moveRight && player.x < pRoadRight - CAR_WIDTH - 3.0f) {
                    player.x += 5.0f;
                }

                // Strict clamping within current street borders
                player.x = std::clamp(player.x, pRoadLeft + 3.0f, pRoadRight - CAR_WIDTH - 3.0f);

                isPlayerBraking = brake;
                if (accel) {
                    speedMultiplier = 1.5f;
                } else if (brake) {
                    speedMultiplier = 0.5f;
                } else {
                    speedMultiplier = 1.0f;
                }
            } else {
                isPlayerBraking = false;
            }

            // Engine sound state
            AudioEngine::EngineState targetEng = AudioEngine::ENG_LOW;
            if (player.isSpinning) {
                targetEng = AudioEngine::ENG_LOW;
            } else {
                if (speedMultiplier == 0.5f) targetEng = AudioEngine::ENG_LOW;
                else if (speedMultiplier == 1.0f) targetEng = AudioEngine::ENG_MID;
                else if (speedMultiplier == 1.5f) targetEng = AudioEngine::ENG_HIGH;
            }

            if (targetEng != curEngState) {
                curEngState = targetEng;
                audio.setEngine(curEngState);
            }

            // Physics & Fuel (skids and stops briefly upon collision)
            float scrollSpeed = 0.0f;
            if (player.isSpinning) {
                int elapsed = frames - player.spinStartFrame;
                float progress = static_cast<float>(elapsed) / 50.0f;

                // Stop forward momentum briefly during skid
                scrollSpeed = 0.0f;
                fuel -= FUEL_DEPLETION_RATE;

                // Fishtail / skid wobble motion
                if (elapsed < 20) {
                    player.spinAngle = std::sin(elapsed * 0.75f) * 28.0f;
                    player.x += std::sin(elapsed * 0.75f) * 2.2f;
                } else if (elapsed < 36) {
                    player.spinAngle += 20.0f;
                } else {
                    player.spinAngle = std::sin(elapsed * 0.4f) * 10.0f * (1.0f - progress);
                }

                player.x = std::clamp(player.x, pRoadLeft + 3.0f, pRoadRight - CAR_WIDTH - 3.0f);

                // Spawn skid marks under rear tires
                if (elapsed < 36 && (elapsed % 2 == 0)) {
                    skidMarks.push_back({player.x + 6.0f, player.y + CAR_HEIGHT - 12.0f, player.x + 6.0f, player.y + CAR_HEIGHT - 4.0f, 220.0f});
                    skidMarks.push_back({player.x + CAR_WIDTH - 6.0f, player.y + CAR_HEIGHT - 12.0f, player.x + CAR_WIDTH - 6.0f, player.y + CAR_HEIGHT - 4.0f, 220.0f});
                }

                // Spawn tire smoke puffs
                if (elapsed < 32 && (elapsed % 3 == 0)) {
                    smokeParticles.push_back({player.x + 6.0f + (rng() % 7 - 3), player.y + CAR_HEIGHT - 8.0f, (static_cast<int>(rng() % 21) - 10) * 0.1f, -0.6f, 5.0f, 180.0f});
                    smokeParticles.push_back({player.x + CAR_WIDTH - 6.0f + (rng() % 7 - 3), player.y + CAR_HEIGHT - 8.0f, (static_cast<int>(rng() % 21) - 10) * 0.1f, -0.6f, 5.0f, 180.0f});
                }

                if (elapsed > 50) {
                    player.isSpinning = false;
                    player.spinAngle = 0.0f;
                    player.color = COLOR_PLAYER;
                }
            } else {
                scrollSpeed = BASE_SCROLL_SPEED * speedMultiplier;
                score += scrollSpeed * 0.1f;
                trackDistance += scrollSpeed;
                fuel -= FUEL_DEPLETION_RATE * speedMultiplier;
            }

            roadOffset += scrollSpeed;

            // Update Skid marks
            for (auto it = skidMarks.begin(); it != skidMarks.end();) {
                it->y1 += scrollSpeed;
                it->y2 += scrollSpeed;
                it->alpha -= (scrollSpeed > 0.0f ? 1.5f : 0.4f);
                if (it->y1 > INTERNAL_HEIGHT || it->alpha <= 0.0f) {
                    it = skidMarks.erase(it);
                } else {
                    ++it;
                }
            }

            // Update Smoke particles
            for (auto it = smokeParticles.begin(); it != smokeParticles.end();) {
                it->x += it->vx;
                it->y += it->vy + scrollSpeed * 0.5f;
                it->size += 0.25f;
                it->alpha -= 5.0f;
                if (it->alpha <= 0.0f) {
                    it = smokeParticles.erase(it);
                } else {
                    ++it;
                }
            }

            // Check goal & fuel conditions:
            // Race is won ONLY when the player's car physically touches and crosses the finish line!
            if (trackDistance >= STAGE_TRACK_LENGTH + 20.0f) {
                gameState = CLEAR;
                audio.setEngine(AudioEngine::ENG_OFF);
                audio.playClear();
            } else if (fuel <= 0.0f) {
                gameState = OVER;
                audio.setEngine(AudioEngine::ENG_OFF);
                audio.playGameOver();
            }

            // Enemy Spawning (clears on home stretch near finish line)
            if (frames % 40 == 0 && std::uniform_real_distribution<float>(0.0f, 1.0f)(rng) < 0.6f && trackDistance < STAGE_TRACK_LENGTH - 1200.0f) {
                float topRoadLeft, topRoadRight;
                getRoadEdges(currentStage, roadOffset + INTERNAL_HEIGHT, trackDistance, topRoadLeft, topRoadRight);
                float availWidth = topRoadRight - topRoadLeft;

                int numLanes = (availWidth < 300.0f) ? 2 : ((availWidth < 370.0f) ? 3 : 4);
                float laneW = availWidth / numLanes;
                std::vector<int> availableLanes;

                for (int lane = 0; lane < numLanes; ++lane) {
                    int lx = static_cast<int>(topRoadLeft + lane * laneW + (laneW - CAR_WIDTH) / 2.0f);
                    bool laneClear = true;
                    for (const auto& e : enemies) {
                        if (std::abs(e.x - lx) < laneW - 5.0f && e.y < CAR_HEIGHT * 2.5f) {
                            laneClear = false;
                            break;
                        }
                    }
                    if (laneClear) availableLanes.push_back(lx);
                }

                if (!availableLanes.empty()) {
                    int ex = availableLanes[std::uniform_int_distribution<size_t>(0, availableLanes.size() - 1)(rng)];
                    Car eCar;
                    eCar.x = static_cast<float>(ex);
                    eCar.y = -static_cast<float>(CAR_HEIGHT);
                    eCar.isPlayer = false;

                    const auto& stageKana = getStageKana(currentStage);
                    if (std::uniform_real_distribution<float>(0.0f, 1.0f)(rng) > 0.4f) {
                        eCar.data = player.data;
                    } else {
                        eCar.data = stageKana[std::uniform_int_distribution<size_t>(0, stageKana.size() - 1)(rng)];
                    }
                    eCar.color = eCar.data.color;
                    eCar.speed = 1.5f + std::uniform_real_distribution<float>(0.0f, 1.5f)(rng);
                    enemies.push_back(eCar);
                }
            }

            // Move enemies & clamp within narrowing street borders
            for (auto it = enemies.begin(); it != enemies.end();) {
                it->y += (scrollSpeed - it->speed);
                float eLeft, eRight;
                getRoadEdges(currentStage, roadOffset + (INTERNAL_HEIGHT - (it->y + CAR_HEIGHT / 2.0f)), trackDistance, eLeft, eRight);
                it->x = std::clamp(it->x, eLeft + 2.0f, eRight - CAR_WIDTH - 2.0f);

                if (it->y > INTERNAL_HEIGHT) {
                    it = enemies.erase(it);
                } else {
                    ++it;
                }
            }

            // Traffic collision avoidance (cars never overlap)
            std::sort(enemies.begin(), enemies.end(), [](const Car& a, const Car& b) { return a.y < b.y; });
            for (size_t i = 0; i < enemies.size(); ++i) {
                for (size_t j = i + 1; j < enemies.size(); ++j) {
                    Car& eFront = enemies[i];
                    Car& eBehind = enemies[j];
                    if (std::abs(eFront.x - eBehind.x) < CAR_WIDTH) {
                        float minGap = CAR_HEIGHT + 15.0f;
                        if (eBehind.y - eFront.y < minGap) {
                            eBehind.y = eFront.y + minGap;
                            eBehind.speed = std::min(eBehind.speed, eFront.speed);
                        }
                    }
                }
            }

            // Player collision check
            for (auto it = enemies.begin(); it != enemies.end();) {
                SDL_FRect pRect = {player.x + 5, player.y + 5, CAR_WIDTH - 10.0f, CAR_HEIGHT - 10.0f};
                SDL_FRect eRect = {it->x + 5, it->y + 5, CAR_WIDTH - 10.0f, CAR_HEIGHT - 10.0f};

                if (!player.isSpinning && SDL_HasIntersectionF(&pRect, &eRect)) {
                    if (it->data.romaji == player.data.romaji) {
                        // Correct -> Refuel
                        fuel = std::min(MAX_FUEL, fuel + FUEL_REWARD);
                        score += 50.0f;
                        const auto& stageKana = getStageKana(currentStage);
                        player.data = stageKana[std::uniform_int_distribution<size_t>(0, stageKana.size() - 1)(rng)];
                        audio.playGas();
                        rumble(0x3000, 0x8000, 160);
                        matchFeedbackTimer = 90;
                        lastMatchSuccess = true;
                        matchStreak++;
                        it = enemies.erase(it);
                    } else {
                        // Wrong -> Collision! Skid and stop briefly
                        fuel -= FUEL_PENALTY;
                        player.isSpinning = true;
                        player.spinStartFrame = frames;
                        player.color = {160, 160, 160, 255};
                        audio.playCrash();
                        audio.playSkid();
                        rumble(0xFFFF, 0xFFFF, 400);
                        matchFeedbackTimer = 90;
                        lastMatchSuccess = false;
                        matchStreak = 0;
                        it = enemies.erase(it);
                    }
                } else {
                    ++it;
                }
            }
        }

        // 3. Render Game Scene to Internal 16:10 (1280x800) Target Texture
        SDL_SetRenderTarget(renderer, targetTexture);
        SDL_SetRenderDrawColor(renderer, COLOR_BG.r, COLOR_BG.g, COLOR_BG.b, 255);
        SDL_RenderClear(renderer);

        // =========================================================================
        // --- CENTRAL GAMEPLAY VIEWPORT (x: GAME_X to GAME_X + GAME_W) ---
        // =========================================================================
        if (currentStage == 1) {
            // Stage 1: Forest Highway with Curbs, Rumble Strips & 4 Distinct Lanes
            // --- 1. Procedural Textured Grass Turf Verges ---
            GameTextures::drawTiled(renderer, textures.grassTex, GAME_X, 0, ROAD_MARGIN, INTERNAL_HEIGHT, 0, static_cast<int>(roadOffset), 256, 256);
            GameTextures::drawTiled(renderer, textures.grassTex, GAME_X + GAME_W - ROAD_MARGIN, 0, ROAD_MARGIN, INTERNAL_HEIGHT, 0, static_cast<int>(roadOffset), 256, 256);

            // Alternating mowed turf bands (semi-transparent tint over grass texture)
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 20, 80, 25, 60);
            for (int i = -100; i < INTERNAL_HEIGHT + 100; i += 70) {
                int y = (static_cast<int>(i + roadOffset) % (INTERNAL_HEIGHT + 70)) - 70;
                SDL_Rect bL = {GAME_X, y, ROAD_MARGIN, 35};
                SDL_Rect bR = {GAME_X + GAME_W - ROAD_MARGIN, y, ROAD_MARGIN, 35};
                SDL_RenderFillRect(renderer, &bL);
                SDL_RenderFillRect(renderer, &bR);
            }
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            // Roadside wildflowers in the grass
            for (int i = 0; i < 16; ++i) {
                int y = (static_cast<int>(i * 53 + roadOffset) % INTERNAL_HEIGHT);
                int fxL = GAME_X + 10 + (i * 17) % (ROAD_MARGIN - 24);
                int fxR = GAME_X + GAME_W - ROAD_MARGIN + 10 + (i * 23) % (ROAD_MARGIN - 24);
                SDL_Color fCol = (i % 3 == 0) ? SDL_Color{255, 245, 100, 255} : (i % 3 == 1 ? SDL_Color{255, 255, 255, 255} : SDL_Color{255, 100, 100, 255});
                SDL_SetRenderDrawColor(renderer, fCol.r, fCol.g, fCol.b, 255);
                SDL_Rect f1 = {fxL, y, 2, 2};
                SDL_Rect f2 = {fxR, (y + 35) % INTERNAL_HEIGHT, 2, 2};
                SDL_RenderFillRect(renderer, &f1);
                SDL_RenderFillRect(renderer, &f2);
            }

            // Roadside Trees (varied broadleaf and pine conifers)
            for (int i = -2; i < 8; ++i) {
                int y = (static_cast<int>(i * 130 + roadOffset) % (INTERNAL_HEIGHT + 130)) - 65;
                drawTree(renderer, GAME_X + 26, y, i % 2);
            }
            for (int i = -2; i < 10; ++i) {
                int y = (static_cast<int>(i * 85 + roadOffset) % (INTERNAL_HEIGHT + 85)) - 40;
                int tx = (GAME_X + GAME_W - 26) + (i % 2 == 0 ? 8 : -8);
                drawTree(renderer, tx, y, (i + 1) % 2);
            }

            // --- 2. Roadside Shoulder & Gravel Strip ---
            SDL_SetRenderDrawColor(renderer, 95, 88, 76, 255);
            SDL_Rect shL = {GAME_X + ROAD_MARGIN - 14, 0, 6, INTERNAL_HEIGHT};
            SDL_Rect shR = {GAME_X + ROAD_MARGIN + ROAD_WIDTH + 8, 0, 6, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &shL);
            SDL_RenderFillRect(renderer, &shR);

            // --- 3. Racing Rumble Strip Curbs (Red & White) ---
            for (int y = -32; y < INTERNAL_HEIGHT + 32; y += 4) {
                bool isRed = (((y + static_cast<int>(roadOffset)) / 20) % 2 == 0);
                if (isRed) SDL_SetRenderDrawColor(renderer, 225, 40, 40, 255);
                else SDL_SetRenderDrawColor(renderer, 245, 245, 245, 255);
                SDL_Rect curbL = {GAME_X + ROAD_MARGIN - 8, y, 8, 4};
                SDL_Rect curbR = {GAME_X + ROAD_MARGIN + ROAD_WIDTH, y, 8, 4};
                SDL_RenderFillRect(renderer, &curbL);
                SDL_RenderFillRect(renderer, &curbR);
            }
            // Inner curb white highlight line
            SDL_SetRenderDrawColor(renderer, 220, 220, 220, 255);
            SDL_Rect cEdgeL = {GAME_X + ROAD_MARGIN - 1, 0, 1, INTERNAL_HEIGHT};
            SDL_Rect cEdgeR = {GAME_X + ROAD_MARGIN + ROAD_WIDTH, 0, 1, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &cEdgeL);
            SDL_RenderFillRect(renderer, &cEdgeR);

            // --- 4. Textured Asphalt Road Surface ---
            GameTextures::drawTiled(renderer, textures.asphaltTex, GAME_X + ROAD_MARGIN, 0, ROAD_WIDTH, INTERNAL_HEIGHT, 0, static_cast<int>(roadOffset), 256, 256);

            // Outer solid edge lines
            SDL_SetRenderDrawColor(renderer, COLOR_EDGE.r, COLOR_EDGE.g, COLOR_EDGE.b, 255);
            SDL_Rect edgeL = {GAME_X + ROAD_MARGIN + 3, 0, 3, INTERNAL_HEIGHT};
            SDL_Rect edgeR = {GAME_X + ROAD_MARGIN + ROAD_WIDTH - 6, 0, 3, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &edgeL);
            SDL_RenderFillRect(renderer, &edgeR);

            // --- 5. 4-Lane Dashed Road Markings (3 Divider Lines) ---
            constexpr int laneW = ROAD_WIDTH / 4; // 105px per lane
            for (int i = -100; i < INTERNAL_HEIGHT + 100; i += 60) {
                int y = (static_cast<int>(i + roadOffset) % (INTERNAL_HEIGHT + 60)) - 60;
                
                // Lane 1/2 Divider (dashed white)
                SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                SDL_Rect d1 = {GAME_X + ROAD_MARGIN + laneW - 1, y, 3, 28};
                SDL_RenderFillRect(renderer, &d1);

                // Center Highway Divider (bright amber / yellow double dash)
                SDL_SetRenderDrawColor(renderer, 255, 215, 30, 255);
                SDL_Rect d2a = {GAME_X + ROAD_MARGIN + laneW * 2 - 3, y, 2, 28};
                SDL_Rect d2b = {GAME_X + ROAD_MARGIN + laneW * 2 + 1, y, 2, 28};
                SDL_RenderFillRect(renderer, &d2a);
                SDL_RenderFillRect(renderer, &d2b);

                // Lane 3/4 Divider (dashed white)
                SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                SDL_Rect d3 = {GAME_X + ROAD_MARGIN + laneW * 3 - 1, y, 3, 28};
                SDL_RenderFillRect(renderer, &d3);
            }
        } else if (currentStage == 2) {
            // Stage 2: Elevated Coastal Highway Bridge over Dynamic Ocean Waters
            constexpr int SLICE_H = 4;
            float waveTime = frames * 0.04f;

            // Deep ocean base water
            SDL_SetRenderDrawColor(renderer, COLOR_WATER_DEEP.r, COLOR_WATER_DEEP.g, COLOR_WATER_DEEP.b, 255);
            SDL_Rect oceanBg = {GAME_X, 0, GAME_W, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &oceanBg);

            // Shimmering caustic water texture overlay
            int waterOffsetX = static_cast<int>(std::sin(waveTime * 0.8f) * 24.0f);
            int waterOffsetY = static_cast<int>(roadOffset * 0.25f + waveTime * 20.0f);
            GameTextures::drawTiled(renderer, textures.waterTex, GAME_X, 0, GAME_W, INTERNAL_HEIGHT, waterOffsetX, waterOffsetY, 256, 256);

            for (int y = 0; y < INTERNAL_HEIGHT; y += SLICE_H) {
                float worldY = roadOffset + (INTERNAL_HEIGHT - y);
                float rLeft = 0.0f, rRight = 0.0f;
                getRoadEdges(2, worldY, trackDistance, rLeft, rRight);

                // Bridge deck bounds
                int deckL = static_cast<int>(rLeft) - 18;
                int deckR = static_cast<int>(rRight) + 18;
                int shadowL = deckL - 10;
                int shadowR = deckR + 10;

                // Rolling ocean swells with alpha blending so water caustics shimmer through
                SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
                int waveBand = (static_cast<int>(y * 0.45f + roadOffset * 0.2f + std::sin(waveTime + y * 0.02f) * 10.0f)) % 40;
                if (waveBand < 12) {
                    SDL_SetRenderDrawColor(renderer, COLOR_WATER_MID.r, COLOR_WATER_MID.g, COLOR_WATER_MID.b, 175);
                    if (shadowL > GAME_X + 4) {
                        SDL_Rect swellL = {GAME_X, y, shadowL - GAME_X, SLICE_H};
                        SDL_RenderFillRect(renderer, &swellL);
                    }
                    if (GAME_X + GAME_W > shadowR) {
                        SDL_Rect swellR = {shadowR, y, (GAME_X + GAME_W) - shadowR, SLICE_H};
                        SDL_RenderFillRect(renderer, &swellR);
                    }
                } else if (waveBand < 18) {
                    SDL_SetRenderDrawColor(renderer, COLOR_WATER_SWELL.r, COLOR_WATER_SWELL.g, COLOR_WATER_SWELL.b, 195);
                    if (shadowL > GAME_X + 8) {
                        SDL_Rect swellL = {GAME_X + 2, y, shadowL - GAME_X - 2, SLICE_H};
                        SDL_RenderFillRect(renderer, &swellL);
                    }
                    if ((GAME_X + GAME_W) - shadowR > 8) {
                        SDL_Rect swellR = {shadowR + 2, y, (GAME_X + GAME_W) - shadowR - 4, SLICE_H};
                        SDL_RenderFillRect(renderer, &swellR);
                    }
                }
                SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

                // Foaming wave crests
                int foamBand = (static_cast<int>(y * 0.35f + roadOffset * 0.15f + std::cos(waveTime * 1.3f + y * 0.03f) * 8.0f)) % 55;
                if (foamBand < 3) {
                    SDL_SetRenderDrawColor(renderer, COLOR_WATER_FOAM.r, COLOR_WATER_FOAM.g, COLOR_WATER_FOAM.b, 255);
                    int crestOffset = static_cast<int>(std::sin(waveTime + y * 0.05f) * 6.0f);
                    if (shadowL > GAME_X + 22) {
                        SDL_Rect foamL = {GAME_X + 6 + crestOffset, y + 1, std::max(4, shadowL - GAME_X - 16), 2};
                        SDL_RenderFillRect(renderer, &foamL);
                    }
                    if ((GAME_X + GAME_W) - shadowR > 22) {
                        SDL_Rect foamR = {shadowR + 4 - crestOffset, y + 1, std::max(4, (GAME_X + GAME_W) - shadowR - 16), 2};
                        SDL_RenderFillRect(renderer, &foamR);
                    }
                }

                // --- 2. Submerged Concrete Bridge Pylons & Water Wake ---
                int pylonCycle = static_cast<int>(worldY) % 360;
                if (pylonCycle < 28) {
                    int pylonW = 16;
                    SDL_SetRenderDrawColor(renderer, 130, 135, 140, 255);
                    SDL_Rect pylonL = {deckL - 22, y, pylonW, SLICE_H};
                    SDL_Rect pylonR = {deckR + 6, y, pylonW, SLICE_H};
                    SDL_RenderFillRect(renderer, &pylonL);
                    SDL_RenderFillRect(renderer, &pylonR);

                    SDL_SetRenderDrawColor(renderer, 175, 180, 185, 255);
                    SDL_Rect pLHighlight = {deckL - 22, y, 4, SLICE_H};
                    SDL_Rect pRHighlight = {deckR + 6, y, 4, SLICE_H};
                    SDL_RenderFillRect(renderer, &pLHighlight);
                    SDL_RenderFillRect(renderer, &pRHighlight);

                    if (pylonCycle < 6 || pylonCycle > 22) {
                        SDL_SetRenderDrawColor(renderer, COLOR_WATER_FOAM.r, COLOR_WATER_FOAM.g, COLOR_WATER_FOAM.b, 255);
                        SDL_Rect wakeL = {deckL - 25, y, pylonW + 6, 1};
                        SDL_Rect wakeR = {deckR + 3, y, pylonW + 6, 1};
                        SDL_RenderFillRect(renderer, &wakeL);
                        SDL_RenderFillRect(renderer, &wakeR);
                    }
                }

                // --- 3. Elevated Bridge Shadow Cast onto Water ---
                SDL_SetRenderDrawColor(renderer, COLOR_BRIDGE_SHADOW.r, COLOR_BRIDGE_SHADOW.g, COLOR_BRIDGE_SHADOW.b, 255);
                if (deckL > GAME_X + 10) {
                    SDL_Rect shL = {deckL - 10, y, 10, SLICE_H};
                    SDL_RenderFillRect(renderer, &shL);
                }
                if (GAME_X + GAME_W >= deckR + 10) {
                    SDL_Rect shR = {deckR, y, 10, SLICE_H};
                    SDL_RenderFillRect(renderer, &shR);
                }

                // --- 4. Outer Bridge Deck / Concrete Catwalk ---
                GameTextures::drawTiled(renderer, textures.concreteTex, deckL, y, 12, SLICE_H, 0, static_cast<int>(roadOffset), 256, 256);
                GameTextures::drawTiled(renderer, textures.concreteTex, deckR - 12, y, 12, SLICE_H, 0, static_cast<int>(roadOffset), 256, 256);

                // Catwalk expansion grooves
                if ((static_cast<int>(worldY) % 36) < 2) {
                    SDL_SetRenderDrawColor(renderer, COLOR_WALKWAY_DARK.r, COLOR_WALKWAY_DARK.g, COLOR_WALKWAY_DARK.b, 255);
                    SDL_Rect walkL = {deckL, y, 12, SLICE_H};
                    SDL_Rect walkR = {deckR - 12, y, 12, SLICE_H};
                    SDL_RenderFillRect(renderer, &walkL);
                    SDL_RenderFillRect(renderer, &walkR);
                }

                // Outer steel safety railing
                SDL_SetRenderDrawColor(renderer, COLOR_RAILING.r, COLOR_RAILING.g, COLOR_RAILING.b, 255);
                SDL_Rect railL = {deckL, y, 2, SLICE_H};
                SDL_Rect railR = {deckR - 2, y, 2, SLICE_H};
                SDL_RenderFillRect(renderer, &railL);
                SDL_RenderFillRect(renderer, &railR);

                // Vertical steel railing stanchions
                if ((static_cast<int>(worldY) % 18) < 3) {
                    SDL_SetRenderDrawColor(renderer, 40, 44, 48, 255);
                    SDL_Rect postL = {deckL, y, 4, SLICE_H};
                    SDL_Rect postR = {deckR - 4, y, 4, SLICE_H};
                    SDL_RenderFillRect(renderer, &postL);
                    SDL_RenderFillRect(renderer, &postR);

                    SDL_SetRenderDrawColor(renderer, 220, 225, 230, 255);
                    SDL_Rect capL = {deckL, y, 3, 2};
                    SDL_Rect capR = {deckR - 3, y, 3, 2};
                    SDL_RenderFillRect(renderer, &capL);
                    SDL_RenderFillRect(renderer, &capR);
                }

                // --- 5. Road Asphalt & 4-Lane Dashed Markings ---
                GameTextures::drawTiled(renderer, textures.asphaltTex, static_cast<int>(rLeft), y, static_cast<int>(rRight - rLeft), SLICE_H, 0, static_cast<int>(roadOffset), 256, 256);

                // 4-Lane Dashed Road Markings on Bridge (3 divider lines)
                float rW = rRight - rLeft;
                float bLaneW = rW / 4.0f;
                if (((y + static_cast<int>(roadOffset)) % 60) < 30) {
                    // Lane 1/2 divider (dashed white)
                    SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                    int x1 = static_cast<int>(rLeft + bLaneW);
                    SDL_Rect d1 = {x1 - 1, y, 2, SLICE_H};
                    SDL_RenderFillRect(renderer, &d1);

                    // Center highway divider (amber double dash)
                    SDL_SetRenderDrawColor(renderer, 255, 215, 30, 255);
                    int x2 = static_cast<int>(rLeft + bLaneW * 2.0f);
                    SDL_Rect d2 = {x2 - 1, y, 3, SLICE_H};
                    SDL_RenderFillRect(renderer, &d2);

                    // Lane 3/4 divider (dashed white)
                    SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                    int x3 = static_cast<int>(rLeft + bLaneW * 3.0f);
                    SDL_Rect d3 = {x3 - 1, y, 2, SLICE_H};
                    SDL_RenderFillRect(renderer, &d3);
                }

                // --- 6. Hazard-Striped Road Curbs & Guardrails ---
                bool isRed = (((y + static_cast<int>(roadOffset)) / 16) % 2 == 0);
                if (isRed) SDL_SetRenderDrawColor(renderer, COLOR_BARRIER_RED.r, COLOR_BARRIER_RED.g, COLOR_BARRIER_RED.b, 255);
                else SDL_SetRenderDrawColor(renderer, 245, 245, 245, 255);

                SDL_Rect barL = {static_cast<int>(rLeft) - 6, y, 6, SLICE_H};
                SDL_Rect barR = {static_cast<int>(rRight), y, 6, SLICE_H};
                SDL_RenderFillRect(renderer, &barL);
                SDL_RenderFillRect(renderer, &barR);

                // Inner curb bevel highlight line
                SDL_SetRenderDrawColor(renderer, 210, 210, 210, 255);
                SDL_Rect curbEdgeL = {static_cast<int>(rLeft) - 1, y, 1, SLICE_H};
                SDL_Rect curbEdgeR = {static_cast<int>(rRight), y, 1, SLICE_H};
                SDL_RenderFillRect(renderer, &curbEdgeL);
                SDL_RenderFillRect(renderer, &curbEdgeR);
            }
        } else {
            // Stage 3: Coastal Beach Highway (Authentic NES Road Fighter Stage 3)
            constexpr int SLICE_H = 4;
            float waveTime = frames * 0.04f;

            // 1. Base Ground (Sunny golden beach sand)
            SDL_SetRenderDrawColor(renderer, COLOR_SAND.r, COLOR_SAND.g, COLOR_SAND.b, 255);
            SDL_Rect sandBg = {GAME_X, 0, GAME_W, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &sandBg);

            // Tiled golden sand texture over the beach area
            GameTextures::drawTiled(renderer, textures.sandTex, GAME_X, 0, GAME_W / 2 + 60, INTERNAL_HEIGHT, 0, static_cast<int>(roadOffset), 256, 256);

            // Alternating soft sand dune ripples
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, COLOR_SAND_DUNE.r, COLOR_SAND_DUNE.g, COLOR_SAND_DUNE.b, 75);
            for (int i = -100; i < INTERNAL_HEIGHT + 100; i += 80) {
                int y = (static_cast<int>(i + roadOffset * 0.7f) % (INTERNAL_HEIGHT + 80)) - 80;
                SDL_Rect dL = {GAME_X, y, ROAD_MARGIN + 20, 36};
                SDL_RenderFillRect(renderer, &dL);
            }
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            // Coastal Beach Props (Beach Parasols, Surfboards, Sunbeds on the sandy beach)
            for (int i = -1; i < 7; ++i) {
                int sy = (static_cast<int>(i * 155 + roadOffset) % (INTERNAL_HEIGHT + 155)) - 60;
                int px = GAME_X + 18 + (std::abs(i * 19) % 28);
                drawBeachProp(renderer, px, sy, std::abs(i) % 3);
            }

            // Roadside Coconut Palm Trees (swaying gently in the tropical breeze)
            for (int i = -2; i < 9; ++i) {
                int py = (static_cast<int>(i * 125 + roadOffset) % (INTERNAL_HEIGHT + 125)) - 55;
                int px = GAME_X + 22 + (i % 2 == 0 ? 8 : -6);
                drawPalmTree(renderer, px, py, frames, std::abs(i * 37 + 13));
            }

            // Wild coastal beach grass tufts
            SDL_SetRenderDrawColor(renderer, COLOR_PALM_LEAF_1.r, COLOR_PALM_LEAF_1.g, COLOR_PALM_LEAF_1.b, 255);
            for (int i = 0; i < 18; ++i) {
                int gy = (static_cast<int>(i * 47 + roadOffset) % INTERNAL_HEIGHT);
                int gx = GAME_X + 8 + (i * 23) % (ROAD_MARGIN - 20);
                SDL_Rect g1 = {gx, gy, 3, 5};
                SDL_Rect g2 = {gx + 2, gy - 2, 2, 4};
                SDL_RenderFillRect(renderer, &g1);
                SDL_RenderFillRect(renderer, &g2);
            }

            // 2. Slice-by-Slice Road & Shoreline Ocean Rendering
            for (int y = 0; y < INTERNAL_HEIGHT; y += SLICE_H) {
                float worldY = roadOffset + (INTERNAL_HEIGHT - y);
                float rLeft = 0.0f, rRight = 0.0f;
                getRoadEdges(3, worldY, trackDistance, rLeft, rRight);

                int iLeft = static_cast<int>(rLeft);
                int iRight = static_cast<int>(rRight);
                int rWidth = iRight - iLeft;

                // --- A. Right Side: Tropical Ocean Waters & Shoreline Surf ---
                int shoreX = iRight + 16;
                if (shoreX < GAME_X + GAME_W) {
                    int oceanW = (GAME_X + GAME_W) - shoreX;

                    // Deep azure base water
                    SDL_SetRenderDrawColor(renderer, COLOR_TROPICAL_DEEP.r, COLOR_TROPICAL_DEEP.g, COLOR_TROPICAL_DEEP.b, 255);
                    SDL_Rect sea = {shoreX, y, oceanW, SLICE_H};
                    SDL_RenderFillRect(renderer, &sea);

                    // Tropical turquoise mid swells
                    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
                    int waveBand = (static_cast<int>(y * 0.4f + roadOffset * 0.2f + std::sin(waveTime + y * 0.03f) * 12.0f)) % 45;
                    if (waveBand < 16) {
                        SDL_SetRenderDrawColor(renderer, COLOR_TROPICAL_MID.r, COLOR_TROPICAL_MID.g, COLOR_TROPICAL_MID.b, 200);
                        SDL_RenderFillRect(renderer, &sea);
                    } else if (waveBand < 24) {
                        SDL_SetRenderDrawColor(renderer, COLOR_TROPICAL_SURF.r, COLOR_TROPICAL_SURF.g, COLOR_TROPICAL_SURF.b, 180);
                        SDL_RenderFillRect(renderer, &sea);
                    }
                    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

                    // Wet shoreline sand band where waves lap the beach
                    int tide = static_cast<int>(std::sin(waveTime * 1.2f + y * 0.04f) * 8.0f);
                    int wetSandW = std::min(oceanW, 14 + tide);
                    if (wetSandW > 0) {
                        SDL_SetRenderDrawColor(renderer, COLOR_SAND_WET.r, COLOR_SAND_WET.g, COLOR_SAND_WET.b, 255);
                        SDL_Rect wetR = {shoreX, y, wetSandW, SLICE_H};
                        SDL_RenderFillRect(renderer, &wetR);
                    }

                    // Foaming white wave crest rolling onto the wet sand
                    int foamBand = (static_cast<int>(y * 0.35f + roadOffset * 0.15f + std::cos(waveTime * 1.4f + y * 0.03f) * 10.0f)) % 50;
                    if (foamBand < 4) {
                        SDL_SetRenderDrawColor(renderer, COLOR_TROPICAL_FOAM.r, COLOR_TROPICAL_FOAM.g, COLOR_TROPICAL_FOAM.b, 255);
                        int fx = shoreX + std::max(0, wetSandW - 4);
                        int fw = std::min(oceanW - (fx - shoreX), 18);
                        if (fw > 0) {
                            SDL_Rect foam = {fx, y + 1, fw, 2};
                            SDL_RenderFillRect(renderer, &foam);
                        }
                    }

                    // Wooden pier breakwaters extending into the surf every 240px
                    int pierCycle = static_cast<int>(worldY) % 240;
                    if (pierCycle < 14) {
                        SDL_SetRenderDrawColor(renderer, 95, 62, 34, 255);
                        SDL_Rect pier = {shoreX + 6, y, std::min(oceanW - 8, 38), SLICE_H};
                        SDL_RenderFillRect(renderer, &pier);

                        // Wood plank highlight
                        SDL_SetRenderDrawColor(renderer, 130, 88, 48, 255);
                        SDL_Rect pHL = {shoreX + 6, y, 3, SLICE_H};
                        SDL_RenderFillRect(renderer, &pHL);

                        // White foam splashing on pier
                        SDL_SetRenderDrawColor(renderer, COLOR_TROPICAL_FOAM.r, COLOR_TROPICAL_FOAM.g, COLOR_TROPICAL_FOAM.b, 255);
                        SDL_Rect sp = {shoreX + 4, y, 2, SLICE_H};
                        SDL_RenderFillRect(renderer, &sp);
                    }
                }

                // --- B. Sandy Roadside Shoulders ---
                SDL_SetRenderDrawColor(renderer, COLOR_SAND_DUNE.r, COLOR_SAND_DUNE.g, COLOR_SAND_DUNE.b, 255);
                SDL_Rect shL = {iLeft - 14, y, 6, SLICE_H};
                SDL_Rect shR = {iRight + 8, y, 8, SLICE_H};
                SDL_RenderFillRect(renderer, &shL);
                SDL_RenderFillRect(renderer, &shR);

                // --- C. Classic NES Road Fighter Red & White Rumble Strip Curbs ---
                bool isRed = (((y + static_cast<int>(roadOffset)) / 20) % 2 == 0);
                if (isRed) SDL_SetRenderDrawColor(renderer, 225, 40, 40, 255);
                else SDL_SetRenderDrawColor(renderer, 245, 245, 245, 255);

                SDL_Rect curbL = {iLeft - 8, y, 8, SLICE_H};
                SDL_Rect curbR = {iRight, y, 8, SLICE_H};
                SDL_RenderFillRect(renderer, &curbL);
                SDL_RenderFillRect(renderer, &curbR);

                // Inner curb white highlight line
                SDL_SetRenderDrawColor(renderer, 225, 225, 225, 255);
                SDL_Rect cEdgeL = {iLeft - 1, y, 1, SLICE_H};
                SDL_Rect cEdgeR = {iRight, y, 1, SLICE_H};
                SDL_RenderFillRect(renderer, &cEdgeL);
                SDL_RenderFillRect(renderer, &cEdgeR);

                // --- D. Sun-Warmed Coastal Asphalt Surface ---
                GameTextures::drawTiled(renderer, textures.asphaltTex, iLeft, y, rWidth, SLICE_H, 0, static_cast<int>(roadOffset), 256, 256);

                // Outer solid edge lines
                SDL_SetRenderDrawColor(renderer, COLOR_EDGE.r, COLOR_EDGE.g, COLOR_EDGE.b, 255);
                SDL_Rect edgeL = {iLeft + 3, y, 3, SLICE_H};
                SDL_Rect edgeR = {iRight - 6, y, 3, SLICE_H};
                SDL_RenderFillRect(renderer, &edgeL);
                SDL_RenderFillRect(renderer, &edgeR);

                // --- E. 4-Lane Dashed Markings ---
                float laneW = static_cast<float>(rWidth) / 4.0f;
                if (((y + static_cast<int>(roadOffset)) % 60) < 30) {
                    // Lane 1/2 Divider (dashed white)
                    SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                    int x1 = static_cast<int>(rLeft + laneW);
                    SDL_Rect d1 = {x1 - 1, y, 3, SLICE_H};
                    SDL_RenderFillRect(renderer, &d1);

                    // Center Highway Divider (bright sunny yellow double dash)
                    SDL_SetRenderDrawColor(renderer, 255, 215, 30, 255);
                    int x2 = static_cast<int>(rLeft + laneW * 2.0f);
                    SDL_Rect d2a = {x2 - 3, y, 2, SLICE_H};
                    SDL_Rect d2b = {x2 + 1, y, 2, SLICE_H};
                    SDL_RenderFillRect(renderer, &d2a);
                    SDL_RenderFillRect(renderer, &d2b);

                    // Lane 3/4 Divider (dashed white)
                    SDL_SetRenderDrawColor(renderer, 240, 240, 240, 255);
                    int x3 = static_cast<int>(rLeft + laneW * 3.0f);
                    SDL_Rect d3 = {x3 - 1, y, 3, SLICE_H};
                    SDL_RenderFillRect(renderer, &d3);
                }
            }
        }

        // Draw Tire Skid Marks on road
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        for (const auto& sm : skidMarks) {
            Uint8 a = static_cast<Uint8>(std::clamp(sm.alpha, 0.0f, 255.0f));
            SDL_SetRenderDrawColor(renderer, 25, 25, 25, a);
            SDL_RenderDrawLine(renderer, static_cast<int>(sm.x1), static_cast<int>(sm.y1), static_cast<int>(sm.x2), static_cast<int>(sm.y2));
            SDL_RenderDrawLine(renderer, static_cast<int>(sm.x1) + 1, static_cast<int>(sm.y1), static_cast<int>(sm.x2) + 1, static_cast<int>(sm.y2));
        }

        // Draw Tire Smoke Particles
        for (const auto& sp : smokeParticles) {
            Uint8 a = static_cast<Uint8>(std::clamp(sp.alpha, 0.0f, 255.0f));
            drawCircle(renderer, static_cast<int>(sp.x), static_cast<int>(sp.y), static_cast<int>(sp.size), {225, 225, 225, a});
        }
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Finish Line: screen Y scrolls smoothly toward the player as trackDistance approaches STAGE_TRACK_LENGTH
        float remainingDistance = STAGE_TRACK_LENGTH - trackDistance;
        int finishLineY = static_cast<int>(player.y - remainingDistance);
        if (finishLineY >= -100 && finishLineY <= INTERNAL_HEIGHT + 100) {
            drawFinishLine(renderer, textRenderer, finishLineY);
        }

        // Forward Headlight Beams (glow cast onto asphalt)
        if (!player.isSpinning) {
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 255, 255, 220, 25);
            for (int b = 0; b < 75; ++b) {
                float prog = static_cast<float>(b) / 75.0f;
                int beamW = 14 + static_cast<int>(prog * 18);
                int by = static_cast<int>(player.y) - b;
                SDL_Rect beamL = {static_cast<int>(player.x) + 3 - static_cast<int>(prog * 5), by, beamW, 1};
                SDL_Rect beamR = {static_cast<int>(player.x) + CAR_WIDTH - 17 + static_cast<int>(prog * 5), by, beamW, 1};
                SDL_RenderFillRect(renderer, &beamL);
                SDL_RenderFillRect(renderer, &beamR);
            }
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
        }

        // Render Entities (with rotation support)
        for (auto& e : enemies) {
            e.draw(renderer, textRenderer, targetTexture, carTexture, false, false, frames);
        }
        player.draw(renderer, textRenderer, targetTexture, carTexture, isPlayerBraking, (speedMultiplier > 1.05f), frames);

        // High-Speed Aerodynamic Wind Streaks (when in Turbo)
        if (speedMultiplier > 1.05f && !player.isSpinning) {
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            for (int s = 0; s < 8; ++s) {
                int sx = static_cast<int>(player.x) - 16 + (s * 9);
                if (sx >= static_cast<int>(player.x) + 4 && sx <= static_cast<int>(player.x) + CAR_WIDTH - 6) continue;
                int sy = static_cast<int>(player.y) - 40 + ((frames * 14 + s * 37) % 180);
                int sLen = 20 + (s % 3) * 10;
                Uint8 sAlpha = static_cast<Uint8>(60 + (s % 4) * 35);
                SDL_SetRenderDrawColor(renderer, 200, 235, 255, sAlpha);
                SDL_RenderDrawLine(renderer, sx, sy, sx, sy + sLen);
            }
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
        }

        // Viewport dividing bezel lines
        SDL_SetRenderDrawColor(renderer, COLOR_PANEL_BORDER.r, COLOR_PANEL_BORDER.g, COLOR_PANEL_BORDER.b, 255);
        SDL_RenderDrawLine(renderer, GAME_X - 1, 0, GAME_X - 1, INTERNAL_HEIGHT);
        SDL_RenderDrawLine(renderer, GAME_X, 0, GAME_X, INTERNAL_HEIGHT);
        SDL_RenderDrawLine(renderer, GAME_X + GAME_W, 0, GAME_X + GAME_W, INTERNAL_HEIGHT);
        SDL_RenderDrawLine(renderer, GAME_X + GAME_W + 1, 0, GAME_X + GAME_W + 1, INTERNAL_HEIGHT);

        // =========================================================================
        // --- LEFT GPS TRACK TELEMETRY & COURSE PROGRESS (x: 0 to GAME_X = 220) ---
        // =========================================================================
        // 1. Carbon fiber background with deep obsidian tint
        GameTextures::drawTiled(renderer, textures.carbonTex, 0, 0, GAME_X, INTERNAL_HEIGHT, 0, 0, 64, 64);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 10, 14, 22, 215);
        SDL_Rect lpTint = {0, 0, GAME_X, INTERNAL_HEIGHT};
        SDL_RenderFillRect(renderer, &lpTint);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Glowing separator line at right border
        SDL_SetRenderDrawColor(renderer, 28, 42, 64, 255);
        SDL_RenderDrawLine(renderer, GAME_X - 2, 0, GAME_X - 2, INTERNAL_HEIGHT);
        SDL_SetRenderDrawColor(renderer, 0, 180, 240, 255);
        SDL_RenderDrawLine(renderer, GAME_X - 1, 0, GAME_X - 1, INTERNAL_HEIGHT);

        // 2. High-Tech Header Card (y: 12 to 86)
        int lhX = 14, lhY = 14, lhW = GAME_X - 28, lhH = 76;
        SDL_SetRenderDrawColor(renderer, 16, 22, 34, 255);
        SDL_Rect lhBox = {lhX, lhY, lhW, lhH};
        SDL_RenderFillRect(renderer, &lhBox);
        SDL_SetRenderDrawColor(renderer, 45, 62, 90, 255);
        SDL_RenderDrawRect(renderer, &lhBox);
        // Top accent line
        SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
        SDL_RenderDrawLine(renderer, lhX, lhY, lhX + lhW - 1, lhY);
        SDL_RenderDrawLine(renderer, lhX, lhY + 1, lhX + lhW - 1, lhY + 1);

        textRenderer.drawTextWithShadow(renderer, "STAGE 0" + std::to_string(currentStage), lhX + lhW / 2, lhY + 22, 20, {255, 230, 60, 255}, true);
        textRenderer.drawTextWithShadow(renderer, (currentStage == 1 ? "FOREST HIGHWAY" : (currentStage == 2 ? "COASTAL BRIDGE" : "COASTAL BEACH")), lhX + lhW / 2, lhY + 46, 13, {100, 220, 255, 255}, true);
        textRenderer.drawText(renderer, "GPS TRACK TELEMETRY", lhX + lhW / 2, lhY + 63, 10, {140, 158, 180, 255}, true);

        // 3. Vertical GPS Track Corridor (y: 104 to 684)
        constexpr int trackX = 110;
        constexpr int trackTopY = 116;
        constexpr int trackBottomY = 676;
        constexpr int trackLength = trackBottomY - trackTopY; // 560px
        float progress = std::clamp(trackDistance / STAGE_TRACK_LENGTH, 0.0f, 1.0f);

        // Miniature roadbed (width 20px)
        SDL_SetRenderDrawColor(renderer, 20, 26, 36, 255);
        SDL_Rect tBed = {trackX - 10, trackTopY, 20, trackLength};
        SDL_RenderFillRect(renderer, &tBed);
        // Cyan guardrail borders
        SDL_SetRenderDrawColor(renderer, 45, 90, 145, 255);
        SDL_RenderDrawLine(renderer, trackX - 10, trackTopY, trackX - 10, trackBottomY);
        SDL_RenderDrawLine(renderer, trackX + 9, trackTopY, trackX + 9, trackBottomY);
        // Subtle dashed center lane divider
        SDL_SetRenderDrawColor(renderer, 255, 235, 59, 160);
        for (int dy = trackTopY + 4; dy < trackBottomY; dy += 16) {
            SDL_RenderDrawLine(renderer, trackX - 1, dy, trackX - 1, dy + 8);
        }

        // Checkpoint ticks & percentage markers (25%, 50%, 75%)
        for (float pct : {0.25f, 0.50f, 0.75f}) {
            int ty = trackBottomY - static_cast<int>(pct * trackLength);
            // Laser checkpoint bar across track
            SDL_SetRenderDrawColor(renderer, 0, 220, 255, 255);
            SDL_Rect tick = {trackX - 14, ty - 1, 28, 2};
            SDL_RenderFillRect(renderer, &tick);

            // Left leader line to milestone tag
            SDL_SetRenderDrawColor(renderer, 55, 75, 105, 255);
            SDL_RenderDrawLine(renderer, trackX - 38, ty, trackX - 14, ty);

            std::string pctLabel = std::to_string(static_cast<int>(pct * 100)) + "%";
            textRenderer.drawTextWithShadow(renderer, pctLabel, trackX - 54, ty, 11, {160, 205, 245, 255}, true);
        }

        // Finish Gate at top
        SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
        SDL_Rect gBox = {trackX - 32, trackTopY - 22, 64, 22};
        SDL_RenderFillRect(renderer, &gBox);
        SDL_SetRenderDrawColor(renderer, 15, 18, 25, 255);
        SDL_RenderDrawRect(renderer, &gBox);
        textRenderer.drawText(renderer, "★ GOAL ★", trackX, trackTopY - 11, 12, {15, 18, 25, 255}, true);

        // Start Gate at bottom
        SDL_SetRenderDrawColor(renderer, 25, 35, 50, 255);
        SDL_Rect sBox = {trackX - 28, trackBottomY + 2, 56, 20};
        SDL_RenderFillRect(renderer, &sBox);
        SDL_SetRenderDrawColor(renderer, 0, 200, 255, 255);
        SDL_RenderDrawRect(renderer, &sBox);
        textRenderer.drawTextWithShadow(renderer, "START", trackX, trackBottomY + 12, 11, {255, 255, 255, 255}, true);

        // High-Tech Player GPS Car Beacon
        int markerY = trackBottomY - static_cast<int>(progress * trackLength);
        // Pulse ring
        int pulsePhase = (frames / 8) % 3;
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 0, 220, 255, 80 - pulsePhase * 25);
        SDL_Rect pRing = {trackX - 12 - pulsePhase * 2, markerY - 12 - pulsePhase * 2, 24 + pulsePhase * 4, 24 + pulsePhase * 4};
        SDL_RenderDrawRect(renderer, &pRing);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Headlight beam forward on minimap
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 255, 255, 200, 90);
        SDL_Rect mBeam = {trackX - 6, markerY - 20, 12, 10};
        SDL_RenderFillRect(renderer, &mBeam);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Red Sports Car marker body
        SDL_SetRenderDrawColor(renderer, 10, 14, 20, 255);
        SDL_Rect mBg = {trackX - 8, markerY - 10, 16, 20};
        SDL_RenderFillRect(renderer, &mBg);
        SDL_SetRenderDrawColor(renderer, 230, 35, 35, 255);
        SDL_Rect mBody = {trackX - 6, markerY - 8, 12, 16};
        SDL_RenderFillRect(renderer, &mBody);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_Rect mRoof = {trackX - 4, markerY - 5, 8, 8};
        SDL_RenderFillRect(renderer, &mRoof);

        // "YOU" leader tag on right
        SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
        SDL_Rect youTag = {trackX + 16, markerY - 8, 38, 16};
        SDL_RenderFillRect(renderer, &youTag);
        SDL_SetRenderDrawColor(renderer, 15, 18, 25, 255);
        SDL_RenderDrawRect(renderer, &youTag);
        textRenderer.drawText(renderer, "YOU", trackX + 35, markerY, 10, {15, 18, 25, 255}, true);

        // 4. Bottom Distance Telemetry Card (y: 706 to 786)
        int distMeters = static_cast<int>(std::max(0.0f, (STAGE_TRACK_LENGTH - trackDistance) * 0.1f));
        int ldX = 14, ldY = 706, ldW = GAME_X - 28, ldH = 80;
        SDL_SetRenderDrawColor(renderer, 16, 22, 34, 255);
        SDL_Rect ldBox = {ldX, ldY, ldW, ldH};
        SDL_RenderFillRect(renderer, &ldBox);
        SDL_SetRenderDrawColor(renderer, 45, 62, 90, 255);
        SDL_RenderDrawRect(renderer, &ldBox);

        textRenderer.drawTextWithShadow(renderer, "REMAINING DISTANCE", ldX + ldW / 2, ldY + 16, 11, {150, 170, 195, 255}, true);
        textRenderer.drawTextWithShadow(renderer, std::to_string(distMeters) + " M", ldX + ldW / 2, ldY + 40, 22, {255, 255, 255, 255}, true);
        int miniPct = static_cast<int>(progress * 100.0f);
        textRenderer.drawText(renderer, std::to_string(miniPct) + "% COMPLETED", ldX + ldW / 2, ldY + 64, 11, {0, 220, 255, 255}, true);

        // =========================================================================
        // --- RIGHT DEDICATED DASHBOARD & INSTRUMENT CLUSTER (x: 820 to 1280) ---
        // =========================================================================
        // 1. Carbon fiber background with deep obsidian tint
        GameTextures::drawTiled(renderer, textures.carbonTex, GAME_X + GAME_W, 0, INTERNAL_WIDTH - (GAME_X + GAME_W), INTERNAL_HEIGHT, 0, 0, 64, 64);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 10, 14, 22, 215);
        SDL_Rect rpTint = {GAME_X + GAME_W, 0, INTERNAL_WIDTH - (GAME_X + GAME_W), INTERNAL_HEIGHT};
        SDL_RenderFillRect(renderer, &rpTint);
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

        // Glowing separator line at left border
        SDL_SetRenderDrawColor(renderer, 0, 180, 240, 255);
        SDL_RenderDrawLine(renderer, GAME_X + GAME_W, 0, GAME_X + GAME_W, INTERNAL_HEIGHT);
        SDL_SetRenderDrawColor(renderer, 28, 42, 64, 255);
        SDL_RenderDrawLine(renderer, GAME_X + GAME_W + 1, 0, GAME_X + GAME_W + 1, INTERNAL_HEIGHT);

        // AAA Card Drawer with drop shadow, glassmorphic header, and glowing accent
        auto drawCard = [&](int bx, int by, int bw, int bh, const std::string& title, SDL_Color tColor = {255, 235, 59, 255}) {
            // Ambient outer drop shadow
            SDL_SetRenderDrawColor(renderer, 6, 9, 15, 200);
            SDL_Rect dShadow = {bx + 3, by + 3, bw, bh};
            SDL_RenderFillRect(renderer, &dShadow);

            // Carbon textured composite backing
            GameTextures::drawTiled(renderer, textures.carbonTex, bx, by, bw, bh, 0, 0, 64, 64);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 14, 19, 30, 200);
            SDL_Rect rTint = {bx, by, bw, bh};
            SDL_RenderFillRect(renderer, &rTint);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            // Double beveled border stroke
            SDL_SetRenderDrawColor(renderer, 42, 58, 82, 255);
            SDL_RenderDrawRect(renderer, &rTint);
            SDL_SetRenderDrawColor(renderer, 22, 30, 44, 255);
            SDL_Rect rInner = {bx + 1, by + 1, bw - 2, bh - 2};
            SDL_RenderDrawRect(renderer, &rInner);

            // Header Bar
            SDL_SetRenderDrawColor(renderer, 24, 32, 46, 255);
            SDL_Rect rHead = {bx, by, bw, 28};
            SDL_RenderFillRect(renderer, &rHead);

            // Header metallic top highlight & bottom divider
            SDL_SetRenderDrawColor(renderer, 75, 100, 138, 255);
            SDL_RenderDrawLine(renderer, bx, by, bx + bw - 1, by);
            SDL_SetRenderDrawColor(renderer, 50, 68, 95, 255);
            SDL_RenderDrawLine(renderer, bx, by + 27, bx + bw - 1, by + 27);

            // Left glowing accent tag
            SDL_SetRenderDrawColor(renderer, tColor.r, tColor.g, tColor.b, 255);
            SDL_Rect headPip = {bx + 10, by + 7, 4, 14};
            SDL_RenderFillRect(renderer, &headPip);

            textRenderer.drawTextWithShadow(renderer, title, bx + 22, by + 14, 13, tColor);
        };

        int rCardX = 836;
        int rCardW = 428;

        // --- Card 1: ACTIVE MISSION // TARGET KANA SCANNER (y: 12 to 176, h: 164) ---
        drawCard(rCardX, 12, rCardW, 164, "MISSION OBJECTIVE // TARGET KANA", {255, 215, 0, 255});

        // Holographic Kana Scanner Chamber (left, w: 104, h: 118)
        int podX = rCardX + 16, podY = 44, podW = 104, podH = 118;
        SDL_SetRenderDrawColor(renderer, 16, 24, 38, 255);
        SDL_Rect podBox = {podX, podY, podW, podH};
        SDL_RenderFillRect(renderer, &podBox);
        SDL_SetRenderDrawColor(renderer, 0, 200, 255, 255);
        SDL_RenderDrawRect(renderer, &podBox);
        // Cyber grid in pod
        SDL_SetRenderDrawColor(renderer, 24, 38, 58, 255);
        for (int gy = podY + 20; gy < podY + podH - 15; gy += 15) {
            SDL_RenderDrawLine(renderer, podX + 2, gy, podX + podW - 3, gy);
        }
        for (int gx = podX + 15; gx < podX + podW; gx += 15) {
            SDL_RenderDrawLine(renderer, gx, podY + 2, gx, podY + podH - 3);
        }
        // Top label
        textRenderer.drawText(renderer, "READ KANA", podX + podW / 2, podY + 11, 10, {0, 220, 255, 255}, true);
        // HUGE 54px BOLD Japanese Hiragana character
        textRenderer.drawTextWithOutline(renderer, player.data.kana, podX + podW / 2, podY + 56, 54, {255, 255, 255, 255}, {0, 0, 0, 255}, 2, true);
        // Bottom badge
        textRenderer.drawText(renderer, "YOUR VEHICLE", podX + podW / 2, podY + podH - 11, 10, {255, 215, 0, 255}, true);

        // Right side: Directive & Dynamic Collision Feedback (x: 968, y: 44, w: 280, h: 118)
        int dirX = rCardX + 132;
        textRenderer.drawTextWithShadow(renderer, "MATCH ROMAJI ON ROAD", dirX, 54, 15, {255, 230, 60, 255});
        textRenderer.drawText(renderer, "Hit traffic car with matching sound", dirX, 74, 12, {175, 190, 210, 255});

        // Dynamic Collision Feedback Card (w: 280, h: 56)
        int fbY = 96;
        if (matchFeedbackTimer > 0) {
            if (lastMatchSuccess) {
                // Flashing Green Success Banner
                SDL_SetRenderDrawColor(renderer, 15, 60, 32, 255);
                SDL_Rect fbBox = {dirX, fbY, 280, 56};
                SDL_RenderFillRect(renderer, &fbBox);
                SDL_SetRenderDrawColor(renderer, 46, 240, 130, 255);
                SDL_RenderDrawRect(renderer, &fbBox);
                textRenderer.drawTextWithShadow(renderer, "★ PERFECT MATCH! ★", dirX + 140, fbY + 17, 16, {46, 240, 130, 255}, true);
                textRenderer.drawTextWithShadow(renderer, "+50 PTS  |  +30% FUEL RECOVERY", dirX + 140, fbY + 38, 12, {255, 255, 255, 255}, true);
            } else {
                // Flashing Red Alert Banner
                SDL_SetRenderDrawColor(renderer, 70, 18, 18, 255);
                SDL_Rect fbBox = {dirX, fbY, 280, 56};
                SDL_RenderFillRect(renderer, &fbBox);
                SDL_SetRenderDrawColor(renderer, 255, 55, 55, 255);
                SDL_RenderDrawRect(renderer, &fbBox);
                textRenderer.drawTextWithShadow(renderer, "⚠ WRONG VEHICLE HIT! ⚠", dirX + 140, fbY + 17, 16, {255, 65, 65, 255}, true);
                textRenderer.drawTextWithShadow(renderer, "-10 FUEL PENALTY  |  SPINOUT!", dirX + 140, fbY + 38, 12, {255, 255, 255, 255}, true);
            }
        } else {
            // Idle Telemetry Status Box
            SDL_SetRenderDrawColor(renderer, 20, 28, 42, 255);
            SDL_Rect fbBox = {dirX, fbY, 280, 56};
            SDL_RenderFillRect(renderer, &fbBox);
            SDL_SetRenderDrawColor(renderer, 42, 60, 88, 255);
            SDL_RenderDrawRect(renderer, &fbBox);

            if (matchStreak > 1) {
                textRenderer.drawTextWithShadow(renderer, "COMBO STREAK ACTIVE", dirX + 140, fbY + 17, 13, {0, 220, 255, 255}, true);
                textRenderer.drawTextWithShadow(renderer, std::to_string(matchStreak) + " CONSECUTIVE MATCHES!", dirX + 140, fbY + 38, 13, {255, 215, 0, 255}, true);
            } else {
                textRenderer.drawTextWithShadow(renderer, "RADAR SCANNING ROAD...", dirX + 140, fbY + 17, 13, {150, 175, 205, 255}, true);
                textRenderer.drawText(renderer, "Dodge mismatched cars to save fuel", dirX + 140, fbY + 38, 11, {125, 145, 170, 255}, true);
            }
        }

        // --- Card 2: SCORE & RACE PROGRESS (y: 184 to 308, h: 124) ---
        drawCard(rCardX, 184, rCardW, 124, "RACE SCORE & TELEMETRY", {100, 220, 255, 255});
        textRenderer.drawText(renderer, "TOTAL SCORE", rCardX + 16, 218, 11, {150, 168, 192, 255});
        textRenderer.drawTextWithShadow(renderer, std::to_string(static_cast<int>(score)), rCardX + 16, 250, 42, {255, 235, 59, 255});

        // Stage Pill & Remaining Distance
        SDL_SetRenderDrawColor(renderer, 24, 35, 52, 255);
        SDL_Rect stPill = {rCardX + rCardW - 134, 216, 118, 22};
        SDL_RenderFillRect(renderer, &stPill);
        SDL_SetRenderDrawColor(renderer, 0, 180, 240, 255);
        SDL_RenderDrawRect(renderer, &stPill);
        textRenderer.drawText(renderer, "STAGE " + std::to_string(currentStage) + " / 3", rCardX + rCardW - 75, 227, 11, {0, 200, 255, 255}, true);

        std::string distStr = std::to_string(distMeters) + " m to finish";
        textRenderer.drawTextRightWithShadow(renderer, distStr, rCardX + rCardW - 16, 252, 14, {180, 215, 245, 255});

        // Multi-stage Progress Bar
        SDL_SetRenderDrawColor(renderer, 28, 36, 50, 255);
        SDL_Rect scBarBg = {rCardX + 16, 280, rCardW - 32, 14};
        SDL_RenderFillRect(renderer, &scBarBg);
        SDL_SetRenderDrawColor(renderer, 50, 68, 95, 255);
        SDL_RenderDrawRect(renderer, &scBarBg);

        int scFillW = static_cast<int>(progress * (rCardW - 36));
        if (scFillW > 0) {
            SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
            SDL_Rect scFill = {rCardX + 18, 282, scFillW, 10};
            SDL_RenderFillRect(renderer, &scFill);

            // Leading glow head
            SDL_SetRenderDrawColor(renderer, 0, 230, 255, 255);
            SDL_Rect headBox = {rCardX + 18 + scFillW - 4, 281, 6, 12};
            SDL_RenderFillRect(renderer, &headBox);
        }

        // --- Card 3: SPEEDOMETER & TACHOMETER (y: 316 to 482, h: 166) ---
        drawCard(rCardX, 316, rCardW, 166, "INSTRUMENT CLUSTER // SPEEDOMETER", {100, 220, 255, 255});

        int kmh = player.isSpinning ? 0 : static_cast<int>(speedMultiplier * 160.0f);
        textRenderer.drawTextWithShadow(renderer, std::to_string(kmh), rCardX + 16, 375, 52, {255, 255, 255, 255});
        textRenderer.drawTextWithShadow(renderer, "KM/H", rCardX + (kmh >= 100 ? 116 : (kmh >= 10 ? 88 : 60)), 382, 17, {165, 185, 210, 255});

        // Drive Mode & Transmission Pill (x: rCardX + 220, y: 350, w: 192, h: 32)
        int modeW = 192, modeH = 32;
        int modeX = rCardX + rCardW - modeW - 16;
        int modeY = 356;
        if (player.isSpinning) {
            SDL_SetRenderDrawColor(renderer, 70, 18, 18, 255);
            SDL_Rect mBox = {modeX, modeY, modeW, modeH};
            SDL_RenderFillRect(renderer, &mBox);
            SDL_SetRenderDrawColor(renderer, 255, 50, 50, 255);
            SDL_RenderDrawRect(renderer, &mBox);
            textRenderer.drawTextWithShadow(renderer, "! SPINOUT SKID !", modeX + modeW / 2, modeY + modeH / 2, 13, {255, 70, 70, 255}, true);
        } else if (speedMultiplier > 1.05f) {
            SDL_SetRenderDrawColor(renderer, 70, 35, 10, 255);
            SDL_Rect mBox = {modeX, modeY, modeW, modeH};
            SDL_RenderFillRect(renderer, &mBox);
            SDL_SetRenderDrawColor(renderer, 255, 130, 30, 255);
            SDL_RenderDrawRect(renderer, &mBox);
            textRenderer.drawTextWithShadow(renderer, "TURBO BOOST // HI", modeX + modeW / 2, modeY + modeH / 2, 13, {255, 145, 45, 255}, true);
        } else if (isPlayerBraking) {
            SDL_SetRenderDrawColor(renderer, 15, 45, 60, 255);
            SDL_Rect mBox = {modeX, modeY, modeW, modeH};
            SDL_RenderFillRect(renderer, &mBox);
            SDL_SetRenderDrawColor(renderer, 0, 200, 255, 255);
            SDL_RenderDrawRect(renderer, &mBox);
            textRenderer.drawTextWithShadow(renderer, "BRAKING // LOW", modeX + modeW / 2, modeY + modeH / 2, 13, {0, 220, 255, 255}, true);
        } else {
            SDL_SetRenderDrawColor(renderer, 20, 32, 48, 255);
            SDL_Rect mBox = {modeX, modeY, modeW, modeH};
            SDL_RenderFillRect(renderer, &mBox);
            SDL_SetRenderDrawColor(renderer, 70, 140, 210, 255);
            SDL_RenderDrawRect(renderer, &mBox);
            textRenderer.drawTextWithShadow(renderer, "CRUISE // MID", modeX + modeW / 2, modeY + modeH / 2, 13, {100, 200, 255, 255}, true);
        }

        // 24-Segmented LED Tachometer (RPM Bar) (y: 418, w: rCardW - 32, h: 22)
        int rpmBarW = rCardW - 32;
        int numLeds = 24;
        int ledGap = 2;
        int ledW = (rpmBarW - (numLeds - 1) * ledGap) / numLeds;
        int activeLeds = player.isSpinning ? 0 : static_cast<int>((speedMultiplier / 1.5f) * numLeds);

        for (int k = 0; k < numLeds; ++k) {
            int lx = rCardX + 16 + k * (ledW + ledGap);
            int ly = 418;
            bool on = (k < activeLeds);

            SDL_Color lColor;
            if (k < 12) {
                // Low revs: Cyan / Emerald Green
                lColor = on ? SDL_Color{0, 230, 160, 255} : SDL_Color{18, 36, 32, 255};
            } else if (k < 18) {
                // Mid revs: High Voltage Yellow
                lColor = on ? SDL_Color{255, 220, 0, 255} : SDL_Color{42, 38, 14, 255};
            } else {
                // High revs: Redline Warning
                bool flashRed = (speedMultiplier > 1.4f && ((frames / 6) % 2 == 0));
                lColor = on ? (flashRed ? SDL_Color{255, 255, 255, 255} : SDL_Color{255, 45, 45, 255}) : SDL_Color{45, 18, 18, 255};
            }

            SDL_SetRenderDrawColor(renderer, lColor.r, lColor.g, lColor.b, 255);
            SDL_Rect ledBox = {lx, ly, ledW, 20};
            SDL_RenderFillRect(renderer, &ledBox);
        }

        textRenderer.drawText(renderer, "ENGINE POWER OUTPUT", rCardX + 16, 452, 11, {145, 165, 188, 255});
        textRenderer.drawTextRightWithShadow(renderer, "MAX TOP SPEED: 240 KM/H", rCardX + rCardW - 16, 452, 11, {255, 215, 0, 255});

        // --- Card 4: FUEL CELL & SYSTEM INTEGRITY (y: 490 to 640, h: 150) ---
        drawCard(rCardX, 490, rCardW, 150, "POWER CELL // FUEL TANK", {255, 215, 0, 255});

        textRenderer.drawText(renderer, "CAPACITY INTEGRITY", rCardX + 16, 526, 11, {150, 168, 192, 255});
        std::string fuelPctStr = std::to_string(static_cast<int>(fuel)) + " %";
        SDL_Color fuelValCol = (fuel > 50.0f) ? SDL_Color{46, 240, 130, 255} : ((fuel > 25.0f) ? SDL_Color{255, 215, 0, 255} : SDL_Color{255, 60, 60, 255});
        textRenderer.drawTextRightWithShadow(renderer, fuelPctStr, rCardX + rCardW - 16, 526, 18, fuelValCol);

        // 16-Segmented LED Battery Cells (w: rCardW - 32, h: 32)
        int numFuelCells = 16;
        int fuelCellGap = 3;
        int fuelCellW = (rCardW - 32 - (numFuelCells - 1) * fuelCellGap) / numFuelCells;
        int activeFuelCells = static_cast<int>((std::max(0.0f, fuel) / MAX_FUEL) * numFuelCells);

        for (int k = 0; k < numFuelCells; ++k) {
            int cx = rCardX + 16 + k * (fuelCellW + fuelCellGap);
            int cy = 548;
            bool on = (k < activeFuelCells);

            SDL_Color bCol;
            if (fuel > 50.0f) {
                bCol = on ? SDL_Color{46, 220, 120, 255} : SDL_Color{18, 38, 28, 255};
            } else if (fuel > 25.0f) {
                bCol = on ? SDL_Color{255, 205, 30, 255} : SDL_Color{42, 36, 14, 255};
            } else {
                bool flash = ((frames / 10) % 2 == 0);
                bCol = on ? (flash ? SDL_Color{255, 50, 50, 255} : SDL_Color{160, 20, 20, 255}) : SDL_Color{40, 16, 16, 255};
            }

            SDL_SetRenderDrawColor(renderer, bCol.r, bCol.g, bCol.b, 255);
            SDL_Rect bBox = {cx, cy, fuelCellW, 26};
            SDL_RenderFillRect(renderer, &bBox);
            SDL_SetRenderDrawColor(renderer, 15, 22, 32, 255);
            SDL_RenderDrawRect(renderer, &bBox);
        }

        // Low Fuel Alert vs Normal Refuel Status
        if (fuel <= 25.0f) {
            bool flash = ((frames / 12) % 2 == 0);
            SDL_Color wColor = flash ? SDL_Color{255, 60, 60, 255} : SDL_Color{255, 200, 200, 255};
            textRenderer.drawTextWithShadow(renderer, "! WARNING: LOW FUEL - HIT MATCHING CARS !", rCardX + rCardW / 2, 598, 13, wColor, true);
        } else {
            textRenderer.drawTextWithShadow(renderer, "REFUEL SYSTEM ACTIVE", rCardX + rCardW / 2, 592, 12, {0, 220, 255, 255}, true);
            textRenderer.drawText(renderer, "Ram into correct Romaji cars to recover +30% fuel", rCardX + rCardW / 2, 612, 11, {150, 168, 192, 255}, true);
        }

        // --- Card 5: PILOT COMMAND INTERFACE (y: 648 to 788, h: 140) ---
        drawCard(rCardX, 648, rCardW, 140, "PILOT COMMAND INTERFACE", {160, 185, 215, 255});

        auto drawKeycap = [&](int kx, int ky, int kw, int kh, const std::string& keyStr, const std::string& actStr, SDL_Color actCol = {220, 230, 245, 255}) {
            SDL_SetRenderDrawColor(renderer, 22, 30, 44, 255);
            SDL_Rect kBox = {kx, ky, kw, kh};
            SDL_RenderFillRect(renderer, &kBox);
            SDL_SetRenderDrawColor(renderer, 50, 70, 100, 255);
            SDL_RenderDrawRect(renderer, &kBox);

            textRenderer.drawTextWithShadow(renderer, keyStr, kx + 8, ky + 6, 11, {255, 235, 59, 255});
            textRenderer.drawTextRightWithShadow(renderer, actStr, kx + kw - 8, ky + kh / 2, 11, actCol, true);
        };

        drawKeycap(rCardX + 16, 684, 190, 24, "D-PAD / STICK", "STEER CAR");
        drawKeycap(rCardX + 218, 684, 194, 24, "UP / (A) / RT", "TURBO BOOST", {255, 140, 40, 255});
        drawKeycap(rCardX + 16, 716, 190, 24, "DOWN / (X) / LT", "BRAKE / DRIFT", {0, 210, 255, 255});
        drawKeycap(rCardX + 218, 716, 194, 24, "START / P", "PAUSE & CONFIG");

        textRenderer.drawTextWithShadow(renderer, "MISSION: Read your roof Kana & match corresponding Romaji!", rCardX + rCardW / 2, 762, 11, {255, 225, 60, 255}, true);

        // =========================================================================
        // --- PAUSE & OPTIONS MENU (Triggered by START / P / ESC) ---
        // =========================================================================
        if (gameState == PAUSED) {
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 0, 0, 0, 225);
            SDL_Rect ov = {0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &ov);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            int mw = 680, mh = 560;
            int mx = (INTERNAL_WIDTH - mw) / 2;
            int my = (INTERNAL_HEIGHT - mh) / 2;

            // Outer drop shadow
            SDL_SetRenderDrawColor(renderer, 5, 8, 14, 180);
            SDL_Rect mShadow = {mx + 8, my + 8, mw, mh};
            SDL_RenderFillRect(renderer, &mShadow);

            // Main Menu Container
            SDL_SetRenderDrawColor(renderer, 20, 26, 38, 255);
            SDL_Rect mBg = {mx, my, mw, mh};
            SDL_RenderFillRect(renderer, &mBg);
            SDL_SetRenderDrawColor(renderer, 58, 80, 115, 255);
            SDL_RenderDrawRect(renderer, &mBg);

            // Header Banner
            SDL_SetRenderDrawColor(renderer, 28, 38, 56, 255);
            SDL_Rect mHead = {mx, my, mw, 52};
            SDL_RenderFillRect(renderer, &mHead);
            SDL_SetRenderDrawColor(renderer, 75, 100, 138, 255);
            SDL_RenderDrawRect(renderer, &mHead);

            textRenderer.drawTextWithShadow(renderer, "★  PAUSE & OPTIONS  ★", mx + mw / 2, my + 26, 22, {255, 235, 59, 255}, true);

            // --- Section 1: Auto-Configuration Telemetry Card ---
            int cardX = mx + 25;
            int cardY = my + 66;
            int cardW = mw - 50;
            int cardH = 116;

            SDL_SetRenderDrawColor(renderer, 24, 32, 46, 255);
            SDL_Rect cBox = {cardX, cardY, cardW, cardH};
            SDL_RenderFillRect(renderer, &cBox);
            GameTextures::drawTiled(renderer, textures.carbonTex, cardX, cardY, cardW, cardH, 0, 0, 64, 64);
            SDL_SetRenderDrawColor(renderer, 55, 75, 105, 255);
            SDL_RenderDrawRect(renderer, &cBox);

            // Telemetry Header
            textRenderer.drawTextWithShadow(renderer, "DISPLAY AUTO-DETECTION", cardX + 16, cardY + 18, 13, {100, 220, 255, 255});

            // "AUTO-CONFIGURED" Status Badge
            SDL_SetRenderDrawColor(renderer, 25, 75, 45, 255);
            SDL_Rect autoPill = {cardX + cardW - 170, cardY + 8, 154, 22};
            SDL_RenderFillRect(renderer, &autoPill);
            SDL_SetRenderDrawColor(renderer, 46, 204, 113, 255);
            SDL_RenderDrawRect(renderer, &autoPill);
            textRenderer.drawTextWithShadow(renderer, "● OPTIMIZED & ACTIVE", cardX + cardW - 93, cardY + 19, 11, {46, 204, 113, 255}, true);

            // Telemetry Specs
            std::string resStr = "Detected Maximum Resolution:  " + std::to_string(autoResW) + " × " + std::to_string(autoResH);
            textRenderer.drawTextWithShadow(renderer, resStr, cardX + 16, cardY + 48, 14, {230, 238, 248, 255});

            std::string aspStr = "Best Aspect Ratio Applied:      " + autoAspectLabel;
            textRenderer.drawTextWithShadow(renderer, aspStr, cardX + 16, cardY + 74, 14, {255, 235, 59, 255});

            std::string engStr = "Hardware Render Pipeline:       SDL2 Accelerated (Locked 60 FPS)";
            textRenderer.drawTextWithShadow(renderer, engStr, cardX + 16, cardY + 98, 12, {160, 175, 195, 255});

            // --- Section 2: Interactive Menu Buttons (0..3) ---
            struct MenuItem {
                std::string label;
                std::string subtext;
                SDL_Color color;
            };

            std::string screenModeSubtext = isFullscreen ? "Mode: [ FULLSCREEN ]  (Press (A) or Left/Right to toggle)"
                                                         : "Mode: [ WINDOWED ]    (Press (A) or Left/Right to toggle)";

            const MenuItem items[4] = {
                {"RESUME RACE", "Return immediately to high-speed action", {100, 220, 255, 255}},
                {"SCREEN MODE: " + std::string(isFullscreen ? "FULLSCREEN" : "WINDOWED"), screenModeSubtext, {255, 235, 59, 255}},
                {"RESTART CURRENT STAGE", "Reset track distance and fuel to initial state", {255, 200, 80, 255}},
                {"QUIT TO DESKTOP", "Exit game session and return to desktop", {255, 90, 90, 255}}
            };

            int startBtnY = cardY + cardH + 16;
            for (int i = 0; i < 4; ++i) {
                int btnY = startBtnY + i * 58;
                int btnW = cardW;
                int btnH = 50;
                int btnX = cardX;
                bool isSelected = (pauseMenuIndex == i);

                if (isSelected) {
                    SDL_SetRenderDrawColor(renderer, 48, 68, 98, 255);
                    SDL_Rect rBtn = {btnX, btnY, btnW, btnH};
                    SDL_RenderFillRect(renderer, &rBtn);
                    SDL_SetRenderDrawColor(renderer, 255, 235, 59, 255);
                    SDL_RenderDrawRect(renderer, &rBtn);

                    // Crisp geometric selection arrow
                    SDL_SetRenderDrawColor(renderer, 255, 235, 59, 255);
                    for (int dx = 0; dx <= 8; ++dx) {
                        SDL_RenderDrawLine(renderer, btnX + 15 + dx, btnY + 25 - (8 - dx), btnX + 15 + dx, btnY + 25 + (8 - dx));
                    }
                } else {
                    SDL_SetRenderDrawColor(renderer, 26, 35, 48, 255);
                    SDL_Rect rBtn = {btnX, btnY, btnW, btnH};
                    SDL_RenderFillRect(renderer, &rBtn);
                    SDL_SetRenderDrawColor(renderer, 44, 58, 78, 255);
                    SDL_RenderDrawRect(renderer, &rBtn);
                }

                // Item Title
                SDL_Color titleCol = isSelected ? SDL_Color{255, 255, 255, 255} : items[i].color;
                textRenderer.drawTextWithShadow(renderer, items[i].label, btnX + (isSelected ? 36 : 18), btnY + 18, 15, titleCol);

                // Subtext
                textRenderer.drawTextWithShadow(renderer, items[i].subtext, btnX + (isSelected ? 36 : 18), btnY + 36, 11, {160, 178, 198, 255});

                // Status pill for Screen Mode
                if (i == 1) {
                    if (isFullscreen) {
                        SDL_SetRenderDrawColor(renderer, 25, 75, 45, 255);
                        SDL_Rect fsPill = {btnX + btnW - 120, btnY + 13, 108, 24};
                        SDL_RenderFillRect(renderer, &fsPill);
                        SDL_SetRenderDrawColor(renderer, 46, 204, 113, 255);
                        SDL_RenderDrawRect(renderer, &fsPill);
                        textRenderer.drawTextWithShadow(renderer, "FULLSCREEN", btnX + btnW - 66, btnY + 25, 11, {46, 204, 113, 255}, true);
                    } else {
                        SDL_SetRenderDrawColor(renderer, 50, 60, 80, 255);
                        SDL_Rect winPill = {btnX + btnW - 120, btnY + 13, 108, 24};
                        SDL_RenderFillRect(renderer, &winPill);
                        SDL_SetRenderDrawColor(renderer, 100, 180, 255, 255);
                        SDL_RenderDrawRect(renderer, &winPill);
                        textRenderer.drawTextWithShadow(renderer, "WINDOWED", btnX + btnW - 66, btnY + 25, 11, {100, 180, 255, 255}, true);
                    }
                }
            }

            // --- Section 3: Footer Help / Toast Notification Bar ---
            int fy = my + mh - 44;
            SDL_SetRenderDrawColor(renderer, 26, 34, 48, 255);
            SDL_Rect fHead = {mx, fy, mw, 44};
            SDL_RenderFillRect(renderer, &fHead);
            SDL_SetRenderDrawColor(renderer, 55, 75, 105, 255);
            SDL_RenderDrawRect(renderer, &fHead);

            if (!statusMessage.empty() && SDL_GetTicks() - statusMessageTime < 3500) {
                textRenderer.drawTextWithShadow(renderer, "●  " + statusMessage, mx + mw / 2, fy + 22, 13, {100, 255, 180, 255}, true);
            } else {
                textRenderer.drawTextWithShadow(renderer, "D-Pad / Stick / W/S: Navigate   |   (A) / Space: Select   |   (B) / START / ESC: Resume", mx + mw / 2, fy + 22, 12, {170, 185, 205, 255}, true);
            }
        } else if (gameState != PLAYING) {
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 0, 0, 0, 220);
            SDL_Rect ov = {0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT};
            SDL_RenderFillRect(renderer, &ov);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            // Dialog Window Box with Carbon backing & drop shadow
            int dw = 600, dh = 380;
            int dx = (INTERNAL_WIDTH - dw) / 2;
            int dy = (INTERNAL_HEIGHT - dh) / 2;

            SDL_SetRenderDrawColor(renderer, 5, 8, 14, 200);
            SDL_Rect dShadow = {dx + 8, dy + 8, dw, dh};
            SDL_RenderFillRect(renderer, &dShadow);

            GameTextures::drawTiled(renderer, textures.carbonTex, dx, dy, dw, dh, 0, 0, 64, 64);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, 16, 22, 34, 210);
            SDL_Rect dTint = {dx, dy, dw, dh};
            SDL_RenderFillRect(renderer, &dTint);
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

            SDL_SetRenderDrawColor(renderer, 65, 90, 130, 255);
            SDL_RenderDrawRect(renderer, &dTint);
            SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
            SDL_RenderDrawLine(renderer, dx, dy, dx + dw - 1, dy);

            if (gameState == CLEAR) {
                if (currentStage == 1) {
                    textRenderer.drawTextWithShadow(renderer, "STAGE 1 CLEAR!", INTERNAL_WIDTH / 2, dy + 70, 38, {255, 235, 59, 255}, true);
                    std::string finalScoreStr = "TOTAL SCORE: " + std::to_string(static_cast<int>(score));
                    textRenderer.drawTextWithShadow(renderer, finalScoreStr, INTERNAL_WIDTH / 2, dy + 150, 24, {255, 255, 255, 255}, true);
                    textRenderer.drawTextWithShadow(renderer, "Press SPACE or (A) for Stage 2", INTERNAL_WIDTH / 2, dy + 225, 20, {100, 220, 255, 255}, true);
                } else if (currentStage == 2) {
                    textRenderer.drawTextWithShadow(renderer, "STAGE 2 CLEAR!", INTERNAL_WIDTH / 2, dy + 70, 38, {255, 235, 59, 255}, true);
                    std::string finalScoreStr = "TOTAL SCORE: " + std::to_string(static_cast<int>(score));
                    textRenderer.drawTextWithShadow(renderer, finalScoreStr, INTERNAL_WIDTH / 2, dy + 150, 24, {255, 255, 255, 255}, true);
                    textRenderer.drawTextWithShadow(renderer, "Press SPACE or (A) for Stage 3", INTERNAL_WIDTH / 2, dy + 225, 20, {100, 220, 255, 255}, true);
                } else {
                    textRenderer.drawTextWithShadow(renderer, "ALL STAGES CLEAR!", INTERNAL_WIDTH / 2, dy + 60, 36, {255, 235, 59, 255}, true);
                    textRenderer.drawTextWithShadow(renderer, "★ CONGRATULATIONS ★", INTERNAL_WIDTH / 2, dy + 115, 24, {255, 215, 0, 255}, true);
                    std::string finalScoreStr = "FINAL SCORE: " + std::to_string(static_cast<int>(score));
                    textRenderer.drawTextWithShadow(renderer, finalScoreStr, INTERNAL_WIDTH / 2, dy + 175, 24, {255, 255, 255, 255}, true);
                    textRenderer.drawTextWithShadow(renderer, "Press SPACE or (A) to play again", INTERNAL_WIDTH / 2, dy + 235, 20, {100, 220, 255, 255}, true);
                }
            } else {
                textRenderer.drawTextWithShadow(renderer, "GAME OVER", INTERNAL_WIDTH / 2, dy + 70, 42, {255, 50, 50, 255}, true);
                std::string finalScoreStr = "FINAL SCORE: " + std::to_string(static_cast<int>(score));
                textRenderer.drawTextWithShadow(renderer, finalScoreStr, INTERNAL_WIDTH / 2, dy + 150, 24, {255, 255, 255, 255}, true);
                textRenderer.drawTextWithShadow(renderer, "Press SPACE or (A) to retry", INTERNAL_WIDTH / 2, dy + 225, 20, {255, 235, 59, 255}, true);
            }

            textRenderer.drawTextWithShadow(renderer, "Press Q or BACK to quit", INTERNAL_WIDTH / 2, dy + 310, 16, {170, 185, 205, 255}, true);
        }

        // 4. Render Target Texture to Window with Auto-Detected Aspect Ratio Scaling
        SDL_SetRenderTarget(renderer, nullptr);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);

        int winW = 0, winH = 0;
        SDL_GetWindowSize(window, &winW, &winH);

        float targetRatio = autoAspectRatio;
        SDL_Rect dstRect;

        if (targetRatio <= 0.0f) {
            // Fill / Stretch mode
            dstRect = {0, 0, winW, winH};
        } else {
            // Maintain optimal aspect ratio with clean pillarboxing/letterboxing
            float windowRatio = static_cast<float>(winW) / static_cast<float>(winH);
            int drawW = 0, drawH = 0;
            if (windowRatio > targetRatio) {
                // Window is wider than target ratio -> pillarbox (left/right bars)
                drawH = winH;
                drawW = static_cast<int>(winH * targetRatio);
            } else {
                // Window is taller than target ratio -> letterbox (top/bottom bars)
                drawW = winW;
                drawH = static_cast<int>(winW / targetRatio);
            }
            dstRect = {(winW - drawW) / 2, (winH - drawH) / 2, drawW, drawH};
        }

        SDL_RenderCopy(renderer, targetTexture, nullptr, &dstRect);
        SDL_RenderPresent(renderer);

        // Cap Frame Rate to 60 FPS
        Uint32 frameTime = SDL_GetTicks() - frameStart;
        if (frameTime < (1000 / TARGET_FPS)) {
            SDL_Delay((1000 / TARGET_FPS) - frameTime);
        }

        if (!screenshotPath.empty() && (screenshotPause ? loopFrames >= screenshotTargetFrame : frames >= screenshotTargetFrame)) {
            SDL_Surface* sSurf = SDL_CreateRGBSurfaceWithFormat(0, INTERNAL_WIDTH, INTERNAL_HEIGHT, 32, SDL_PIXELFORMAT_RGBA8888);
            SDL_SetRenderTarget(renderer, targetTexture);
            SDL_RenderReadPixels(renderer, nullptr, SDL_PIXELFORMAT_RGBA8888, sSurf->pixels, sSurf->pitch);
            SDL_SaveBMP(sSurf, screenshotPath.c_str());
            SDL_FreeSurface(sSurf);
            break;
        }
    }

    // Cleanup
    for (auto* c : controllers) SDL_GameControllerClose(c);
    for (auto* j : joysticks) SDL_JoystickClose(j);
    textures.destroy();
    SDL_DestroyTexture(carTexture);
    SDL_DestroyTexture(targetTexture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}
