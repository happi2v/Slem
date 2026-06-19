# Slem
# 🧠 J.A.R.V.I.S. — Голосовой ассистент

> *Just A Rather Very Intelligent System*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-35.0-red.svg)]()

Полностью локальный голосовой ассистент с нейросетью, автоиндексацией программ, управлением музыкой и системой. Вдохновлён Джарвисом из фильма «Железный человек».

<p align="center">
  <img src="jarvis_icon.png" width="128" alt="JARVIS Icon">
</p>

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Использование](#-использование)
- [Команды](#-команды)
- [Структура проекта](#-структура-проекта)
- [Технологии](#-технологии)
- [Тестирование](#-тестирование)
- [Требования](#-требования)
- [Лицензия](#-лицензия)

---

## 🚀 Возможности

- 🎤 **Голосовая активация** — слово «Джарвис»
- 🧠 **Whisper large-v3** — распознавание речи на GPU
- 🤖 **Ollama + llama3.2** — нейросеть для ответов
- 🔊 **Edge-TTS** — синтез русской речи
- 🖥 **Поиск любых программ** — автоиндексация всех .exe
- 🌐 **20+ сайтов** — браузер, YouTube, ВК, ChatGPT...
- 🎵 **Яндекс Музыка** — управление голосом
- 🔊 **Громкость** — системное управление
- ✍️ **Голосовой ввод** — печать текста в блокнот
- 📊 **GUI оверлей** — CPU, RAM, GPU монитор

---

## 🔧 Установка
Автоматическая
```bash
setup.bat
```
Ручная
```bash
# Основные зависимости
pip install pyaudio faster-whisper edge-tts pygame numpy

# GUI и трей
pip install pystray pillow

# Системные
pip install keyboard pyautogui pyperclip

# Мониторинг
pip install psutil gputil

# Ollama
# Скачайте с https://ollama.com/download
ollama pull llama3.2:3b
```



## ⚡ Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/jarvis.git
cd jarvis

# 2. Установите зависимости
setup.bat

# 3. Обучите Wake Word
python train_wakeword.py

# 4. Запустите
python jarvis_core.py
```



