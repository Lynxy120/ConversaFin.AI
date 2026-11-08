# UI/UX DESIGN DOCUMENT (DESIGN.MD)
**Project Name:** ConversaFin.AI (KasirChat.AI)
**Document Version:** 1.0.0
**Target Platform:** Web Dashboard (PWA untuk Mobile Android & Layar Desktop)
**Design Theme:** Modern Minimalist, Glassmorphism, Trustworthy & Approachable.

---

## 1. Filosofi & Konsep Desain
Desain ConversaFin.AI mengusung konsep **"Zero Friction & Crystal Clear"**. Mengingat target audiens adalah pelaku UMKM yang memiliki mobilitas tinggi, antarmuka harus terasa ringan, tidak mengintimidasi, dan sangat mudah dinavigasi. 
*   **Modern Minimalist:** Mengurangi elemen visual yang tidak perlu. Fokus pada data (grafik, angka omset, daftar pesanan).
*   **Glassmorphism:** Memberikan kesan modern dan *depth* (kedalaman) tanpa membuat layar terasa penuh. Digunakan pada kartu (cards), modal/pop-up, dan navigasi.
*   **Aksesibilitas (A11y):** Kontras warna yang tinggi untuk teks, tombol berukuran proporsional (mudah di-tap di HP), dan label yang jelas.

---

## 2. Panduan Warna (Color Palette)
Warna utama menggunakan **Biru Langit (Sky Blue)**. Biru melambangkan kepercayaan, keamanan finansial, dan teknologi, sangat cocok untuk aplikasi kasir dan asisten keuangan.

### Primary Colors (Gradient & Solid)
*   **Primary Blue:** `#0EA5E9` (Sky Blue) - Digunakan untuk tombol utama, ikon aktif, dan elemen interaktif.
*   **Gradient Background:** Kombinasi halus dari `#E0F2FE` (Light Sky) ke `#F3E8FF` (Soft Purple/Indigo) di sudut-sudut layar. Ini memberikan latar belakang yang menenangkan dan membuat efek *glassmorphism* menonjol.
*   **Gradient Brand:** `linear-gradient(135deg, #0EA5E9 0%, #3B82F6 100%)` - Untuk tombol *Call to Action* utama (misal: "Simpan Produk").

### Semantic Colors (Status & Indikator)
Penting agar UMKM langsung paham status keuangan atau transaksinya tanpa harus membaca secara detail.
*   **Success (Pemasukan/Lunas):** `#10B981` (Emerald Green) - Latar belakang transparan `rgba(16, 185, 129, 0.1)` untuk tag.
*   **Danger (Pengeluaran/Hapus):** `#EF4444` (Red) - Untuk tombol hapus atau grafik pengeluaran.
*   **Warning (Pending/Draft):** `#F59E0B` (Amber/Yellow) - Untuk transaksi QRIS yang belum dibayar.

### Neutral Colors (Teks & Background)
*   **Text Primary:** `#0F172A` (Slate 900) - Abu-abu sangat gelap (bukan hitam pekat) untuk teks utama agar mata tidak cepat lelah.
*   **Text Secondary:** `#64748B` (Slate 500) - Untuk deskripsi, label input, dan placeholder.
*   **Base Surface:** `#FFFFFF` (White) atau efek Glass.

---

## 3. Efek Glassmorphism & Komponen UI
Untuk memenuhi permintaan tema *Glassmorphism* yang stabil dan tidak berlebihan, terapkan aturan CSS (atau Tailwind) berikut secara konsisten:

### Spesifikasi Glass Card
Gunakan ini pada Card Grafik, Card Tabel, dan Navbar/Bottom Navigation.
*   **Background:** `rgba(255, 255, 255, 0.7)` (Putih dengan transparansi 70%)
*   **Backdrop Filter (Blur):** `blur(12px)`
*   **Border:** `1px solid rgba(255, 255, 255, 0.5)`
*   **Shadow:** `box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05)`
*   *Catatan:* Pastikan fallback background solid putih (opsional) untuk browser/perangkat lama yang tidak mendukung `backdrop-filter`.

### Tombol Interaktif (Clear & Unambiguous)
Tidak boleh ada ambiguitas. Semua tombol harus terlihat seperti tombol (bukan sekadar teks).
*   **Primary Button (Aksi Utama):** Background Gradient Biru, Teks Putih tebal (Semibold), sudut membulat (border-radius: 8px atau 12px), efek hover sedikit terangkat (transform: translateY(-1px)) dan bayangan bertambah.
*   **Secondary/Ghost Button:** Background transparan, Border Biru/Abu-abu, efek hover background menjadi biru sangat muda.
*   **Sizing (PWA Mobile):** Tinggi tombol minimal `44px` hingga `48px` sesuai standar *touch target* Apple/Material Design agar mudah ditekan oleh jempol.

---

