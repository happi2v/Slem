# wakeword.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
import pyaudio
import numpy as np
import threading
import time
import os
import json
from collections import deque

class VoiceWakeWord:
    def __init__(self, wake_word="джарвис", sensitivity=0.6, debug=False):
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.debug = debug
        
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        self.custom_model = None
        self.custom_threshold = 0.5
        self.load_custom_model()
        
        self.audio_buffer = deque(maxlen=int(self.RATE / self.CHUNK * 2.0))
        self.energy_history = deque(maxlen=100)
        
        self.speech_multiplier = 3.0
        self.silence_stop_frames = 15  # 1 сек тишины
        
        self.running = False
        self.audio = None
        self.stream = None
        self.detection_callbacks = []
        self.last_detection_time = 0
        self.cooldown_period = 2.0
        
        if self.custom_model:
            print(f"✓ Модель загружена (порог: {self.custom_threshold:.3f})")
    
    def load_custom_model(self):
        model_path = f"models/{self.wake_word}_model.json"
        if os.path.exists(model_path):
            try:
                with open(model_path, 'r', encoding='utf-8') as f:
                    self.custom_model = json.load(f)
                if 'threshold' in self.custom_model:
                    self.custom_threshold = self.custom_model['threshold']
                return True
            except:
                pass
        return False
    
    def extract_features(self, audio):
        if len(audio) < 512:
            return None
        audio = audio.astype(np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        
        features = {}
        features['duration'] = len(audio) / self.RATE
        features['rms'] = float(np.sqrt(np.mean(audio**2)))
        features['peak'] = float(np.max(np.abs(audio)))
        features['zcr'] = float(np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio)))
        
        n_fft = min(1024, len(audio))
        fft = np.abs(np.fft.rfft(audio[:n_fft] * np.hanning(n_fft)))
        freqs = np.fft.rfftfreq(n_fft, 1/self.RATE)
        
        if np.sum(fft) > 0:
            features['centroid'] = float(np.sum(freqs * fft) / np.sum(fft))
        else:
            features['centroid'] = 0.0
        
        cumsum = np.cumsum(fft)
        if cumsum[-1] > 0:
            idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
            features['rolloff'] = float(freqs[idx[0]]) if len(idx) > 0 else 0.0
        
        n_mels = 16
        def hz_to_mel(hz): return 2595 * np.log10(1 + hz/700)
        def mel_to_hz(mel): return 700 * (10**(mel/2595) - 1)
        min_mel = hz_to_mel(0)
        max_mel = hz_to_mel(self.RATE/2)
        mel_points = np.linspace(min_mel, max_mel, n_mels+2)
        hz_points = mel_to_hz(mel_points)
        bin_idx = np.clip(np.floor((n_fft+1) * hz_points / self.RATE).astype(int), 0, len(fft)-1)
        for i in range(n_mels):
            if bin_idx[i] < bin_idx[i+2]:
                features[f'mel_{i}'] = float(np.sum(fft[bin_idx[i]:bin_idx[i+2]]))
        
        return features
    
    def compare_features(self, test, model):
        if not test or not model:
            return 0.0
        ignore = {'threshold', 'count', 'min', 'max'}
        common = (set(test.keys()) & set(model.keys())) - ignore
        if len(common) < 5:
            return 0.0
        scores = []
        for key in common:
            tv = test[key]
            ms = model[key]
            if isinstance(ms, dict) and 'mean' in ms:
                mean = ms['mean']
                std = ms.get('std', 1.0)
                if std > 0:
                    dev = abs(tv - mean) / (std + 1e-6)
                    scores.append(np.exp(-dev * 2.0))
        return float(np.mean(scores)) if scores else 0.0
    
    def on_detected(self, callback):
        self.detection_callbacks.append(callback)
    
    def _trigger(self):
        now = time.time()
        if now - self.last_detection_time < self.cooldown_period:
            return
        self.last_detection_time = now
        print("\n🔔 АКТИВАЦИЯ!")
        for cb in self.detection_callbacks:
            cb()
    
    def start_listening(self):
        self.audio = pyaudio.PyAudio()
        self.running = True
        self.stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
        )
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"Слушаю... (порог: {self.custom_threshold:.3f})")
    
    def _loop(self):
        speaking = False
        speech_frames = 0
        silence_frames = 0
        buffer = []
        
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                chunk = np.frombuffer(data, dtype=np.int16)
                self.audio_buffer.append(chunk)
                
                energy = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                self.energy_history.append(energy)
                
                if len(self.energy_history) > 30:
                    noise_level = np.median(list(self.energy_history))
                    threshold = max(80, noise_level * self.speech_multiplier)
                else:
                    threshold = 100
                
                is_speech = energy > threshold
                
                if is_speech:
                    if not speaking:
                        speaking = True
                        buffer = list(self.audio_buffer)[-5:]
                        if self.debug:
                            print(f"\n🎤 (e={energy:.0f})", end="", flush=True)
                    speech_frames += 1
                    silence_frames = 0
                    buffer.append(chunk)
                    
                elif speaking:
                    silence_frames += 1
                    buffer.append(chunk)
                    
                    if silence_frames >= self.silence_stop_frames:
                        dur = len(buffer) * self.CHUNK / self.RATE
                        
                        if speech_frames >= 3:
                            segment = np.concatenate(buffer)
                            
                            if self.custom_model:
                                features = self.extract_features(segment)
                                if features:
                                    score = self.compare_features(features, self.custom_model)
                                    
                                    if self.debug:
                                        m = " ✓АКТИВАЦИЯ!" if score > self.custom_threshold else ""
                                        print(f" {dur:.1f}с s={score:.3f}{m}", flush=True)
                                    
                                    if score > self.custom_threshold:
                                        self._trigger()
                        
                        speaking = False
                        speech_frames = 0
                        silence_frames = 0
                        buffer = []
                        
            except Exception as e:
                time.sleep(0.1)
    
    def stop(self):
        self.running = False
        time.sleep(0.3)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
    
    def record_samples(self, num_samples=8):
        print(f"\nЗапись {num_samples} образцов")
        self.audio = pyaudio.PyAudio()
        samples = []
        
        for i in range(num_samples):
            print(f"Образец {i+1}/{num_samples}")
            for c in [2, 1]:
                print(f"  {c}...")
                time.sleep(0.7)
            print("  ▶ ГОВОРИТЕ!")
            
            stream = self.audio.open(
                format=self.FORMAT, channels=self.CHANNELS,
                rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
            )
            frames = []
            for _ in range(int(self.RATE / self.CHUNK * 2.0)):
                try:
                    frames.append(stream.read(self.CHUNK, exception_on_overflow=False))
                except:
                    break
            stream.stop_stream()
            stream.close()
            
            if frames:
                audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                energy = np.abs(audio_data)
                thresh = np.mean(energy) * 2.0
                mask = energy > thresh
                if np.any(mask):
                    idx = np.where(mask)[0]
                    margin = int(0.1 * self.RATE)
                    start = max(0, idx[0] - margin)
                    end = min(len(audio_data), idx[-1] + margin)
                    audio_data = audio_data[start:end]
                dur = len(audio_data) / self.RATE
                if 0.2 < dur < 2.0:
                    samples.append(audio_data)
                    print(f"  ✓ {dur:.1f}с\n")
                else:
                    print(f"  ✗ {dur:.1f}с\n")
            time.sleep(0.3)
        
        self.audio.terminate()
        self.audio = None
        
        if len(samples) < 4:
            print("Мало образцов!")
            return False
        
        all_features = [self.extract_features(s) for s in samples if self.extract_features(s)]
        self.custom_model = {}
        all_keys = set()
        for f in all_features:
            if f: all_keys.update(f.keys())
        for key in all_keys:
            vals = [f[key] for f in all_features if f and key in f]
            if len(vals) >= 2:
                self.custom_model[key] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}
        
        scores = [self.compare_features(f, self.custom_model) for f in all_features if f]
        for i, s in enumerate(scores):
            print(f"  Score {i+1}: {s:.4f}")
        
        avg = np.mean(scores) if scores else 0
        self.custom_threshold = max(0.35, min(0.6, avg * 0.75))
        self.custom_model['threshold'] = self.custom_threshold
        
        os.makedirs("models", exist_ok=True)
        with open(f"models/{self.wake_word}_model.json", 'w', encoding='utf-8') as f:
            json.dump(self.custom_model, f, indent=2, ensure_ascii=False)
        
        print(f"\nСредний score: {avg:.4f}")
        print(f"Порог: {self.custom_threshold:.4f}")
        print("✓ Модель сохранена")
        return True