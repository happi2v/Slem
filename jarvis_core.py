# jarvis_core.py
"""
ДЖАРВИС — ГОЛОСОВОЙ АССИСТЕНТ
v10.0 — финальное ядро
"""
import os
import sys
import time
import datetime
import webbrowser
import random
import re

# ============================================================
# НАСТРОЙКИ
# ============================================================
WAKE_THRESHOLD = 0.35
MODEL_SIZE = "medium"
LLM_MODEL = "llama3.2:3b"

# ============================================================
# ИМПОРТЫ
# ============================================================
print("=" * 55)
print("  ДЖАРВИС v10.0")
print("=" * 55)
print("  Загрузка модулей...")

ok = {}

try:
    from stt import VoiceRecognizer
    ok['stt'] = True
    print("  ✓ STT")
except Exception as e:
    print(f"  ✗ STT: {e}")
    sys.exit(1)

try:
    from tts import VoiceSpeaker
    ok['tts'] = True
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

try:
    from wakeword import VoiceWakeWord
    ok['wake'] = True
    print("  ✓ Wake Word")
except Exception as e:
    ok['wake'] = False
    print(f"  ⚠ Wake Word: {e}")

try:
    from llm import LLM
    ok['llm'] = True
    print("  ✓ LLM")
except Exception as e:
    ok['llm'] = False
    print(f"  ⚠ LLM: {e}")

try:
    from gui import JarvisGUI
    ok['gui'] = True
    print("  ✓ GUI")
except Exception as e:
    ok['gui'] = False
    print(f"  ⚠ GUI: {e}")

try:
    from music import YandexMusic
    ok['music'] = True
    print("  ✓ Яндекс Музыка")
except Exception as e:
    ok['music'] = False
    print(f"  ⚠ Музыка: {e}")

try:
    from volume import VolumeControl
    ok['volume'] = True
    print("  ✓ Громкость")
except Exception as e:
    ok['volume'] = False
    print(f"  ⚠ Громкость: {e}")


