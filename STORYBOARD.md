# Storyboard — "Template Motion Graphic" (Reels 1080×1920, 30 fps)

Durasi dubbing **–** dtk + outro 3,6 dtk = **–** dtk. Waktu diambil dari timestamp per kata
(`build/words.json`, Whisper lalu disejajarkan ke naskah). Setiap elemen muncul tepat pada kata di kolom "Cue".

> Agen: isi tabel ini setelah `tools/transcribe.py`. Detik = `start` kata di `build/words.json`.

| # | Waktu | Naskah (ringkas) | Visual | Cue kata → aksi |
|---|-------|------------------|--------|-----------------|
| 1 | 0,0–… | Halo, boilerplate siap dipakai agen AI | Ikon sparkles, judul "Motion Graphic", 3 pil agen | "boilerplate" → judul · "agen" → pil agen |
| 2 | …–… | Tulis naskah, buat dubbing, ilustrasi muncul tepat pada kata | 3 kartu langkah + garis waktu | "naskah" · "dubbing" · "ilustrasi" → kartu · "tepat" → garis waktu |
| 3 | …–… | Subtitle karaoke, efek suara, render otomatis, video vertikal | 3 baris fitur, blok terminal, bingkai ponsel | "subtitle" · "efek" · "render" → baris · "vertikal" → ponsel |
| 4 | …–akhir | Selamat berkarya! (+ outro tanpa suara) | Judul penutup + kredit | "Selamat" → judul + hit |

Elemen tetap: header brand, ticker berjalan, progress bar per adegan, subtitle karaoke (kata aktif = blok aksen),
kredit di outro. Semua teks di dalam safe zone Reels/TikTok (dicek `tools/check.py`).

## Sumber elemen
- Font: Plus Jakarta Sans & JetBrains Mono (Google Fonts, SIL OFL 1.1).
- Ikon: [Lucide](https://lucide.dev) v0.460.0 (ISC).
- Foto: — (salin judul, pembuat & lisensi dari `assets/img/CREDITS.json` bila ada).
- SFX & pad latar: disintesis sendiri di `tools/sfx.py`, tanpa audio pihak ketiga.
- Dubbing: (sebutkan layanan TTS / pengisi suara).
