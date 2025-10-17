# Pass Suite - Distribution Guide

Это руководство описывает, как создать дистрибутив Pass Suite для установки на других машинах.

## 📦 Варианты Распространения

### 1. PyInstaller Executable (Рекомендуется) ⭐

**Плюсы:**
- ✅ Один исполняемый файл
- ✅ Не требует Python на целевой машине
- ✅ Включает все зависимости
- ✅ Прост в распространении

**Минусы:**
- ❌ Большой размер (~100-200 MB)
- ❌ Специфичен для платформы (Linux/Windows/macOS)

**Как создать:**

```bash
# Установить PyInstaller
pip install pyinstaller

# Собрать executable
./build_executable.sh

# Результат: dist/pass-suite
```

**Как распространять:**
```bash
# Скопировать на другую машину
scp dist/pass-suite user@target:/tmp/

# На целевой машине
chmod +x pass-suite
sudo cp pass-suite /usr/local/bin/

# Готово!
pass-suite
```

---

### 2. Pip Package (Wheel) ⭐⭐

**Плюсы:**
- ✅ Стандартный способ Python
- ✅ Малый размер (~1-5 MB)
- ✅ Автоматическая установка зависимостей
- ✅ Легко обновлять

**Минусы:**
- ❌ Требует Python на целевой машине
- ❌ Требует установку зависимостей

**Как создать:**

```bash
# Установить build
pip install build

# Собрать wheel
./build_package.sh

# Результат: dist/pass_suite-1.0.0-py3-none-any.whl
```

**Как распространять:**
```bash
# Способ 1: Локальная установка
pip install dist/pass_suite-1.0.0-py3-none-any.whl

# Способ 2: Через репозиторий (GitHub/GitLab)
pip install git+https://github.com/username/pass-suite.git

# Способ 3: Через PyPI (публично)
# Загрузить на PyPI:
pip install twine
twine upload dist/*

# Установка:
pip install pass-suite
```

---

### 3. Исходный Код + setup.py

**Плюсы:**
- ✅ Самый простой
- ✅ Пользователи могут изменять код
- ✅ Минимальный размер

**Минусы:**
- ❌ Требует Python и pip
- ❌ Пользователи должны сами собирать

**Как распространять:**

```bash
# Создать архив
tar -czf pass-suite-1.0.0.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='dist' \
    --exclude='build' \
    .

# На целевой машине
tar -xzf pass-suite-1.0.0.tar.gz
cd pass-suite-1.0.0
pip install .
```

---

### 4. AppImage (Linux Only)

**Плюсы:**
- ✅ Portable (не требует установки)
- ✅ Работает на любом Linux
- ✅ Включает все зависимости

**Как создать:**

```bash
# Использовать PyInstaller, затем упаковать в AppImage
# (требует дополнительные инструменты)
```

---

### 5. Docker Container

**Плюсы:**
- ✅ Изолированная среда
- ✅ Воспроизводимость
- ✅ Кросс-платформенность

**Минусы:**
- ❌ Требует Docker
- ❌ Сложности с GUI и GPG

**Dockerfile уже готов в INSTALL.md**

---

## 🚀 Быстрый Старт - Рекомендации

### Для личного использования на нескольких машинах:

**Вариант 1: PyInstaller Executable**
```bash
./build_executable.sh
# Копируем dist/pass-suite на другие машины
```

**Вариант 2: Git Repository**
```bash
# На каждой машине:
git clone <your-repo>
cd pass-suite
pip install .
```

---

### Для распространения друзьям/коллегам:

**Рекомендуется: PyInstaller Executable**
```bash
./build_executable.sh

# Отправить dist/pass-suite
# Инструкция для получателя:
chmod +x pass-suite
sudo cp pass-suite /usr/local/bin/
pass-suite
```

---

### Для публичного релиза:

**Рекомендуется: GitHub Release + Wheel**

1. Создать релиз на GitHub
2. Прикрепить файлы:
   - `pass-suite` (executable)
   - `pass_suite-1.0.0-py3-none-any.whl`
   - `pass-suite-1.0.0.tar.gz` (source)

3. В README указать:
```bash
# Вариант 1: Executable
wget https://github.com/user/pass-suite/releases/download/v1.0.0/pass-suite
chmod +x pass-suite
sudo cp pass-suite /usr/local/bin/

# Вариант 2: Pip
pip install https://github.com/user/pass-suite/releases/download/v1.0.0/pass_suite-1.0.0-py3-none-any.whl

# Вариант 3: Из исходников
pip install git+https://github.com/user/pass-suite.git
```

---

## 📋 Чеклист перед Релизом

- [ ] Обновить версию в `setup.py` и `pyproject.toml`
- [ ] Обновить `README.md` с актуальной информацией
- [ ] Проверить все зависимости в `requirements.txt`
- [ ] Собрать и протестировать executable
- [ ] Собрать и протестировать wheel
- [ ] Создать CHANGELOG.md с изменениями
- [ ] Добавить скриншоты в README
- [ ] Протестировать установку на чистой системе
- [ ] Создать git tag для версии
- [ ] Создать GitHub Release

---

## 🔧 Структура Проекта для Дистрибуции

```
pass-suite/
├── pass_client.py              # Main app
├── pass_backend.py             # Backend
├── components/                 # UI components
├── setup.py                    # Setup script
├── pyproject.toml             # Modern Python config
├── requirements.txt           # Dependencies
├── MANIFEST.in                # Package data
├── README.md                  # Documentation
├── LICENSE                    # License
├── INSTALL.md                 # Installation guide
├── build_executable.sh        # Build script for exe
├── build_package.sh           # Build script for wheel
├── pass-suite.spec           # PyInstaller config
└── pass-suite.desktop        # Desktop entry
```

---

## 📝 Примеры Команд

### Создать все типы дистрибутивов:

```bash
# 1. Executable
./build_executable.sh

# 2. Wheel package
./build_package.sh

# 3. Source archive
python -m build --sdist

# Результат:
# dist/pass-suite                      (executable)
# dist/pass_suite-1.0.0-py3-none-any.whl   (wheel)
# dist/pass_suite-1.0.0.tar.gz         (source)
```

### Загрузить на PyPI:

```bash
# Test PyPI (сначала протестировать)
twine upload --repository testpypi dist/*

# Проверка установки
pip install --index-url https://test.pypi.org/simple/ pass-suite

# Production PyPI
twine upload dist/*
```

---

## 🐛 Troubleshooting

### PyInstaller не находит модули:

```bash
# Добавить в hidden imports в pass-suite.spec:
hiddenimports=[
    'PySide6.QtCore',
    'qt_material',
    'qtawesome',
]
```

### Большой размер executable:

```bash
# Использовать UPX для сжатия
upx=True  # в pass-suite.spec
```

### Ошибки импорта на целевой машине:

```bash
# Убедиться что все зависимости в requirements.txt
pip freeze > requirements.txt
```
