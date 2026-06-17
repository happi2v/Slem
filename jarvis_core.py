# jarvis_core.py
"""
ДЖАРВИС - ГОЛОСОВОЙ АССИСТЕНТ
Ядро v3.3 — с частичным совпадением команд
"""
import os
import sys
import time
import datetime
import webbrowser
import random
import traceback

# ============================================================
# НАСТРОЙКИ
# ============================================================
WAKE_WORD_THRESHOLD = 0.3
DEFAULT_MODEL_SIZE = "medium"

# ============================================================
# ИМПОРТЫ
# ============================================================
print("=" * 55)
print("  ДЖАРВИС v3.3 — ЗАПУСК")
print("=" * 55)

def check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  ✓ GPU: {name} ({mem:.1f} ГБ)")
            return "cuda", "float16"
    except:
        pass
    print("  ℹ CPU")
    return "cpu", "int8"

DEVICE, COMPUTE_TYPE = check_gpu()

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
    print("  ✓ Sounds")
except:
    play_listen_signal = lambda: None
    play_confirm_signal = lambda: None
    play_error_signal = lambda: None
    print("  ⚠ Sounds отключены")

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
    def __init__(self, model_size=DEFAULT_MODEL_SIZE, use_wake=False, 
                 wake_threshold=WAKE_WORD_THRESHOLD):
        
        self.model_size = model_size
        self.wake_threshold = wake_threshold
        self.running = True
        self.active = False
        
        self.stats = {
            "commands": 0,
            "wakes": 0,
            "errors": 0,
            "start": datetime.datetime.now()
        }
        
        print(f"\n  Инициализация...")
        print(f"  Модель: {model_size} | Устройство: {DEVICE}")
        
        self.rec = VoiceRecognizer(
            model_size=model_size,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        
        self.wakeword = None
        self.use_wake = use_wake and WAKE_OK
        
        if self.use_wake:
            print(f"  Wake Word: порог {self.wake_threshold}")
            try:
                self.wakeword = VoiceWakeWord(
                    wake_word="джарвис",
                    sensitivity=self.wake_threshold,
                    debug=False
                )
                self.wakeword.custom_threshold = self.wake_threshold
                self.wakeword.on_detected(self._on_wake)
                
                if self.wakeword.custom_model is None:
                    print("  ⚠ Модель не обучена!")
                    self.use_wake = False
                else:
                    print("  ✓ Готово")
            except Exception as e:
                print(f"  ✗ Ошибка: {e}")
                self.use_wake = False
        
        self._init_phrases()
        print("  ✓ Ядро запущено\n")
    
    def _init_phrases(self):
        self.p = {
            "greet": ["Да, сэр.", "Слушаю.", "К вашим услугам.", "Джарвис на связи."],
            "unknown": ["Не знаю такой команды.", "Не могу выполнить.", "Повторите."],
            "thanks": ["Пожалуйста.", "Рад помочь.", "Не стоит."],
            "status": ["Всё в норме.", "Работаю штатно.", "Готов к задачам."],
            "bye": ["До свидания.", "Отключаюсь.", "Завершаю работу."]
        }
    
    def _say(self, text):
        self.speaker.speak_async(text)
    
    def _r(self, key):
        return random.choice(self.p.get(key, ["..."]))
    
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
        """
        Проверяет наличие ключевого слова с учётом:
        - точного совпадения
        - частичного (начало слова)
        - обрезанного распознавания
        """
        for w in words.split(","):
            w = w.strip()
            
            # Точное совпадение
            if w in text:
                return True
            
            # Частичное: начало текста содержит начало слова
            if len(w) >= 4:
                prefix = w[:4]
                if text.startswith(prefix):
                    return True
            
            # Частичное: любое слово в тексте начинается с ключа
            for tw in text.split():
                if len(tw) >= 3 and len(w) >= 3:
                    if tw.startswith(w[:3]) or w.startswith(tw[:3]):
                        return True
        
        return False
    
    def execute(self, command):
        if not command:
            self._say("Не расслышал. Повторите.")
            return True
        
        cmd = command.lower().strip()
        self.stats["commands"] += 1
        n = self.stats["commands"]
        print(f"📝 [{n}] «{cmd}»")
        
        # Выход
        if self._has(cmd, "выход,пока,отключись,завершение,выключись,стоп,хватит"):
            self._say(self._r("bye"))
            time.sleep(0.8)
            return False
        
        if self._has(cmd, "спокойной ночи,спать"):
            self._say("Спокойной ночи.")
            time.sleep(0.8)
            return False
        
        # Приложения
        if self._has(cmd, "браузер,интернет,веб,гугл,браузе,открой"):
            self._say("Запускаю браузер.")
            webbrowser.open("https://google.com")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "ютуб,youtube,видео,ютюб"):
            self._say("YouTube.")
            webbrowser.open("https://youtube.com")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "калькулятор,посчитать,калькул"):
            self._say("Калькулятор.")
            os.system("calc" if os.name == "nt" else "gnome-calculator &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "блокнот,notepad,заметки,блокно,записи,текст"):
            self._say("Блокнот.")
            os.system("notepad" if os.name == "nt" else "gedit &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "терминал,консоль,cmd,командная,термин"):
            self._say("Терминал.")
            os.system("start cmd" if os.name == "nt" else "gnome-terminal &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "проводник,файлы,папки,провод,файл"):
            self._say("Проводник.")
            os.system("explorer ." if os.name == "nt" else "nautilus . &")
            self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "диспетчер задач,процессы,диспетч"):
            self._say("Диспетчер задач.")
            os.system("taskmgr" if os.name == "nt" else "gnome-system-monitor &")
            self._beep(play_confirm_signal)
            return True
        
        # Время и дата
        if self._has(cmd, "время,который час,часы,сколько время"):
            self._tell_time()
            return True
        
        if self._has(cmd, "дата,число,сегодня,день,какое число"):
            self._tell_date()
            return True
        
        # Статистика
        if self._has(cmd, "статистика,стата,аптайм,сколько работаешь"):
            self._tell_stats()
            return True
        
        # Общение
        if self._has(cmd, "привет,здравствуй,хай,хелло,здарова,добрый"):
            h = datetime.datetime.now().hour
            g = "Доброй ночи" if h < 6 else "Доброе утро" if h < 12 else "Добрый день" if h < 18 else "Добрый вечер"
            self._say(f"{g}! Я Джарвис.")
            return True
        
        if self._has(cmd, "как дела,настроение,как ты,как жизнь"):
            self._say(self._r("status"))
            return True
        
        if self._has(cmd, "что ты умеешь,помощь,команды,справка,help,что можешь"):
            self._say("Могу открыть браузер, YouTube, калькулятор, блокнот, терминал, проводник. Сказать время и дату. Для выхода — «пока».")
            return True
        
        if self._has(cmd, "кто ты,имя,как зовут"):
            self._say("Я Джарвис — голосовой ассистент.")
            return True
        
        if self._has(cmd, "спасибо,благодарю,молодец,красава,отлично"):
            self._say(self._r("thanks"))
            return True
        
        if self._has(cmd, "шутка,анекдот,пошути,рассмеши"):
            jokes = [
                "31 октября = 25 декабря. Вот почему программисты путают Хэллоуин и Рождество.",
                "Сколько программистов вкрутят лампочку? Ни одного. Это hardware.",
                "Почему Python спокойный? Нет скобок.",
            ]
            self._say(random.choice(jokes))
            return True
        
        # Неизвестно
        print(f"  ↳ Не совпало ни с одной командой")
        self._say(self._r("unknown"))
        self._beep(play_error_signal)
        self.stats["errors"] += 1
        return True
    
    def _tell_time(self):
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        
        if 11 <= h % 100 <= 14: hw = "часов"
        elif h % 10 == 1: hw = "час"
        elif 2 <= h % 10 <= 4: hw = "часа"
        else: hw = "часов"
        
        if 11 <= m <= 14: mw = "минут"
        elif m % 10 == 1: mw = "минута"
        elif 2 <= m % 10 <= 4: mw = "минуты"
        else: mw = "минут"
        
        t = f"{h} {hw} ровно" if m == 0 else f"{h} {hw} {m} {mw}"
        self._say(f"Сейчас {t}.")
    
    def _tell_date(self):
        now = datetime.datetime.now()
        months = ["января","февраля","марта","апреля","мая","июня",
                  "июля","августа","сентября","октября","ноября","декабря"]
        wdays = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]
        self._say(f"Сегодня {wdays[now.weekday()]}, {now.day} {months[now.month-1]}.")
    
    def _tell_stats(self):
        up = datetime.datetime.now() - self.stats["start"]
        h = up.seconds // 3600
        m = (up.seconds % 3600) // 60
        self._say(f"Работаю {h} ч {m} мин. Команд: {self.stats['commands']}. Ошибок: {self.stats['errors']}.")
    
    # ============================================================
    # ЦИКЛ
    # ============================================================
    
    def run(self):
        if self.use_wake and self.wakeword:
            self._run_voice()
        else:
            self._run_manual()
    
    def _run_voice(self):
        self.wakeword.start_listening()
        self._say(f"Джарвис запущен. Скажите «Джарвис».")
        
        print(f"\n{'='*55}")
        print(f"  ГОЛОСОВОЙ РЕЖИМ (порог: {self.wake_threshold})")
        print(f"  Модель: {self.model_size} | {DEVICE.upper()}")
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
        print(f"  Модель: {self.model_size} | {DEVICE.upper()}")
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
    threshold = WAKE_WORD_THRESHOLD
    
    if use_wake:
        if not os.path.exists("models/джарвис_model.json"):
            print("\n  ! Модель не найдена. python train_wakeword.py")
            if input("  Ручной режим? [y/n]: ").lower() != 'y':
                return
            use_wake = False
        else:
            t = input(f"  Порог [Enter={WAKE_WORD_THRESHOLD}]: ").strip()
            if t:
                try:
                    threshold = max(0.3, min(0.95, float(t)))
                except:
                    pass
    
    print("\n  Модель: 1=tiny 2=base 3=small 4=medium")
    mc = input("  Выбор [Enter=4]: ").strip()
    models = {"1":"tiny","2":"base","3":"small","4":"medium"}
    model = models.get(mc, DEFAULT_MODEL_SIZE)
    
    jarvis = Jarvis(
        model_size=model,
        use_wake=use_wake,
        wake_threshold=threshold
    )
    jarvis.run()


if __name__ == "__main__":
    main()