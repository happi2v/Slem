# train_wakeword.py
"""
Обучение Wake Word модели.
Записывает образцы голоса с микрофона и создаёт модель.
"""
import os
import sys
import json
import time
import numpy as np
import pyaudio

# ============================================================
# НАСТРОЙКИ
# ============================================================
RATE = 16000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECORD_SECONDS = 2.0
MIN_DURATION = 0.2
MAX_DURATION = 2.0


# ============================================================
# ЗАПИСЬ
# ============================================================
def record_sample():
    """Записывает один образец с микрофона."""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)
    
    frames = []
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        try:
            frames.append(stream.read(CHUNK, exception_on_overflow=False))
        except:
            break
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    if not frames:
        return None
    
    audio = np.frombuffer(b''.join(frames), dtype=np.int16)
    
    # Обрезаем тишину
    energy = np.abs(audio.astype(np.float32))
    threshold = np.mean(energy) * 2.0
    mask = energy > threshold
    
    if np.any(mask):
        idx = np.where(mask)[0]
        margin = int(0.1 * RATE)
        start = max(0, idx[0] - margin)
        end = min(len(audio), idx[-1] + margin)
        audio = audio[start:end]
    
    dur = len(audio) / RATE
    if MIN_DURATION < dur < MAX_DURATION:
        return audio
    
    return None


# ============================================================
# ПРИЗНАКИ
# ============================================================
def extract_features(audio):
    """Извлекает признаки из аудио."""
    if len(audio) < 512:
        return None
    
    audio = audio.astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    
    f = {}
    f['duration'] = len(audio) / RATE
    f['rms'] = float(np.sqrt(np.mean(audio**2)))
    f['zcr'] = float(np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio)))
    
    n_fft = min(1024, len(audio))
    fft = np.abs(np.fft.rfft(audio[:n_fft] * np.hanning(n_fft)))
    freqs = np.fft.rfftfreq(n_fft, 1/RATE)
    
    if np.sum(fft) > 0:
        f['centroid'] = float(np.sum(freqs * fft) / np.sum(fft))
    
    cumsum = np.cumsum(fft)
    if cumsum[-1] > 0:
        idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
        if len(idx) > 0:
            f['rolloff'] = float(freqs[idx[0]])
    
    # Мел-полосы
    n_mels = 16
    def hz_to_mel(hz): return 2595 * np.log10(1 + hz/700)
    def mel_to_hz(mel): return 700 * (10**(mel/2595) - 1)
    
    mel_max = hz_to_mel(RATE/2)
    mel_points = np.linspace(0, mel_max, n_mels+2)
    hz_points = mel_to_hz(mel_points)
    bins = np.clip(np.floor((n_fft+1) * hz_points / RATE).astype(int), 0, len(fft)-1)
    
    for i in range(n_mels):
        if bins[i] < bins[i+2]:
            f[f'mel_{i}'] = float(np.sum(fft[bins[i]:bins[i+2]]))
    
    # Пики
    peaks = np.argsort(fft)[-3:]
    for i, p in enumerate(peaks):
        if p < len(freqs):
            f[f'peak_{i}'] = float(freqs[p])
    
    return f


# ============================================================
# МОДЕЛЬ
# ============================================================
def build_model(features_list):
    """Строит модель из списка признаков."""
    if len(features_list) < 3:
        return None
    
    all_keys = set()
    for feat in features_list:
        all_keys.update(feat.keys())
    
    model = {}
    for key in all_keys:
        vals = [f[key] for f in features_list if key in f]
        if len(vals) >= 2:
            model[key] = {
                'mean': float(np.mean(vals)),
                'std': float(np.std(vals))
            }
    
    return model


def compare_to_model(features, model):
    """Сравнивает признаки с моделью. Возвращает 0..1."""
    if not features or not model:
        return 0.0
    
    ignore = {'threshold', 'count'}
    common = set(features.keys()) & set(model.keys()) - ignore
    
    if len(common) < 5:
        return 0.0
    
    scores = []
    for key in common:
        tv = features[key]
        ms = model[key]
        if isinstance(ms, dict) and 'mean' in ms:
            mean = ms['mean']
            std = ms.get('std', 1.0)
            if std > 0:
                dev = abs(tv - mean) / (std + 1e-6)
                scores.append(np.exp(-dev * 2.0))
    
    return float(np.mean(scores)) if scores else 0.0


# ============================================================
# ГЛАВНОЕ
# ============================================================
def main():
    print("=" * 50)
    print("  ОБУЧЕНИЕ WAKE WORD")
    print("=" * 50)
    
    word = input("\nКлючевое слово [джарвис]: ").strip().lower() or "джарвис"
    
    try:
        num = int(input("Количество образцов [8]: ").strip() or "8")
    except:
        num = 8
    
    print(f"\n  Слово: «{word}» | Образцов: {num}")
    print("\n  ВАЖНО:")
    print("  • Полная тишина")
    print("  • Говорите ТОЛЬКО слово")
    print("  • Одинаково каждый раз")
    print("  • Не двигайтесь\n")
    
    input("Нажмите Enter...")
    
    # Запись
    samples = []
    
    for i in range(num):
        print(f"\n  Образец {i+1}/{num}")
        for c in [2, 1]:
            print(f"    {c}...")
            time.sleep(0.6)
        print("    ▶ ГОВОРИТЕ!")
        
        audio = record_sample()
        
        if audio is not None:
            dur = len(audio) / RATE
            samples.append(audio)
            print(f"    ✓ {dur:.1f}с")
        else:
            print(f"    ✗ Не удалось")
        
        time.sleep(0.3)
    
    if len(samples) < 4:
        print(f"\n  ✗ Мало образцов: {len(samples)}/4")
        return
    
    print(f"\n  Записано: {len(samples)} образцов")
    
    # Извлекаем признаки
    print("  Извлечение признаков...")
    all_features = []
    for audio in samples:
        feat = extract_features(audio)
        if feat:
            all_features.append(feat)
    
    # Строим модель
    model = build_model(all_features)
    
    if not model:
        print("  ✗ Не удалось построить модель")
        return
    
    print(f"  Признаков: {len(model)}")
    
    # Проверка
    print("\n  Проверка:")
    scores = []
    for i, feat in enumerate(all_features):
        s = compare_to_model(feat, model)
        scores.append(s)
        print(f"    Образец {i+1}: {s:.4f}")
    
    avg = np.mean(scores)
    print(f"\n  Средний score: {avg:.4f}")
    
    # Порог
    threshold = max(0.3, min(0.5, avg * 0.75))
    model['threshold'] = threshold
    print(f"  Порог: {threshold:.4f}")
    
    # Сохраняем
    os.makedirs("models", exist_ok=True)
    path = f"models/{word}_model.json"
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✓ Модель сохранена: {path}")
    print(f"  ✓ Порог для ядра: {threshold:.2f}")
    print(f"\n  Запуск: python jarvis_core.py")


if __name__ == "__main__":
    main()