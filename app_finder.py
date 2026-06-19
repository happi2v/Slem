# app_finder.py
"""
Поиск и запуск программ — полный доступ к файловой системе.
"""
import os
import subprocess
import time


class AppFinder:
    """Ищет приложения по всей системе."""
    
    def __init__(self):
        self.cache = {}
        self._build_index()
        print("  ✓ Поиск приложений готов")
    
    def _build_index(self):
        """Сканирует систему и строит индекс всех .exe файлов."""
        print("  Индексация приложений...")
        
        drives = self._get_drives()
        exe_files = []
        
        for drive in drives:
            try:
                # Быстрый поиск через where / dir
                result = subprocess.run(
                    f'dir "{drive}\\*.exe" /s /b 2>nul',
                    capture_output=True, text=True, shell=True, timeout=60
                )
                if result.stdout:
                    exe_files.extend(result.stdout.strip().split("\n"))
            except:
                pass
        
        # Индексируем: имя_файла -> полный_путь
        for path in exe_files:
            path = path.strip()
            if path:
                name = os.path.basename(path).lower().replace(".exe", "")
                if name not in self.cache:
                    self.cache[name] = path
        
        print(f"  ✓ Найдено приложений: {len(self.cache)}")
    
    def _get_drives(self):
        """Возвращает список доступных дисков."""
        drives = []
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(f"{letter}:"):
                drives.append(f"{letter}:")
        # Добавляем рабочий стол и папки пользователя
        drives.append(os.path.expanduser("~\\Desktop"))
        drives.append(os.path.expanduser("~\\AppData"))
        return drives
    
    def find(self, name):
        """
        Ищет программу по названию.
        Возвращает полный путь или None.
        """
        name = name.lower().strip()
        
        # 1. Точное совпадение в кэше
        if name in self.cache:
            return self.cache[name]
        
        # 2. Частичное совпадение
        matches = []
        for exe_name, path in self.cache.items():
            # Все части имени должны быть в названии
            name_parts = name.replace("-", " ").replace("_", " ").split()
            if all(part in exe_name for part in name_parts):
                matches.append((exe_name, path))
            
            # Или название файла начинается с запроса
            if exe_name.startswith(name.replace(" ", "")):
                matches.append((exe_name, path))
        
        if matches:
            # Сортируем по длине имени (самое короткое — точнее)
            matches.sort(key=lambda x: len(x[0]))
            return matches[0][1]
        
        # 3. Быстрый поиск через PowerShell (если нет в кэше)
        try:
            ps = f'Get-ChildItem -Path C:\\ -Filter "*{name}*.exe" -Recurse -ErrorAction SilentlyContinue -Depth 5 | Select-Object -First 1 -ExpandProperty FullName'
            result = subprocess.run(
                ["powershell", "-Command", ps],
                capture_output=True, text=True, shell=True, timeout=10
            )
            if result.stdout.strip():
                path = result.stdout.strip()
                if os.path.exists(path):
                    exe_name = os.path.basename(path).lower().replace(".exe", "")
                    self.cache[exe_name] = path
                    return path
        except:
            pass
        
        return None
    
    def find_and_run(self, name):
        """Ищет и запускает программу."""
        name = name.lower().strip()
        
        # Системные команды
        system_commands = {
            "блокнот": "notepad", "notepad": "notepad",
            "калькулятор": "calc", "calc": "calc",
            "терминал": "cmd", "cmd": "cmd", "консоль": "cmd",
            "проводник": "explorer", "explorer": "explorer",
            "пейнт": "mspaint", "paint": "mspaint",
            "диспетчер задач": "taskmgr", "taskmgr": "taskmgr",
        }
        
        if name in system_commands:
            cmd = system_commands[name]
            os.system(f"start {cmd}")
            print(f"  ✓ Запущено: {cmd}")
            return True
        
        # Ищем в системе
        path = self.find(name)
        
        if path:
            try:
                os.system(f'start "" "{path}"')
                print(f"  ✓ Запущено: {os.path.basename(path)}")
                return True
            except Exception as e:
                print(f"  ✗ Ошибка запуска: {e}")
                return False
        
        print(f"  ✗ Не найдено: {name}")
        print(f"    Попробуйте другое название")
        return False


# Тест
if __name__ == "__main__":
    print("=" * 50)
    print("  ИНДЕКСАЦИЯ СИСТЕМЫ")
    print("=" * 50)
    
    start = time.time()
    finder = AppFinder()
    elapsed = time.time() - start
    print(f"  Время: {elapsed:.1f} сек\n")
    
    print("  Введите название: 'выход' для выхода\n")
    
    while True:
        name = input("  > ").strip()
        if name.lower() in ["выход", "exit"]:
            break
        if name:
            finder.find_and_run(name)