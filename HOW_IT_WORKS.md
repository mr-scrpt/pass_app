# Как работает система распространения

## 📊 Визуальная схема

```
┌─────────────────────────────────────────────────────────────────┐
│  Ваш код (pass_client.py, components/, etc.)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  setup.py                                                       │
│  • Определяет зависимости                                       │
│  • Создает entry point: pass-kb → main()                       │
│  • Устанавливает .desktop файл                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PKGBUILD                                                       │
│  • Скачивает исходники с GitHub                                │
│  • Собирает Python wheel пакет                                 │
│  • Устанавливает в систему                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Установка в систему                                           │
│                                                                 │
│  /usr/bin/pass-kb                  ← Исполняемый файл          │
│  /usr/lib/python3.11/site-packages ← Python пакет              │
│  /usr/share/applications/...       ← Desktop entry             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Пользователь может запустить:                                 │
│                                                                 │
│  • Из терминала: pass-kb                                       │
│  • Из меню приложений                                          │
│  • Через Rofi: "pass"                                          │
│  • Через dmenu, wofi и т.д.                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Жизненный цикл релиза

```
1. Разработка
   ↓
2. Тестирование локально
   $ pip install -e .
   $ pass-kb
   ↓
3. Commit → Push на GitHub
   ↓
4. Создание релиза на GitHub
   Tag: v1.0.0
   ↓
5. Обновление PKGBUILD
   • URL релиза
   • sha256sum
   ↓
6. Тестирование сборки
   $ makepkg -si
   ↓
7. Публикация в AUR
   $ git push origin master
   ↓
8. Пользователи устанавливают
   $ yay -S pass-cli-with-keyboard-total-control
```

## 🎯 Что делает каждый файл

### setup.py
```python
entry_points={
    "console_scripts": [
        "pass-kb=pass_client:main",
        #    ↑         ↑        ↑
        #    |         |        └─ функция для вызова
        #    |         └─────────── модуль
        #    └──────────────────────── имя команды в системе
    ],
}
```

**Результат:** При вызове `pass-kb` в терминале:
1. Python находит модуль `pass_client`
2. Вызывает функцию `main()`
3. Приложение запускается

### pass-kb.desktop
```ini
[Desktop Entry]
Name=Pass Keyboard Control   # Имя в меню
Exec=pass-kb                # Команда для запуска
Icon=dialog-password        # Иконка
Categories=Utility;Security; # Где показывать в меню
```

**Результат:** Приложение появляется в:
- Application Menu (все DE)
- Rofi (`rofi -show drun`)
- dmenu
- wofi
- Любой application launcher

### PKGBUILD
```bash
pkgname=pass-cli-with-keyboard-total-control
pkgver=1.0.0
source=("${url}/archive/v${pkgver}.tar.gz")

build() {
    python -m build --wheel  # Создает .whl файл
}

package() {
    python -m installer ...  # Устанавливает .whl
    install ... .desktop     # Копирует desktop file
}
```

**Результат:** 
- Автоматическая установка всех файлов
- Управление через pacman/yay
- Простое обновление и удаление

## 🔍 Как Rofi находит приложение

```
1. Вы нажимаете Super+D (или другой хоткей для Rofi)
   ↓
2. Rofi сканирует:
   /usr/share/applications/
   ~/.local/share/applications/
   ↓
3. Находит pass-kb.desktop
   ↓
4. Парсит поля:
   • Name → "Pass Keyboard Control"
   • Keywords → "password;manager;pass;..."
   • Categories → "Utility;Security;"
   ↓
5. Показывает в списке при поиске:
   • "pass" → находит по Name
   • "password" → находит по Keywords
   • "manager" → находит по Keywords
   ↓
6. При нажатии Enter:
   Выполняет: Exec=pass-kb
   ↓
7. Система запускает /usr/bin/pass-kb
   ↓
8. Python вызывает pass_client.main()
   ↓
9. Ваше приложение открывается
```

## 📦 Структура установки

После установки через AUR:

```
/usr/
├── bin/
│   └── pass-kb                        ← Исполняемый скрипт
├── lib/
│   └── python3.11/
│       └── site-packages/
│           ├── pass_client.py         ← Ваш код
│           ├── components/            ← Ваши компоненты
│           ├── ui_theme.py           ← Темы
│           └── ...                   ← Остальные файлы
└── share/
    ├── applications/
    │   └── pass-kb.desktop           ← Desktop entry
    ├── licenses/
    │   └── pass-cli.../LICENSE       ← Лицензия
    └── doc/
        └── pass-cli.../README.md     ← Документация
```

## 🎨 Кастомизация

### Изменение имени команды

В `setup.py`:
```python
entry_points={
    "console_scripts": [
        "password-manager=pass_client:main",  # Вместо pass-kb
    ],
}
```

Теперь команда будет: `password-manager`

### Изменение имени в меню

В `pass-kb.desktop`:
```ini
Name=My Awesome Password Manager
GenericName=Secure Password Storage
```

### Добавление собственной иконки

1. Создайте PNG иконку 256x256
2. Положите в `icons/pass-kb.png`
3. Обновите `setup.py` и PKGBUILD (см. DISTRIBUTION_GUIDE.md)

## 🐛 Отладка

### Приложение не запускается

```bash
# Проверьте, установлен ли пакет
which pass-kb

# Запустите напрямую
python -m pass_client

# Проверьте зависимости
pip list | grep -i pyside
```

### Не появляется в Rofi

```bash
# Проверьте desktop file
desktop-file-validate pass-kb.desktop

# Обновите кеш
update-desktop-database ~/.local/share/applications/

# Проверьте, установлен ли файл
ls /usr/share/applications/pass-kb.desktop
```

### Ошибка при сборке пакета

```bash
# Проверьте PKGBUILD
namcap PKGBUILD

# Проверьте собранный пакет
namcap pass-cli-*.pkg.tar.zst

# Очистите и пересоберите
rm -rf pkg src *.pkg.tar.zst
makepkg -f
```

## 💡 Полезные советы

1. **Версионирование**: Используйте semantic versioning
   - `1.0.0` → `1.0.1` (bugfix)
   - `1.0.0` → `1.1.0` (новая функция)
   - `1.0.0` → `2.0.0` (breaking changes)

2. **Changelog**: Ведите CHANGELOG.md
   ```markdown
   ## [1.1.0] - 2025-10-17
   ### Added
   - Новая фича
   ### Fixed
   - Исправлен баг
   ```

3. **Тестирование**: Всегда тестируйте перед публикацией
   ```bash
   pip install -e .  # development mode
   pass-kb           # тест
   ```

4. **Документация**: Поддерживайте README.md актуальным

5. **Feedback**: Следите за issues в AUR и GitHub
