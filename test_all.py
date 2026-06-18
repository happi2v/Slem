# test_all.py
"""
Полное тестирование всех функций Джарвиса.
"""
import os
import sys
import time

print("=" * 60)
print("  ПОЛНОЕ ТЕСТИРОВАНИЕ ДЖАРВИСА")
print("=" * 60)

errors = []
passed = []

def test(name, func):
    """Запускает тест и считает результат."""
    try:
        print(f"\n  [{len(passed)+len(errors)+1}] {name}...", end=" ")
        func()
        print("✓")
        passed.append(name)
    except Exception as e:
        print(f"✗ ({e})")
        errors.append((name, str(e)))

# ============================================================
# ТЕСТЫ
# ============================================================

def test_imports():
    print("\n--- ИМПОРТЫ ---")
    
    def t_stt(): __import__("stt")
    test("STT модуль", t_stt)
    
    def t_tts(): __import__("tts")
    test("TTS модуль", t_tts)
    
    def t_sounds(): __import__("sounds")
    test("Sounds модуль", t_sounds)
    
    def t_wakeword(): __import__("wakeword")
    test("WakeWord модуль", t_wakeword)
    
    def t_llm(): __import__("llm")
    test("LLM модуль", t_llm)
    
    def t_gui(): __import__("gui")
    test("GUI модуль", t_gui)
    
    def t_music(): __import__("music")
    test("Music модуль", t_music)
    
    def t_volume(): __import__("volume")
    test("Volume модуль", t_volume)


def test_stt():
    print("\n--- РАСПОЗНАВАНИЕ РЕЧИ ---")
    from stt import VoiceRecognizer
    
    def t1():
        r = VoiceRecognizer(model_size="tiny", device="cpu")
        r.close()
    test("Создание (tiny, CPU)", t1)
    
    try:
        import torch
        if torch.cuda.is_available():
            def t2():
                r = VoiceRecognizer(model_size="tiny", device="cuda")
                r.close()
            test("Создание (tiny, GPU)", t2)
    except:
        pass


def test_tts():
    print("\n--- СИНТЕЗ РЕЧИ ---")
    from tts import VoiceSpeaker
    
    def t():
        s = VoiceSpeaker(voice="ru-RU-DmitryNeural")
    test("Создание спикера", t)


def test_wakeword():
    print("\n--- WAKE WORD ---")
    from wakeword import VoiceWakeWord
    
    def t():
        w = VoiceWakeWord(wake_word="джарвис", sensitivity=0.5, debug=False)
    test("Создание детектора", t)


def test_llm():
    print("\n--- LLM ---")
    
    import subprocess
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, shell=True)
    
    if "llama" in result.stdout.lower():
        from llm import LLM
        
        def t1():
            llm = LLM(model="llama3.2:3b")
        test("Создание LLM", t1)
        
        def t2():
            llm = LLM(model="llama3.2:3b")
            answer = llm.ask("Привет")
        test("Запрос к LLM", t2)
    else:
        print("  ⚠ Ollama не найдена, LLM тесты пропущены")


def test_volume():
    print("\n--- ГРОМКОСТЬ ---")
    from volume import VolumeControl
    
    def t1():
        v = VolumeControl()
    test("Создание VolumeControl", t1)
    
    def t2():
        v = VolumeControl()
        vol = v.get_volume()
    test("Получение громкости", t2)


def test_music():
    print("\n--- МУЗЫКА ---")
    from music import YandexMusic
    
    def t():
        m = YandexMusic()
    test("Создание YandexMusic", t)


def test_gui():
    print("\n--- GUI ---")
    from gui import GUI
    
    def t():
        g = GUI(core=None)
        time.sleep(0.3)
        g.running = False
    test("Создание GUI", t)


def test_jarvis_core():
    print("\n--- ЯДРО ---")
    from jarvis_core import Jarvis
    
    def t():
        j = Jarvis(model_size="tiny", use_wake=False, wake_threshold=0.5)
        j.running = False
    test("Создание ядра", t)


def test_has_method():
    print("\n--- МЕТОД _has ---")
    from jarvis_core import Jarvis
    j = Jarvis(model_size="tiny", use_wake=False)
    j.running = False
    
    def t1():
        if not j._has("привет мир", "привет"):
            raise Exception("Не найдено")
    test("Точное совпадение", t1)
    
    def t2():
        if not j._has("калькулятор", "калькулятор"):
            raise Exception("Не найдено")
    test("Полное совпадение", t2)
    
    def t3():
        if j._has("браузер", "музыка"):
            raise Exception("Ложное срабатывание")
    test("Несовпадение", t3)
    
    def t4():
        if not j._has("стим", "стим,steam,игры"):
            raise Exception("Не найдено")
    test("Синонимы", t4)


# ============================================================
# ЗАПУСК
# ============================================================

print("\n" + "=" * 60)
print("  ЗАПУСК ТЕСТОВ...")
print("=" * 60)

time.sleep(1)

test_imports()
test_stt()
test_tts()
test_wakeword()
test_llm()
test_volume()
test_music()
test_gui()
test_jarvis_core()
test_has_method()

# ============================================================
# ИТОГИ
# ============================================================
print("\n" + "=" * 60)
print("  РЕЗУЛЬТАТЫ")
print("=" * 60)

total = len(passed) + len(errors)
print(f"\n  Всего тестов: {total}")
print(f"  Пройдено: {len(passed)} ✓")
print(f"  Ошибок: {len(errors)} ✗")

if errors:
    print("\n  Ошибки:")
    for name, err in errors:
        print(f"    ✗ {name}: {err}")

print(f"\n  Пройдено: {len(passed)}/{total} ({len(passed)*100//total if total > 0 else 0}%)")

if not errors:
    print("\n  Все тесты пройдены! Джарвис работает отлично!")
else:
    print(f"\n  Есть проблемы: {len(errors)} тестов не пройдены")

print("\n" + "=" * 60)
input("  Нажмите Enter для выхода...")