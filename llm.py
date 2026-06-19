# llm.py
"""
Модуль для общения с LLM через Ollama.
Быстрые ответы.
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
            "2. Отвечай КРАТКО — 1 предложение максимум. "
            "3. Не используй маркдаун, списки, звёздочки, эмодзи. "
            "4. Не говори что ты ИИ, модель или программа. Ты — Джарвис. "
            "5. Если не знаешь ответ — скажи честно, но кратко. "
            "6. Не повторяй вопрос в ответе. "
            "7. Говори как человек, естественно."
        )
        
        self.history = []
        print(f"  LLM: {model}")
    
    def ask(self, question, max_tokens=50):
        """
        Задаёт вопрос и возвращает ответ.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-2:],  # Только 2 последних сообщения
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
                    "repeat_penalty": 1.1,
                    "stop": ["\n", "\n\n", "Сэр:", "Джарвис:"]
                }
            )
            
            answer = response["message"]["content"].strip()
            answer = self._clean(answer)
            
            # Сохраняем историю
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            
            # Держим историю короткой
            if len(self.history) > 6:
                self.history = self.history[-4:]
            
            return answer
            
        except Exception as e:
            return "Простите, я задумался."
    
    def _clean(self, text):
        """Очищает ответ."""
        for char in ['*', '#', '`', '_', '~']:
            text = text.replace(char, '')
        
        # Убираем английские фразы
        english = ["various", "tasks", "calendar", "fluent", "I can", "I am", "As an"]
        for phrase in english:
            text = text.replace(phrase, '')
        
        # Убираем пустые строки
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        text = ' '.join(lines)
        
        # Убираем двойные пробелы
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        # Обрезаем до первой точки
        if '.' in text[:100]:
            text = text.split('.')[0] + '.'
        
        # Максимум 150 символов
        if len(text) > 150:
            text = text[:147] + '...'
        
        return text.strip()
    
    def clear_history(self):
        """Очищает историю."""
        self.history = []
    
    def change_model(self, model):
        """Меняет модель."""
        self.model = model
        self.clear_history()
        print(f"  Модель изменена: {model}")


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
        
        if q.lower() in ["выход", "пока", "exit"]:
            break
        
        if not q:
            continue
        
        answer = llm.ask(q)
        print(f"  Джарвис: {answer}\n")
    
    print("  До свидания!")