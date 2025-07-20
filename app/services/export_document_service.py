from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Dict, Any, Optional
from app.models.export_document_country import ExportDocumentCountry
from app.models.export_document import ExportDocument
import re
from datetime import datetime

class ExportDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_documents_by_country(self, country_name: str) -> List[Dict[str, Any]]:
        """
        Get all required documents for a specific country
        """
        try:
            # Search for documents by country name (case insensitive)
            query = select(ExportDocumentCountry).where(
                or_(
                    func.lower(ExportDocumentCountry.country_name).contains(country_name.lower()),
                    func.lower(ExportDocumentCountry.country_name) == country_name.lower()
                )
            )
            
            result = await self.db.execute(query)
            documents = result.scalars().all()
            
            if not documents:
                return []
            
            # Get template information for documents that have id_doc
            documents_with_templates = []
            
            for doc in documents:
                doc_info = {
                    "id": doc.id,
                    "country_name": doc.country_name,
                    "document_name": doc.document_name,
                    "source": doc.source,
                    "country_code": doc.country_code,
                    "has_template": False,
                    "template": None
                }
                
                # If document has id_doc, get the template
                if doc.id_doc:
                    template = await self.get_document_template(doc.id_doc)
                    if template:
                        doc_info["has_template"] = True
                        doc_info["template"] = template
                
                documents_with_templates.append(doc_info)
            
            return documents_with_templates
            
        except Exception as e:
            print(f"Error getting documents by country: {e}")
            return []

    async def get_document_template(self, id_doc: str) -> Optional[Dict[str, Any]]:
        """
        Get document template by id_doc
        """
        try:
            query = select(ExportDocument).where(ExportDocument.id_doc == id_doc)
            result = await self.db.execute(query)
            template = result.scalar_one_or_none()
            
            if template:
                # Clean the template HTML more carefully
                cleaned_template = template.template_dokumen
                # Remove carriage returns
                cleaned_template = cleaned_template.replace('\r', '')
                # Replace multiple newlines with single newlines
                cleaned_template = re.sub(r'\n+', '\n', cleaned_template)
                # Remove leading/trailing whitespace
                cleaned_template = cleaned_template.strip()
                
                return {
                    "id_doc": template.id_doc,
                    "nama_dokumen": template.nama_dokumen,
                    "template_dokumen": cleaned_template
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting document template: {e}")
            return None

    def render_template(self, template_html: str, data: Dict[str, Any]) -> str:
        """
        Render HTML template with provided data
        """
        try:
            rendered_template = template_html
            
            # Replace placeholders with actual data
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_template = rendered_template.replace(placeholder, str(value))
            
            # Add default values for common fields if not provided
            if "{{tanggal}}" not in rendered_template:
                rendered_template = rendered_template.replace("{{tanggal}}", datetime.now().strftime("%d/%m/%Y"))
            
            if "{{negara_asal}}" not in rendered_template:
                rendered_template = rendered_template.replace("{{negara_asal}}", "Indonesia")
            
            return rendered_template
            
        except Exception as e:
            print(f"Error rendering template: {e}")
            return template_html

    def extract_country_from_query(self, query: str) -> Optional[str]:
        """
        Extract country name from user query
        """
        # Common country names and their variations
        country_mappings = {
            "india": "India",
            "indian": "India",
            "china": "China",
            "chinese": "China",
            "tiongkok": "China",
            "bangladesh": "Bangladesh",
            "malaysia": "Malaysia",
            "singapore": "Singapore",
            "singapura": "Singapore",
            "thailand": "Thailand",
            "vietnam": "Vietnam",
            "japan": "Japan",
            "jepang": "Japan",
            "korea": "Korea",
            "korea selatan": "Korea",
            "australia": "Australia",
            "amerika": "USA",
            "usa": "USA",
            "united states": "USA",
            "eropa": "Europe",
            "europe": "Europe"
        }
        
        query_lower = query.lower()
        
        # Check for exact matches first
        for country_key, country_name in country_mappings.items():
            if country_key in query_lower:
                return country_name
        
        # Check for partial matches
        for country_key, country_name in country_mappings.items():
            if country_key.split()[0] in query_lower:
                return country_name
        
        return None

    def extract_requested_document_name(self, query: str) -> Optional[str]:
        """
        Extract the specific document name requested by user
        """
        query_lower = query.lower()
        
        # Common document names and their variations
        document_mappings = {
            "commercial invoice": "Commercial Invoice",
            "invoice": "Commercial Invoice",
            "packing list": "Packing List",
            "packing": "Packing List",
            "shipping instruction": "Shipping Instruction",
            "shipping": "Shipping Instruction",
            "proforma invoice": "Proforma Invoice",
            "proforma": "Proforma Invoice",
            "delivery order": "Delivery Order",
            "delivery": "Delivery Order",
            "letter of credit": "Letter of Credit",
            "lc": "Letter of Credit",
            "credit": "Letter of Credit"
        }
        
        # Check for exact matches first
        for doc_key, doc_name in document_mappings.items():
            if doc_key in query_lower:
                return doc_name
        
        return None

    async def get_export_documents_response(self, query: str, show_template: bool = False) -> dict:
        """
        Main function to get export documents response based on user query, following ExportMate prompt strictly.
        :param query: User query
        :param show_template: If True, will return template HTML for requested document(s)
        :return: Dict with formatted answer and details
        """
        country = self.extract_country_from_query(query)
        if not country:
            return {
                "success": False,
                "message": (
                    "Maaf, dokumen ekspor untuk negara tersebut belum tersedia di database. "
                    "Silakan hubungi instansi resmi seperti Kemendag atau atase perdagangan negara tujuan."
                ),
                "documents": [],
                "country": None
            }

        documents = await self.get_documents_by_country(country)
        if not documents:
            return {
                "success": False,
                "message": (
                    f"Maaf, dokumen ekspor untuk negara {country} belum tersedia di database. "
                    "Silakan hubungi instansi resmi seperti Kemendag atau atase perdagangan negara tujuan."
                ),
                "documents": [],
                "country": country
            }

        # Group documents
        docs_auto = []  # with template
        docs_manual = []  # without template
        for doc in documents:
            if doc["has_template"]:
                docs_auto.append(doc)
            else:
                docs_manual.append(doc)

        # If show_template=True, filter documents based on requested document name
        if show_template:
            requested_doc_name = self.extract_requested_document_name(query)
            if requested_doc_name:
                # Filter docs_auto to only include the requested document
                filtered_docs_auto = [
                    doc for doc in docs_auto 
                    if doc["document_name"].strip().lower() == requested_doc_name.strip().lower()
                ]
                docs_auto = filtered_docs_auto

        # Detect if the query is only asking for the list of required documents (not template/preview)
        query_lower = query.lower()
        is_just_asking_documents = (
            any(keyword in query_lower for keyword in ["dokumen", "document", "surat", "form", "template", "persyaratan"]) and
            not any(keyword in query_lower for keyword in ["buat", "buatkan", "generate", "tampilkan", "show", "lihat", "preview"])
        )

        if is_just_asking_documents:
            # Only mention the country, do not use placeholders or template lookup
            response_lines = [
                f"Berikut adalah daftar dokumen yang umumnya diperlukan untuk ekspor ke {country}:",
                "",
                "Dokumen yang bisa dibantu sistem (otomatis):"
            ]
            if docs_auto:
                for doc in docs_auto:
                    response_lines.append(f"- {doc['document_name']}")
            else:
                response_lines.append("(Belum ada dokumen otomatis untuk negara ini)")
            response_lines.append("")
            response_lines.append("Dokumen yang perlu disiapkan manual:")
            if docs_manual:
                for doc in docs_manual:
                    if doc["source"]:
                        response_lines.append(f"- {doc['document_name']} (sumber: {doc['source']})")
                    else:
                        response_lines.append(f"- {doc['document_name']}")
            else:
                response_lines.append("(Tidak ada dokumen manual untuk negara ini)")
            response_lines.append("")
            response_lines.append("Catatan: Untuk dokumen otomatis, Anda dapat meminta bantuan sistem untuk membuatkan template.")
            return {
                "success": True,
                "country": country,
                "message": "\n".join(response_lines),
                "documents_with_templates": docs_auto,
                "documents_without_templates": docs_manual,
                "total_documents": len(documents)
            }

        # Format output as per new prompt (for template/preview intent)
        response_lines = [
            f"PERSIAPAN DOKUMEN EKSPOR KE {country.upper()}\n",
            f"Terima kasih. Berikut adalah daftar lengkap dokumen yang perlu Anda siapkan untuk melakukan ekspor dari Indonesia ke {country}:",
            "\n==="
        ]

        # Section: Dokumen otomatis
        response_lines.append("\nDOKUMEN YANG BISA KAMI BANTU BUATKAN SECARA OTOMATIS\n")
        if docs_auto:
            response_lines.append("Dokumen-dokumen di bawah ini tersedia dalam sistem kami dan dapat kami bantu buatkan jika Anda membutuhkannya:")
            for doc in docs_auto:
                response_lines.append(f"- {doc['document_name']}")
            response_lines.append("")
            response_lines.append(f"Jika Anda ingin memproses salah satu dokumen di atas, cukup beri perintah seperti:")
            response_lines.append(f'"Tolong buatkan invoice untuk pengiriman ke {country}."')
            response_lines.append(f'"Tampilkan template packing list."')
        else:
            response_lines.append("(Belum ada dokumen yang dapat dibuat otomatis untuk negara ini)")
        response_lines.append("\n===\n")

        # Section: Dokumen manual
        response_lines.append("DOKUMEN YANG PERLU ANDA SIAPKAN SECARA MANUAL\n")
        if docs_manual:
            response_lines.append("Dokumen berikut belum tersedia dalam sistem dan umumnya disiapkan oleh pihak terkait atau instansi resmi. Mohon pastikan Anda telah mengurus dokumen-dokumen berikut:")
            for doc in docs_manual:
                if doc["source"]:
                    response_lines.append(f"- {doc['document_name']} (sumber: {doc['source']})")
                else:
                    response_lines.append(f"- {doc['document_name']}")
        else:
            response_lines.append("(Tidak ada dokumen manual untuk negara ini)")
        response_lines.append("\n===\n")

        # Section: Catatan
        response_lines.append("CATATAN\n")
        response_lines.append("- Dokumen yang tersedia di sistem dapat kami bantu buatkan dalam bentuk template yang bisa Anda lengkapi dan konversi ke file PDF.")
        response_lines.append("- Silakan sampaikan jika Anda ingin melihat pratinjau salah satu dokumen, atau meminta bantuan pembuatan dokumen tersebut.")
        response_lines.append("- ExportMate siap mendampingi proses ekspor Anda agar berjalan lebih mudah dan sesuai ketentuan.\n")

        # Only show template if explicitly requested
        template_previews = []
        if show_template and docs_auto:
            template_previews.append("\n===\nTEMPLATE DOKUMEN:\n")
            for doc in docs_auto:
                if doc["template"] and doc["template"].get("template_dokumen"):
                    # The template is already properly formatted, just show it
                    template_html = doc['template']['template_dokumen']
                    template_previews.append(f"\n{doc['document_name']}\n```html\n{template_html[:1000]}...\n```")
            response_lines.extend(template_previews)

        return {
            "success": True,
            "country": country,
            "message": "\n".join(response_lines),
            "documents_with_templates": docs_auto,
            "documents_without_templates": docs_manual,
            "total_documents": len(documents)
        } 

    def detect_intent_and_action(self, query: str) -> str:
        query_lower = query.lower()

        # 1. Intent: Generate/Preview Dokumen (Template)
        template_keywords = [
            "buatkan", "buat", "generate", "tampilkan", "show", "lihat", "preview", "template", "contoh",
            "form", "surat", "invoice", "packing list", "proforma", "delivery order", "letter of credit",
            "shipping instruction", "proforma invoice", "delivery order", "lc", "si"
        ]
        if any(k in query_lower for k in template_keywords):
            return "document_template"

        # 2. Intent: Daftar Dokumen Ekspor ke Negara
        list_keywords = [
            "dokumen apa saja", "daftar dokumen", "persyaratan ekspor", "syarat ekspor", "dokumen ekspor ke",
            "list of export documents", "export requirements", "dokumen ekspor", "dokumen untuk ekspor",
            "dokumen yang dibutuhkan", "dokumen yang diperlukan", "apa saja dokumen", "apa saja syarat",
            "persyaratan dokumen", "requirement", "requirements"
        ]
        if any(k in query_lower for k in list_keywords):
            return "document_list"

        # Default: fallback
        return "default"