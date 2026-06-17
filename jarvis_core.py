# jarvis_core.py
"""
ДЖАРВИС - ГОЛОСОВОЙ АССИСТЕНТ
Ядро системы с поддержкой GPU и настраиваемым порогом активации
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
WAKE_WORD_THRESHOLD = 0.7      # Порог голосовой активации (0.0 - 1.0)
DEFAULT_MODEL_SIZE = "medium"   # Размер модели Whisper по умолчанию

# ============================================================
# ИМПОРТ МОДУЛЕЙ С ПРОВЕРКОЙ
# ============================================================
print("=" * 60)
print("  ДЖАРВИС v2.1 — ЗАПУСК ЯДРА")
print("=" * 60)

# Проверка GPU
print("\n--- Проверка оборудования ---")
GPU_AVAILABLE = False
try:
    import torch
    if torch.cuda.is_available():
        GPU_AVAILABLE = True
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✓ Видеокарта обнаружена: {gpu_name} ({gpu_memory:.1f} ГБ)")
    else:
        print("ℹ Видеокарта NVIDIA не найдена. Будет использоваться CPU.")
except ImportError:
    print("ℹ PyTorch не установлен. Будет использоваться CPU.")
except Exception as e:
    print(f"ℹ Ошибка проверки GPU: {e}")

# 1. Распознавание речи
print("\n[1/4] Загрузка модуля распознавания речи...")
try:
    from stt import VoiceRecognizer
    print("  ✓ VoiceRecognizer готов")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")
    sys.exit(1)

# 2. Синтез речи
print("[2/4] Загрузка модуля синтеза речи...")
try:
    from tts import VoiceSpeaker
    print("  ✓ VoiceSpeaker готов")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")
    sys.exit(1)

# 3. Звуковые сигналы
print("[3/4] Загрузка звуковых сигналов...")
try:
    from sounds import play_listen_signal, play_confirm_signal, play_error_signal
    print("  ✓ Sounds готов")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")
    def play_listen_signal(): pass
    def play_confirm_signal(): pass
    def play_error_signal(): pass
    print("  ⚠ Использую заглушки")

# 4. Wake Word
print("[4/4] Загрузка модуля голосовой активации...")
WAKE_WORD_AVAILABLE = False
try:
    from wakeword import VoiceWakeWord
    WAKE_WORD_AVAILABLE = True
    print("  ✓ VoiceWakeWord готов")
except Exception as e:
    print(f"  ⚠ Модуль недоступен: {e}")
    print("  Будет использоваться активация по клавише Enter")


# ============================================================
# КЛАСС ЯДРА
# ============================================================
class JarvisCore:
    """Главный класс голосового ассистента с поддержкой GPU."""
    
    def __init__(self, model_size=DEFAULT_MODEL_SIZE, use_wake_word=False, 
                 wake_threshold=WAKE_WORD_THRESHOLD, debug_wake=False):
        """
        Инициализация Джарвиса.
        
        Параметры:
        - model_size: размер модели Whisper
        - use_wake_word: использовать голосовую активацию
        - wake_threshold: порог срабатывания Wake Word (0.0 - 1.0)
        - debug_wake: режим отладки Wake Word
        """
        print("\n--- Инициализация ядра ---")
        
        # Настройки
        self.wake_threshold = wake_threshold
        self.model_size = model_size
        
        # Определяем устройство для инференса
        if GPU_AVAILABLE:
            self.device = "cuda"
            self.compute_type = "float16"
            print(f"🚀 Использую GPU: {torch.cuda.get_device_name(0)}")
        else:
            self.device = "cpu"
            self.compute_type = "int8"
            print("💻 Использую CPU")
        
        # Распознаватель речи
        print(f"Загружаю модель Whisper '{model_size}'...")
        self.recognizer = VoiceRecognizer(
            model_size=model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        
        # Синтезатор речи
        print("Инициализирую синтезатор речи...")
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        
        # Состояние
        self.is_active = False
        self.running = True
        self.use_wake_word = use_wake_word and WAKE_WORD_AVAILABLE
        
        # Статистика
        self.stats = {
            "commands_processed": 0,
            "wake_word_detections": 0,
            "errors": 0,
            "start_time": datetime.datetime.now()
        }
        
        # Wake Word детектор
        self.wakeword = None
        if self.use_wake_word:
            print(f"Инициализирую голосовую активацию (порог: {self.wake_threshold})...")
            try:
                self.wakeword = VoiceWakeWord(
                    wake_word="джарвис",
                    sensitivity=self.wake_threshold,
                    debug=debug_wake
                )
                # Принудительно устанавливаем порог
                self.wakeword.custom_threshold = self.wake_threshold
                self.wakeword.sensitivity = self.wake_threshold
                
                self.wakeword.on_detected(self._on_wake_word)
                
                if self.wakeword.custom_model is None:
                    print("  ⚠ Модель голоса не обучена!")
                    print("  Запустите: python train_wakeword.py")
                    self.use_wake_word = False
                else:
                    print(f"  ✓ Модель загружена")
                    print(f"  ✓ Порог активации: {self.wake_threshold}")
            except Exception as e:
                print(f"  ✗ Ошибка: {e}")
                self.use_wake_word = False
        
        # База ответов
        self._init_responses()
        
        print("✓ Ядро инициализировано успешно\n")
    
    def _init_responses(self):
        """Инициализирует базу фраз для ответов."""
        self.greetings = [
            "Да, сэр.",
            "Слушаю вас.",
            "Весь во внимании.",
            "К вашим услугам.",
            "Джарвис на связи.",
            "Готов к работе.",
            "Чем могу помочь?",
            "Да, я здесь."
        ]
        
        self.unknown_responses = [
            "Извините, я не знаю такой команды.",
            "Не могу выполнить это действие.",
            "Команда не распознана. Попробуйте 'помощь'.",
            "Я пока не умею этого делать.",
            "Этого нет в моих возможностях."
        ]
        
        self.thanks_responses = [
            "Всегда пожалуйста.",
            "Рад помочь.",
            "К вашим услугам.",
            "Не стоит благодарности.",
            "Обращайтесь."
        ]
        
        self.how_are_you_responses = [
            "Все системы функционируют нормально.",
            "Отлично. Процессор почти не загружен.",
            "Работаю в штатном режиме. Жду указаний.",
            "Лучше всех. Я же искусственный интеллект.",
            "Все показатели в норме."
        ]
    
    # ============================================================
    # ОБРАБОТЧИКИ СОБЫТИЙ
    # ============================================================
    
    def _on_wake_word(self):
        """Callback при обнаружении Wake Word."""
        if not self.is_active:
            self.is_active = True
            self.stats["wake_word_detections"] += 1
            threading = __import__('threading')
            t = threading.Thread(target=self._greet, daemon=True)
            t.start()
    
    def _greet(self):
        """Приветствие при активации."""
        try:
            play_listen_signal()
        except:
            pass
        greeting = random.choice(self.greetings)
        print(f"\n{'='*40}")
        print(f"🔔 {greeting}")
        print(f"{'='*40}")
    
    def activate_manual(self):
        """Ручная активация (по Enter)."""
        self.is_active = True
        self._greet()
    
    def deactivate(self):
        """Деактивация после выполнения команды."""
        self.is_active = False
    
    # ============================================================
    # ВЫПОЛНЕНИЕ КОМАНД
    # ============================================================
    
    def execute_command(self, command):
        """
        Анализирует и выполняет голосовую команду.
        Возвращает False если нужно завершить работу.
        """
        if not command:
            self.speaker.speak_async("Я ничего не услышал. Повторите.")
            return True
        
        cmd = command.lower().strip()
        self.stats["commands_processed"] += 1
        print(f"📝 [{self.stats['commands_processed']}] Распознано: \"{cmd}\"")
        
        # --- ЗАВЕРШЕНИЕ РАБОТЫ ---
        
        if self._match(cmd, ["выход", "пока", "отключись", "завершение", 
                             "выключись", "стоп", "хватит", "закройся"]):
            farewell = random.choice([
                "Завершаю работу. До свидания.",
                "Отключаюсь. Хорошего дня.",
                "До встречи. Буду ждать.",
                "Работа завершена."
            ])
            self.speaker.speak_async(farewell)
            time.sleep(1)
            return False
        
        if self._match(cmd, ["спокойной ночи", "режим сна", "спать"]):
            self.speaker.speak_async("Спокойной ночи. Отключаю системы.")
            time.sleep(1)
            return False
        
        # --- ЗАПУСК ПРИЛОЖЕНИЙ ---
        
        if self._match(cmd, ["браузер", "интернет", "веб", "гугл", 
                             "открой браузер", "запусти браузер"]):
            self.speaker.speak_async("Запускаю браузер.")
            webbrowser.open("https://google.com")
            self._confirm()
            return True
        
        if self._match(cmd, ["ютуб", "youtube", "видео"]):
            self.speaker.speak_async("Открываю YouTube.")
            webbrowser.open("https://youtube.com")
            self._confirm()
            return True
        
        if self._match(cmd, ["калькулятор", "посчитать", "вычисления"]):
            self.speaker.speak_async("Открываю калькулятор.")
            os.system("calc" if os.name == "nt" else "gnome-calculator &")
            self._confirm()
            return True
        
        if self._match(cmd, ["блокнот", "notepad", "заметки", "текстовый редактор"]):
            self.speaker.speak_async("Запускаю блокнот.")
            os.system("notepad" if os.name == "nt" else "gedit &")
            self._confirm()
            return True
        
        if self._match(cmd, ["терминал", "консоль", "командная строка", "cmd"]):
            self.speaker.speak_async("Открываю терминал.")
            os.system("start cmd" if os.name == "nt" else "gnome-terminal &")
            self._confirm()
            return True
        
        if self._match(cmd, ["проводник", "файлы", "папки", "explorer"]):
            self.speaker.speak_async("Открываю проводник.")
            os.system("explorer ." if os.name == "nt" else "nautilus . &")
            self._confirm()
            return True
        
        if self._match(cmd, ["диспетчер задач", "процессы"]):
            self.speaker.speak_async("Открываю диспетчер задач.")
            os.system("taskmgr" if os.name == "nt" else "gnome-system-monitor &")
            self._confirm()
            return True
        
        # --- ВРЕМЯ И ДАТА ---
        
        if self._match(cmd, ["время", "который час", "сколько времени", "часы", "тайм"]):
            self._tell_time()
            return True
        
        if self._match(cmd, ["дата", "число", "какой сегодня день", "сегодня", "день"]):
            self._tell_date()
            return True
        
        if self._match(cmd, ["день недели", "какой день"]):
            now = datetime.datetime.now()
            weekdays = ["понедельник", "вторник", "среда", 
                       "четверг", "пятница", "суббота", "воскресенье"]
            self.speaker.speak_async(f"Сегодня {weekdays[now.weekday()]}.")
            return True
        
        # --- СТАТИСТИКА ДЖАРВИСА ---
        
        if self._match(cmd, ["статистика", "стата", "аптайм", "сколько работаешь"]):
            self._tell_stats()
            return True
        
        # --- ОБЩЕНИЕ ---
        
        if self._match(cmd, ["привет", "здравствуй", "хай", "хелло", "здарова"]):
            self._greeting_response()
            return True
        
        if self._match(cmd, ["как дела", "как настроение", "как жизнь", "как ты", "чё как"]):
            self.speaker.speak_async(random.choice(self.how_are_you_responses))
            return True
        
        if self._match(cmd, ["что ты умеешь", "помощь", "команды", "справка", 
                             "возможности", "хелп", "help"]):
            self._show_help()
            return True
        
        if self._match(cmd, ["кто ты", "ты кто", "как тебя зовут", "твоё имя", "имя"]):
            self.speaker.speak_async(
                "Я Джарвис — голосовой ассистент. "
                "Создан помогать с повседневными задачами на компьютере."
            )
            return True
        
        if self._match(cmd, ["кто тебя создал", "создатель", "разработчик"]):
            self.speaker.speak_async("Меня создал талантливый разработчик. Это вы, сэр.")
            return True
        
        if self._match(cmd, ["спасибо", "благодарю", "отлично", "хорошо", "красава", "молодец"]):
            self.speaker.speak_async(random.choice(self.thanks_responses))
            return True
        
        if self._match(cmd, ["шутка", "анекдот", "пошути", "рассмеши"]):
            self._tell_joke()
            return True
        
        if self._match(cmd, ["погода", "прогноз"]):
            self.speaker.speak_async("Извините, модуль погоды ещё не подключён. Но за окном наверняка что-то происходит.")
            return True
        
        # --- НЕИЗВЕСТНАЯ КОМАНДА ---
        
        self.speaker.speak_async(random.choice(self.unknown_responses))
        try:
            play_error_signal()
        except:
            pass
        self.stats["errors"] += 1
        return True
    
    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================
    
    def _match(self, text, keywords):
        """Проверяет, содержит ли текст любое из ключевых слов."""
        return any(kw in text for kw in keywords)
    
    def _confirm(self):
        """Звуковой сигнал подтверждения."""
        try:
            play_confirm_signal()
        except:
            pass
    
    def _tell_time(self):
        """Сообщает текущее время с правильным склонением."""
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        
        # Склонение часов
        if 11 <= h % 100 <= 14:
            hour_word = "часов"
        elif h % 10 == 1:
            hour_word = "час"
        elif 2 <= h % 10 <= 4:
            hour_word = "часа"
        else:
            hour_word = "часов"
        
        # Формируем строку
        if m == 0:
            time_str = f"{h} {hour_word} ровно"
        elif m == 30:
            next_h = h + 1 if h < 23 else 0
            time_str = f"половина {next_h}-го"
        elif m == 15:
            time_str = f"четверть {h + 1 if h < 23 else 0}-го" if m == 45 else f"четверть {h}-го" if m == 15 else ""
        else:
            # Склонение минут
            if 11 <= m <= 14:
                min_word = "минут"
            elif m % 10 == 1:
                min_word = "минута"
            elif 2 <= m % 10 <= 4:
                min_word = "минуты"
            else:
                min_word = "минут"
            time_str = f"{h} {hour_word} {m} {min_word}"
        
        self.speaker.speak_async(f"Сейчас {time_str}.")
    
    def _tell_date(self):
        """Сообщает текущую дату."""
        now = datetime.datetime.now()
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        weekdays = [
            "понедельник", "вторник", "среда",
            "четверг", "пятница", "суббота", "воскресенье"
        ]
        self.speaker.speak_async(
            f"Сегодня {weekdays[now.weekday()]}, "
            f"{now.day} {months[now.month - 1]} {now.year} года."
        )
    
    def _tell_stats(self):
        """Сообщает статистику работы."""
        uptime = datetime.datetime.now() - self.stats["start_time"]
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        stats_text = (
            f"Статистика Джарвиса: "
            f"работаю {hours} часов {minutes} минут. "
            f"Обработано команд: {self.stats['commands_processed']}. "
            f"Обнаружений Wake Word: {self.stats['wake_word_detections']}. "
            f"Ошибок: {self.stats['errors']}. "
            f"Модель: {self.model_size}. "
            f"Устройство: {'GPU' if GPU_AVAILABLE else 'CPU'}."
        )
        self.speaker.speak_async(stats_text)
    
    def _greeting_response(self):
        """Ответ на приветствие с учётом времени суток."""
        hour = datetime.datetime.now().hour
        if hour < 6:
            greeting = "Доброй ночи"
        elif hour < 12:
            greeting = "Доброе утро"
        elif hour < 18:
            greeting = "Добрый день"
        else:
            greeting = "Добрый вечер"
        self.speaker.speak_async(f"{greeting}! Я Джарвис. Чем могу помочь?")
    
    def _show_help(self):
        """Показывает список доступных команд."""
        help_text = (
            "Я могу выполнять следующие команды: "
            "открыть браузер, YouTube, калькулятор, блокнот, "
            "терминал, проводник, диспетчер задач. "
            "Сообщить время, дату, день недели. "
            "Рассказать статистику работы. "
            "Ответить на приветствие и простые вопросы. "
            "Рассказать шутку. "
            "Для выхода скажите 'пока' или 'отключись'."
        )
        self.speaker.speak_async(help_text)
    
    def _tell_joke(self):
        """Рассказывает случайную шутку."""
        jokes = [
            "Почему программисты путают Хэллоуин и Рождество? Потому что 31 октября — это 25 декабря.",
            "Сколько программистов нужно, чтобы вкрутить лампочку? Ни одного. Это проблема оборудования.",
            "Идёт медведь по лесу. Видит — машина горит. Сел в неё и сгорел.",
            "Почему у программистов нет друзей? Потому что они всё время находят ошибки в людях.",
            "Что говорит один бит другому? У нас всё по байтам.",
            "Почему Python такой спокойный? Потому что у него нет скобок.",
            "Жена отправляет мужа-программиста в магазин: — Купи батон. Если будут яйца — возьми десяток. Муж возвращается с десятью батонами. — Ты зачем столько? — Так яйца были!",
            "Программист ставит будильник. Просыпается. Ложится спать. Опять ставит будильник. Это называется рекурсия.",
        ]
        self.speaker.speak_async(random.choice(jokes))
    
    # ============================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ============================================================
    
    def run(self):
        """Запускает главный цикл ассистента."""
        if self.use_wake_word and self.wakeword:
            self._run_voice_mode()
        else:
            self._run_manual_mode()
    
    def _run_voice_mode(self):
        """Режим с голосовой активацией."""
        print("Запуск фонового прослушивания...")
        self.wakeword.start_listening()
        
        self.speaker.speak(
            f"Джарвис активирован. Порог срабатывания: {self.wake_threshold}. "
            "Скажите 'Джарвис' для вызова."
        )
        
        print("\n" + "=" * 60)
        print(f"  РЕЖИМ ГОЛОСОВОЙ АКТИВАЦИИ (порог: {self.wake_threshold})")
        print(f"  Устройство: {'GPU' if GPU_AVAILABLE else 'CPU'}")
        print(f"  Модель: {self.model_size}")
        print("  Скажите 'Джарвис' — я отвечу")
        print("  'помощь' — список команд")
        print("  'статистика' — информация о работе")
        print("  Ctrl+C для выхода")
        print("=" * 60 + "\n")
        
        try:
            while self.running:
                if self.is_active:
                    command = self.recognizer.listen_for_command(play_signal=False)
                    if command:
                        self.running = self.execute_command(command)
                    self.deactivate()
                    if self.running:
                        print(f"💤 Ожидаю 'Джарвис'... (порог: {self.wake_threshold})")
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            self.speaker.speak("Принудительное завершение.")
        except Exception as e:
            print(f"\nОшибка в главном цикле: {e}")
            traceback.print_exc()
            self.stats["errors"] += 1
        finally:
            self._cleanup()
    
    def _run_manual_mode(self):
        """Режим с активацией по клавише Enter."""
        self.speaker.speak("Джарвис запущен в ручном режиме. Нажмите Enter для активации.")
        
        print("\n" + "=" * 60)
        print("  РУЧНОЙ РЕЖИМ")
        print(f"  Устройство: {'GPU' if GPU_AVAILABLE else 'CPU'}")
        print(f"  Модель: {self.model_size}")
        print("  Нажмите Enter → говорите команду")
        print("  'помощь' — список команд")
        print("  'пока' или 'выход' — завершение")
        print("  Ctrl+C для экстренного выхода")
        print("=" * 60 + "\n")
        
        try:
            while self.running:
                try:
                    input("▶ Нажмите Enter для команды...")
                except EOFError:
                    break
                    
                self.activate_manual()
                
                command = self.recognizer.listen_for_command(play_signal=False)
                if command:
                    self.running = self.execute_command(command)
                
                self.deactivate()
                print()
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            self.speaker.speak("Принудительное завершение.")
        except Exception as e:
            print(f"\nОшибка в главном цикле: {e}")
            traceback.print_exc()
            self.stats["errors"] += 1
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Очистка ресурсов при завершении."""
        print("\nОчистка ресурсов...")
        
        # Показываем итоговую статистику
        uptime = datetime.datetime.now() - self.stats["start_time"]
        print(f"  Время работы: {uptime}")
        print(f"  Команд обработано: {self.stats['commands_processed']}")
        print(f"  Обнаружений Wake Word: {self.stats['wake_word_detections']}")
        print(f"  Ошибок: {self.stats['errors']}")
        
        # Освобождаем ресурсы
        try:
            self.recognizer.close()
        except:
            pass
        try:
            if self.wakeword:
                self.wakeword.stop()
        except:
            pass
        
        # Очистка GPU памяти
        if GPU_AVAILABLE:
            try:
                import torch
                torch.cuda.empty_cache()
                print("  ✓ Память GPU очищена")
            except:
                pass
        
        print("✓ Джарвис отключён. До встречи!")


