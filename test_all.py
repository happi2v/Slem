# test_all.py
"""
Полное тестирование Джарвиса.
"""
import os
import sys
import time

print("=" * 60)
print("  ТЕСТИРОВАНИЕ ДЖАРВИСА v42.0")
print("=" * 60)

errors = []
passed = []

def test(name, func):
    try:
        print(f"  [{len(passed)+len(errors)+1}] {name}...", end=" ")
        func()
        print("✓")
        passed.append(name)
    except Exception as e:
        print(f"✗ ({e})")
        errors.append((name, str(e)))

# ============================================================
# ИМПОРТЫ
# ============================================================
def test_imports():
    print("\n--- ИМПОРТЫ ---")
    
    def t(name):
        __import__(name)
    
    test("STT", lambda: t("stt"))
    test("TTS", lambda: t("tts"))
    test("Sounds", lambda: t("sounds"))
    test("WakeWord", lambda: t("wakeword"))
    test("LLM", lambda: t("llm"))
    test("GUI", lambda: t("gui"))
    test("Volume", lambda: t("volume"))
    test("AppFinder", lambda: t("app_finder"))

# ============================================================
# STT
# ============================================================
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

# ============================================================
# TTS
# ============================================================
def test_tts():
    print("\n--- СИНТЕЗ РЕЧИ ---")
    from tts import VoiceSpeaker
    
    def t():
        s = VoiceSpeaker()
    test("Создание VoiceSpeaker", t)

# ============================================================
# WAKE WORD
# ============================================================
def test_wakeword():
    print("\n--- WAKE WORD ---")
    from wakeword import VoiceWakeWord
    
    def t():
        w = VoiceWakeWord(wake_word="джарвис", sensitivity=0.5, debug=False)
    test("Создание детектора", t)

# ============================================================
# LLM
# ============================================================
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
            llm.ask("Привет")
        test("Запрос к LLM", t2)
    else:
        print("  ⚠ Ollama не найдена")

# ============================================================
# VOLUME
# ============================================================
def test_volume():
    print("\n--- ГРОМКОСТЬ ---")
    from volume import VolumeControl
    
    def t1():
        v = VolumeControl()
    test("Создание VolumeControl", t1)
    
    def t2():
        v = VolumeControl()
        v.get_volume()
    test("Получение громкости", t2)

# ============================================================
# APP FINDER
# ============================================================
def test_finder():
    print("\n--- ПОИСК ПРИЛОЖЕНИЙ ---")
    from app_finder import AppFinder
    
    def t1():
        f = AppFinder()
    test("Создание AppFinder", t1)
    
    def t2():
        f = AppFinder()
        # Проверяем системную команду
        f.find_and_run("notepad")
    test("Запуск notepad", t2)

# ============================================================
# GUI
# ============================================================
def test_gui():
    print("\n--- GUI ---")
    from gui import GUI
    
    def t():
        g = GUI(core=None)
        time.sleep(0.3)
        g.running = False
    test("Создание GUI", t)

# ============================================================
# ЯДРО
# ============================================================
def test_core():
    print("\n--- ЯДРО ---")
    from jarvis_core import Jarvis
    
    def t1():
        j = Jarvis(model_size="tiny", use_wake=False)
        j.running = False
    test("Создание ядра", t1)
    
    def t2():
        j = Jarvis(model_size="tiny", use_wake=False)
        j.running = False
        
        if not j._has("привет мир", "привет"):
            raise Exception("_has не нашёл")
    test("Метод _has (совпадение)", t2)
    
    def t3():
        j = Jarvis(model_size="tiny", use_wake=False)
        j.running = False
        
        if j._has("браузер", "музыка"):
            raise Exception("_has ложное срабатывание")
    test("Метод _has (несовпадение)", t3)

# ============================================================
# ЗАПУСК
# ============================================================
print("\n" + "=" * 60)
print("  ЗАПУСК ТЕСТОВ...")
print("=" * 60)

test_imports()
test_stt()
test_tts()
test_wakeword()
test_llm()
test_volume()
test_finder()
test_gui()
test_core()

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
    print("\n  🎉 Все тесты пройдены!")
else:
    print(f"\n  ⚠ Есть проблемы: {len(errors)}")

print("\n" + "=" * 60)
input("  Нажмите Enter...")