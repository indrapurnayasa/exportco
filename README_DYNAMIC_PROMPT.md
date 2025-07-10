# Sistem Prompt Dinamis dengan Similarity Search

## Overview

Sistem ini mengimplementasikan pemilihan prompt dinamis berdasarkan similarity search dengan threshold 70%. Query user akan dikonversi menjadi vector embedding, kemudian dicari prompt yang paling relevan dari database `prompt_library`.

## Mekanisme Kerja

### 1. **Vector Embedding Query User**
```python
# Create embedding for user query
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.embeddings.create(
    input=query,
    model="text-embedding-ada-002"
)
query_embedding = response.data[0].embedding
```

### 2. **Similarity Search**
```python
# Search for most similar prompt with 70% threshold
service = PromptLibraryService(db)
result = await service.get_most_similar_prompt(query_embedding, threshold=0.7)
```

### 3. **Prompt Selection**
- Jika similarity > 70%: Gunakan prompt dari database
- Jika similarity ≤ 70%: Gunakan default prompt

## Prompt Template Baru

Prompt yang digunakan untuk ekstraksi data:

```
Kamu adalah ExportMate, asisten AI ekspor yang membantu menghitung estimasi bea keluar (pajak ekspor) berdasarkan regulasi yang berlaku di Indonesia.

Tugasmu adalah:
1. Mengekstrak informasi penting dari pernyataan pengguna dalam bentuk teks bebas.
2. Menjelaskan perhitungan estimasi bea keluar berdasarkan rumus yang berlaku, jika semua informasi telah tersedia.

Pertama, ekstrak dan tampilkan 3 informasi berikut secara eksplisit dalam format JSON:
- nama_produk: nama komoditas atau barang yang akan diekspor (contoh: Crude Palm Oil, Karet, Kopi)
- berat_bersih_kg: berat bersih produk dalam satuan kilogram (kg)
- negara_tujuan: negara tujuan ekspor (contoh: India, Tiongkok, Bangladesh)

Jika salah satu dari informasi tersebut tidak disebutkan secara eksplisit oleh pengguna, isi nilainya dengan null.

Gunakan format JSON berikut:
{
"nama_produk": "...",
"berat_bersih_kg": ...,
"negara_tujuan": "..."
}

Setelah ekstraksi, jika seluruh informasi tersedia dan relevan, kamu dapat menjelaskan bahwa estimasi bea keluar dihitung berdasarkan rumus berikut:

Bea Keluar = Tarif Bea Keluar × Harga Ekspor × Jumlah Satuan Barang × Nilai Tukar Mata Uang

Penjelasan komponen:
- **Tarif Bea Keluar**: persentase tertentu yang dikenakan pada harga ekspor, atau tarif spesifik per satuan barang.
- **Harga Ekspor**: harga barang yang diekspor, bisa merujuk pada Harga Patokan Ekspor (HPE) yang ditetapkan pemerintah.
- **Jumlah Satuan Barang**: total kuantitas barang, misalnya dalam kg atau ton.
- **Nilai Tukar Mata Uang**: kurs tengah yang ditetapkan oleh Menteri Keuangan saat ekspor dilakukan.

Contoh perhitungan:
Jika perusahaan mengekspor 10 ton biji kakao dengan harga ekspor USD 2.000 per ton, tarif bea keluar 5%, dan nilai tukar Rp10.000 per USD, maka:
- Total harga ekspor: 10 × 2.000 = USD 20.000
- Dalam Rupiah: 20.000 × 10.000 = Rp200.000.000
- Bea Keluar: 5% × Rp200.000.000 = Rp10.000.000
```

## Implementasi dalam Kode

### 1. **Fungsi Dynamic Prompt Selection**
```python
async def get_dynamic_prompt_from_db(query: str, db: AsyncSession) -> tuple[str, float]:
    """
    Get the most relevant prompt from prompt_library using similarity search
    Returns (prompt_template, similarity_score)
    """
```

### 2. **Fungsi Ekstraksi Data dengan Dynamic Prompt**
```python
async def extract_data_from_query(query: str, db: AsyncSession) -> dict:
    """
    Extract product name, weight, and destination country from user query using AI
    with dynamic prompt selection based on similarity search
    """
```

