# jarvis_core.py
"""
ДЖАРВИС - ГОЛОСОВОЙ АССИСТЕНТ
Финал v4.0 — всё работает
"""
import os
import sys
import time
import datetime
import webbrowser
import random

# ============================================================
# НАСТРОЙКИ
# ============================================================
WAKE_THRESHOLD = 0.35
MODEL_SIZE = "medium"

# ============================================================
# ИМПОРТЫ
# ============================================================
print("=" * 55)
print("  ДЖАРВИС v4.0")
print("=" * 55)

print("  Загрузка модулей...")

try:
    from stt import VoiceRecognizer
    print("  ✓ STT")
except Exception as e:
    print(f"  ✗ STT: {e}")
    sys.exit(1)

try:
    from tts import VoiceSpeaker
    print("  ✓ TTS")
except Exception as e:
    print(f"  ✗ TTS: {e}")
    sys.exit(1)

try:
    from sounds import play_listen_signal, play_confirm_signal, play_error_signal
except:
    play_listen_signal = lambda: None
    play_confirm_signal = lambda: None
    play_error_signal = lambda: None

WAKE_OK = False
try:
    from wakeword import VoiceWakeWord
    WAKE_OK = True
    print("  ✓ Wake Word")
except Exception as e:
    print(f"  ⚠ Wake Word: {e}")


