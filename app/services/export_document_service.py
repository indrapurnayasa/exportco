from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Dict, Any, Optional
from app.models.export_document_country import ExportDocumentCountry
from app.models.export_document import ExportDocument
import re
import math
from datetime import datetime

class ExportDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_countries(self) -> List[str]:
        """
        Get list of available countries in the database
        """
        try:
            query = select(ExportDocumentCountry.country_name).distinct()
            result = await self.db.execute(query)
            countries = result.scalars().all()
            return [country for country in countries if country]
        except Exception as e:
            print(f"Error getting available countries: {e}")
            return []

    async def get_country_document_summary(self) -> Dict[str, int]:
        """
        Get summary of available documents per country
        """
        try:
            query = select(
                ExportDocumentCountry.country_name,
                func.count(ExportDocumentCountry.id).label('doc_count')
            ).group_by(ExportDocumentCountry.country_name)
            
            result = await self.db.execute(query)
            summary = {}
            for row in result:
                summary[row.country_name] = row.doc_count
            
            return summary
        except Exception as e:
            print(f"Error getting country document summary: {e}")
            return {}

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
        
        # Check for country names that might be in the database
        # This will be handled by the database query in get_documents_by_country
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
        Main function to get export documents response based on user query, following ExportIn prompt strictly.
        :param query: User query
        :param show_template: If True, will return template HTML for requested document(s)
        :return: Dict with formatted answer and details
        """
        country = self.extract_country_from_query(query)
        
        # Handle general document requests when no specific country is mentioned
        if not country:
            # Check if this is a general document creation request
            query_lower = query.lower()
            
            # Keywords for document creation/request
            creation_keywords = [
                "buat", "buatkan", "generate", "membuat", "ingin buat", "ingin membuat", 
                "mau buat", "mau membuat", "tolong buat", "bisa buat", "bisa buatkan",
                "saya ingin", "saya mau", "saya butuh", "saya perlu", "tolong", "bisa",
                "mohon", "minta", "request", "create", "generate", "make"
            ]
            
            document_keywords = [
                "dokumen", "document", "surat", "form", "template", "invoice", 
                "packing", "shipping", "ekspor", "export", "perdagangan", "trade",
                "commercial", "proforma", "delivery", "letter of credit", "lc"
            ]
            
            # Check for general document requests (creation + document keywords)
            is_general_document_request = (
                any(keyword in query_lower for keyword in creation_keywords) and
                any(keyword in query_lower for keyword in document_keywords)
            )
            
            # Also check for general questions about documents
            general_document_questions = [
                "apa dokumen", "dokumen apa", "dokumen yang", "dokumen untuk",
                "surat apa", "surat yang", "form apa", "template apa",
                "dokumen ekspor", "dokumen perdagangan", "dokumen export",
                "surat ekspor", "surat perdagangan", "surat export"
            ]
            
            is_general_question = any(phrase in query_lower for phrase in general_document_questions)
            
            # Combine both conditions
            is_general_document_request = is_general_document_request or is_general_question
            
            if is_general_document_request:
                # Get available countries and provide a helpful response
                available_countries = await self.get_available_countries()
                country_summary = await self.get_country_document_summary()
                
                if available_countries:
                    # Take first 2 countries as examples
                    example_countries = available_countries[:2]
                    country_list = ", ".join(example_countries)
                    
                    # Determine the type of question and provide appropriate response
                    query_lower = query.lower()
                    
                    # Check if it's a creation request vs general question
                    is_creation_request = any(keyword in query_lower for keyword in [
                        "buat", "buatkan", "generate", "membuat", "ingin buat", "ingin membuat", 
                        "mau buat", "mau membuat", "tolong buat", "bisa buat", "bisa buatkan"
                    ])
                    
                    # Provide flexible data for AI to generate natural response
                    response_data = {
                        "available_countries": available_countries,
                        "total_countries": len(available_countries),
                        "example_countries": example_countries,
                        "country_summary": country_summary,
                        "is_creation_request": is_creation_request,
                        "total_documents": sum(country_summary.values()) if country_summary else 0
                    }
                    
                    # Let AI generate the response naturally
                    response_parts = [
                        f"Sistem mendukung dokumen ekspor untuk {len(available_countries)} negara.",
                        f"Contoh negara: {country_list}.",
                        "Sebutkan negara tujuan untuk melihat dokumen yang diperlukan."
                    ]
                    
                    return {
                        "success": True,
                        "country": None,
                        "message": "\n".join(response_parts),
                        "documents": [],
                        "available_countries": available_countries,
                        "country_summary": country_summary
                    }
                else:
                    return {
                        "success": False,
                        "message": (
                            "Maaf, saat ini belum ada data dokumen ekspor yang tersedia di database. "
                            "Silakan hubungi instansi resmi seperti Kemendag atau atase perdagangan negara tujuan."
                        ),
                        "documents": [],
                        "country": None
                    }
            else:
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
        ask_template_keywords = ["buat", "buatkan", "generate", "tampilkan", "show", "lihat", "preview", "template"]
        is_requesting_template = any(k in query_lower for k in ask_template_keywords)
        is_just_asking_documents = (
            any(keyword in query_lower for keyword in ["dokumen", "document", "surat", "form", "template", "persyaratan"]) and
            not is_requesting_template
        )

        if is_just_asking_documents:
            # Provide simple, flexible response with clear distinction
            response_lines = [
                f"Dokumen ekspor ke {country}:",
                f"Sistem dapat bantu buat: {', '.join([doc['document_name'] for doc in docs_auto]) if docs_auto else 'Tidak ada'}",
                f"Perlu apply ke instansi: {', '.join([doc['document_name'] for doc in docs_manual]) if docs_manual else 'Tidak ada'}"
            ]
            return {
                "success": True,
                "country": country,
                "message": "\n".join(response_lines),
                "documents_with_templates": docs_auto,
                "documents_without_templates": docs_manual,
                "total_documents": len(documents)
            }

        # Provide structured data for AI to generate natural response
        response_data = {
            "country": country,
            "auto_documents": docs_auto,
            "manual_documents": docs_manual,
            "total_documents": len(documents),
            "auto_count": len(docs_auto),
            "manual_count": len(docs_manual)
        }
        
        # Generate simple, flexible response with clear distinction
        response_lines = [
            f"Dokumen ekspor untuk {country}:",
            f"- Sistem dapat bantu buat ({len(docs_auto)}): {', '.join([doc['document_name'] for doc in docs_auto]) if docs_auto else 'Tidak ada'}",
            f"- Perlu apply ke instansi ({len(docs_manual)}): {', '.join([doc['document_name'] for doc in docs_manual]) if docs_manual else 'Tidak ada'}"
        ]

        # Only show template if explicitly requested
        template_previews = []
        if (show_template or is_requesting_template) and docs_auto:
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