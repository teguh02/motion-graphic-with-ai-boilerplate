# AGENTS.md — Panduan untuk agen AI (Claude Code, Codex, OpenCode, Gemini CLI, dll.)

Repo ini adalah boilerplate video **motion graphic berbasis kode**: HTML/CSS/JS dirender frame demi frame
oleh Playwright, lalu di-encode ffmpeg dan dicampur dengan dubbing + SFX sintetis. Setiap ilustrasi muncul
**tepat pada kata yang diucapkan** narator, memakai timestamp per kata dari Whisper.

Baca file ini sampai habis sebelum mengubah apa pun. `README.md` adalah versi untuk manusia.

---

## 1. Peta repo

```
project.json            ← SATU-SATUNYA config: judul, ukuran, fps, tempo, brand, ticker, keyword subtitle, safe zone
content/
  narasi.txt            ← naskah dubbing (paragraf dipisah baris kosong). Sumber kebenaran ejaan kata.
  brief.md              ← brief visual per adegan: narasi, CUE kata → aksi, teks/kode verbatim
  dubing.wav            ← hasil TTS (Google AI Studio, ElevenLabs, dll.) — disediakan manusia
STORYBOARD.md           ← tabel adegan + waktu + cue (diisi setelah timestamp ada) + sumber/lisensi aset
src/
  index.html            ← daftar <script> adegan (urut tayang)
  style.css             ← token desain di :root (warna, font, radius, zona layout)
  engine.js             ← E.*: easing, pop/rise/draw/typed/shake/float, cue(), sfx(), icon(), rand()
  components.js         ← SCENES[], helper: pill, disc, codeBlock, img, codeWord, offsetIn
  subtitles.js          ← subtitle karaoke (jangan diubah kecuali perlu)
  main.js               ← boot, ICON_NAMES, renderAt(t), chrome (header/ticker/progress/kredit)
  scenes/NN-nama.js     ← satu file per adegan
assets/fonts|icons|img  ← font OFL, ikon Lucide, foto (+ img/CREDITS.json)
tools/                  ← pipeline Python (lihat §3)
build/  output/         ← hasil generate (di-.gitignore)
```

## 2. Alur kerja (ikuti urutannya)

| Fase | Yang dikerjakan | Perintah |
|------|-----------------|----------|
| 0. Setup | Pasang dependensi, cek lingkungan | `pip install -r requirements.txt` · `python -m playwright install chromium` · `python tools/doctor.py` |
| 1. Naskah | Tulis `content/narasi.txt` + `content/brief.md`, isi `project.json` (title, output, brand, ticker, subtitles) | — |
| 2. Dubbing | **Manusia** membuat `content/dubing.wav` dari `narasi.txt`. Jika belum ada: lanjut dengan timing estimasi | `python tools/estimate_words.py` |
| 3. Timing | Timestamp per kata + tempo → `build/words.json`, `build/voice.wav` | `python tools/transcribe.py` |
| 4. Storyboard | Isi `STORYBOARD.md`: tiap adegan, rentang waktu, kata cue + detiknya (baca `build/words.json`) | — |
| 5. Adegan | Buat `src/scenes/NN-*.js`, daftarkan di `index.html`, ikon di `main.js` | `python tools/fetch_icons.py --from-main` |
| 6. QA | Harus PASS, lalu lihat contact sheet (buka gambarnya!) dan perbaiki | `python tools/check.py` · `python tools/render.py --scenes` |
| 7. Render | Video final → `output/` | `python tools/render.py` |

Aturan fase:
- Naskah yang berubah setelah dubbing ⇒ dubbing harus dibuat ulang. Jangan ubah `narasi.txt` diam-diam.
- Setelah `dubing.wav` muncul, **selalu** jalankan `transcribe.py` lagi (timing estimasi pasti meleset), lalu `check.py`.
- Ubah `tempo` di project.json (mis. 1.15 agar muat batas durasi) ⇒ `python tools/transcribe.py --retime`.
- Agen tidak bisa membuat dubbing sendiri kecuali diberi akses TTS. Jika `dubing.wav` belum ada, selesaikan
  fase 1, 2 (estimasi), 4–6, render `--draft`, lalu laporkan bahwa video menunggu dubbing.

## 3. Tools

| Perintah | Fungsi |
|----------|--------|
| `python tools/doctor.py` | Cek Python, paket, Chromium, font, naskah, dubbing, timing |
| `python tools/estimate_words.py [--wps 2.6]` | Timing kata DRAF dari naskah (tanpa audio) |
| `python tools/transcribe.py [--model small] [--retime]` | Whisper + penyelarasan ke naskah + tempo |
| `python tools/preview.py [--t 12.5]` | Preview di browser: scrubber + play dengan suara (`?dev`) |
| `python tools/check.py` | QA: error JS, safe zone, sinkron subtitle, teks verbatim, kesinambungan adegan |
| `python tools/render.py --stills 1.5,8,12` | Screenshot di detik tertentu → `build/stills/` |
| `python tools/render.py --scenes` | 3 still per adegan + contact sheet `build/sheet_*.jpg` |
| `python tools/render.py [--draft]` | Render penuh (draft = setengah resolusi) → `output/` |
| `python tools/fetch_icons.py <nama…> / --from-main` | Unduh ikon Lucide v0.460.0 |
| `python tools/fetch_images.py stem="kueri"` | Foto dari API publik tanpa kunci (Wikimedia → Openverse → NASA, otomatis pindah provider) + kredit |
| `python tools/fetch_images.py --register x.png --source "AI-generated (model)"` | Catat kredit gambar buatan sendiri |

## 4. Kontrak adegan

