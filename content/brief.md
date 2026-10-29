# Brief Visual — "Template Motion Graphic"

Pasangan dari: `content/narasi.txt` (naskah dubbing). Ganti seluruh isi file ini untuk video baru.

## Tujuan & penonton
- Topik: demo boilerplate motion graphic.
- Penonton: kreator konten yang memakai agen AI.
- Platform: Reels / TikTok / Shorts (1080×1920, 30 fps).

## Arah visual
- Gaya: editorial kertas hangat, kartu putih berbayang, aksen biru tegas + kuning sorotan.
- Palet: lihat token `:root` di `src/style.css`.
- Font: Plus Jakarta Sans (teks), JetBrains Mono (label/kode).
- Ikon: Lucide. Foto: (tidak ada untuk demo ini).

## Aturan khusus proyek
- (Tulis batasan identitas/merek di sini. Contoh: jangan pakai logo lembaga, jangan beri kesan resmi pemerintah.)
- Kode/angka/kutipan yang tampil di layar harus PERSIS seperti di file ini (dicek `tools/check.py`).

---

## ADEGAN 1 — HOOK
NARASI:
Halo! Ini adalah boilerplate motion graphic yang siap dipakai oleh agen AI mana pun.

CUE:
- "boilerplate" → judul besar "Motion Graphic" pop-in
- "agen"        → tiga pil nama agen: Claude Code · Codex · OpenCode

## ADEGAN 2 — ALUR KERJA
NARASI:
Cukup tulis naskah, buat dubbing, lalu setiap ilustrasi akan muncul tepat pada kata yang diucapkan.

CUE:
- "naskah"     → kartu langkah 1 (ikon file-text)
- "dubbing"    → kartu langkah 2 (ikon mic)
- "ilustrasi"  → kartu langkah 3 (ikon sparkles)
- "tepat"      → garis waktu tergambar + penanda kata menyala

## ADEGAN 3 — FITUR
NARASI:
Sudah ada subtitle karaoke, efek suara sintetis, dan render otomatis ke video vertikal.

CUE:
- "subtitle" → baris fitur "Subtitle karaoke"
- "efek"     → baris fitur "Efek suara sintetis"
- "render"   → baris fitur "Render otomatis"
- "vertikal" → bingkai ponsel 1080×1920

KODE (contoh teks verbatim yang dicek otomatis):
python tools/render.py

## ADEGAN 4 — PENUTUP
NARASI:
Selamat berkarya!

CUE:
- "Selamat" → judul "Selamat berkarya!" + kredit

PENUTUP LAYAR (tanpa suara, selama `outro` detik di project.json):
- Kredit: Video By Nama Kamu
