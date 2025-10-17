# Pass Suite - Arch User Repository (AUR) Guide

Это руководство описывает как добавить Pass Suite в AUR и как пользователи будут его устанавливать.

## 📦 Как работает интеграция с rofi/walker

Когда приложение правильно установлено, оно автоматически появляется в rofi/walker потому что:

1. **Desktop Entry** устанавливается в системную директорию:
   - System-wide: `/usr/share/applications/pass-suite.desktop`
   - User: `~/.local/share/applications/pass-suite.desktop`

2. **Desktop файл содержит** всю нужную информацию:
   ```ini
   [Desktop Entry]
   Name=Pass Suite           # Имя в лончере
   Exec=pass-suite          # Команда для запуска
   Icon=dialog-password     # Иконка
   Categories=Utility;Security;  # Категории
   ```

3. **Лончеры** (rofi, walker, dmenu_run и т.д.) автоматически сканируют:
   - `/usr/share/applications/`
   - `~/.local/share/applications/`
   - И находят все `.desktop` файлы

4. **После установки** приложение сразу доступно:
   - В rofi: просто начните печатать "Pass Suite"
   - В walker: так же
   - В меню GNOME/KDE/XFCE: появится в категории "Утилиты" или "Безопасность"

---

## 🚀 Быстрая Установка (для пользователей)

### Вариант 1: Интерактивная установка (Рекомендуется)

```bash
cd /home/mr/Hellkitchen/solution/pass/project
./install.sh
```

Выберите опцию:
- **1** - System-wide (требует sudo, доступно всем пользователям)
- **2** - User only (только для текущего пользователя)

### Вариант 2: Командная строка

```bash
# System-wide
./install.sh --system

# User only
./install.sh --user

# Проверка зависимостей
./install.sh --check

# Удаление
./install.sh --uninstall
```

### Вариант 3: Вручную

```bash
# Установить пакет
pip install .

# Установить desktop entry (system-wide)
sudo install -Dm644 pass-suite.desktop /usr/share/applications/pass-suite.desktop
sudo update-desktop-database /usr/share/applications

# Или для пользователя
install -Dm644 pass-suite.desktop ~/.local/share/applications/pass-suite.desktop
update-desktop-database ~/.local/share/applications
```

---

## 📋 Публикация в AUR

### Шаг 1: Создайте Git репозиторий

```bash
# Создать репозиторий на GitHub/GitLab
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/pass-suite.git
git push -u origin main

# Создать релиз (tag)
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Шаг 2: Создайте source tarball

GitHub автоматически создаст:
`https://github.com/username/pass-suite/archive/v1.0.0.tar.gz`

### Шаг 3: Получите SHA256

```bash
wget https://github.com/username/pass-suite/archive/v1.0.0.tar.gz
sha256sum v1.0.0.tar.gz
```

Обновите в `PKGBUILD`:
```bash
sha256sums=('полученный_хэш_здесь')
```

### Шаг 4: Протестируйте PKGBUILD локально

```bash
# В директории с PKGBUILD
makepkg -si

# После установки проверьте:
pass-suite        # Должно запуститься
rofi -show drun   # "Pass Suite" должен быть в списке
```

### Шаг 5: Создайте AUR репозиторий

```bash
# Клонируйте пустой AUR repo
git clone ssh://aur@aur.archlinux.org/pass-suite.git
cd pass-suite

# Скопируйте файлы
cp /path/to/PKGBUILD .
cp /path/to/.SRCINFO .  # Будет создан автоматически

# Создайте .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Закоммитьте и пушьте
git add PKGBUILD .SRCINFO
git commit -m "Initial import: Pass Suite v1.0.0"
git push
```

### Шаг 6: Пользователи установят через AUR helper

```bash
# С yay
yay -S pass-suite

# С paru
paru -S pass-suite

# Или вручную
git clone https://aur.archlinux.org/pass-suite.git
cd pass-suite
makepkg -si
```

---

## 🔍 Структура установки

После установки через `install.sh --system`:

```
/usr/
├── local/
│   └── bin/
│       └── pass-suite              # Исполняемый файл (entry point)
├── lib/
│   └── python3.11/
│       └── site-packages/
│           ├── pass_client.py      # Основной код
│           ├── components/         # Компоненты UI
│           └── pass_suite-1.0.0.dist-info/
└── share/
    └── applications/
        └── pass-suite.desktop      # Desktop entry для лончеров
```

После установки через `install.sh --user`:

