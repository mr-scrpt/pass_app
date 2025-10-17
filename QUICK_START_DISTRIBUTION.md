# Быстрый старт: Публикация в AUR

## ✅ Что уже готово

У вас УЖЕ есть все необходимые файлы:
- ✅ `setup.py` - конфигурация установки Python
- ✅ `PKGBUILD` - рецепт сборки для Arch Linux
- ✅ `pass-kb.desktop` - файл для меню приложений и Rofi
- ✅ `main()` функция в `pass_client.py` - точка входа

## 🚀 Минимальные шаги для публикации

### 1. Локальное тестирование (СНАЧАЛА!)

```bash
# Установите локально для тестирования
pip install -e .

# Запустите
pass-kb

# Проверьте, что всё работает
```

### 2. Создайте репозиторий на GitHub

```bash
# Инициализируйте git (если еще не сделали)
git init
git add .
git commit -m "Initial commit"

# Создайте репозиторий на GitHub: https://github.com/new
# Назовите его, например: pass-suite

# Свяжите локальный репозиторий с GitHub
git remote add origin git@github.com:ВАШ_USERNAME/pass-suite.git
git branch -M main
git push -u origin main
```

### 3. Создайте первый релиз

На GitHub:
1. Перейдите в "Releases" → "Create a new release"
2. Tag version: `v1.0.0`
3. Release title: `v1.0.0 - Initial Release`
4. Опишите изменения
5. Нажмите "Publish release"

### 4. Обновите PKGBUILD

```bash
# Скачайте ваш релиз
wget https://github.com/ВАШ_USERNAME/pass-suite/archive/v1.0.0.tar.gz

# Вычислите sha256sum
sha256sum v1.0.0.tar.gz
# Вывод: abc123def456... v1.0.0.tar.gz

# Отредактируйте PKGBUILD:
nano PKGBUILD
```

Измените строки:
```bash
# Maintainer: Ваше Имя <ваш@email.com>
url="https://github.com/ВАШ_USERNAME/pass-suite"
sha256sums=('сюда_вставьте_вычисленный_хеш')
```

### 5. Протестируйте сборку

```bash
# В директории с PKGBUILD
makepkg -si

# Это соберет и установит пакет
# Протестируйте:
pass-kb

# Проверьте в Rofi:
rofi -show drun
# Начните печатать "pass"
```

### 6. Публикация в AUR (если всё работает)

```bash
# 1. Создайте аккаунт: https://aur.archlinux.org/register/

# 2. Добавьте SSH ключ в профиль AUR
# https://aur.archlinux.org/account/

# 3. Клонируйте (замените ИМЯ_ПАКЕТА на ваше)
git clone ssh://aur@aur.archlinux.org/pass-cli-with-keyboard-total-control.git aur-package
cd aur-package

# 4. Скопируйте файлы
cp ../PKGBUILD .

# 5. Создайте .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# 6. Commit и push
git add PKGBUILD .SRCINFO
git commit -m "Initial release v1.0.0"
git push origin master
```

## 📱 Как пользователи будут устанавливать

После публикации в AUR, любой пользователь Arch Linux сможет установить:

```bash
# Используя yay (AUR helper)
yay -S pass-cli-with-keyboard-total-control

# Или paru
paru -S pass-cli-with-keyboard-total-control

# Вручную
git clone https://aur.archlinux.org/pass-cli-with-keyboard-total-control.git
cd pass-cli-with-keyboard-total-control
makepkg -si
```

После установки:
- Команда `pass-kb` доступна в терминале
- Появится в меню приложений (категория Utility → Security)
- Будет виден в Rofi при поиске

## 🔄 Обновление версии

Когда выпускаете новую версию:

```bash
# 1. Обновите версию в setup.py
nano setup.py
# version="1.1.0"

# 2. Сделайте commit и tag
git add .
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags

# 3. Создайте релиз на GitHub (как в шаге 3)

# 4. Обновите PKGBUILD
# - pkgver=1.1.0
# - новый sha256sum

# 5. Обновите AUR
cd aur-package
cp ../PKGBUILD .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Update to v1.1.0"
git push
```

## 🛠️ Полезные команды

```bash
# Проверить desktop file
desktop-file-validate pass-kb.desktop

# Обновить кеш приложений
update-desktop-database ~/.local/share/applications/

# Удалить локальную установку
pip uninstall pass-cli-with-keyboard-total-control

# Удалить системную установку (AUR)
yay -R pass-cli-with-keyboard-total-control

# Пересобрать пакет
makepkg -f
```

## ⚠️ Важные моменты

1. **Тестируйте локально** перед публикацией в AUR
2. **Проверьте зависимости** - все ли пакеты доступны в official repos или AUR
3. **Обновляйте .SRCINFO** при каждом изменении PKGBUILD
4. **Версионирование** - используйте semantic versioning (1.0.0, 1.1.0, 2.0.0)
5. **Описывайте изменения** в релизах на GitHub

## 🎯 Минимальный чеклист

- [ ] Код работает (`pass-kb` запускается без ошибок)
- [ ] Создан репозиторий на GitHub
- [ ] Создан первый релиз (v1.0.0)
- [ ] Обновлен URL в PKGBUILD
- [ ] Обновлен sha256sum в PKGBUILD
- [ ] Протестирована локальная сборка (`makepkg -si`)
- [ ] Работает запуск через `pass-kb`
- [ ] Появляется в Rofi
- [ ] Создан аккаунт на AUR
- [ ] Добавлен SSH ключ в профиль AUR
- [ ] Опубликован в AUR

## 💡 Подсказка

Если не хотите сразу публиковать в AUR, можете:
1. Создать свой персональный репозиторий пакетов
2. Делиться PKGBUILD через GitHub
3. Пользователи смогут устанавливать вручную через `makepkg`

Удачи! 🚀
