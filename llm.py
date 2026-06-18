# llm.py
"""
Модуль для общения с LLM через Ollama.
"""
import ollama


class LLM:
    """Локальная языковая модель."""
    
    def __init__(self, model="llama3.2:3b", system_prompt=None):
        self.model = model
        
        if system_prompt is None:
            self.system_prompt = (
                "Ты — Джарвис, голосовой ассистент и дворецкий из фильма Железный человек. "
                "Твой создатель — сэр, ты обращаешься к нему уважительно. "
                "Ты помогаешь с задачами на компьютере: открыть программы, найти информацию, "
                "ответить на вопросы, управлять файлами, включать музыку. "
                "ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. "
                "Отвечай КРАТКО — не более 2-3 предложений. "
                "Не используй маркдаун, звёздочки, списки. "
                "Говори как человек, а не как робот. "
                "Будь вежливым, но с лёгким сарказмом. "
                "Не упоминай что ты языковая модель или ИИ. "
                "Ты — Джарвис, и точка."
            )
        else:
            self.system_prompt = system_prompt
        
        self.history = []
        print(f"  LLM: {model}")
    
    def ask(self, question, max_tokens=100):
        """
        Задаёт вопрос модели.
        Возвращает ответ строкой.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-6:],  # Последние 6 сообщений для контекста
            {"role": "user", "content": question}
        ]
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "stop": ["\n\n", "Сэр,"]  # Останавливаем на повторах
                }
            )
            
            answer = response["message"]["content"].strip()
            
            # Убираем мусор
            answer = self._clean_answer(answer)
            
            # Сохраняем историю
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            
            # Ограничиваем историю
            if len(self.history) > 20:
                self.history = self.history[-10:]
            
            return answer
            
        except Exception as e:
            return f"Простите, произошла ошибка. {str(e)[:50]}"
    
    def _clean_answer(self, text):
        """Очищает ответ от мусора."""
        # Убираем маркдаун
        text = text.replace("*", "").replace("#", "").replace("`", "")
        
        # Убираем английские фразы
        lines = text.split("\n")
        clean_lines = []
        for line in lines:
            # Пропускаем строки с английским
            english_words = ["various", "calendar", "fluent", "try", "tasks", "information"]
            if any(w in line.lower() for w in english_words):
                continue
            clean_lines.append(line)
        
        text = " ".join(clean_lines)
        
        # Убираем дубликаты
        sentences = text.split(". ")
        unique = []
        for s in sentences:
            if s not in unique:
                unique.append(s)
        text = ". ".join(unique)
        
        # Обрезаем до разумной длины
        if len(text) > 300:
            text = text[:300] + "..."
        
        return text.strip()
    
    def clear_history(self):
        """Очищает историю диалога."""
        self.history = []
    
    def change_model(self, model):
        """Меняет модель."""
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
    
    print("\n  Задавайте вопросы. 'выход' для завершения.\n")
    
    while True:
        q = input("  Вы: ").strip()
        if q.lower() in ["выход", "пока", "exit"]:
            break
        
        answer = llm.ask(q)
        print(f"  Джарвис: {answer}\n")
    
    print("  До встречи!")