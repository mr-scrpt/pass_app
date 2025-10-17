# Pass Suite - Quick Start

## 🚀 Самый быстрый способ установить

### Для Arch Linux пользователей:

```bash
# Перейдите в директорию проекта
cd /home/mr/Hellkitchen/solution/pass/project

# Запустите установщик
./install.sh
```

Выберите:
- **Опция 1** (system-wide) - если хотите доступ для всех пользователей
- **Опция 2** (user only) - если только для себя

**Готово!** Приложение теперь доступно:
- ✅ В rofi - просто начните печатать "Pass Suite"
- ✅ В walker - так же
- ✅ В меню приложений вашего DE
- ✅ Через команду `pass-suite` в терминале

---

## 🎯 Что именно делает установщик?

1. **Устанавливает Python пакет**
   - Создаёт команду `pass-suite` в вашем PATH
   - Устанавливает все зависимости

2. **Устанавливает Desktop Entry**
   - System: `/usr/share/applications/pass-suite.desktop`
   - User: `~/.local/share/applications/pass-suite.desktop`

3. **Обновляет Desktop Database**
   - Чтобы rofi/walker сразу увидели приложение

---

## 📋 Альтернативные способы

### Способ 1: Одной командой (system-wide)
```bash
./install.sh --system
```

### Способ 2: Одной командой (user only)
```bash
./install.sh --user
```

### Способ 3: Через pip напрямую
```bash
# User installation
pip install --user .
mkdir -p ~/.local/share/applications
cp pass-suite.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications

# System installation
sudo pip install .
sudo cp pass-suite.desktop /usr/share/applications/
sudo update-desktop-database /usr/share/applications
```

---

## 🔧 Проверка установки

После установки проверьте:

```bash
# 1. Команда доступна?
which pass-suite
pass-suite --help  # Должно открыть приложение или показать help

# 2. Desktop файл на месте?
ls ~/.local/share/applications/pass-suite.desktop  # Для user
ls /usr/share/applications/pass-suite.desktop      # Для system

# 3. Появился в rofi?
rofi -show drun | grep "Pass Suite"
```

---

## ❌ Удаление

```bash
# Интерактивное удаление
./install.sh --uninstall

# Или вручную
pip uninstall pass-suite
rm ~/.local/share/applications/pass-suite.desktop
# или
sudo rm /usr/share/applications/pass-suite.desktop
```

---

## 🐛 Проблемы?

### "pass-suite: command not found"

**Для user installation:**
```bash
# Добавьте в ~/.bashrc или ~/.zshrc:
export PATH="$HOME/.local/bin:$PATH"

# Затем:
source ~/.bashrc
```

### "Не вижу в rofi"

```bash
# Обновите desktop database
update-desktop-database ~/.local/share/applications  # User
# или
sudo update-desktop-database /usr/share/applications  # System
```

### "Python ошибки"

```bash
# Переустановите зависимости
pip install --upgrade -r requirements.txt

# Затем переустановите
./install.sh
```

---

## 📚 Дальше

- Прочитайте `README.md` для полной документации
- Смотрите `AUR_GUIDE.md` для публикации в AUR
- Смотрите `INSTALL.md` для advanced установки

**Нажмите F1 в приложении** чтобы увидеть все горячие клавиши! 🎹
