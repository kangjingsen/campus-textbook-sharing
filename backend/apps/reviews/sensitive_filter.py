"""
基于 DFA（确定有限自动机）的敏感词过滤器
时间复杂度 O(n)，n 为待检测文本长度
"""
from .models import SensitiveWord


class DFAFilter:
    """DFA 敏感词过滤器"""

    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'
        self._loaded = False

    def load_words(self):
        """从数据库加载敏感词并构建 DFA 树"""
        self.keyword_chains = {}
        words = SensitiveWord.objects.filter(is_active=True).values_list('word', flat=True)
        for word in words:
            self._add_word(word.strip().lower())
        self._loaded = True

    def _add_word(self, word):
        """添加一个敏感词到 DFA 树"""
        if not word:
            return
        level = self.keyword_chains
        for i, char in enumerate(word):
            if char not in level:
                level[char] = {}
            level = level[char]
        level[self.delimit] = 0

    def check(self, text):
        """
        检测文本中的敏感词
        返回: (bool, list) -> (是否包含敏感词, 命中的敏感词列表)
        """
        if not self._loaded:
            self.load_words()

        if not self.keyword_chains:
            return False, []

        text = text.lower()
        found_words = set()
        i = 0

        while i < len(text):
            level = self.keyword_chains
            j = i
            word_buffer = ''
            found_word = ''

            while j < len(text) and text[j] in level:
                word_buffer += text[j]
                level = level[text[j]]
                if self.delimit in level:
                    found_word = word_buffer
                j += 1

            if found_word:
                found_words.add(found_word)
                i = j
            else:
                i += 1

        return bool(found_words), list(found_words)

    def filter_text(self, text, replace_char='*'):
        """替换文本中的敏感词为指定字符"""
        if not self._loaded:
            self.load_words()

        if not self.keyword_chains:
            return text

        result = list(text)
        text_lower = text.lower()
        i = 0

        while i < len(text_lower):
            level = self.keyword_chains
            j = i
            match_length = 0

            while j < len(text_lower) and text_lower[j] in level:
                level = level[text_lower[j]]
                j += 1
                if self.delimit in level:
                    match_length = j - i

            if match_length > 0:
                for k in range(i, i + match_length):
                    result[k] = replace_char
                i += match_length
            else:
                i += 1

        return ''.join(result)


# 全局单例
_filter_instance = None


def get_sensitive_filter():
    """获取敏感词过滤器实例"""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = DFAFilter()
    return _filter_instance


def reload_sensitive_filter():
    """重新加载敏感词库"""
    global _filter_instance
    _filter_instance = DFAFilter()
    _filter_instance.load_words()
    return _filter_instance


def check_sensitive(text):
    """便捷函数：检测是否包含敏感词"""
    f = get_sensitive_filter()
    return f.check(text)
