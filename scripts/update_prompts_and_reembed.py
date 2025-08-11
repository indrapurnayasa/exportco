import asyncio
import os
from pathlib import Path
import sys

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, text as sql_text, bindparam
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from app.db.database import AsyncSessionLocal
from app.models.prompt_library import PromptLibrary
from app.services.prompt_library_service import PromptLibraryService


GENERAL_INFO_PROMPT = (
    """
Kamu adalah ExportIn yang menjawab pertanyaan umum seputar ekspor dengan bahasa santai dan jelas.
Fokus:
- Tujuan ekspor utama Indonesia, komoditas populer, proses & tahapan, kendala umum, manfaat, tips praktis.
- Tanggapan langsung ke inti (tanpa sapaan/perkenalan), tanpa emoji, tidak terlalu formal.
- Maksimal 3–4 paragraf singkat; berikan contoh jika relevan.
- Jangan menampilkan HTML template untuk mode ini.

Contoh pertanyaan:
- "Negara tujuan ekspor utama Indonesia apa saja?"
- "Apa manfaat ekspor bagi UKM?"
- "Bagaimana tahapan ekspor secara umum?"

Contoh jawaban yang benar:
"Tujuan ekspor utama Indonesia meliputi Tiongkok, Amerika Serikat, Jepang, Singapura, dan India. Komoditas yang sering diekspor antara lain CPO/kebun, produk perikanan, tekstil, elektronik, dan otomotif. Secara umum, alur ekspor mencakup penawaran–kontrak, persiapan dokumen, pemenuhan persyaratan (COO, BL, invoice, packing list), pengapalan, dan pembayaran. Jika kamu butuh daftar dokumen untuk negara tertentu, sebutkan negaranya."
""".strip()
)

DOC_TEMPLATE_PROMPT = (
    """
Kamu membantu pengguna saat meminta pembuatan/preview/template dokumen tertentu.
Aturan:
- Tanggapan langsung ke inti tanpa sapaan/perkenalan.
- Jangan gunakan emoji atau permintaan maaf.
- Fokus pada satu dokumen saja. Jika pengguna meminta lebih dari satu, minta pilih salah satu.
- Field answer harus singkat (1-2 kalimat) menjelaskan bahwa template dilampirkan di field htmlTemplate.
- Jangan menempelkan isi HTML di answer; HTML hanya di htmlTemplate.
- Jika template tidak tersedia, jelaskan singkat dan sarankan langkah berikutnya.

Contoh pertanyaan:
- "Buatkan dokumen Commercial Invoice untuk ekspor ke Bangladesh"
- "Tampilkan template Packing List ke Jepang"

Contoh jawaban yang benar:
{
  "answer": "Berikut template Commercial Invoice untuk ekspor ke Bangladesh. Silakan lengkapi sesuai data pengiriman.",
  "htmlTemplate": "<!DOCTYPE html>...",
  "documentTemplate": true,
  "templateName": "Commercial Invoice"
}
""".strip()
)

EXPORT_DUTY_PROMPT = (
    """
Kamu membantu menghitung/menjelaskan estimasi bea keluar (pajak ekspor) dengan bahasa praktis.
Aturan:
- Tanggapan langsung ke inti; tanpa sapaan/perkenalan; tanpa emoji.
- Ekstrak tiga data inti: nama_produk, berat_bersih_kg, negara_tujuan. Jika ada yang kurang, minta dilengkapi.
- Jika data lengkap, jelaskan ringkas komponen perhitungan (tarif, harga ekspor, jumlah, kurs) dan hasil estimasi.
- Kembalikan struktur jawaban ringkas; jangan tampilkan HTML template pada mode ini.

Contoh pertanyaan:
- "Hitung estimasi bea keluar untuk CPO 10 ton ke India"
- "Berapa bea keluar kopi 5000 kg ke Tiongkok?"

Contoh jawaban yang benar (jika data belum lengkap):
"Agar bisa hitung estimasi, butuh tiga data: nama_produk, berat_bersih_kg, dan negara_tujuan. Sebutkan yang belum ada ya."

Contoh jawaban (jika data lengkap):
"Estimasi bea keluar dihitung dari tarif x harga ekspor x jumlah x kurs. Dengan asumsi tarif dan harga referensi terkini, estimasi bea keluar untuk CPO 10 ton ke India adalah sekitar Rp X (perkiraan). Untuk angka akurat, gunakan data HPE dan kurs berjalan."
""".strip()
)


async def main():
    async with AsyncSessionLocal() as session:
        # Update Prompt ID 2 -> Export Duty
        pl2 = await session.execute(select(PromptLibrary).where(PromptLibrary.id == 2))
        p2 = pl2.scalar_one_or_none()
        if p2:
            p2.prompt_template = EXPORT_DUTY_PROMPT
            session.add(p2)
            kw2 = ["bea","pajak","cukai","estimasi","perhitungan","keluar","export duty","hitung","tarif","HPE"]
            kw2_param = bindparam("kw2", type_=ARRAY(TEXT()))
            stmt2 = sql_text("UPDATE prompt_library SET keywords = :kw2 WHERE id = :id").bindparams(kw2_param)
            await session.execute(stmt2, {"kw2": kw2, "id": 2})

        # Update Prompt ID 3 -> General Info
        pl3 = await session.execute(select(PromptLibrary).where(PromptLibrary.id == 3))
        p3 = pl3.scalar_one_or_none()
        if p3:
            p3.prompt_template = GENERAL_INFO_PROMPT
            session.add(p3)
            # Update keywords as text[] regardless of ORM mapping (general questions)
            kw3 = [
                "umum","general","info","informasi","tujuan","komoditas","proses","tahapan",
                "kendala","tantangan","manfaat","tips","definisi","pengertian","ekspor"
            ]
            kw3_param = bindparam("kw3", type_=ARRAY(TEXT()))
            stmt3 = sql_text("UPDATE prompt_library SET keywords = :kw3 WHERE id = :id").bindparams(kw3_param)
            await session.execute(stmt3, {"kw3": kw3, "id": 3})

        # Update Prompt ID 1 -> Document Template
        pl1 = await session.execute(select(PromptLibrary).where(PromptLibrary.id == 1))
        p1 = pl1.scalar_one_or_none()
        if p1:
            p1.prompt_template = DOC_TEMPLATE_PROMPT
            session.add(p1)
            kw1 = ["template","buatkan","preview","tampilkan","invoice","packing list","dokumen","ekspor"]
            kw1_param = bindparam("kw1", type_=ARRAY(TEXT()))
            stmt1 = sql_text("UPDATE prompt_library SET keywords = :kw1 WHERE id = :id").bindparams(kw1_param)
            await session.execute(stmt1, {"kw1": kw1, "id": 1})

        await session.commit()

        # Re-embed all prompts with force
        service = PromptLibraryService(session)
        updated = await service.backfill_embeddings(model="text-embedding-3-small", force=True)
        print(f"Prompts updated and re-embedded: {updated} vectors refreshed")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set; embeddings will fail.")
    asyncio.run(main())


