# generate_wakeword.py
"""
Генератор Wake Word модели с фильтрацией плохих образцов.
"""
import os
import sys
import json
import wave
import numpy as np
import time


def print_title(text):
    print("\n" + "=" * 55)
    print(f"  {text}")
    print("=" * 55)


def extract_features(audio, rate=16000):
    """Извлекает признаки из аудио."""
    if len(audio) < 512:
        return None
    
    audio = audio.astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    
    features = {}
    features['duration'] = len(audio) / rate
    features['rms'] = float(np.sqrt(np.mean(audio ** 2)))
    features['peak'] = float(np.max(np.abs(audio)))
    features['std'] = float(np.std(audio))
    
    zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
    features['zcr'] = float(zcr)
    
    n_fft = min(1024, len(audio))
    window = np.hanning(n_fft)
    fft = np.abs(np.fft.rfft(audio[:n_fft] * window))
    freqs = np.fft.rfftfreq(n_fft, 1 / rate)
    
    if np.sum(fft) > 0:
        features['centroid'] = float(np.sum(freqs * fft) / np.sum(fft))
    else:
        features['centroid'] = 0.0
    
    cumsum = np.cumsum(fft)
    if cumsum[-1] > 0:
        idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
        features['rolloff'] = float(freqs[idx[0]]) if len(idx) > 0 else 0.0
    else:
        features['rolloff'] = 0.0
    
    features['flux'] = float(np.sum(np.diff(fft) ** 2))
    
    # Мел-полосы
    n_mels = 16
    def hz_to_mel(hz): return 2595 * np.log10(1 + hz / 700)
    def mel_to_hz(mel): return 700 * (10 ** (mel / 2595) - 1)
    
    min_mel = hz_to_mel(0)
    max_mel = hz_to_mel(rate / 2)
    mel_points = np.linspace(min_mel, max_mel, n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bin_idx = np.floor((n_fft + 1) * hz_points / rate).astype(int)
    bin_idx = np.clip(bin_idx, 0, len(fft) - 1)
    
    for i in range(n_mels):
        if bin_idx[i] < bin_idx[i + 2]:
            features[f'mel_{i}'] = float(np.sum(fft[bin_idx[i]:bin_idx[i + 2]]))
    
    # Пики спектра
    peaks = np.argsort(fft)[-3:]
    for i, p in enumerate(peaks):
        if p < len(freqs):
            features[f'peak_{i}_freq'] = float(freqs[p])
            features[f'peak_{i}_mag'] = float(fft[p])
    
    return features


def load_wav(filepath, target_rate=16000):
    """Загружает WAV и приводит к 16 кГц."""
    try:
        with wave.open(filepath, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            rate = wf.getframerate()
            
            if rate != target_rate:
                try:
                    from scipy import signal
                    duration = len(audio) / rate
                    new_len = int(duration * target_rate)
                    audio = signal.resample(audio, new_len).astype(np.int16)
                except:
                    print(f"    ⚠ Не удалось ресемплировать, частота: {rate} Гц")
                    return None, None
            
            return audio, target_rate
    except Exception as e:
        print(f"    ✗ Ошибка: {e}")
        return None, None


def trim_silence(audio, rate, threshold_ratio=0.03):
    """Обрезает тишину."""
    energy = np.abs(audio.astype(np.float32))
    max_energy = np.max(energy)
    
    if max_energy == 0:
        return audio
    
    threshold = max_energy * threshold_ratio
    mask = energy > threshold
    
    if not np.any(mask):
        return audio
    
    indices = np.where(mask)[0]
    margin = int(0.05 * rate)  # 50 мс
    
    start = max(0, indices[0] - margin)
    end = min(len(audio), indices[-1] + margin)
    
    return audio[start:end]


def normalize_audio(audio):
    """Нормализует громкость к -3 дБ."""
    audio = audio.astype(np.float32)
    rms = np.sqrt(np.mean(audio ** 2))
    if rms > 0:
        target_rms = 0.2  # -3 дБ
        audio = audio * (target_rms / rms)
        audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767).astype(np.int16)


def compare_to_model(features, model):
    """Сравнивает признаки с моделью."""
    if not features or not model:
        return 0.0
    
    ignore = {'threshold', 'count'}
    common = set(features.keys()) & set(model.keys()) - ignore
    
    if len(common) < 5:
        return 0.0
    
    scores = []
    for key in common:
        test_val = features[key]
        model_stats = model[key]
        
        if isinstance(model_stats, dict) and 'mean' in model_stats:
            mean = model_stats['mean']
            std = model_stats.get('std', 1.0)
            
            if std > 0:
                dev = abs(test_val - mean) / (std + 1e-6)
                score = np.exp(-dev * 2.0)
                scores.append(score)
    
    return float(np.mean(scores)) if scores else 0.0


def filter_samples(samples, rate):
    """
    Фильтрует образцы: оставляет только качественные.
    Сначала грубо оценивает, потом итеративно удаляет выбросы.
    """
    if len(samples) < 5:
        return samples  # Слишком мало для фильтрации
    
    print("\n  Фильтрация образцов...")
    
    # Извлекаем признаки
    all_features = []
    valid_samples = []
    
    for i, audio in enumerate(samples):
        dur = len(audio) / rate
        
        # Фильтр по длительности
        if dur < 0.2 or dur > 2.5:
            print(f"    ✗ Образец {i+1}: длительность {dur:.1f}с (пропущен)")
            continue
        
        features = extract_features(audio, rate)
        if features:
            all_features.append((i, features))
            valid_samples.append(audio)
            print(f"    ✓ Образец {i+1}: {dur:.1f}с")
        else:
            print(f"    ✗ Образец {i+1}: нет признаков (пропущен)")
    
    if len(valid_samples) < 4:
        return valid_samples
    
    # Итеративная фильтрация выбросов
    for iteration in range(3):
        if len(valid_samples) <= 4:
            break
        
        # Строим временную модель
        temp_model = build_model_from_features(
            [extract_features(s, rate) for s in valid_samples]
        )
        
        if not temp_model:
            break
        
        # Считаем score для каждого
        scores = []
        for audio in valid_samples:
            feat = extract_features(audio, rate)
            if feat:
                scores.append(compare_to_model(feat, temp_model))
            else:
                scores.append(0)
        
        # Находим выбросы
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        threshold = mean_score - 2.0 * std_score  # Всё что ниже 2 сигм — выброс
        
        new_samples = []
        removed = False
        
        for i, (audio, score) in enumerate(zip(valid_samples, scores)):
            if score >= threshold:
                new_samples.append(audio)
            else:
                print(f"    🗑 Удалён выброс: score={score:.3f} (порог: {threshold:.3f})")
                removed = True
        
        if not removed:
            break  # Сошлось
        
        valid_samples = new_samples
    
    return valid_samples


def build_model_from_features(all_features):
    """Строит модель из списка признаков."""
    if len(all_features) < 3:
        return None
    
    all_keys = set()
    for feat in all_features:
        if feat:
            all_keys.update(feat.keys())
    
    model = {}
    for key in all_keys:
        values = []
        for feat in all_features:
            if feat and key in feat:
                values.append(feat[key])
        
        if len(values) >= 2:
            model[key] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'count': len(values)
            }
    
    return model