# ============================================================
# ЯДРО
# ============================================================
class Jarvis:
    def __init__(self, model_size=MODEL_SIZE, use_wake=False, wake_threshold=WAKE_THRESHOLD):
        self.running = True
        self.active = False
        self.use_wake = use_wake and ok.get('wake', False)
        self.stats = {"commands": 0, "wakes": 0, "errors": 0, "start": datetime.datetime.now()}
        
        print(f"\n  Инициализация...")
        
        self.rec = VoiceRecognizer(model_size=model_size, device="auto", compute_type="auto")
        info = self.rec.info()
        print(f"  Whisper: {info['model']} | {info['device']}")
        
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        self.llm = LLM(model=LLM_MODEL) if ok.get('llm') else None
        
        self.wakeword = None
        if self.use_wake:
            self.wakeword = VoiceWakeWord(wake_word="джарвис", sensitivity=wake_threshold, debug=False)
            if self.wakeword.custom_model and 'threshold' in self.wakeword.custom_model:
                self.wakeword.custom_threshold = min(wake_threshold, self.wakeword.custom_model['threshold'])
            else:
                self.wakeword.custom_threshold = wake_threshold
            self.wakeword.on_detected(self._on_wake)
            if self.wakeword.custom_model is None:
                self.use_wake = False
            else:
                print(f"  Wake Word: порог {self.wakeword.custom_threshold:.3f}")
        
        self.music = YandexMusic() if ok.get('music') else None
        self.volume = VolumeControl() if ok.get('volume') else None
        
        self.gui = None
        if ok.get('gui'):
            try:
                self.gui = JarvisGUI(jarvis_core=self)
                self.gui.run_async()
            except:
                pass
        
        self.p = {
            "greet": ["Да, сэр.", "Слушаю.", "К вашим услугам.", "Джарвис на связи.", "Готов."],
            "unknown": ["Не знаю такой команды.", "Не могу выполнить.", "Повторите."],
            "thanks": ["Пожалуйста.", "Рад помочь.", "Не стоит."],
            "bye": ["До свидания.", "Отключаюсь.", "Завершаю работу."]
        }
        
        print("  ✓ Готово\n")
    
    def _say(self, text):
        self.speaker.speak_async(text)
    
    def _r(self, key):
        return random.choice(self.p.get(key, ["..."]))
    
    def _beep(self, func):
        try: func()
        except: pass
    
    def _has(self, text, words):
        for w in words.split(","):
            w = w.strip()
            if w in text:
                return True
            if len(w) >= 4 and w[:4] in text:
                return True
        return False
    
    def _extract_number(self, text):
        match = re.search(r'\b(\d+)\b', text)
        return int(match.group(1)) if match else None
    
    def _on_wake(self):
        if not self.active:
            self.active = True
            self.stats["wakes"] += 1
            self._beep(play_listen_signal)
            print(f"\n{'='*40}")
            print(f"🔔 {self._r('greet')}")
            print(f"{'='*40}")
    
    def execute(self, command):
        if not command:
            self._say("Не расслышал.")
            return True
        
        cmd = command.lower().strip()
        self.stats["commands"] += 1
        n = self.stats["commands"]
        print(f"📝 [{n}] «{cmd}»")
        
        if self._sys(cmd): return self.running
        if self.volume and self._vol(cmd): return True
        if self._apps(cmd): return True
        if self._time(cmd): return True
        if self.music and self._mus(cmd): return True
        if self._talk(cmd): return True
        
        if self.llm:
            print("  🤖 LLM...")
            answer = self.llm.ask(cmd)
            print(f"  Джарвис: {answer}")
            self._say(answer)
            return True
        
        self._say(self._r("unknown"))
        self._beep(play_error_signal)
        self.stats["errors"] += 1
        return True
    
    def _sys(self, cmd):
        if self._has(cmd, "выход,пока,отключись,выключись,стоп,хватит,завершение"):
            self._say(self._r("bye"))
            time.sleep(0.8)
            self.running = False
            return True
        if self._has(cmd, "спокойной ночи,спать"):
            self._say("Спокойной ночи.")
            time.sleep(0.8)
            self.running = False
            return True
        if self._has(cmd, "статистика,стата,аптайм"):
            self._tell_stats()
            return True
        return False
    
    def _vol(self, cmd):
        # Уровни
        if self._has(cmd, "максимальная,максимум,на всю,полная,сотка,сто"):
            self.volume.set_volume(100)
            self._say("Максимальная громкость.")
            return True
        if self._has(cmd, "средняя,половина,половинку,половину"):
            self.volume.set_volume(50)
            self._say("Средняя громкость.")
            return True
        if self._has(cmd, "минимальная,минимум,в ноль,ноль"):
            self.volume.set_volume(0)
            self._say("Минимальная громкость.")
            return True
        
        # Относительные
        if self._has(cmd, "громче,погромче,прибавь громкость,увеличь громкость"):
            vol = self.volume.volume_up(10)
            self._say(f"Громкость {vol}.")
            return True
        if self._has(cmd, "тише,потише,убавь громкость,уменьши громкость"):
            vol = self.volume.volume_down(10)
            self._say(f"Громкость {vol}.")
            return True
        
        # Mute
        if self._has(cmd, "выключи звук,без звука,мут,mute,отключи звук,заглуши"):
            self.volume.mute()
            self._say("Звук выключен.")
            return True
        if self._has(cmd, "включи звук,верни звук,анмут,unmute,включи обратно,отключи мут"):
            self.volume.mute()
            self._say("Звук включён.")
            return True
        
        # Инфо
        if self._has(cmd, "какая громкость,уровень громкости,сколько громкость,громкость сейчас"):
            vol = self.volume.get_volume()
            self._say(f"Текущая громкость {vol} процентов.")
            return True
        
        # Конкретное число: только если "громкость" + число
        if ("громкость" in cmd or "громкости" in cmd):
            num = self._extract_number(cmd)
            if num is not None and 1 <= num <= 100:
                self.volume.set_volume(num)
                self._say(f"Громкость {num} процентов.")
                return True
        
        return False
    
    def _apps(self, cmd):
        if self._has(cmd, "браузер,интернет,веб,гугл"):
            self._say("Запускаю браузер.")
            webbrowser.open("https://google.com")
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "ютуб,youtube,видео"):
            self._say("Открываю YouTube.")
            webbrowser.open("https://youtube.com")
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "калькулятор,посчитать"):
            self._say("Калькулятор.")
            os.system("calc" if os.name == "nt" else "gnome-calculator &")
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "блокнот,notepad,заметки,текст"):
            self._say("Блокнот.")
            os.system("notepad" if os.name == "nt" else "gedit &")
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "терминал,консоль,cmd"):
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
        return False
    
    def _time(self, cmd):
        if self._has(cmd, "время,который час,часы,сколько время"):
            self._tell_time()
            return True
        if self._has(cmd, "дата,число,сегодня,день,какое число"):
            self._tell_date()
            return True
        return False
    
    def _mus(self, cmd):
        if self._has(cmd, "включи музыку,открой музыку,яндекс музыка,запусти музыку"):
            self._say("Открываю Яндекс Музыку.")
            self.music.open()
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "пауза,стоп, pause,останови музыку,поставь на паузу"):
            self._say("Пауза.")
            self.music.play_pause()
            return True
        if self._has(cmd, "продолжи,играй,плей, play,продолжи музыку"):
            self._say("Продолжаю.")
            self.music.play_pause()
            return True
        if self._has(cmd, "следующий,некст,вперёд,следующий трек,скип,дальше"):
            self._say("Следующий трек.")
            self.music.next_track()
            return True
        if self._has(cmd, "предыдущий,назад,прошлый,предыдущий трек"):
            self._say("Предыдущий трек.")
            self.music.prev_track()
            return True
        if self._has(cmd, "лайк,нравится, like,мне нравится"):
            self._say("Лайк.")
            self.music.like()
            return True
        if self._has(cmd, "закрой музыку,выключи музыку"):
            self._say("Закрываю музыку.")
            self.music.close()
            return True
        
        for prefix in ["включи ", "поставь ", "запусти "]:
            if cmd.startswith(prefix):
                query = cmd[len(prefix):].strip()
                if query and query not in ["музыку", "музыка", "песню", "трек", "звук"]:
                    self._say(f"Ищу {query}.")
                    self.music.search(query)
                    return True
        return False
    
    def _talk(self, cmd):
        if self._has(cmd, "привет,здравствуй,хай,хелло,добрый"):
            h = datetime.datetime.now().hour
            if h < 6: g = "Доброй ночи"
            elif h < 12: g = "Доброе утро"
            elif h < 18: g = "Добрый день"
            else: g = "Добрый вечер"
            self._say(f"{g}! Я Джарвис.")
            return True
        if self._has(cmd, "как дела,настроение,как ты,как жизнь"):
            self._say(random.choice(["Всё в норме.", "Работаю штатно.", "Готов к задачам.", "Отлично."]))
            return True
        if self._has(cmd, "что ты умеешь,помощь,команды,справка,help"):
            self._say("Браузер, YouTube, калькулятор, блокнот, терминал, проводник, музыка, громкость, время, дата. «пока» — выход.")
            return True
        if self._has(cmd, "кто ты,имя,как зовут"):
            self._say("Я Джарвис — голосовой ассистент.")
            return True
        if self._has(cmd, "спасибо,благодарю,молодец,красава"):
            self._say(self._r("thanks"))
            return True
        if self._has(cmd, "шутка,анекдот,пошути,рассмеши"):
            jokes = [
                "31 октября = 25 декабря. Программисты путают Хэллоуин и Рождество.",
                "Сколько программистов вкрутят лампочку? Ни одного. Это hardware.",
                "Почему Python спокойный? Нет скобок.",
                "Программист ставит будильник. Просыпается. Ложится. Это рекурсия.",
            ]
            self._say(random.choice(jokes))
            return True
        return False
    
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
        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        wdays = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]
        self._say(f"Сегодня {wdays[now.weekday()]}, {now.day} {months[now.month-1]}.")
    
    def _tell_stats(self):
        up = datetime.datetime.now() - self.stats["start"]
        h, m = up.seconds // 3600, (up.seconds % 3600) // 60
        info = self.rec.info()
        self._say(f"Работаю {h} ч {m} мин. Команд: {self.stats['commands']}. Whisper на {info['device']}.")
    
    def run(self):
        if self.use_wake and self.wakeword:
            self._run_voice()
        else:
            self._run_manual()
        self._cleanup()
    
    def _run_voice(self):
        self.wakeword.start_listening()
        self._say("Джарвис запущен.")
        
        print(f"\n{'='*55}")
        print(f"  ГОЛОСОВОЙ РЕЖИМ")
        mods = []
        if self.llm: mods.append("LLM")
        if self.music: mods.append("Музыка")
        if self.volume: mods.append("Громкость")
        if mods: print(f"  {' • '.join(mods)}")
        print(f"  Скажите «Джарвис»")
        print(f"{'='*55}\n")
        
        try:
            while self.running:
                if self.active:
                    cmd = self.rec.listen()
                    if cmd: self.execute(cmd)
                    self.active = False
                    if self.running: print("💤 Жду «Джарвис»...")
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nЗавершение...")
            self._say("Завершение работы.")
    
    def _run_manual(self):
        self._say("Джарвис запущен. Нажмите Enter.")
        
        print(f"\n{'='*55}")
        print(f"  РУЧНОЙ РЕЖИМ")
        print(f"  Enter — команда | «пока» — выход")
        print(f"{'='*55}\n")
        
        try:
            while self.running:
                try: input("▶ Enter...")
                except EOFError: break
                
                self.active = True
                self._beep(play_listen_signal)
                print("🎤 Говорите...")
                
                cmd = self.rec.listen()
                if cmd: self.execute(cmd)
                self.active = False
                print()
        except KeyboardInterrupt:
            print("\nЗавершение...")
            self._say("Завершение работы.")
    
    def _cleanup(self):
        print("\nОчистка...")
        try: self.rec.close()
        except: pass
        if self.wakeword:
            try: self.wakeword.stop()
            except: pass
        if self.llm: self.llm.clear_history()
        if self.gui and self.gui.tray_icon:
            try: self.gui.tray_icon.stop()
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
    except: return
    
    if c == "3": return
    
    use_wake = (c == "1")
    threshold = WAKE_THRESHOLD
    
    if use_wake:
        if not os.path.exists("models/джарвис_model.json"):
            print("\n  ! Модель не найдена.")
            if input("  Ручной режим? [y/n]: ").lower() != 'y': return
            use_wake = False
        else:
            t = input(f"  Порог [Enter={WAKE_THRESHOLD}]: ").strip()
            if t:
                try: threshold = max(0.2, min(0.95, float(t)))
                except: pass
    
    print("\n  Whisper: 1=tiny 2=base 3=small 4=medium")
    mc = input("  Выбор [Enter=4]: ").strip()
    models = {"1":"tiny","2":"base","3":"small","4":"medium"}
    model = models.get(mc, MODEL_SIZE)
    
    jarvis = Jarvis(model_size=model, use_wake=use_wake, wake_threshold=threshold)
    jarvis.run()


if __name__ == "__main__":
    main()