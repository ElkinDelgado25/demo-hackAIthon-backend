import csv
import io
import json
import zipfile
import xml.etree.ElementTree as ET

import PyPDF2


class FileParser:
    async def parse(self, content: bytes, filename: str) -> str:
        """Extrae texto de documentos soportados sin ejecutar contenido externo."""
        file_type = filename.split(".")[-1].lower()

        if file_type == "pdf":
            return self._parse_pdf(content)
        if file_type == "json":
            return self._parse_json(content)
        if file_type == "csv":
            return self._parse_csv(content)
        if file_type == "xlsx":
            return self._parse_xlsx(content)
        if file_type in {"png", "jpg", "jpeg"}:
            return ""
        return content.decode("utf-8", errors="ignore")

    def _parse_pdf(self, content: bytes) -> str:
        pdf = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text if text else "No se pudo extraer texto del PDF"

    def _parse_json(self, content: bytes) -> str:
        data = json.loads(content.decode("utf-8"))
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _parse_csv(self, content: bytes) -> str:
        text_content = content.decode("utf-8", errors="ignore")
        csv_reader = csv.DictReader(io.StringIO(text_content))
        rows = list(csv_reader)

        if not rows:
            return "CSV vacio"

        result = []
        headers = list(rows[0].keys())
        result.append(" | ".join(headers))
        result.append("-" * 50)

        for row in rows[:30]:
            result.append(" | ".join(str(row.get(header, "")) for header in headers))

        return "\n".join(result)

    def _parse_xlsx(self, content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as workbook:
                shared_strings = self._read_shared_strings(workbook)
                sheet_names = [name for name in workbook.namelist() if name.startswith("xl/worksheets/sheet")]
                result = []

                for sheet_name in sheet_names[:3]:
                    root = ET.fromstring(workbook.read(sheet_name))
                    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                    rows = root.findall(".//x:sheetData/x:row", namespace)
                    result.append(f"Hoja: {sheet_name}")

                    for row in rows[:30]:
                        values = []
                        for cell in row.findall("x:c", namespace):
                            value = cell.find("x:v", namespace)
                            if value is None:
                                values.append("")
                                continue
                            raw_value = value.text or ""
                            if cell.attrib.get("t") == "s":
                                try:
                                    values.append(shared_strings[int(raw_value)])
                                except (ValueError, IndexError):
                                    values.append(raw_value)
                            else:
                                values.append(raw_value)
                        result.append(" | ".join(values))

                return "\n".join(result).strip() or "XLSX sin filas legibles"
        except Exception:
            return "No se pudo extraer texto del XLSX"

    def _read_shared_strings(self, workbook: zipfile.ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in workbook.namelist():
            return []

        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        values = []
        for item in root.findall("x:si", namespace):
            texts = [node.text or "" for node in item.findall(".//x:t", namespace)]
            values.append("".join(texts))
        return values
