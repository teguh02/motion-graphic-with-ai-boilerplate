# Motion Graphic Boilerplate

Template kosongan untuk membuat video **motion graphic vertikal (Reels / TikTok / Shorts)** dengan kode,
dikerjakan bersama agen AI apa pun — Claude Code, Codex, OpenCode, Gemini CLI, Cursor, dan lainnya.

- Visual dibuat dengan HTML/CSS/JS, dirender **frame demi frame** (deterministik, tanpa patah-patah).
- Setiap ilustrasi muncul **tepat pada kata yang diucapkan** (timestamp per kata dari Whisper).
- Subtitle karaoke, SFX & pad latar disintesis sendiri (tanpa audio berlisensi), loudness siap upload (−14 LUFS).
- QA otomatis: safe zone Reels/TikTok, sinkron subtitle, teks kode verbatim, error JS.

Instruksi untuk agen ada di [AGENTS.md](AGENTS.md) (Claude Code membaca lewat `CLAUDE.md`, Gemini lewat `GEMINI.md`).

## Persyaratan

- Python 3.10+ (diuji di 3.14)
- Tidak perlu Node.js maupun ffmpeg sistem — ffmpeg dibawa oleh `imageio-ffmpeg`.

```bash
pip install -r requirements.txt
```

```bash
python -m playwright install chromium
```

```bash
python tools/doctor.py
```

## Coba demo (tanpa dubbing)

```bash
python tools/estimate_words.py
```

```bash
python tools/preview.py
```

Browser terbuka dengan scrubber. Untuk render video draf: `python tools/render.py --draft`.

## Membuat video baru

1. **Naskah** — tulis `content/narasi.txt` (paragraf dipisah baris kosong) dan `content/brief.md`
   (adegan, kata cue → aksi, teks/kode yang harus persis). Sesuaikan `project.json`.
2. **Dubbing** — tempel `narasi.txt` ke TTS (mis. Google AI Studio), ekspor ke `content/dubing.wav`
   (mp3/m4a juga bisa; ubah `audio.voice` di `project.json`). Panduan bergambar langkah demi langkah:
   [Panduan_Dubbing_Google_AI_Studio.pdf](Panduan_Dubbing_Google_AI_Studio.pdf).
3. **Timing** — `python tools/transcribe.py` → `build/words.json` + `build/voice.wav`.
4. **Adegan** — satu file per adegan di `src/scenes/`, daftarkan di `src/index.html`.
   Ikon baru: tambahkan ke `ICON_NAMES` di `src/main.js`, lalu `python tools/fetch_icons.py --from-main`.
   Foto pendukung (tanpa API key): `python tools/fetch_images.py laptop="laptop on desk"` — mencoba
   Wikimedia Commons, lalu Openverse, lalu NASA; provider yang error/timeout otomatis dilewati. Hanya lisensi
   CC0 / Public Domain / CC BY / CC BY-SA yang diambil, kreditnya tercatat di `assets/img/CREDITS.json`.
   Gambar buatan sendiri (mis. hasil AI) taruh di `assets/img/` lalu `--register nama.png --source "AI-generated (model)"`.
5. **QA** — `python tools/check.py` harus PASS; `python tools/render.py --scenes` lalu lihat `build/sheet_*.jpg`.
6. **Render** — `python tools/render.py` → `output/<nama di project.json>`.

Atau serahkan semuanya ke agen: "Buat video motion graphic tentang <topik> mengikuti AGENTS.md."

## project.json

| Kunci | Arti |
|-------|------|
| `title`, `output` | Judul proyek & nama file MP4 |
| `width`, `height`, `fps` | Default 1080×1920 @ 30 fps. Layout CSS dirancang untuk portrait |
| `outro` | Detik layar penutup tanpa suara setelah kata terakhir |
| `language`, `whisper_model` | Bahasa narasi & ukuran model Whisper (`tiny` … `large-v3`) |
| `tempo` | Percepat dubbing tanpa ubah nada (mis. `1.15`); lalu `transcribe.py --retime` |
| `audio` | Path dubbing, level SFX, pad latar on/off & level, target loudness |
| `render` | Jumlah worker paralel, kualitas (CRF, JPEG), port server lokal |
| `brand`, `ticker` | Header, tag, kredit (HTML), dan isi ticker berjalan |
| `subtitles` | `max_chars` per baris, kata berwarna `accent`, kata `code` (chip mono), `rename` tampilan kata |
| `safe_zone` | Margin aman (px) yang dicek `tools/check.py` |

## Struktur

```
project.json  AGENTS.md  STORYBOARD.md
content/   narasi.txt · brief.md · dubing.wav
src/       index.html · style.css · engine.js · components.js · subtitles.js · main.js · scenes/
assets/    fonts/ · icons/ · img/
tools/     doctor · estimate_words · transcribe · preview · check · render · contact · sfx · fetch_icons · fetch_images
```

## Lisensi aset bawaan

- Plus Jakarta Sans, JetBrains Mono — SIL Open Font License 1.1 (lihat `assets/fonts/LICENSE.md`).
- Ikon Lucide — ISC License (lihat `assets/icons/LICENSE.md`).