```
~/.local/
├── bin/
│   └── pass-suite                  # Исполняемый файл
├── lib/
│   └── python3.11/
│       └── site-packages/
│           └── ...                 # Python код
└── share/
    └── applications/
        └── pass-suite.desktop      # Desktop entry
```

---

## 🛠️ Как это работает изнутри

### Entry Point (команда `pass-suite`)

В `setup.py` определен entry point:
```python
entry_points={
    'console_scripts': [
        'pass-suite=pass_client:main',
    ],
},
```

pip автоматически создаёт исполняемый файл `pass-suite` в:
- System: `/usr/local/bin/pass-suite` или `/usr/bin/pass-suite`
- User: `~/.local/bin/pass-suite`

### Desktop Entry

Файл `pass-suite.desktop` содержит:
```ini
Exec=pass-suite  # Запускает команду из $PATH
```

### Сканирование лончерами

Все modern launchers (rofi, walker, dmenu, etc.) сканируют:
1. `/usr/share/applications/` (system apps)
2. `/usr/local/share/applications/` (locally installed apps)
3. `~/.local/share/applications/` (user apps)
4. `$XDG_DATA_DIRS/applications/` (custom dirs)

И автоматически показывают все найденные `.desktop` файлы.

---

## 🎯 Troubleshooting

### Приложение не появляется в rofi/walker

**Проверка 1:** Установлен ли desktop file?
```bash
# System
ls -la /usr/share/applications/pass-suite.desktop

# User
ls -la ~/.local/share/applications/pass-suite.desktop
```

**Проверка 2:** Обновлён ли desktop database?
```bash
# System
sudo update-desktop-database /usr/share/applications

# User
update-desktop-database ~/.local/share/applications
```

**Проверка 3:** Доступна ли команда?
```bash
which pass-suite
pass-suite --help
```

**Проверка 4:** Правильный ли desktop файл?
```bash
desktop-file-validate ~/.local/share/applications/pass-suite.desktop
```

### Команда pass-suite не найдена

**Для user installation:**
```bash
# Проверьте PATH
echo $PATH | grep -o "$HOME/.local/bin"

# Если не найдено, добавьте в ~/.bashrc или ~/.zshrc:
export PATH="$HOME/.local/bin:$PATH"

# Перезагрузите shell:
source ~/.bashrc
```

**Для system installation:**
```bash
# Переустановите с sudo
sudo pip install .
```

### Иконка не отображается

Desktop файл использует стандартную иконку `dialog-password`.

Чтобы использовать свою иконку:
1. Создайте иконку: `icons/pass-suite.png` (256x256px)
2. Обновите `setup.py`:
   ```python
   data_files=[
       ('share/applications', ['pass-suite.desktop']),
       ('share/icons/hicolor/256x256/apps', ['icons/pass-suite.png']),
   ],
   ```
3. Обновите `pass-suite.desktop`:
   ```ini
   Icon=pass-suite  # Вместо dialog-password
   ```
4. Переустановите

---

## 📝 Обновление в AUR

Когда выходит новая версия:

```bash
# 1. Обновите версию в setup.py и pyproject.toml
# 2. Создайте новый git tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1

# 3. Получите новый SHA256
wget https://github.com/username/pass-suite/archive/v1.0.1.tar.gz
sha256sum v1.0.1.tar.gz

# 4. Обновите PKGBUILD
pkgver=1.0.1
pkgrel=1
sha256sums=('новый_хэш')

# 5. Обновите .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# 6. Коммит и пуш в AUR
git add PKGBUILD .SRCINFO
git commit -m "Update to v1.0.1"
git push
```

Пользователи обновят:
```bash
yay -Syu pass-suite
```

---

## ✅ Чеклист публикации

- [ ] Код работает без ошибок
- [ ] README.md актуален
- [ ] Версия обновлена в setup.py и pyproject.toml
- [ ] Создан git tag для релиза
- [ ] PKGBUILD протестирован локально (`makepkg -si`)
- [ ] SHA256 правильный в PKGBUILD
- [ ] .SRCINFO создан (`makepkg --printsrcinfo > .SRCINFO`)
- [ ] Desktop file проверен (`desktop-file-validate`)
- [ ] Приложение появляется в rofi/walker после установки
- [ ] Все зависимости указаны в PKGBUILD
- [ ] Создан аккаунт на aur.archlinux.org
- [ ] SSH ключ добавлен в AUR аккаунт
- [ ] AUR репозиторий создан и запушен

После этого ваше приложение будет доступно всем пользователям Arch Linux! 🎉