## 4. Sistem Tata Letak & Responsivitas (Layouting)

Proyek ini adalah PWA dan digunakan di Laptop. UI/UX harus adaptif (bukan sekadar mengecil).

### Tampilan Laptop / Desktop (> 1024px)
*   **Sidebar Navigation (Kiri):** Lebar tetap (sekitar 250px). Berisi menu: Dashboard, Katalog, Transaksi, Pengaturan. Menggunakan efek Glassmorphism.
*   **Main Content (Kanan):** Area luas untuk visualisasi data (Grafik Chart.js/Recharts). Tabel transaksi dapat menampilkan lebih banyak kolom (Tanggal, Kategori, Nominal, Status, Aksi).

### Tampilan Mobile PWA (Android / iOS) (< 768px)
*   **Bottom Navigation Bar:** Menggantikan Sidebar. Posisi di paling bawah layar (Thumb Zone) dengan ikon yang jelas (Beranda, Katalog, Riwayat, Profil).
*   **Layout Susun (Stacking):** Grafik berubah dari *bar chart* yang lebar menjadi *line chart* atau *doughnut chart* yang padat. Tabel transaksi berubah menjadi desain *Card List* (Daftar Kartu), di mana 1 baris transaksi menjadi 1 kartu dengan status warna di sudutnya.
*   **Floating Action Button (FAB):** Tombol "+" melayang di pojok kanan bawah (khusus di halaman Katalog) untuk "Tambah Produk".

---

## 5. Rekomendasi Peningkatan Standar UI/UX

Berdasarkan analisis PRD Anda, berikut adalah fitur UI/UX ekstra yang **wajib** ditambahkan untuk menjamin kualitas standar industri aplikasi B2B/UMKM:

1.  **Empty States yang Ramah (State Kosong):**
    *   *Kasus:* Saat penjual baru mendaftar, belum ada produk atau transaksi.
    *   *Solusi:* Jangan tampilkan tabel kosong atau grafik datar ("0"). Tampilkan ilustrasi/ikon menarik dengan teks pendukung yang memotivasi: *"Belum ada produk di etalasemu. Yuk, tambahkan menu andalanmu sekarang!"* beserta tombol CTA "Tambah Produk".

2.  **Sistem Umpan Balik (Feedback Loops & Toasts):**
    *   *Kasus:* User menghapus produk, menyimpan produk, atau mengekspor data Excel.
    *   *Solusi:* Gunakan *Toast Notification* di sudut kanan atas (Desktop) atau atas/bawah layar (Mobile). Misal: *✅ "Produk Kopi Susu berhasil diperbarui."* Jangan biarkan user menebak apakah sistem merespons perintah mereka.

3.  **Skeleton Loading State:**
    *   *Kasus:* Memuat data agregat grafik atau tabel dari Supabase bisa memakan waktu 1-2 detik.
    *   *Solusi:* Jangan gunakan "Spinner" atau tulisan "Loading...". Gunakan *Skeleton Screen* (bayangan komponen berwarna abu-abu yang berkedip halus) dengan efek *glassmorphism* agar transisi terasa cepat dan modern.

4.  **Optimasi Interaksi Hapus Data (Destructive Action):**
    *   *Kasus:* Menghapus produk atau transaksi (FR-DB-02).
    *   *Solusi:* Selalu gunakan *Confirmation Modal* (Pop-up konfirmasi) untuk mencegah hapus tak sengaja. Judul harus jelas: "Hapus Produk?", Tombol merah untuk "Ya, Hapus", tombol abu-abu untuk "Batal".

5.  **Typography yang Mudah Dibaca (Legibility):**
    *   Gunakan Font Sans-Serif modern seperti **Plus Jakarta Sans**, **Inter**, atau **Poppins**.
    *   Angka (Uang/Rupiah) harus menggunakan font *Tabular Figures* atau font monospace untuk laporan, agar karakter angka sejajar dan mudah dibaca (misal di halaman tabel transaksi).

## 6. Integrasi UX Sisi WhatsApp (Conversational UI)
Walaupun desain visual difokuskan pada PWA, UX interaksi WA harus diatur:
*   **Formatting Pesan:** Gunakan *bold* (`*teks*`) untuk nominal uang dan nama produk, serta *italic* (`_teks_`) untuk instruksi.
*   **Emoji Secukupnya:** Gunakan emoji sebagai indikator visual (✅ untuk berhasil, 📊 untuk laporan, 🧾 untuk struk) agar pesan bot tidak terlihat monoton.
*   **Error Handling (AI Ambigu - FR-BE-02):** Jika Voice Note/Foto Nota tidak jelas, bot tidak boleh sekadar diam/error. Balasan bot harus memandu: *"Maaf, suara kurang jelas / foto terlalu gelap. Bisa tolong ulangi atau ketik manual jumlah pengeluarannya?"*