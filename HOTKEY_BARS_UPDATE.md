# Обновление системы подсказок хоткеев

## Изменения

### Проблема
Ранее каждое модальное окно имело свои собственные бары с подсказками по хоткеям внизу диалога. Это создавало визуальный шум и дублирование информации.

### Решение
Теперь подсказки по хоткеям всех модальных окон отображаются в барах основного окна приложения. При открытии диалога:
1. Сохраняется текущее состояние баров основного окна
2. Бары обновляются информацией о хоткеях диалога
3. После закрытия диалога восстанавливается предыдущее состояние

### Технические детали

#### Модифицированные диалоги

1. **PasswordGeneratorDialog** (`components/password_generator_dialog.py`)
   - Удалены собственные HotkeyHelpWidget
   - Добавлен статический метод `get_hotkey_info()` для предоставления информации о хоткеях
   - Возвращает:
     - Navigation: "Up/Down - Navigate fields | Left/Right - Adjust length | Space - Toggle option"
     - Actions: "Enter - Copy & close | Ctrl+C - Copy | Esc - Cancel"

2. **ConfirmationDialog** (`components/confirmation_dialog.py`)
   - Удален собственный HotkeyHelpWidget
   - Добавлен метод `get_hotkey_info()` (не статический, т.к. зависит от наличия третьей кнопки)
   - Возвращает:
     - С кнопкой Save: "Enter - Confirm | Ctrl+S - Save | Esc - Cancel"
     - Без: "Enter - Confirm | Esc - Cancel"

#### Основное окно (`pass_client.py`)

Добавлен новый метод `_exec_dialog_with_hotkeys(dialog)`:
```python
def _exec_dialog_with_hotkeys(self, dialog):
    # Сохраняет текущее состояние баров
    # Обновляет бары информацией из dialog.get_hotkey_info()
    # Выполняет dialog.exec()
    # Восстанавливает предыдущее состояние баров
    # Возвращает результат диалога
```

Этот callback передается во все дочерние виджеты через параметр `exec_dialog_callback`.

#### Дочерние виджеты

**SecretDetailWidget** и **SecretCreateWidget**:
- Добавлен параметр `exec_dialog_callback` в конструктор
- Все вызовы `dialog.exec()` заменены на `self.exec_dialog_callback(dialog)`

### Преимущества

1. **Единообразие UX** - пользователь всегда смотрит в одно место для подсказок
2. **Меньше визуального шума** - диалоги стали чище и компактнее
3. **Адаптивность** - бары в основном окне автоматически переносят текст при узком экране
4. **Централизованное управление** - вся логика обновления баров в одном месте

### Пример использования

```python
# Открытие диалога с автоматическим обновлением баров хоткеев
dialog = PasswordGeneratorDialog(self, show_status_callback=self.show_status)
self._exec_dialog_with_hotkeys(dialog)

# Для диалога с параметрами
dialog = ConfirmationDialog(self, text="Delete?", confirm_text="Yes")
result = self._exec_dialog_with_hotkeys(dialog)
if result == QDialog.Accepted:
    # Действие подтверждено
```

### Совместимость

Все существующие диалоги теперь используют централизованный механизм. Старый код полностью удален, дублирования нет.