def create_model(samples, word, rate=16000, output_dir="models"):
    """Создаёт модель из образцов."""
    print_title(f"СОЗДАНИЕ МОДЕЛИ: «{word}»")
    print(f"  Образцов на входе: {len(samples)}")
    
    # Нормализуем
    print("\n  Нормализация громкости...")
    samples = [normalize_audio(s) for s in samples]
    
    # Фильтруем
    samples = filter_samples(samples, rate)
    
    if len(samples) < 4:
        print(f"\n  ✗ Недостаточно образцов после фильтрации: {len(samples)}")
        print("  Советы:")
        print("    • Говорите одинаково ВСЕ разы")
        print("    • Не меняйте расстояние до микрофона")
        print("    • Записывайте в тишине")
        print("    • Сделайте 10+ образцов для лучшего качества")
        return None
    
    print(f"\n  Образцов после фильтрации: {len(samples)}")
    
    # Извлекаем признаки
    all_features = []
    for i, audio in enumerate(samples):
        feat = extract_features(audio, rate)
        if feat:
            all_features.append(feat)
    
    # Строим модель
    model = build_model_from_features(all_features)
    
    if not model:
        print("  ✗ Не удалось построить модель")
        return None
    
    print(f"  Признаков: {len(model)}")
    
    # Проверка
    print("\n  Проверка качества:")
    scores = []
    
    for i, feat in enumerate(all_features):
        score = compare_to_model(feat, model)
        scores.append(score)
        
        if score > 0.7:
            status = "✓"
        elif score > 0.5:
            status = "○"
        else:
            status = "✗"
        
        print(f"    {status} Образец {i+1}: {score:.4f}")
    
    avg = np.mean(scores)
    min_s = np.min(scores)
    std = np.std(scores)
    
    print(f"\n  Средняя схожесть: {avg:.4f}")
    print(f"  Минимальная: {min_s:.4f}")
    print(f"  Разброс (std): {std:.4f}")
    
    # Автопорог
    threshold = max(0.45, min(0.8, avg - std * 0.5))
    model['threshold'] = threshold
    print(f"  Порог: {threshold:.4f}")
    
    # Качество
    if avg > 0.7 and std < 0.15:
        quality = "⭐ ОТЛИЧНОЕ"
    elif avg > 0.5 and std < 0.25:
        quality = "✓ ХОРОШЕЕ"
    elif avg > 0.3:
        quality = "○ СРЕДНЕЕ"
    else:
        quality = "✗ НИЗКОЕ"
    
    print(f"  Качество: {quality}")
    
    # Сохраняем
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, f"{word}_model.json")
    
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✓ Модель: {model_path}")
    
    # Советы
    if avg < 0.5:
        print("\n  💡 Для улучшения качества:")
        print("    • Запишите 10-15 образцов вместо 5-8")
        print("    • Говорите монотонно, без эмоций")
        print("    • Держите микрофон на одном расстоянии")
        print("    • Исключите фоновый шум")
        print("    • Не двигайтесь во время записи")
    
    return model


