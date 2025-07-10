# Perhitungan Bea Keluar Ekspor - Implementasi Baru

## Rumus Perhitungan

Berdasarkan regulasi yang berlaku, rumus perhitungan bea keluar ekspor adalah:

```
Bea Keluar = Tarif Bea Keluar × Harga Ekspor × Jumlah Satuan Barang × Nilai Tukar Mata Uang
```

## Komponen Perhitungan

### 1. **Tarif Bea Keluar**
Persentase tertentu yang dikenakan pada harga ekspor, bervariasi berdasarkan komoditas:

| Komoditas | Tarif Bea Keluar |
|-----------|------------------|
| CPO/Crude Palm Oil | 3% |
| Karet | 5% |
| Kopi | 7% |
| Kakao | 5% |
| Cokelat | 8% |
| Teh | 6% |
| Beras | 4% |
| Jagung | 4% |
| Kedelai | 5% |
| Gula | 6% |
| Tembakau | 10% |
| Kayu | 8% |
| Batu Bara | 3% |
| Minyak | 5% |
| Gas | 4% |
| Default | 5% |

### 2. **Harga Ekspor**
Harga barang yang diekspor per satuan (ton), diambil dari tabel `komoditi` sebagai Harga Patokan Ekspor (HPE).

### 3. **Jumlah Satuan Barang**
Jumlah barang yang diekspor dalam satuan ton (konversi dari kg).

### 4. **Nilai Tukar Mata Uang**
Kurs USD/IDR yang berlaku, diambil dari tabel `currency_rates`.

## Contoh Perhitungan

### Skenario: Ekspor 10 ton biji kakao
- **Harga ekspor per ton**: USD 2.000
- **Jumlah ton**: 10
- **Kurs USD/IDR**: Rp 10.000
- **Tarif bea keluar**: 5%

### Perhitungan:
1. **Total harga ekspor USD**: 10 ton × USD 2.000/ton = USD 20.000
2. **Total harga ekspor IDR**: USD 20.000 × Rp 10.000/USD = Rp 200.000.000
3. **Bea Keluar**: 5% × Rp 200.000.000 = Rp 10.000.000

## Implementasi dalam Kode

### 1. **Fungsi Perhitungan Utama**

```python
async def calculate_export_duty(self, nama_produk: str, berat_bersih: float, negara_tujuan: str) -> Dict[str, Any]:
    """
    Menghitung bea keluar ekspor berdasarkan rumus:
    Bea Keluar = Tarif Bea Keluar x Harga Ekspor x Jumlah Satuan Barang x Nilai Tukar Mata Uang
    """
```

### 2. **Fungsi Tarif Bea Keluar**

```python
def _get_tarif_bea_keluar(self, nama_produk: str, negara_tujuan: str) -> float:
    """
    Mendapatkan tarif bea keluar berdasarkan komoditas dan negara tujuan
    """
```

### 3. **Response Format Baru**

Chatbot sekarang memberikan response yang lebih informatif:

```
📊 **HASIL PERHITUNGAN BEA KELUAR EKSPOR**

**Detail Ekspor:**
• Nama Produk: CPO
• Berat: 1000 kg (1.000 ton)
• Negara Tujuan: India

**Perhitungan Harga:**
• Harga Ekspor: USD 1,200.00/ton
• Total Harga Ekspor: USD 1,200.00
• Kurs USD/IDR: Rp 15,500.00
• Total Harga dalam Rupiah: Rp 18,600,000.00

**Perhitungan Bea Keluar:**
• Tarif Bea Keluar: 3.0%
• **BEA KELUAR: Rp 558,000.00**

**Rumus:** Bea Keluar = Tarif × Harga Ekspor × Jumlah Barang × Nilai Tukar
```

## Testing

### 1. **Test Perhitungan Bea Keluar**
```bash
python examples/export_duty_calculation_test.py
```

### 2. **Test Cases yang Dicakup**
- CPO 1 ton ke India
- Karet 5 ton ke Tiongkok
- Kopi 2 ton ke Jepang
- Beras 10 ton ke Bangladesh

### 3. **Verifikasi Rumus**
Script testing juga memverifikasi bahwa perhitungan sesuai dengan rumus yang diberikan.

## Keunggulan Implementasi Baru

### 1. **Akurasi Perhitungan**
- Menggunakan rumus resmi yang berlaku
- Tarif yang berbeda untuk setiap komoditas
- Konversi satuan yang tepat (kg → ton)

### 2. **Transparansi**
- Menampilkan semua komponen perhitungan
- User bisa melihat detail setiap langkah
- Verifikasi rumus yang jelas

### 3. **Fleksibilitas**
- Mudah menambah komoditas baru
- Tarif bisa diupdate tanpa deploy ulang
- Support untuk berbagai negara tujuan

### 4. **Error Handling**
- Validasi data input
- Fallback untuk data yang tidak ditemukan
- Pesan error yang informatif

## Integrasi dengan Chatbot

### 1. **Ekstraksi Data**
- AI mengekstrak `nama_produk`, `berat_bersih_kg`, `negara_tujuan`
- Validasi kelengkapan data
- Fallback manual jika AI gagal

### 2. **Perhitungan Otomatis**
- Mengambil harga dari database `komoditi`
- Mengambil kurs dari database `currency_rates`
- Menghitung bea keluar secara otomatis

### 3. **Response Format**
- Format yang mudah dibaca
- Detail perhitungan lengkap
- Rumus yang digunakan

## Database Requirements

### 1. **Tabel `komoditi`**
- `nama_komoditi`: Nama komoditas
- `harga_komoditi`: Harga per satuan (USD)
- `satuan_komoditi`: Satuan (ton, kg, dll)

### 2. **Tabel `currency_rates`**
- `base_currency`: USD
- `target_currency`: IDR
- `rate`: Kurs yang berlaku

### 3. **Tabel `export_duty_chunks`**
- `content`: Regulasi bea keluar
- `created_at`: Timestamp

## Troubleshooting

### Jika harga komoditas tidak ditemukan:
1. Pastikan data komoditas sudah ada di database
2. Cek apakah nama produk cocok dengan data di database
3. Gunakan nama produk yang lebih spesifik

### Jika kurs tidak ditemukan:
1. Pastikan data kurs USD/IDR sudah ada di database
2. Cek tanggal kurs yang digunakan
3. Update data kurs jika diperlukan

### Jika tarif tidak sesuai:
1. Update fungsi `_get_tarif_bea_keluar()`
2. Tambahkan komoditas baru ke dictionary tarif
3. Sesuaikan dengan regulasi terbaru

Implementasi ini memberikan perhitungan bea keluar yang akurat dan transparan sesuai dengan regulasi yang berlaku. 