```js
// src/scenes/05-contoh.js
SCENES.push({
  id: 'contoh', mood: 'accent',                       // mood: accent | warm | ink (glow latar)
  get start() { return cue('Kalimat') - 0.15; },       // getter: timing baru ada saat boot
  get end() { return cue('Berikutnya') - 0.15; },      // = start adegan berikutnya (tanpa celah)
  build(root) {                                        // dipanggil SEKALI: bangun DOM, daftarkan SFX
    const tA = cue('angka'), tB = cue('naik turun');   // cue boleh frasa beberapa kata
    const card = abs(h('div', { cls: 'card', text: 'Halo' }), 'left:60px;top:100px;width:960px');
    root.append(card);
    E.sfx(tA, 'pop');
    return (t) => {                                    // dipanggil TIAP FRAME: hanya set style dari t
      E.pop(card, t, tA);
    };
  },
});
```

- Adegan pertama `start: 0`; adegan terakhir `end: cueEnd('kataTerakhir') + CFG.outro` (lihat `04-outro.js`).
- `cue(kata, n, after)` = detik mulai kemunculan ke-n kata itu. Kata dicocokkan tanpa tanda baca & huruf besar.
  Jika kata tidak ada di naskah → boot gagal dengan pesan jelas (dilaporkan `check.py`).
- Area panggung (`#stage`): 1080×830 px, mulai y=410. Koordinat `abs(...)` relatif ke panggung.
- SFX yang tersedia: `whoosh pop tick click hit stamp ding swell fall coins` (`hit` juga memicu kilat putih).
- Teks kode/angka yang wajib persis → pakai `codeBlock(...)` (atribut `data-verbatim`), dan tulis teksnya di `brief.md`.

## 5. Aturan wajib

1. **Deterministik.** Visual = fungsi murni dari `t`. DILARANG: `Date.now()`, `setTimeout/setInterval`,
   CSS `transition`/`animation`, `Math.random()` tanpa seed (pakai `E.rand(seed)`), video/GIF yang berputar sendiri.
2. **Sinkron kata.** Setiap kemunculan penting dikunci ke `cue()`, bukan ke detik hard-code. Isi kolom cue di STORYBOARD.
3. **Safe zone** (Reels/TikTok/Shorts): teks tidak boleh di atas y=200, di bawah y=1500, atau melewati x=950 di
   paruh bawah (tombol like/komentar). `check.py` memverifikasi; elemen dekoratif yang sengaja keluar diberi `data-safe-ignore`.
4. **Satu sumber config.** Warna/font hanya lewat token di `style.css :root`; ukuran/fps/brand/keyword lewat `project.json`.
   Jangan hard-code warna hex baru di adegan bila token sudah ada.
5. **Aset legal & tercatat.** Hanya font OFL, ikon Lucide (ISC), foto dari `fetch_images.py` (otomatis hanya CC0 /
   Public Domain / CC BY / CC BY-SA, kredit di `assets/img/CREDITS.json`), atau buatan sendiri (SVG/CSS, atau gambar
   AI jika kamu mampu membuatnya — simpan di `assets/img/` lalu `--register`). SFX & musik disintesis di `tools/sfx.py`.
   Tulis semua sumber di bagian "Sumber elemen" `STORYBOARD.md`; foto CC BY/BY-SA wajib dicantumkan nama pembuatnya.
6. **Gambar: pilih jalur, jangan macet.** Urutan: (a) ilustrasi SVG/CSS sendiri bila cukup, (b) `fetch_images.py`
   — provider yang timeout/sibuk/kosong otomatis dilewati, (c) bila semua gagal: ubah kueri (pendek, konkret,
   bahasa Inggris), ubah urutan `--providers`, atau buat gambar sendiri (AI) / gambar ulang dalam SVG.
   Selalu lihat hasil unduhan sebelum dipakai — kueri bisa memberi gambar yang tidak relevan.
7. **Teks di layar mengikuti naskah & brief.** Jangan mengarang fakta, angka, kutipan, atau kode yang tidak ada di
   `brief.md`/`narasi.txt`. Ejaan subtitle berasal dari `narasi.txt`; penggantian tampilan nama lewat `subtitles.rename`.
8. **Identitas.** Patuhi "Aturan khusus proyek" di `brief.md` (mis. larangan logo lembaga, lambang negara, kesan resmi).
9. **Selesai = terverifikasi.** Sebelum melapor selesai: `check.py` PASS, contact sheet sudah DILIHAT (bukan hanya
   dibuat), dan render final ada di `output/`. Laporkan durasi, jumlah adegan, dan apa pun yang belum (mis. dubbing estimasi).

## 6. Tips kualitas visual

- Satu ide per adegan; 1 judul besar + 2–4 elemen pendukung yang muncul bertahap sesuai kata.
- Hierarki tegas: judul 90–150 px, isi 36–52 px, label mono 22–26 px. Minimal 60 px dari tepi kiri/kanan.
- Gerak masuk: `E.rise` (geser + fade + blur) untuk teks, `E.pop` (overshoot) untuk ikon/badge,
  `E.draw` untuk garis/grafik SVG (`pathLength="1"`), `E.count` untuk angka, `E.typed` untuk efek mengetik.
- Beri gerak idle kecil (`E.float`) agar frame tidak mati, tapi jangan sampai mengganggu teks.
- SFX secukupnya: `pop` untuk kemunculan, `whoosh` untuk transisi besar, `tick` untuk deret, `ding` untuk penegasan.
- Narasi TTS: tulis angka sebagai kata ("sebelas koma lima persen"), singkatan yang dibaca per huruf beri penjelasan,
  kalimat pendek, satu gagasan per paragraf (paragraf = pemisah blok subtitle).
