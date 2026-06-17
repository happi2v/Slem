# tts.py
import asyncio
import io
import threading
import pygame
import edge_tts

class VoiceSpeaker:
    def __init__(self, voice="ru-RU-DmitryNeural"):
        """
        Инициализация синтезатора речи.
        Доступные русские голоса (можно менять):
        - ru-RU-DmitryNeural (мужской, спокойный)
        - ru-RU-SvetlanaNeural (женский)
        - ru-RU-DariyaNeural (женский, мягкий)
        """
        self.voice = voice
        # Инициализируем pygame микшер для воспроизведения
        pygame.mixer.init()
        print(f"Синтезатор речи готов. Голос: {voice}")
        
    def _play_audio(self, audio_data):
        """Воспроизводит mp3-данные из памяти."""
        # Загружаем аудио из объекта BytesIO
        sound = pygame.mixer.Sound(io.BytesIO(audio_data))
        sound.play()
        # Ждём окончания воспроизведения
        pygame.time.wait(int(sound.get_length() * 1000))
        
    def speak(self, text):
        """Синтезирует и произносит текст вслух (блокирующий вызов)."""
        if not text:
            return
            
        print(f"Джарвис: {text}")
        
        async def generate_and_play():
            # Создаём объект Communicate для синтеза
            communicate = edge_tts.Communicate(text, self.voice)
            # Собираем все аудио-чанки в один байтовый массив
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            audio_data = b''.join(audio_chunks)
            return audio_data
        
        # Запускаем асинхронную функцию и получаем результат
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(generate_and_play())
        loop.close()
        
        # Воспроизводим
        self._play_audio(audio_data)
    
    def speak_async(self, text):
        """Произносит текст в отдельном потоке (не блокирует программу)."""
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()
        return thread