### 3. **Response dengan Prompt Similarity**
```python
return {
    "answer": response_text,
    "similarity": similarity,
    "prompt_id": prompt.id,
    "extracted_data": extracted_data,
    "calculation_details": hasil,
    "prompt_similarity": extracted_data.get("prompt_similarity", 0.0)
}
```

## Setup Database

### 1. **Menambahkan Prompt Dinamis**
```bash
python examples/add_dynamic_prompt.py
```

Script ini akan:
- Menambahkan prompt dinamis ke tabel `prompt_library`
- Membuat embedding untuk prompt tersebut
- Testing similarity search functionality
- Menampilkan daftar semua prompt

### 2. **Struktur Prompt di Database**
Prompt dinamis akan disimpan dengan:
- **Keywords**: `["ExportMate", "bea keluar", "pajak ekspor", "ekstrak", "data", "nama_produk", "berat_bersih", "negara_tujuan", "export", "regulasi", "Indonesia"]`
- **Template**: Prompt lengkap untuk ekstraksi data
- **Active**: `True`
- **Embedding**: Vector embedding dari prompt

## Testing Similarity Search

### 1. **Test Queries**
```python
test_queries = [
    "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
    "Berapa pajak ekspor Karet 5000 kg ke Tiongkok?",
    "Ekspor Kopi 2000 kg ke Jepang, berapa bea keluar?",
    "Saya ingin mengekspor teh 300 kg ke Bangladesh",
    "Hitung estimasi bea keluar untuk ekspor beras 10000 kg ke Malaysia"
]
```

### 2. **Expected Results**
- Query yang relevan dengan bea keluar/ekspor akan menemukan prompt dengan similarity > 70%
- Query yang tidak relevan akan menggunakan default prompt

## Keunggulan Sistem

### 1. **Fleksibilitas**
- Prompt bisa diupdate tanpa deploy ulang
- Multiple prompt versions bisa disimpan
- Threshold similarity bisa disesuaikan

### 2. **Akurasi**
- Similarity search memastikan prompt yang paling relevan
- Fallback ke default prompt jika tidak ada yang cocok
- Embedding mempertahankan konteks semantik

### 3. **Transparansi**
- Response menyertakan similarity score
- User bisa melihat prompt yang digunakan
- Debugging lebih mudah

### 4. **Scalability**
- Mudah menambah prompt baru
- Support untuk berbagai jenis query
- Performance yang baik dengan vector search

## Flow Diagram

```
User Query
    ↓
Create Embedding
    ↓
Similarity Search (threshold 70%)
    ↓
Found Prompt? → Yes → Use Dynamic Prompt
    ↓ No
Use Default Prompt
    ↓
Extract Data
    ↓
Calculate Export Duty
    ↓
Return Response with Similarity Score
```

## Troubleshooting

### Jika similarity selalu rendah:
1. Cek apakah embedding prompt sudah dibuat dengan benar
2. Pastikan query user relevan dengan domain ekspor
3. Sesuaikan threshold similarity jika diperlukan

### Jika prompt tidak ditemukan:
1. Jalankan `python examples/add_dynamic_prompt.py`
2. Cek apakah prompt sudah ditambahkan ke database
3. Verifikasi embedding sudah dibuat

### Jika ekstraksi data gagal:
1. Cek format JSON yang dihasilkan
2. Pastikan prompt template sesuai dengan format yang diharapkan
3. Gunakan fallback manual extraction

## Monitoring

### 1. **Log Output**
```
[DYNAMIC PROMPT] Found prompt ID: 1 with similarity: 0.85
[DYNAMIC PROMPT] No prompt found with similarity > 70%
```

### 2. **Response Metrics**
- `prompt_similarity`: Score similarity prompt yang digunakan
- `similarity`: Score similarity untuk chatbot response
- `prompt_id`: ID prompt yang digunakan

Sistem ini memberikan fleksibilitas maksimal dalam pemilihan prompt berdasarkan relevansi query user, dengan fallback yang robust untuk memastikan fungsionalitas tetap berjalan. 