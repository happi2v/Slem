# jarvis_core.py
"""
ДЖАРВИС — ГОЛОСОВОЙ АССИСТЕНТ
v32.0 — финальное ядро с GUI
"""
import os
import sys
import time
import datetime
import webbrowser
import random
import re
import subprocess
import glob

# ============================================================
# НАСТРОЙКИ
# ============================================================
WAKE_THRESHOLD = 0.35
MODEL_SIZE = "large-v3"
LLM_MODEL = "llama3.2:3b"
STEAM_PATH = r"C:\Program Files (x86)\Steam\Steam.exe"

# ============================================================
# ИМПОРТЫ
# ============================================================
print("=" * 55)
print("  ДЖАРВИС v32.0")
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
    from gui import GUI
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

try:
    import pyperclip
    CLIPBOARD_OK = True
except:
    CLIPBOARD_OK = False

KEYBOARD_OK = False
try:
    import keyboard
    KEYBOARD_OK = True
except:
    try:
        import pyautogui
        KEYBOARD_OK = True
    except:
        pass


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
        
        try:
            self.rec = VoiceRecognizer(model_size=model_size, device="auto", compute_type="auto")
        except:
            self.rec = VoiceRecognizer(model_size="medium", device="auto", compute_type="auto")
        
        print(f"  Whisper: {self.rec.info()['model']} | {self.rec.info()['device']}")
        
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
        
        self.gui = GUI(core=self) if ok.get('gui') else None
        
        self.p = {
            "greet": ["Да, сэр.", "Слушаю.", "К вашим услугам.", "Джарвис на связи.", "Готов."],
            "unknown": ["Не знаю такой команды.", "Не могу выполнить.", "Повторите."],
            "thanks": ["Пожалуйста.", "Рад помочь.", "Не стоит."],
            "bye": ["До свидания.", "Отключаюсь.", "Завершаю работу."]
        }
        
        print("  ✓ Готово\n")
    
    def _say(self, text):
        if self.gui: self.gui.set_speaking(True)
        self.speaker.speak_async(text)
    
    def _r(self, key):
        return random.choice(self.p.get(key, ["..."]))
    
    def _beep(self, func):
        try: func()
        except: pass
    
    def _has(self, text, words):
        for w in words.split(","):
            w = w.strip()
            if w in text: return True
            if len(w) >= 6 and w[:5] in text: return True
        return False
    
    def _num(self, text):
        m = re.search(r'\b(\d+)\b', text)
        return int(m.group(1)) if m else None
    
    def _discord_path(self):
        base = os.path.expanduser(r"~\AppData\Local\Discord")
        matches = glob.glob(os.path.join(base, "app-*", "Discord.exe"))
        return sorted(matches, reverse=True)[0] if matches else None
    
    def _run_exe(self, path):
        if path and os.path.exists(path):
            os.system(f'start "" "{path}"')
            return True
        return False
    
    def _site(self, name, url):
        webbrowser.open(url)
        self._beep(play_confirm_signal)
        print(f"  🌐 {name}")
    
    def _paste(self, text):
        if not CLIPBOARD_OK or not KEYBOARD_OK: return False
        try:
            pyperclip.copy(text)
            time.sleep(0.3)
            try: keyboard.press_and_release("ctrl+v")
            except: pyautogui.hotkey("ctrl", "v")
            return True
        except: return False
    
    def _on_wake(self):
        if not self.active:
            self.active = True
            self.stats["wakes"] += 1
            if self.gui: self.gui.set_listening(True)
            self._beep(play_listen_signal)
            print(f"\n{'='*40}\n🔔 {self._r('greet')}\n{'='*40}")
    
    def execute(self, command):
        if not command:
            self._say("Не расслышал.")
            return True
        
        cmd = command.lower().strip()
        self.stats["commands"] += 1
        print(f"📝 [{self.stats['commands']}] «{cmd}»")
        
        if self._sys(cmd): return self.running
        if self._write(cmd): return True
        if self.music and self._mus(cmd): return True
        if self.volume and self._vol(cmd): return True
        if self._apps(cmd): return True
        if self._search(cmd): return True
        if self._sites(cmd): return True
        if self._time(cmd): return True
        if self._talk(cmd): return True
        
        if self.llm:
            if self.gui: self.gui.set_speaking(True)
            answer = self.llm.ask(cmd)
            print(f"  🤖 {answer}")
            self._say(answer)
            return True
        
        self._say(self._r("unknown"))
        self._beep(play_error_signal)
        self.stats["errors"] += 1
        return True
    
    def _sys(self, cmd):
        if self._has(cmd, "выход,пока,отключись,выключись,стоп,хватит,завершение,закройся"):
            self._say(self._r("bye"))
            time.sleep(0.8)
            self.running = False
            return True
        if self._has(cmd, "спокойной ночи,спать"):
            self._say("Спокойной ночи.")
            time.sleep(0.8)
            self.running = False
            return True
        if self._has(cmd, "статистика,стата,аптайм,отчёт"):
            self._tell_stats()
            return True
        return False
    
    def _write(self, cmd):
        for p in ["напиши ", "запиши ", "напечатай ", "печатай ", "введи ", "текст ", "набрать "]:
            if cmd.startswith(p):
                t = cmd[len(p):].strip()
                if t: return self._do_write(t)
        for w in ["напиши", "запиши", "напечатай", "введи"]:
            if w in cmd:
                parts = cmd.split(w, 1)
                if len(parts) > 1 and parts[1].strip():
                    return self._do_write(parts[1].strip())
        return False
    
    def _do_write(self, text):
        print(f"  ✍️ {text}")
        os.system("start notepad" if os.name == "nt" else "gedit &")
        time.sleep(1.5)
        ok = self._paste(text)
        self._say("Готово." if ok else "Не получилось.")
        self._beep(play_confirm_signal)
        return True
    
    def _mus(self, cmd):
        if self._has(cmd, "музыку,музыка,музыке,музыкой,яндекс,яндекса,яндексе,музыки"):
            self._say("Открываю Яндекс Музыку.")
            self.music.open()
            self._beep(play_confirm_signal)
            return True
        if self._has(cmd, "пауза,стоп, pause,останови,поставь на паузу,приостанови,паузу"):
            self._say("Пауза."); self.music.play_pause(); return True
        if self._has(cmd, "продолжи,играй,плей, play,продолжи музыку,возобнови,дальше играй"):
            self._say("Продолжаю."); self.music.play_pause(); return True
        if self._has(cmd, "следующий,некст,вперёд,следующий трек,скип,дальше трек,следующая,переключи"):
            self._say("Следующий трек."); self.music.next_track(); return True
        if self._has(cmd, "предыдущий,назад,прошлый,предыдущий трек,назад трек,предыдущая,верни"):
            self._say("Предыдущий трек."); self.music.prev_track(); return True
        if self._has(cmd, "лайк,нравится, like,мне нравится,лайкни,лайк трек,сохрани"):
            self._say("Лайк."); self.music.like(); return True
        if self._has(cmd, "закрой музыку,выключи музыку,останови музыку,хватит музыки,выруби музыку"):
            self._say("Закрываю музыку."); self.music.close(); return True
        for p in ["включи ", "поставь ", "запусти "]:
            if cmd.startswith(p):
                q = cmd[len(p):].strip()
                skip = ["музыку", "музыка", "песню", "трек", "звук", "громкость", "громче", "тише",
                        "стим", "steam", "дискорд", "discord", "браузер", "ютуб", "блокнот",
                        "калькулятор", "терминал", "проводник"]
                if q and q not in skip:
                    self._say(f"Ищу {q}."); self.music.search(q); return True
        return False
    
    def _vol(self, cmd):
        if "громкость" in cmd:
            n = self._num(cmd)
            if n and 1 <= n <= 100:
                self.volume.set_volume(n)
                self._say(f"Громкость {n}.")
                return True
        
        for words, lvl, rsp in [
            (["максимальная", "максимум", "на всю", "полная", "сотка", "сто", "макс", "полную"], 100, "Максимальная."),
            (["громкая", "высокая", "сильно"], 80, "Громкая."),
            (["средняя", "половина", "половинку", "середина", "пятьдесят", "среднюю", "половину"], 50, "Средняя."),
            (["тихая", "низкая", "фон", "чуть", "тихо", "двадцать", "тихую"], 20, "Тихая."),
            (["минимальная", "минимум", "в ноль", "ноль", "мин", "минимальную"], 0, "Минимальная."),
        ]:
            if any(w in cmd for w in words):
                self.volume.set_volume(lvl); self._say(rsp); return True
        
        if self._has(cmd, "громче,погромче,прибавь,увеличь,повысь,вверх,плюс"):
            self._say(f"Громкость {self.volume.volume_up(10)}."); return True
        if self._has(cmd, "тише,потише,убавь,уменьши,понизь,вниз,минус"):
            self._say(f"Громкость {self.volume.volume_down(10)}."); return True
        if self._has(cmd, "выключи звук,без звука,мут,mute,отключи звук,заглуши,тишина"):
            self.volume.mute(); self._say("Звук выключен."); return True
        if self._has(cmd, "включи звук,верни звук,анмут,unmute,со звуком"):
            self.volume.mute(); self._say("Звук включён."); return True
        if self._has(cmd, "какая громкость,уровень громкости,сколько громкость,текущая,скажи громкость"):
            self._say(f"Громкость {self.volume.get_volume()} процентов."); return True
        return False
    
    def _apps(self, cmd):
        if self._has(cmd, "дискорд,discord,дискард,дискор,диска,дискордом,дискорда,дискорде"):
            self._say("Запускаю Discord.")
            path = self._discord_path()
            if path and self._run_exe(path): self._beep(play_confirm_signal)
            else: os.system("start discord:"); self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "стим,steam,игры,стимул,стимом,стиму,стиме,стима"):
            self._say("Запускаю Steam.")
            if self._run_exe(STEAM_PATH): self._beep(play_confirm_signal)
            else: os.system("start steam://open/main"); self._beep(play_confirm_signal)
            return True
        
        if self._has(cmd, "калькулятор,посчитать,кальк"):
            self._say("Калькулятор."); os.system("calc"); self._beep(play_confirm_signal); return True
        if self._has(cmd, "блокнот,notepad,заметки,текст,запись"):
            self._say("Блокнот."); os.system("start notepad"); self._beep(play_confirm_signal); return True
        if self._has(cmd, "терминал,консоль,cmd,командная"):
            self._say("Терминал."); os.system("start cmd"); self._beep(play_confirm_signal); return True
        if self._has(cmd, "проводник,файлы,папки,провод,эксплорер"):
            self._say("Проводник."); os.system("explorer ."); self._beep(play_confirm_signal); return True
        if self._has(cmd, "диспетчер задач,процессы,диспетч"):
            self._say("Диспетчер задач."); os.system("taskmgr"); self._beep(play_confirm_signal); return True
        return False
    
    def _search(self, cmd):
        for p in ["найди ", "поищи ", "загугли ", "погугли ", "найди в интернете ", "поищи в интернете ", "что такое ", "кто такой ", "что значит "]:
            if cmd.startswith(p):
                q = cmd[len(p):].strip()
                if q:
                    self._say(f"Ищу {q}.")
                    webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
                    self._beep(play_confirm_signal)
                    return True
        for e, u in [("гугл ", "https://www.google.com/search?q="), ("яндекс ", "https://ya.ru/search?text=")]:
            if cmd.startswith(e):
                q = cmd[len(e):].strip()
                if q:
                    self._say(f"Ищу {q}.")
                    webbrowser.open(u + q.replace(" ", "+"))
                    self._beep(play_confirm_signal)
                    return True
        return False
    
    def _sites(self, cmd):
        sites = {
            "браузер,интернет,веб,гугл,хром": ("Браузер", "https://google.com"),
            "ютуб,youtube,видео,ютюб": ("YouTube", "https://youtube.com"),
            "вк,вконтакте,vk,вконтакт": ("ВКонтакте", "https://vk.com"),
            "телеграм,telegram,тг,веб телеграм": ("Telegram", "https://web.telegram.org"),
            "github,гитхаб,гит хаб,гейтхаб": ("GitHub", "https://github.com"),
            "почта,gmail,мыло,почту,мейл,email": ("Почта", "https://mail.google.com"),
            "нетфликс,netflix,нетflix": ("Netflix", "https://netflix.com"),
            "твич,twitch,твичь,стрим": ("Twitch", "https://twitch.tv"),
            "чат,chatgpt,чат джипити,гпт,gpt,чаты": ("ChatGPT", "https://chat.openai.com"),
            "перевод,переводчик,translate,транслейт": ("Переводчик", "https://translate.google.com"),
            "карты,карта,навигатор,гугл карты,2гис,2gis": ("Карты", "https://maps.google.com"),
            "погода,прогноз,weather": ("Погода", "https://yandex.ru/pogoda"),
            "новости,news,новость": ("Новости", "https://news.google.com"),
            "реддит,reddit,редит": ("Reddit", "https://reddit.com"),
            "вики,википедия,wikipedia,википедию": ("Википедия", "https://wikipedia.org"),
            "одноклассники,ок,однокласники": ("Одноклассники", "https://ok.ru"),
            "авито,avito,авита": ("Авито", "https://avito.ru"),
            "озон,ozon,озоне": ("Ozon", "https://ozon.ru"),
            "вб,wb,вайлдберриз,wildberries": ("Wildberries", "https://wildberries.ru"),
            "яндекс,яндекса,яндексом,яша": ("Яндекс", "https://ya.ru"),
        }
        for words, (name, url) in sites.items():
            if self._has(cmd, words):
                self._say(f"Открываю {name}.")
                self._site(name, url)
                return True
        return False
    
    def _time(self, cmd):
        if self._has(cmd, "время,который час,часы,сколько время,тайм,время сейчас"):
            self._tell_time(); return True
        if self._has(cmd, "дата,число,сегодня,день,какое число,число сегодня,дата сегодня"):
            self._tell_date(); return True
        return False
    
    def _talk(self, cmd):
        if self._has(cmd, "привет,здравствуй,хай,хелло,добрый,здарова,салют"):
            h = datetime.datetime.now().hour
            g = "Доброй ночи" if h < 6 else "Доброе утро" if h < 12 else "Добрый день" if h < 18 else "Добрый вечер"
            self._say(f"{g}! Я Джарвис."); return True
        if self._has(cmd, "как дела,настроение,как ты,как жизнь,как сам"):
            self._say(random.choice(["Всё в норме.", "Работаю штатно.", "Готов к задачам.", "Отлично."])); return True
        if self._has(cmd, "что ты умеешь,помощь,команды,справка,help,что можешь"):
            self._say("Поиск, сайты, калькулятор, блокнот, терминал, проводник, Steam, Discord, музыка, громкость, время, дата. «пока» — выход."); return True
        if self._has(cmd, "кто ты,имя,как зовут,твоё имя"):
            self._say("Я Джарвис — голосовой ассистент."); return True
        if self._has(cmd, "спасибо,благодарю,молодец,красава,отлично,супер"):
            self._say(self._r("thanks")); return True
        if self._has(cmd, "шутка,анекдот,пошути,рассмеши,юмор"):
            self._say(random.choice(["31 октября = 25 декабря.", "Сколько программистов вкрутят лампочку? Ни одного.", "Почему Python спокойный? Нет скобок."])); return True
        return False
    
    def _tell_time(self):
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        hw = "часов" if 11 <= h % 100 <= 14 else "час" if h % 10 == 1 else "часа" if 2 <= h % 10 <= 4 else "часов"
        mw = "минут" if 11 <= m <= 14 else "минута" if m % 10 == 1 else "минуты" if 2 <= m % 10 <= 4 else "минут"
        self._say(f"Сейчас {h} {hw} {m} {mw}." if m > 0 else f"Сейчас {h} {hw} ровно.")
    
    def _tell_date(self):
        now = datetime.datetime.now()
        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        wdays = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]
        self._say(f"Сегодня {wdays[now.weekday()]}, {now.day} {months[now.month-1]}.")
    
    def _tell_stats(self):
        up = datetime.datetime.now() - self.stats["start"]
        h, m = up.seconds // 3600, (up.seconds % 3600) // 60
        self._say(f"Работаю {h} ч {m} мин. Команд: {self.stats['commands']}.")
    
    def run(self):
        if self.use_wake and self.wakeword:
            self._voice()
        else:
            self._manual()
        self._cleanup()
    
    def _voice(self):
        self.wakeword.start_listening()
        self._say("Джарвис запущен.")
        print(f"\n{'='*55}\n  ГОЛОСОВОЙ РЕЖИМ\n  Скажите «Джарвис»\n{'='*55}\n")
        try:
            while self.running:
                if self.active:
                    if self.gui: self.gui.set_listening(True)
                    cmd = self.rec.listen()
                    if self.gui: self.gui.set_listening(False)
                    if cmd: self.execute(cmd)
                    self.active = False
                    if self.running: print("💤 Жду «Джарвис»...")
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self._say("Завершение работы.")
    
    def _manual(self):
        self._say("Джарвис запущен. Нажмите Enter.")
        print(f"\n{'='*55}\n  РУЧНОЙ РЕЖИМ\n  Enter — команда | «пока» — выход\n{'='*55}\n")
        try:
            while self.running:
                try: input("▶ Enter...")
                except EOFError: break
                self.active = True
                self._beep(play_listen_signal)
                if self.gui: self.gui.set_listening(True)
                cmd = self.rec.listen()
                if self.gui: self.gui.set_listening(False)
                if cmd: self.execute(cmd)
                self.active = False
                print()
        except KeyboardInterrupt:
            self._say("Завершение работы.")
    
    def _cleanup(self):
        print("\nОчистка...")
        try: self.rec.close()
        except: pass
        if self.wakeword: self.wakeword.stop()
        if self.llm: self.llm.clear_history()
        if self.gui:
            self.gui.running = False
            try: self.gui.root.after(0, self.gui.root.destroy)
            except: pass
        print("✓ Джарвис отключён.")


def main():
    print(f"\n{'='*55}\n  ВЫБОР РЕЖИМА\n{'='*55}")
    print("  1 — Голосовая активация\n  2 — Ручная\n  3 — Выход")
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
    
    print("\n  Whisper: 1=tiny 2=base 3=small 4=medium 5=large")
    mc = input("  Выбор [Enter=5]: ").strip()
    models = {"1":"tiny","2":"base","3":"small","4":"medium","5":"large-v3"}
    model = models.get(mc, MODEL_SIZE)
    
    Jarvis(model_size=model, use_wake=use_wake, wake_threshold=threshold).run()


if __name__ == "__main__":
    main()