# ============================================================
# ТОЧКА ВХОДА
# ============================================================
def main():
    """Главная функция — запуск ассистента."""
    print("\n" + "=" * 60)
    print("  ДЖАРВИС — НАСТРОЙКА ЗАПУСКА")
    print("=" * 60)
    
    print("\nВыберите режим активации:")
    print("  1 — Голосовая (скажите 'Джарвис')")
    print("  2 — Ручная (нажмите Enter)")
    print("  3 — Выход")
    
    try:
        choice = input("\nВаш выбор [1-3]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nВыход.")
        return
    
    if choice == "3":
        print("До свидания!")
        return
    
    use_wake = (choice == "1")
    
    # Проверяем модель для голосовой активации
    if use_wake:
        model_path = "models/джарвис_model.json"
        if not os.path.exists(model_path):
            print("\n" + "!" * 60)
            print("  Модель голосовой активации не найдена!")
            print(f"  Ожидается: {model_path}")
            print("  Сначала запустите обучение:")
            print("    python train_wakeword.py")
            print("!" * 60)
            
            fallback = input("\nЗапустить в ручном режиме? [y/n]: ").strip().lower()
            if fallback != 'y':
                return
            use_wake = False
    
    # Порог активации (только для голосового режима)
    wake_threshold = WAKE_WORD_THRESHOLD
    if use_wake:
        print(f"\nТекущий порог активации: {WAKE_WORD_THRESHOLD}")
        custom_threshold = input(
            "Введите новый порог (0.3-0.95) или Enter для стандартного: "
        ).strip()
        if custom_threshold:
            try:
                wake_threshold = float(custom_threshold)
                wake_threshold = max(0.1, min(0.95, wake_threshold))
            except ValueError:
                print(f"Неверное значение. Использую {WAKE_WORD_THRESHOLD}")
    
    # Выбор модели распознавания
    print("\nМодель распознавания речи:")
    print("  1 — tiny   (самая быстрая)")
    print("  2 — base   (быстрая)")
    print("  3 — small  (сбалансированная)")
    print("  4 — medium (высокая точность) [рекомендуется]")
    if GPU_AVAILABLE:
        print("  5 — large  (максимальная, требует GPU)")
    
    model_choice = input(f"\nВыбор [1-5, по умолчанию 4]: ").strip()
    models = {
        "1": "tiny", "2": "base", "3": "small", 
        "4": "medium", "5": "large-v3"
    }
    model_size = models.get(model_choice, DEFAULT_MODEL_SIZE)
    
    # Итоговая информация
    print("\n" + "=" * 60)
    print("  НАСТРОЙКИ ЗАПУСКА")
    print("=" * 60)
    print(f"  Режим активации: {'Голосовой' if use_wake else 'Ручной'}")
    if use_wake:
        print(f"  Порог Wake Word: {wake_threshold}")
    print(f"  Модель Whisper: {model_size}")
    print(f"  Устройство: {'GPU' if GPU_AVAILABLE else 'CPU'}")
    print("=" * 60)
    
    input("\nНажмите Enter для запуска...")
    
    # Запускаем ядро
    try:
        jarvis = JarvisCore(
            model_size=model_size,
            use_wake_word=use_wake,
            wake_threshold=wake_threshold,
            debug_wake=False
        )
        jarvis.run()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    main()