# ============================================================
# ЯДРО
# ============================================================
class Jarvis:
    def __init__(self, model_size=MODEL_SIZE, use_wake=False, wake_threshold=WAKE_THRESHOLD):
        self.running = True
        self.active = False
        self.use_wake = use_wake and WAKE_OK
        
        # Статистика
        self.stats = {"commands": 0, "wakes": 0, "errors": 0, "start": datetime.datetime.now()}
        
        # Распознаватель
        print(f"\n  Загрузка Whisper «{model_size}»...")
        self.rec = VoiceRecognizer(model_size=model_size, device="auto", compute_type="auto")
        
        # Синтезатор
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        
        # Wake Word
        self.wakeword = None
        if self.use_wake:
            print(f"  Wake Word (порог: {wake_threshold})...")
            self.wakeword = VoiceWakeWord(wake_word="джарвис", sensitivity=wake_threshold, debug=False)
            
            # Берём порог из модели если есть
            if self.wakeword.custom_model and 'threshold' in self.wakeword.custom_model:
                model_threshold = self.wakeword.custom_model['threshold']
                self.wakeword.custom_threshold = min(wake_threshold, model_threshold)
            else:
                self.wakeword.custom_threshold = wake_threshold
            
            self.wakeword.on_detected(self._on_wake)
            
            if self.wakeword.custom_model is None:
                print("  ⚠ Модель не обучена!")
                self.use_wake = False
            else:
                print(f"  ✓ Порог: {self.wakeword.custom_threshold:.3f}")
        
        # Фразы
        self.phrases = {
            "greet": ["Да, сэр.", "Слушаю.", "К вашим услугам.", "Джарвис на связи.", "Готов."],
            "unknown": ["Не знаю такой команды.", "Не могу выполнить.", "Повторите."],
            "thanks": ["Пожалуйста.", "Рад помочь.", "Не стоит."],
            "status": ["Всё в норме.", "Работаю.", "Готов к задачам."],
            "bye": ["До свидания.", "Отключаюсь.", "Завершаю работу."]
        }
        
        print("  ✓ Готово\n")
    
    def _say(self, text):
        self.speaker.speak_async(text)
    
    def _r(self, key):
        return random.choice(self.phrases.get(key, ["..."]))
    
    def _beep(self, func):
        try: func()
        except: pass
    
    def _on_wake(self):
        if not self.active:
            self.active = True
            self.stats["wakes"] += 1
            self._beep(play_listen_signal)
            print(f"\n{'='*40}")
            print(f"🔔 {self._r('greet')}")
            print(f"{'='*40}")
    
    def _has(self, text, words):
        """Проверяет наличие любого слова в тексте."""
        for w in words.split(","):
            w = w.strip()
            if w in text:
                return True
            # Частичное совпадение (первые 4 буквы)
            if len(w) >= 4 and w[:4] in text:
                return True
        return False
    
    def execute(self, command):
        if not command:
            self._say("Не расслышал.")
            return True
        
        cmd = command.lower().strip()
        self.stats["commands"] += 1
        n = self.stats["commands"]
        print(f"📝 [{n}] «{cmd}»")
        
        # ========== ВЫХОД ==========
        if self._has(cmd, "выход,пока,отключись,выключись,стоп,хватит,завершение"):
            self._say(self._r("bye"))
            time.sleep(0.8)
            return False
        
        if self._has(cmd, "спокойной ночи,спать"):
            self._say("Спокойной ночи.")
            time.sleep(0.8)
            return False
        
        # ========== ПРИЛОЖЕНИЯ ==========
        if self._has(cmd, "браузер,интернет,веб,гугл,открой браузер"):
            self._say("Запускаю браузер.")
            webbrowser.open("https://google.com")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "ютуб,youtube,видео"):
            self._say("YouTube.")
            webbrowser.open("https://youtube.com")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "калькулятор,посчитать"):
            self._say("Калькулятор.")
            os.system("calc" if os.name == "nt" else "gnome-calculator &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "блокнот,notepad,заметки,блокно,записи"):
            self._say("Блокнот.")
            os.system("notepad" if os.name == "nt" else "gedit &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "терминал,консоль,cmd,командная"):
            self._say("Терминал.")
            os.system("start cmd" if os.name == "nt" else "gnome-terminal &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "проводник,файлы,папки,провод"):
            self._say("Проводник.")
            os.system("explorer ." if os.name == "nt" else "nautilus . &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "диспетчер задач,процессы"):
            self._say("Диспетчер задач.")
            os.system("taskmgr" if os.name == "nt" else "gnome-system-monitor &")
            self._beep(play_confirm_signal)
            return True
        
        # ========== ВРЕМЯ / ДАТА ==========
        if self._has(cmd, "время,который час,часы,сколько время"):
            self._tell_time()
            return True
        
        if self._has(cmd, "дата,число,сегодня,день"):
            self._tell_date()
            return True
        
        # ========== СТАТИСТИКА ==========
        if self._has(cmd, "статистика,стата,аптайм,сколько работаешь"):
            self._tell_stats()
            return True
        
        # ========== ОБЩЕНИЕ ==========
        if self._has(cmd, "привет,здравствуй,хай,хелло,добрый"):
            h = datetime.datetime.now().hour
            if h < 6: g = "Доброй ночи"
            elif h < 12: g = "Доброе утро"
            elif h < 18: g = "Добрый день"
            else: g = "Добрый вечер"
            self._say(f"{g}! Я Джарвис.")
            return True
        
        if self._has(cmd, "как дела,настроение,как ты"):
            self._say(self._r("status"))
            return True
        
        if self._has(cmd, "что ты умеешь,помощь,команды,справка,help"):
            self._say("Браузер, YouTube, калькулятор, блокнот, терминал, проводник. Время, дата. «пока» — выход.")
            return True
        
        if self._has(cmd, "кто ты,имя,как зовут"):
            self._say("Я Джарвис — голосовой ассистент.")
            return True
        
        if self._has(cmd, "спасибо,благодарю,молодец,красава"):
            self._say(self._r("thanks"))
            return True
        
        if self._has(cmd, "шутка,анекдот,пошути"):
            jokes = [
                "31 октября = 25 декабря. Программисты путают Хэллоуин и Рождество.",
                "Сколько программистов вкрутят лампочку? Ни одного. Это hardware.",
                "Почему Python спокойный? Нет скобок.",
            ]
            self._say(random.choice(jokes))
            return True
        
        # ========== НЕИЗВЕСТНО ==========
        self._say(self._r("unknown"))
        self._beep(play_error_signal)
        self.stats["errors"] += 1
        return True
    
    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ
    # ============================================================
    
    def _tell_time(self):
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        hw = "часов" if 11 <= h % 100 <= 14 else "час" if h % 10 == 1 else "часа" if 2 <= h % 10 <= 4 else "часов"
        mw = "минут" if 11 <= m <= 14 else "минута" if m % 10 == 1 else "минуты" if 2 <= m % 10 <= 4 else "минут"
        t = f"{h} {hw} ровно" if m == 0 else f"{h} {hw} {m} {mw}"
        self._say(f"Сейчас {t}.")
    
    def _tell_date(self):
        now = datetime.datetime.now()
        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        wdays = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]
        self._say(f"Сегодня {wdays[now.weekday()]}, {now.day} {months[now.month-1]}.")
    
    def _tell_stats(self):
        up = datetime.datetime.now() - self.stats["start"]
        h, m = up.seconds // 3600, (up.seconds % 3600) // 60
        info = self.rec.info()
        self._say(f"Работаю {h} ч {m} мин. Команд: {self.stats['commands']}. {info['model']} на {info['device']}.")
    
    # ============================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ============================================================
    
    def run(self):
        if self.use_wake and self.wakeword:
            self._run_voice()
        else:
            self._run_manual()
    
    def _run_voice(self):
        self.wakeword.start_listening()
        self._say("Джарвис запущен.")
        
        print(f"\n{'='*55}")
        print(f"  ГОЛОСОВОЙ РЕЖИМ")
        print(f"  Скажите «Джарвис» — я отвечу")
        print(f"  Ctrl+C — выход")
        print(f"{'='*55}\n")
        
        try:
            while self.running:
                if self.active:
                    cmd = self.rec.listen()
                    if cmd:
                        self.running = self.execute(cmd)
                    self.active = False
                    if self.running:
                        print("💤 Жду «Джарвис»...")
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nЗавершение...")
            self._say("Завершение работы.")
        finally:
            self._cleanup()
    
    def _run_manual(self):
        self._say("Джарвис запущен. Нажмите Enter.")
        
        print(f"\n{'='*55}")
        print(f"  РУЧНОЙ РЕЖИМ")
        print(f"  Enter — команда | «пока» — выход")
        print(f"{'='*55}\n")
        
        try:
            while self.running:
                try:
                    input("▶ Enter...")
                except EOFError:
                    break
                
                self.active = True
                self._beep(play_listen_signal)
                print("🎤 Говорите...")
                
                cmd = self.rec.listen()
                if cmd:
                    self.running = self.execute(cmd)
                self.active = False
                print()
        except KeyboardInterrupt:
            print("\nЗавершение...")
            self._say("Завершение работы.")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        print("\nОчистка...")
        try: self.rec.close()
        except: pass
        try:
            if self.wakeword:
                self.wakeword.stop()
        except: pass
        print("✓ Джарвис отключён.")


# ============================================================
# ЗАПУСК
# ============================================================
def main():
    print(f"\n{'='*55}")
    print("  ВЫБОР РЕЖИМА")
    print(f"{'='*55}")
    print("  1 — Голосовая активация")
    print("  2 — Ручная (Enter)")
    print("  3 — Выход")
    
    try:
        c = input("\n  Выбор [1-3]: ").strip()
    except:
        return
    
    if c == "3":
        return
    
    use_wake = (c == "1")
    threshold = WAKE_THRESHOLD
    
    if use_wake:
        if not os.path.exists("models/джарвис_model.json"):
            print("\n  ! Модель не найдена.")
            print("  python train_wakeword.py")
            if input("  Ручной режим? [y/n]: ").lower() != 'y':
                return
            use_wake = False
        else:
            t = input(f"  Порог [Enter={WAKE_THRESHOLD}]: ").strip()
            if t:
                try:
                    threshold = max(0.2, min(0.95, float(t)))
                except:
                    pass
    
    print("\n  Whisper: 1=tiny 2=base 3=small 4=medium")
    mc = input("  Выбор [Enter=4]: ").strip()
    models = {"1":"tiny","2":"base","3":"small","4":"medium"}
    model = models.get(mc, MODEL_SIZE)
    
    jarvis = Jarvis(
        model_size=model,
        use_wake=use_wake,
        wake_threshold=threshold
    )
    jarvis.run()


if __name__ == "__main__":
    main()