def record_microphone(duration=2.0, rate=16000):
    """Запись с микрофона."""
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        for _ in range(int(rate / 1024 * duration)):
            try:
                frames.append(stream.read(1024, exception_on_overflow=False))
            except:
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return np.frombuffer(b''.join(frames), dtype=np.int16)
    except ImportError:
        print("  ✗ pip install pyaudio")
        return None


def main():
    print_title("ГЕНЕРАТОР WAKE WORD v2")
    
    print("\n  Источник аудио:")
    print("  1 — Записать с микрофона")
    print("  2 — Загрузить WAV из папки")
    print("  3 — Нарезать один WAV")
    
    try:
        choice = input("\n  Выбор [1-3]: ").strip()
    except:
        return
    
    word = input("  Ключевое слово [джарвис]: ").strip().lower() or "джарвис"
    
    samples = []
    
    if choice == "1":
        try:
            num = int(input("  Образцов [10]: ").strip() or "10")
        except:
            num = 10
        
        print(f"\n  Запись {num} образцов.")
        print("  Говорите ОДИНАКОВО каждый раз!")
        print("  Не меняйте позу и расстояние до микрофона.\n")
        
        for i in range(num):
            print(f"  Образец {i+1}/{num}")
            for c in [2, 1]:
                print(f"    {c}...")
                time.sleep(0.6)
            print("    ▶ ГОВОРИТЕ!")
            
            audio = record_microphone(2.0)
            
            if audio is not None:
                audio = trim_silence(audio, 16000)
                dur = len(audio) / 16000
                
                if 0.2 < dur < 2.5:
                    samples.append(audio)
                    print(f"    ✓ {dur:.1f}с\n")
                else:
                    print(f"    ✗ {dur:.1f}с — пропущено\n")
            else:
                print("    ✗ Ошибка\n")
            
            time.sleep(0.3)
    
    elif choice == "2":
        folder = input("  Папка с WAV: ").strip()
        if not os.path.isdir(folder):
            print(f"  ✗ Не найдена: {folder}")
            return
        
        wavs = [f for f in os.listdir(folder) if f.endswith('.wav')]
        print(f"\n  Найдено: {len(wavs)} файлов")
        
        for wf in wavs:
            fp = os.path.join(folder, wf)
            audio, rate = load_wav(fp)
            if audio is not None:
                audio = trim_silence(audio, rate)
                samples.append(audio)
                print(f"    ✓ {wf}: {len(audio)/rate:.1f}с")
    
    elif choice == "3":
        fp = input("  Путь к WAV: ").strip()
        if not os.path.isfile(fp):
            print(f"  ✗ Не найден: {fp}")
            return
        
        audio, rate = load_wav(fp)
        if audio is None:
            return
        
        chunk_size = int(1.5 * rate)
        overlap = int(0.3 * rate)
        
        for start in range(0, len(audio) - chunk_size, chunk_size - overlap):
            chunk = audio[start:start + chunk_size]
            chunk = trim_silence(chunk, rate)
            dur = len(chunk) / rate
            if 0.3 < dur < 2.0:
                samples.append(chunk)
        
        print(f"  Нарезано: {len(samples)} образцов")
    
    if samples:
        create_model(samples, word, 16000)
    else:
        print("\n  ✗ Нет образцов")


if __name__ == "__main__":
    main()