# 💬 ConversaFin.AI
> **AI-Powered WhatsApp Commerce & Smart Bookkeeping for MSMEs / UMKM**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Multimodal-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## 📌 Tentang Proyek

**ConversaFin.AI** adalah solusi *Conversational Commerce* dan *Smart Financial Accounting* yang dirancang khusus untuk memodernisasi operasional UMKM di Indonesia. 

Sistem ini mengubah nomor WhatsApp menjadi **Kasir Digital Otomatis** untuk pembeli sekaligus **Asisten Keuangan Pintar** bagi pemilik usaha. Pembeli dapat memesan dan membayar via QRIS langsung di dalam chat WA, sedangkan pemilik usaha dapat mencatat pengeluaran dan pemasukan bisnis hanya dengan mengirim **pesan teks, Voice Note (pesan suara), atau foto nota/struk belanjaan**.

Proyek ini dikembangkan untuk memenuhi tugas mata kuliah **Kewirausahaan & E-Commerce**.

---

## ✨ Fitur Utama

### 🛒 1. Conversational E-Commerce (Sisi Pembeli)
* **Katalog Interaktif Native:** Menampilkan daftar produk/menu langsung di dalam aplikasi WhatsApp.
* **Keranjang Belanja & Checkout:** Pembeli dapat memilih beberapa item dan melakukan *checkout* tanpa keluar dari WA.
* **Pembayaran QRIS Dinamis:** Generasi kode QRIS otomatis berbasis **Midtrans Payment Gateway**.
* **Auto-Settlement & Struk Digital:** Verifikasi pembayaran instan dan pengiriman struk belanja digital berbasis PDF.

### 🎙️ 2. AI Financial Assistant (Sisi Penjual via WA)
* **Multi-Input Keuangan:** Pencatatan otomatis dari pesan **Teks**, **Voice Note** (Speech-to-Text), maupun **Foto Nota/Struk** (Vision OCR).
* **Klasifikasi Otomatis (Bisnis vs. Pribadi):** AI (Google Gemini) mengurai isi pesan dan memisahkan transaksi bisnis dari pengeluaran pribadi secara akurat.
* **Ringkasan Laporan Instan:** Cek kondisi keuangan harian/mingguan cukup dengan mengetik *command* di WA (misal: `/laporan`, `/omset`).

### 📊 3. Web Dashboard (PWA Frontend)
* **Visual Analytics:** Grafik tren omset, rasio laba-rugi, dan analisis pengeluaran.
* **Manajemen Katalog (CRUD):** Kelola produk, harga, dan kategori menu WA.
* **Ekspor Laporan:** Fitur unduh rekap transaksi ke dalam format **Excel (.xlsx)** dan **PDF**.

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
| :--- | :--- |
| **Backend Framework** | Python 3.11+ (FastAPI + Async Background Tasks) |
| **AI Engine** | Google Gemini API (Multimodal: Audio STT & Vision OCR) |
| **WhatsApp Interface** | Meta WhatsApp Cloud API |
| **Payment Gateway** | Midtrans Core API (Mode Sandbox QRIS) |
| **Database & Storage** | PostgreSQL (Supabase) & Supabase Object Storage |
| **Reverse Proxy & Security** | Cloudflare (SSL/WAF) + Nginx + Docker |

---

## 🏗️ Arsitektur Sistem

```text
[ Pembeli (WA) ] ───> [ Meta WA Cloud API ] ───┐
                                              ├───> [ Cloudflare / Nginx ] ───> [ FastAPI Backend ]
[ Penjual (WA) ] ───> [ Meta WA Cloud API ] ───┘                                     │
                                                                                     ├───> [ Gemini AI API ]
[ Penjual (Web) ] ──> [ Web Dashboard PWA ] ─────────────────────────────────────────┼───> [ Supabase PostgreSQL ]
                                                                                     └───> [ Midtrans Payment ]
