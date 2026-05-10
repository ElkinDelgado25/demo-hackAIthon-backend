import PyPDF2
import json
import csv
import io
from typing import Union

class FileParser:
    async def parse(self, content: bytes, filename: str) -> str:
        """Extrae texto de PDF, JSON o CSV"""
        file_type = filename.split('.')[-1].lower()
        
        if file_type == "pdf":
            return self._parse_pdf(content)
        elif file_type == "json":
            return self._parse_json(content)
        elif file_type == "csv":
            return self._parse_csv(content)
        else:
            # Fallback a texto plano
            return content.decode('utf-8', errors='ignore')
    
    def _parse_pdf(self, content: bytes) -> str:
        pdf = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text if text else "No se pudo extraer texto del PDF"
    
    def _parse_json(self, content: bytes) -> str:
        data = json.loads(content.decode('utf-8'))
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _parse_csv(self, content: bytes) -> str:
        text_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(text_content))
        rows = list(csv_reader)
        
        if not rows:
            return "CSV vacío"
        
        result = []
        headers = list(rows[0].keys())
        result.append(" | ".join(headers))
        result.append("-" * 50)
        
        for row in rows[:30]:
            result.append(" | ".join(str(row.get(h, "")) for h in headers))
        
        return "\n".join(result)