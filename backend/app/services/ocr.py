"""
PDF OCR 处理 - 扫描版 PDF
"""

from typing import Optional, List, Dict, Any
from loguru import logger
import asyncio
from dataclasses import dataclass


@dataclass
class OCRResult:
    """OCR 结果"""

    text: str
    confidence: float
    blocks: List[Dict[str, Any]]


class OCRService:
    """OCR 服务"""

    def __init__(self):
        self.enabled = False
        self._init_ocr()

    def _init_ocr(self):
        """初始化 OCR"""
        try:
            import pytesseract
            from PIL import Image

            self.enabled = True
            logger.info("OCR service initialized (Tesseract)")
        except ImportError:
            logger.warning("Tesseract not installed, OCR disabled")
            self.enabled = False

    async def extract_text_from_image(self, image_data: bytes) -> OCRResult:
        """从图片提取文字"""
        if not self.enabled:
            raise RuntimeError("OCR service not available")

        try:
            from PIL import Image
            import pytesseract
            import io

            # 打开图片
            image = Image.open(io.BytesIO(image_data))

            # OCR 提取
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")

            # 提取置信度
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # 计算平均置信度
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100,
                blocks=data.get("blocks", []),
            )

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise

    async def extract_text_from_pdf_page(self, page) -> OCRResult:
        """从 PDF 页面提取文字 (扫描版)"""
        # 获取页面图片
        pix = page.get_pixmap(dpi=300)
        image_data = pix.tobytes()

        return await self.extract_text_from_image(image_data)

    async def process_scanned_pdf(self, pdf_document) -> Dict[str, Any]:
        """处理扫描版 PDF"""
        results = []
        total_confidence = 0

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # 首先尝试普通提取
            normal_text = page.get_text()

            if normal_text.strip():
                # 普通提取成功
                results.append(
                    {
                        "page": page_num + 1,
                        "text": normal_text,
                        "method": "text_layer",
                        "confidence": 1.0,
                    }
                )
            elif self.enabled:
                # 尝试 OCR
                ocr_result = await self.extract_text_from_pdf_page(page)
                results.append(
                    {
                        "page": page_num + 1,
                        "text": ocr_result.text,
                        "method": "ocr",
                        "confidence": ocr_result.confidence,
                    }
                )
                total_confidence += ocr_result.confidence
            else:
                results.append(
                    {
                        "page": page_num + 1,
                        "text": "",
                        "method": "failed",
                        "confidence": 0,
                    }
                )

        # 合并结果
        full_text = "\n\n".join([r["text"] for r in results if r["text"]])

        avg_confidence = (
            total_confidence / len(results) if results and self.enabled else 0
        )

        return {
            "text": full_text,
            "pages": results,
            "method": "mixed",
            "confidence": avg_confidence,
            "total_pages": len(results),
        }


# 全局实例
ocr_service = OCRService()


# ==================== 使用示例 ====================


async def process_pdf_with_ocr(pdf_bytes: bytes) -> Dict[str, Any]:
    """处理 PDF (包含 OCR)"""
    import fitz

    # 打开 PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 尝试普通提取
    has_text = False
    for page in doc:
        if page.get_text().strip():
            has_text = True
            break

    if has_text:
        # 普通 PDF
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())

        return {
            "text": "\n\n".join(text_parts),
            "method": "text_layer",
            "confidence": 1.0,
            "total_pages": len(doc),
        }
    else:
        # 扫描版 PDF
        if ocr_service.enabled:
            return await ocr_service.process_scanned_pdf(doc)
        else:
            return {
                "text": "",
                "method": "ocr_disabled",
                "confidence": 0,
                "total_pages": len(doc),
            }
