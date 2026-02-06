"""
中文分词服务
"""
from typing import List, Set, Dict, Any
from collections import Counter
from loguru import logger
import re


class ChineseTokenizer:
    """中文分词器"""
    
    def __init__(self):
        self.enabled = False
        self._init_tokenizer()
    
    def _init_tokenizer(self):
        """初始化分词器"""
        try:
            import jieba
            import jieba.posseg as pseg
            import jieba.analyse
            
            self.enabled = True
            logger.info("Chinese tokenizer initialized (jieba)")
            
            # 加载默认词典
            jieba.initialize()
        
        except ImportError:
            logger.warning("jieba not installed, Chinese tokenization disabled")
    
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        if not self.enabled:
            return self._simple_tokenize(text)
        
        try:
            import jieba
            return list(jieba.cut(text))
        
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return self._simple_tokenize(text)
    
    def tokenize_with_pos(self, text: str) -> List[tuple]:
        """分词 + 词性标注"""
        if not self.enabled:
            return [(w, 'x') for w in self._simple_tokenize(text)]
        
        try:
            import jieba.posseg as pseg
            return list(pseg.cut(text))
        
        except Exception as e:
            logger.error(f"POS tagging failed: {e}")
            return [(w, 'x') for w in self._simple_tokenize(text)]
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """简单分词 (英文/数字)"""
        # 移除标点，按空格分割
        text = re.sub(r'[^\w\s]', ' ', text)
        return [w for w in text.split() if w.strip()]
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        if not self.enabled:
            return self._simple_keywords(text, top_k)
        
        try:
            import jieba.analyse
            return jieba.analyse.extract_tags(text, topK=top_k)
        
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return self._simple_keywords(text, top_k)
    
    def _simple_keywords(self, text: str, top_k: int) -> List[str]:
        """简单关键词提取"""
        words = self.tokenize(text)
        word_freq = Counter(words)
        
        # 过滤停用词
        stopwords = self.get_stopwords()
        filtered = {w: f for w, f in word_freq.items() 
                   if len(w) > 1 and w not in stopwords}
        
        return sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    def extract_keyphrases(self, text: str, top_k: int = 5) -> List[str]:
        """提取关键短语"""
        if not self.enabled:
            return self._simple_keyphrases(text, top_k)
        
        try:
            import jieba.analyse
            return jieba.analyse.textrank(text, topK=top_k, withWeight=False)
        
        except Exception as e:
            logger.error(f"Keyphrase extraction failed: {e}")
            return self._simple_keyphrases(text, top_k)
    
    def _simple_keyphrases(self, text: str, top_k: int) -> List[str]:
        """简单关键短语提取"""
        # 提取连续的中文词组
        pattern = r'[\u4e00-\u9fa5]{2,5}'
        phrases = re.findall(pattern, text)
        phrase_freq = Counter(phrases)
        return [p for p, _ in phrase_freq.most_common(top_k)]
    
    def get_stopwords(self) -> Set[str]:
        """获取停用词"""
        return {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '么', '她', '他', '它', '们', '这个', '什么', '可以', '对',
            'but', 'the', 'and', 'is', 'in', 'to', 'of', 'for', 'on',
            'with', 'as', 'at', 'be', 'this', 'that', 'by', 'it'
        }
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """文本摘要"""
        if not self.enabled:
            return self._simple_summarize(text, max_length)
        
        try:
            import jieba.analyse
            return jieba.analyse.extract_sentences(text)[0][:max_length]
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return self._simple_summarize(text, max_length)
    
    def _simple_summarize(self, text: str, max_length: int) -> str:
        """简单摘要"""
        sentences = re.split(r'[。！？]', text)
        result = []
        
        for sentence in sentences:
            if len(result) + len(sentence) <= max_length:
                result.append(sentence)
            else:
                break
        
        return ''.join(result) if result else text[:max_length]


# 全局实例
chinese_tokenizer = ChineseTokenizer()


# ==================== 搜索增强 ====================

class SearchTokenizer:
    """搜索分词器"""
    
    def __init__(self):
        self.chinese = chinese_tokenizer
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """分析查询"""
        tokens = self.chinese.tokenize(query)
        
        # 提取关键词
        keywords = self.chinese.extract_keywords(query, top_k=5)
        
        # 提取短语
        keyphrases = self.chinese.extract_keyphrases(query, top_k=3)
        
        return {
            "original": query,
            "tokens": tokens,
            "keywords": keywords,
            "keyphrases": keyphrases,
            "token_count": len(tokens)
        }
    
    def expand_query(self, query: str) -> List[str]:
        """扩展查询 (同义词等)"""
        analysis = self.analyze(query)
        expansions = [query]
        
        # 添加关键词
        expansions.extend(analysis["keywords"])
        
        # 添加短语
        expansions.extend(analysis["keyphrases"])
        
        return list(set(expansions))


# 全局实例
search_tokenizer = SearchTokenizer()
