# llm.py
"""
Модуль для общения с LLM через Ollama.
Исправлено: не обрезает ответы.
"""
import ollama


class LLM:
    """Локальная языковая модель через Ollama."""
    
    def __init__(self, model="llama3.2:3b"):
        self.model = model
        
        self.system_prompt = (
            "Ты — Джарвис, голосовой ассистент из фильма Железный человек. "
            "Твой хозяин — сэр. Ты должен быть вежливым, полезным и иногда саркастичным. "
            "ПРАВИЛА ОТВЕТА: "
            "1. Отвечай ТОЛЬКО на русском языке. "
            "2. Отвечай КРАТКО — 1-2 предложения максимум. "
            "3. Не используй маркдаун, списки, звёздочки, эмодзи. "
            "4. Не говори что ты ИИ, модель или программа. Ты — Джарвис. "
            "5. Если не знаешь ответ — скажи честно, но кратко. "
            "6. Не повторяй вопрос в ответе. "
            "7. Говори как человек, естественно."
            "8. ВСЕГДА заканчивай предложение точкой."
        )
        
        self.history = []
        print(f"  LLM: {model}")
    
    def ask(self, question, max_tokens=120):
        """
        Задаёт вопрос и возвращает ответ.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-4:],
            {"role": "user", "content": question}
        ]
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.5,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "repeat_penalty": 1.2,
                    "stop": ["\n\n\n"]  # Только на тройном переносе
                }
            )
            
            answer = response["message"]["content"].strip()
            answer = self._clean(answer)
            
            # Сохраняем историю
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            
            if len(self.history) > 10:
                self.history = self.history[-6:]
            
            return answer
            
        except Exception as e:
            return "Простите, я задумался. Повторите вопрос."
    
    def _clean(self, text):
        """Очищает ответ от мусора и обрезанных слов."""
        # Убираем маркдаун
        for char in ['*', '#', '`', '_', '~']:
            text = text.replace(char, '')
        
        # Убираем типичные английские вставки
        english_phrases = [
            "various", "tasks", "calendar", "fluent", "try",
            "information", "automation", "weather", "forecast",
            "I can", "I am", "As an", "Let me", "Sure"
        ]
        for phrase in english_phrases:
            text = text.replace(phrase, '')
        
        # Убираем пустые строки
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        text = ' '.join(lines)
        
        # Убираем двойные пробелы
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        # Обрезаем до последнего законченного предложения
        if len(text) > 200:
            # Ищем последнюю точку, восклицательный или вопросительный знак
            cut = text[:200]
            last_sentence_end = -1
            
            for char in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                pos = cut.rfind(char)
                if pos > last_sentence_end:
                    last_sentence_end = pos
            
            if last_sentence_end > 30:
                text = text[:last_sentence_end + 1].strip()
            else:
                # Если нет точки — ищем последний пробел
                last_space = text[:200].rfind(' ')
                if last_space > 50:
                    text = text[:last_space].strip()
        
        # Убираем обрезанные слова в конце
        # Если последнее слово короткое и без гласных — обрезаем
        words = text.split()
        if words:
            last_word = words[-1].strip('.,!?;:')
            # Если слово из 1-2 букв или выглядит обрезанным
            if len(last_word) <= 2 and len(words) > 3:
                text = ' '.join(words[:-1])
        
        return text.strip()
    
    def clear_history(self):
        """Очищает историю диалога."""
        self.history = []
    
    def change_model(self, model):
        """Меняет модель Ollama."""
        self.model = model
        self.clear_history()
        print(f"  Модель изменена: {model}")


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ LLM")
    print("=" * 50)
    
    llm = LLM()
    
    print("\n  Спрашивайте. 'выход' для выхода.\n")
    
    while True:
        try:
            q = input("  Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if q.lower() in ["выход", "пока", "exit", "quit"]:
            break
        
        if not q:
            continue
        
        answer = llm.ask(q)
        print(f"  Джарвис: {answer}\n")
    
    print("  До свидания!")