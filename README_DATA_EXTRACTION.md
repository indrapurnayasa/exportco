# Data Extraction Solution untuk Chatbot ExportMate

## Masalah yang Diatasi

Sebelumnya, chatbot mengalami error karena tidak bisa mengekstrak data yang diperlukan dari query user:

```
"answer": "Mohon lengkapi data berikut: nama_produk, berat_bersih (kg), dan negara_tujuan."
```

## Solusi yang Diimplementasikan

### 1. Fungsi Ekstraksi Data dengan AI

Kami menambahkan fungsi `extract_data_from_query()` yang menggunakan AI untuk mengekstrak informasi penting dari query user:

```python
def extract_data_from_query(query: str) -> dict:
    """
    Extract product name, weight, and destination country from user query using AI
    """
```

### 2. Prompt Ekstraksi yang Optimal

Menggunakan prompt yang Anda berikan untuk mengekstrak data dengan akurat:

```
Kamu adalah ExportMate, asisten AI ekspor yang membantu menghitung estimasi bea keluar (pajak ekspor) berdasarkan regulasi yang berlaku.

Tugasmu adalah mengekstrak informasi penting dari kalimat pengguna dalam bentuk teks bebas.

Ekstrak dan kembalikan tiga informasi berikut secara eksplisit:
- nama_produk: nama komoditas atau barang yang akan diekspor (contoh: Crude Palm Oil, Karet, Kopi)
- berat_bersih_kg: berat bersih produk dalam satuan kilogram (kg)
- negara_tujuan: negara tujuan ekspor (contoh: India, Tiongkok, Bangladesh)

Jika ada informasi yang tidak disebutkan secara eksplisit oleh pengguna, isi dengan null.

Tampilkan hasil ekstraksi dalam format JSON sebagai berikut:

{
"nama_produk": "...",
"berat_bersih_kg": ...,
"negara_tujuan": "..."
}
```

### 3. Fallback Manual Extraction

Jika AI parsing gagal, sistem menggunakan regex patterns untuk ekstraksi manual:

```python
def extract_data_manually(text: str) -> dict:
    # Cari berat dalam kg
    weight_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram)'
    
    # Cari negara tujuan
    countries = ["Indonesia", "India", "Tiongkok", "China", ...]
    
    # Cari nama produk
    commodities = ["CPO", "Crude Palm Oil", "Karet", "Kopi", ...]
```

### 4. Response yang Lebih Informatif

Sekarang chatbot memberikan response yang lebih detail:

- **Jika data lengkap**: Menghitung bea keluar dan menampilkan hasil
- **Jika data tidak lengkap**: Menunjukkan field mana yang masih kurang
- **Selalu menampilkan**: Data yang berhasil diekstrak untuk transparansi

## Contoh Penggunaan

### Query Lengkap
```
Input: "Saya ingin mengekspor Crude Palm Oil seberat 1000 kg ke India"
Output: {
  "answer": "Berikut hasil perhitungan bea keluar: {...}",
  "extracted_data": {
    "nama_produk": "Crude Palm Oil",
    "berat_bersih_kg": 1000,
    "negara_tujuan": "India"
  }
}
```

### Query Tidak Lengkap
```
Input: "Saya ingin mengekspor Karet ke Tiongkok"
Output: {
  "answer": "Mohon lengkapi data berikut: berat_bersih (kg).",
  "extracted_data": {
    "nama_produk": "Karet",
    "berat_bersih_kg": null,
    "negara_tujuan": "Tiongkok"
  }
}
```

## Fitur Tambahan

### 1. Error Handling yang Robust
- JSON parsing dengan regex fallback
- Exception handling untuk semua operasi AI
- Graceful degradation jika AI service down

### 2. Transparansi Data
- Response selalu menyertakan `extracted_data`
- User bisa melihat apa yang berhasil diekstrak
- Debugging lebih mudah

### 3. Fleksibilitas Input
- Mendukung berbagai format input
- Natural language processing
- Case-insensitive matching

## Testing

Gunakan file `examples/data_extraction_example.py` untuk menguji berbagai skenario:

```bash
python examples/data_extraction_example.py
```

## Keuntungan Solusi Ini

1. **Otomatis**: Tidak perlu user mengisi form terpisah
2. **Natural**: User bisa bertanya dalam bahasa natural
3. **Robust**: Multiple fallback mechanisms
4. **Transparan**: User tahu apa yang diekstrak
5. **Scalable**: Mudah ditambah pattern baru

## Cara Kerja

1. User mengirim query ke `/api/v1/prompt-library/chatbot/`
2. Sistem mendeteksi intent (bea keluar/pajak)
3. AI mengekstrak data dari query menggunakan prompt
4. Jika data lengkap, hitung bea keluar
5. Jika tidak lengkap, minta data yang kurang
6. Return response dengan data yang diekstrak

Solusi ini mengatasi masalah error sebelumnya dan memberikan user experience yang lebih baik dengan ekstraksi data otomatis dari query natural language. 