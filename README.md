# 💬 ConversaFin.AI (KasirChat.AI)
> **AI-Powered WhatsApp Commerce & Smart Bookkeeping for MSMEs / UMKM**

![Version](https://img.shields.io/badge/Version-1.4.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.14.8-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini-3.5_Flash_Lite-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-PWA-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

---

## 📌 Tentang Proyek

**ConversaFin.AI** adalah solusi *Conversational Commerce* dan *Smart Financial Accounting* yang dirancang khusus untuk memodernisasi operasional UMKM di Indonesia. 

Sistem ini mengubah WhatsApp menjadi **Kasir Digital Otomatis** untuk pembeli sekaligus **Asisten Keuangan Pintar** bagi pemilik usaha, memecahkan masalah rekapitulasi manual, tercampurnya uang pribadi dan bisnis, serta risiko *fraud* pada verifikasi pembayaran transfer manual.

Proyek ini dikembangkan dalam konteks pemenuhan tugas mata kuliah **Kewirausahaan & E-Commerce (D3 Manajemen Informatika, Politeknik Negeri Padang)**.  
🎯 **Target Rilis:** 24 November 2026

---

## 🚀 Value Proposition

1. **Zero Friction Operations:** Pencatatan keuangan tanpa aplikasi akuntansi rumit. Cukup kirim teks, pesan suara (Voice Note), atau foto nota ke WhatsApp.
2. **Automated Sales Pipeline:** Memotong waktu proses transaksi pembeli melalui pesan daftar interaktif yang terhubung langsung ke database toko, serta pembayaran instan via QRIS Dinamis.
3. **Separation of Concerns:** Memisahkan arus data pengeluaran/pemasukan Bisnis dan Pribadi secara otomatis menggunakan NLP dan Vision AI.

---

## ✨ Ruang Lingkup Fitur (Modul Utama)

### 🛒 1. Conversational E-Commerce (Sisi Pembeli - WA)
* **Katalog Interaktif Native:** Menampilkan daftar produk (maksimal 10 item menu) menggunakan *Interactive List Message* bawaan WhatsApp API.
* **Keranjang Belanja & Checkout:** Sistem menghitung total tagihan secara otomatis dari *payload order*.
* **Pembayaran QRIS Dinamis:** Generasi kode QRIS spesifik per transaksi via **Midtrans API**.
* **Auto-Settlement & Struk Digital:** Verifikasi status LUNAS tanpa intervensi manual (Webhook Midtrans) & pengiriman Struk Belanja Digital (PDF/Gambar) ke WA.

### 🎙️ 2. AI Financial Assistant (Sisi Penjual - WA)
* **Multi-Input Processing:** Mendukung Pesan Teks, Audio Voice Note (`.ogg`), dan Foto Struk Belanja (`.jpg/.png`).
* **Speech-to-Text & Vision OCR:** Menggunakan Google Gemini API untuk mentranskripsikan suara dan membaca rincian nota fisik.
* **Auto-Domain Classification:** AI secara cerdas memilah transaksi menjadi kategori **Bisnis** (Operasional, Bahan Baku, Penjualan) atau **Pribadi**.
* **Command-based Quick Report:** Pengecekan laporan cepat via chat (misal: `/laporan`, `/omset`, `/hari-ini`).

### 📊 3. Web Dashboard (Sisi Penjual - PWA)
* **Visual Analytics:** Grafik tren omset, rasio laba-rugi, dan distribusi pengeluaran bisnis vs pribadi.
* **Manajemen Katalog (CRUD):** Tambah, Edit, Hapus, Ubah Harga, dan Upload Foto Menu.
* **Data Export:** Filter tabel transaksi dan ekspor laporan ke format `.xlsx` (Excel) dan `.pdf`.
* **PWA Capability:** Mendukung instalasi *Add to Home Screen* dengan desain responsif untuk mobilitas tinggi.

---

## 🛠️ Spesifikasi Arsitektur & Tech Stack

| Komponen | Teknologi & Spesifikasi |
| :--- | :--- |
| **Backend Framework** | Python 3.14.8 (FastAPI) - *Async I/O, BackgroundTasks* |
| **AI Engine** | Google Gemini API (`gemini-3.5-flash-lite`) - *Text Intent, Audio STT, Image Vision OCR* |
| **Messaging API** | Meta WhatsApp Cloud API (Graph API v26.0) - *Sandbox Mode* |
| **Payment Gateway** | Midtrans Core API - *Dynamic QRIS & HTTP Webhook* |
| **Database & Storage** | PostgreSQL (Supabase) & Supabase Storage (Audio, Image, PDF Bucket) |
| **Frontend Dashboard** | Next.js (Responsive Web Framework) - *PWA Enabled* |
| **Security & Network** | Cloudflare Tunnel + Nginx (SSL/TLS, WAF) |
| **Containerization** | Docker & Docker Compose |

---

## 🏗️ Arsitektur Sistem

```text
[ Pembeli (WA) ] ───> [ Meta WA Cloud API ] ───┐
                                              ├───> [ Cloudflare / Nginx ] ───> [ FastAPI Backend ]
[ Penjual (WA) ] ───> [ Meta WA Cloud API ] ───┘                                     │
                                                                                     ├───> [ Gemini AI API ]
[ Penjual (Web) ] ──> [ Next.js PWA ] ───────────────────────────────────────────────┼───> [ Supabase PostgreSQL ]
                                                                                     └───> [ Midtrans Payment ]
```

---

## 🗓️ Roadmap Pengembangan (8 Minggu)

* **W1 (06/10/26):** Setup Infrastruktur (Docker, Repositori) & Konfigurasi Kredensial API.
* **W2 (13/10/26):** Core Webhook WhatsApp & Role Routing (Penjual vs Pembeli).
* **W3 (20/10/26):** Integrasi Katalog Interaktif (Interactive Message) & Keranjang Belanja Supabase.
* **W4 (27/10/26):** Integrasi Midtrans QRIS Dinamis & Auto-Settlement Struk PDF.
* **W5 (03/11/26):** Integrasi *AI Financial Engine* (Gemini 3.5 Flash Lite) untuk Teks, VN, & OCR.
* **W6 (10/11/26):** Pengembangan Web Dashboard PWA (Next.js), Chart Analytics & CRUD Produk.
* **W7 (17/11/26):** End-to-End Testing, Optimasi Kueri, dan Pengamanan Cloudflare Tunnel.
* **W8 (24/11/26):** Final Deployment, Persiapan Presentasi & Live Demo. 