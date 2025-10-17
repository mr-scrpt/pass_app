# Унификация кеймапов между страницами

## Изменения

### Проблема
Ранее на странице просмотра ресурса (SecretDetailWidget) и странице создания ресурса (SecretCreateWidget) использовались разные горячие клавиши для одинаковых действий, что создавало путаницу.

### Решение
Унифицированы кеймапы для обеих страниц, чтобы одинаковые действия выполнялись одинаковыми клавишами.

## Таблица изменений

### Режим навигации (Normal/Create)

| Действие | Было (Detail) | Было (Create) | **СТАЛО (оба)** |
|----------|---------------|---------------|-----------------|
| Войти в режим редактирования | `Enter` копировал | `Enter` активировал | ✨ **Enter - Edit** |
| Копировать в буфер | `Enter` | - | ✨ **Ctrl+C - Copy** |
| Deep Edit / Редактирование ключа | `Ctrl+Shift+E` | - | ✨ **Ctrl+E - Deep Edit** |
| Простое редактирование | `Ctrl+E` | - | ❌ Удалено (теперь Enter) |

### Новые кеймапы

#### SecretDetailWidget (страница информации о ресурсе)

**Режим навигации:**
- `Enter` - войти в режим редактирования поля ✨ **НОВОЕ**
- `Ctrl+C` - скопировать значение в буфер ✨ **НОВОЕ**
- `Ctrl+E` - войти в режим глубокого редактирования (редактирование ключа и значения) ✨ **ИЗМЕНЕНО**
- `Ctrl+T` - переключить видимость (password/text)
- `Ctrl+N` - добавить новое поле
- `Ctrl+D` - удалить поле
- `Ctrl+S` - сохранить изменения
- `Esc` - вернуться назад

#### SecretCreateWidget (страница создания ресурса)

**Режим навигации:**
- `Enter` - войти в режим редактирования текущего поля ✨ **БЕЗ ИЗМЕНЕНИЙ**
- `Ctrl+T` - добавить тег
- `Ctrl+N` - добавить новое поле
- `Ctrl+S` - сохранить новый ресурс
- `Ctrl+G` - генерировать пароль
- `Esc` - вернуться назад

## Технические детали

### Изменения в SecretDetailWidget

**Файл:** `components/secret_detail_view.py`

**Было:**
```python
if key in (Qt.Key_Return, Qt.Key_Enter):
    self._copy_to_clipboard(row_data["le"].text())  # Enter копировал
    return

if modifiers == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_E:
    self._enter_deep_edit_mode(self.current_field_index)  # Ctrl+Shift+E для deep edit
    return

if modifiers == Qt.ControlModifier:
    # ...
    elif key == Qt.Key_E:
        self._enable_editing(row_data["le"])  # Ctrl+E для простого редактирования
```

**Стало:**
```python
if key in (Qt.Key_Return, Qt.Key_Enter):
    self._enable_editing(row_data["le"])  # Enter для редактирования
    return

if modifiers == Qt.ControlModifier:
    # ...
    elif key == Qt.Key_C:
        self._copy_to_clipboard(row_data["le"].text())  # Ctrl+C для копирования
    elif key == Qt.Key_E:
        self._enter_deep_edit_mode(self.current_field_index)  # Ctrl+E для deep edit
```

### Изменения в подсказках (pass_client.py)

**Normal mode (страница просмотра ресурса):**
```python
# Было:
"action": "Enter - Copy  |  Ctrl+E - Edit  |  Ctrl+Shift+E - Deep Edit  |  ..."

# Стало:
"action": "Enter - Edit  |  Ctrl+C - Copy  |  Ctrl+E - Deep Edit  |  ..."
```

**Create mode (страница создания ресурса):**
```python
# Было:
"action": "Enter - Activate  |  Ctrl+E - Edit  |  Ctrl+T - Add Tag  |  ..."

# Стало:
"action": "Enter - Edit  |  Ctrl+T - Add Tag  |  ..."  # Убрали дублирование
```

### Исправление стилизации Resource label

**Проблема:** На странице создания ресурса лейбл "Resource:" не становился желтым при редактировании.

**Решение:** 
1. Сделали `resource_label` атрибутом класса (`self.resource_label`)
2. Добавили изменение его стиля в методе `_on_editing_state_changed()`:

```python
# При редактировании:
self.resource_label.setStyleSheet(
    "color: #f9e2af; font-size: 16px; font-weight: bold; border: none;"
)

# При выходе из редактирования:
self.resource_label.setStyleSheet(
    f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;"
)
```

## Преимущества

1. **Единообразие** - одинаковые действия теперь выполняются одинаковыми клавишами
2. **Интуитивность** - `Enter` всегда активирует режим редактирования
3. **Логичность** - `Ctrl+C` - стандартная клавиша для копирования
4. **Упрощение** - `Ctrl+E` для расширенного редактирования (без Shift)
5. **Визуальная согласованность** - лейбл Resource теперь тоже становится желтым

## Совместимость

Изменения обратно несовместимы с предыдущими версиями в части горячих клавиш. Пользователям нужно будет запомнить новые кеймапы:
- `Enter` теперь **не копирует**, а **редактирует**
- Для копирования используйте `Ctrl+C`
- Для deep edit используйте `Ctrl+E` (без Shift)
