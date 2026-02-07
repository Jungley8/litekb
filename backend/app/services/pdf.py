"""
PDF 文档解析
"""

import io
from typing import Optional
from loguru import logger

# 尝试导入 PDF 库
try:
    import fitz  # PyMuPDF

    PYMMUPDF_AVAILABLE = True
except ImportError:
    PYMMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF 未安装，PDF 解析功能受限")

try:
    from pdfplumber import pdf

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFProcessor:
    """PDF 处理器"""

    def __init__(self):
        self.method = self._get_best_method()

    def _get_best_method(self) -> str:
        """选择最佳解析方法"""
        if PYMMUPDF_AVAILABLE:
            return "pymupdf"
        elif PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        else:
            return "textract"

    async def extract_text(self, content: bytes) -> str:
        """从 PDF 提取文本"""
        if self.method == "pymupdf":
            return await self._extract_pymupdf(content)
        elif self.method == "pdfplumber":
            return await self._extract_pdfplumber(content)
        else:
            return await self._extract_with_fallback(content)

    async def _extract_pymupdf(self, content: bytes) -> str:
        """使用 PyMuPDF 提取"""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()
            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PyMuPDF 解析失败: {e}")
            return ""

    async def _extract_pdfplumber(self, content: bytes) -> str:
        """使用 pdfplumber 提取"""
        try:
            pdf_file = io.BytesIO(content)
            text_parts = []

            with pdf.open(pdf_file) as pdf_doc:
                for page in pdf_doc.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"pdfplumber 解析失败: {e}")
            return ""

    async def _extract_with_fallback(self, content: bytes) -> str:
        """使用命令行工具 fallback"""
        import subprocess
        import tempfile
        import os

        # 尝试使用 pdftotext
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                f.write(content)
                temp_path = f.name

            result = subprocess.run(
                ["pdftotext", "-layout", temp_path, "-"], capture_output=True, text=True
            )

            os.unlink(temp_path)

            if result.returncode == 0:
                return result.stdout

        except Exception as e:
            logger.error(f"pdftotext 失败: {e}")

        return ""

    def extract_metadata(self, content: bytes) -> dict:
        """提取 PDF 元数据"""
        metadata = {}

        if self.method == "pymupdf":
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                metadata = {
                    "page_count": len(doc),
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                }
                doc.close()
            except Exception as e:
                logger.error(f"提取元数据失败: {e}")

        return metadata


# 便捷函数
async def extract_pdf_text(content: bytes) -> str:
    """提取 PDF 文本"""
    processor = PDFProcessor()
    return await processor.extract_text(content)
