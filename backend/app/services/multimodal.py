"""
多模态处理服务 - 图片和音频
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from loguru import logger
import base64
import io


@dataclass
class ImageResult:
    """图片处理结果"""
    text: str
    confidence: float
    objects: list
    faces: list


@dataclass
class AudioResult:
    """音频处理结果"""
    text: str
    confidence: float
    language: str
    duration: float


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self):
        self.enabled = False
        self._init_processor()
    
    def _init_processor(self):
        """初始化"""
        try:
            # 尝试加载图像处理库
            from PIL import Image
            self.enabled = True
            logger.info("Image processor initialized")
        except ImportError:
            logger.warning("PIL not installed")
    
    async def extract_text(self, image_data: bytes) -> ImageResult:
        """提取图片文字 (OCR)"""
        if not self.enabled:
            raise RuntimeError("Image processor not available")
        
        try:
            from PIL import Image
            import pytesseract
            
            image = Image.open(io.BytesIO(image_data))
            
            # OCR 提取
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 对象检测 (使用 pytesseract)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # 提取对象
            objects = []
            for i, label in enumerate(data['text']):
                if data['conf'][i] > 30 and label.strip():
                    objects.append({
                        "text": label,
                        "confidence": data['conf'][i] / 100,
                        "bbox": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    })
            
            return ImageResult(
                text=text.strip(),
                confidence=sum(o['confidence'] for o in objects) / len(objects) if objects else 0,
                objects=objects,
                faces=[]
            )
        
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            raise
    
    async def describe_image(self, image_data: bytes) -> str:
        """图片描述 (使用 VLM)"""
        # TODO: 使用 LLM Vision 模型描述图片
        result = await self.extract_text(image_data)
        return result.text or "图片中包含文字和视觉元素"


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        self.enabled = False
        self._init_processor()
    
    def _init_processor(self):
        """初始化"""
        try:
            import whisper
            self.model = whisper.load_model("base")
            self.enabled = True
            logger.info("Audio processor initialized (Whisper)")
        except ImportError:
            logger.warning("openai-whisper not installed")
    
    async def transcribe(self, audio_data: bytes) -> AudioResult:
        """语音转文字"""
        if not self.enabled:
            raise RuntimeError("Audio processor not available")
        
        try:
            import whisper
            import torch
            
            # 保存临时文件
            with open("/tmp/audio.wav", "wb") as f:
                f.write(audio_data)
            
            # 转写
            result = self.model.transcribe("/tmp/audio.wav")
            
            # 计算置信度
            segments = result.get("segments", [])
            avg_confidence = 0
            for seg in segments:
                if "avg_logprob" in seg:
                    avg_confidence += seg["avg_logprob"]
            avg_confidence = (avg_confidence / len(segments) + 1) / 2 if segments else 0
            
            return AudioResult(
                text=result["text"],
                confidence=avg_confidence,
                language=result.get("language", "unknown"),
                duration=result.get("duration", 0)
            )
        
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            raise
    
    async def translate(self, audio_data: bytes, target_lang: str = "en") -> str:
        """翻译音频"""
        # TODO: 实现翻译
        result = await self.transcribe(audio_data)
        return result.text


# ==================== 多模态 RAG ====================

class MultimodalRAG:
    """多模态 RAG"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
    
    async def process_attachment(
        self,
        attachment_type: str,
        data: bytes
    ) -> Dict[str, Any]:
        """处理附件"""
        processors = {
            "image": self.image_processor,
            "audio": self.audio_processor,
            "pdf": self._process_pdf_page,
            "video": self._process_video_frame,
        }
        
        processor = processors.get(attachment_type)
        if not processor:
            raise ValueError(f"Unsupported type: {attachment_type}")
        
        return await processor(data)
    
    async def _process_pdf_page(self, data: bytes) -> Dict[str, Any]:
        """处理 PDF 页面"""
        from app.services.pdf import PDFProcessor
        processor = PDFProcessor()
        return await processor.extract_text(data)
    
    async def _process_video_frame(self, data: bytes) -> Dict[str, Any]:
        """处理视频帧"""
        return await self.image_processor.extract_text(data)
    
    async def describe_media(self, media_type: str, data: bytes) -> str:
        """描述媒体内容"""
        if media_type == "image":
            return await self.image_processor.describe_image(data)
        elif media_type == "audio":
            result = await self.audio_processor.transcribe(data)
            return f"[音频转写]\n{result.text}"
        else:
            return "不支持的媒体类型"


# 全局实例
multimodal_rag = MultimodalRAG()


# ==================== 附件处理 API ====================

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()


@router.post("/api/v1/media/extract-text")
async def extract_text_from_image(file: UploadFile = File(...)):
    """从图片提取文字"""
    content = await file.read()
    
    result = await multimodal_rag.image_processor.extract_text(content)
    
    return {
        "text": result.text,
        "confidence": result.confidence,
        "objects": result.objects
    }


@router.post("/api/v1/media/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """语音转文字"""
    content = await file.read()
    
    result = await multimodal_rag.audio_processor.transcribe(content)
    
    return {
        "text": result.text,
        "confidence": result.confidence,
        "language": result.language,
        "duration": result.duration
    }


@router.post("/api/v1/media/describe")
async def describe_media(
    media_type: str,
    file: UploadFile = File(...)
):
    """描述媒体内容"""
    content = await file.read()
    
    description = await multimodal_rag.describe_media(media_type, content)
    
    return {"description": description}
