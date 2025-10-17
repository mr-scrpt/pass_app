# Руководство по распространению приложения Pass Keyboard Control

## Обзор инфраструктуры

Ваше приложение уже имеет полную инфраструктуру для распространения через AUR (Arch User Repository) и локальной установки.

## 📦 Компоненты системы сборки

### 1. **setup.py** - Основной файл установки Python

Это сердце системы установки. Он делает следующее:

```python
entry_points={
    "console_scripts": [
        "pass-kb=pass_client:main",  # Создает команду 'pass-kb' в системе
    ],
}
```

**Что происходит при установке:**
1. Устанавливает Python-пакет в систему
2. Создает исполняемый файл `/usr/bin/pass-kb` (или `/usr/local/bin/pass-kb`)
3. Этот файл запускает функцию `main()` из `pass_client.py`
4. Устанавливает `.desktop` файл в `/usr/share/applications/`

**Зависимости:**
- `PySide6>=6.5.0` - Qt6 для Python
- `qt-material>=2.14` - Material Design темы
- `QtAwesome>=1.2.0` - Иконки Font Awesome

### 2. **pass-kb.desktop** - Desktop Entry файл

Это файл, который делает ваше приложение видимым в:
- Меню приложений (GNOME, KDE, XFCE и т.д.)
- Rofi
- Другие application launchers

**Ключевые поля:**
```ini
Name=Pass Keyboard Control           # Название в меню
Exec=pass-kb                         # Команда для запуска
Icon=dialog-password                 # Иконка (стандартная системная)
Categories=Utility;Security;         # Категории в меню
Keywords=password;manager;pass;...   # Ключевые слова для поиска
```

**Где устанавливается:**
- `/usr/share/applications/pass-kb.desktop` - системная установка
- `~/.local/share/applications/pass-kb.desktop` - пользовательская установка

### 3. **PKGBUILD** - Файл для создания пакета AUR

Это рецепт сборки пакета для Arch Linux и производных.

**Структура:**
```bash
pkgname=pass-keyboard-control  # Имя пакета в AUR
pkgver=1.0.0                                  # Версия
depends=('python' 'python-pyside6' ...)       # Зависимости
```

**Процесс сборки:**
1. `build()` - компилирует Python wheel пакет
2. `package()` - устанавливает файлы в систему:
   - Python пакет
   - Desktop entry
   - Документацию
   - Лицензию

## 🚀 Процесс публикации в AUR

### Шаг 1: Подготовка репозитория

Нужно добавить функцию `main()` в `pass_client.py`:

```python
def main():
    """Entry point for the application"""
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="dark_blue.xml", extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### Шаг 2: Создание релиза на GitHub

1. Создайте репозиторий на GitHub
2. Загрузите весь код
3. Создайте релиз (Release) с версией v1.0.0
4. GitHub автоматически создаст архив: `v1.0.0.tar.gz`

### Шаг 3: Обновление PKGBUILD

Обновите URL и sha256sum:

```bash
# Скачайте архив релиза
wget https://github.com/USERNAME/REPO/archive/v1.0.0.tar.gz

# Вычислите sha256sum
sha256sum v1.0.0.tar.gz

# Обновите PKGBUILD:
url="https://github.com/USERNAME/REPO"
sha256sums=('вычисленный_хеш')
```

### Шаг 4: Тестирование локальной сборки

```bash
# В директории с PKGBUILD
makepkg -si

# Это:
# - Скачает исходники
# - Соберет пакет
# - Установит его (-i)
```

### Шаг 5: Публикация в AUR

```bash
# 1. Создайте аккаунт на https://aur.archlinux.org
# 2. Настройте SSH ключи

# 3. Клонируйте пустой AUR репозиторий
git clone ssh://aur@aur.archlinux.org/pass-keyboard-control.git aur-repo
cd aur-repo

# 4. Скопируйте PKGBUILD и .SRCINFO
cp ../PKGBUILD .
makepkg --printsrcinfo > .SRCINFO

# 5. Commit и push
git add PKGBUILD .SRCINFO
git commit -m "Initial commit: v1.0.0"
git push origin master
```

### Шаг 6: Обновление пакета в AUR

При выходе новой версии:

```bash
# 1. Обновите версию в setup.py и PKGBUILD
# 2. Создайте новый релиз на GitHub
# 3. Обновите sha256sums в PKGBUILD
# 4. Пересоберите .SRCINFO и запушьте

makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Update to v1.1.0"
git push
```

## 🎯 Использование после установки

### Через командную строку
```bash
pass-kb
```

### Через Rofi
1. Запустите Rofi: `rofi -show drun`
2. Начните печатать: "pass" или "password"
3. Появится "Pass Keyboard Control"
4. Enter для запуска

### Через системное меню
- В категории "Utilities" → "Security"
- Или поиск по словам: password, manager, pass

## 📝 Локальная установка (без AUR)

Для разработки или тестирования:

```bash
# Установка в режиме разработки
pip install -e .

# Или полная установка
pip install .

# Установка desktop entry вручную
mkdir -p ~/.local/share/applications
cp pass-kb.desktop ~/.local/share/applications/
```

## 🔧 Отладка

### Проверка desktop entry
```bash
# Проверка синтаксиса
desktop-file-validate pass-kb.desktop

# Обновление кеша приложений
update-desktop-database ~/.local/share/applications/
```

### Проверка установки
```bash
# Где находится команда
which pass-kb

# Запуск с отладочной информацией
pass-kb --help  # если добавите argparse
```

## 📋 Checklist перед публикацией в AUR

- [ ] Код работает корректно
- [ ] Все зависимости указаны в PKGBUILD
- [ ] setup.py содержит правильные метаданные
- [ ] Создан релиз на GitHub
- [ ] Вычислен sha256sum архива
- [ ] Обновлен PKGBUILD (URL, sha256sums)
- [ ] Протестирована локальная сборка (`makepkg -si`)
- [ ] Создан .SRCINFO (`makepkg --printsrcinfo`)
- [ ] Добавлен README.md с инструкциями
- [ ] Добавлен LICENSE файл

## 🎨 Добавление собственной иконки (опционально)

1. Создайте иконку 256x256 px: `icons/pass-kb.png`
2. Обновите `setup.py`:
```python
data_files=[
    ("share/applications", ["pass-kb.desktop"]),
    ('share/icons/hicolor/256x256/apps', ['icons/pass-kb.png']),
]
```
3. Обновите `pass-kb.desktop`:
```ini
Icon=pass-kb  # вместо dialog-password
```
4. Обновите PKGBUILD (добавьте в `package()`):
```bash
install -Dm644 icons/pass-kb.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/pass-kb.png"
```

## 📚 Полезные ссылки

- [AUR Submission Guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [PKGBUILD Manual](https://wiki.archlinux.org/title/PKGBUILD)
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)
