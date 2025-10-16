# Полная карта хоткеев для всех экранов и режимов

## 🔍 Search View (search)
**Navigation:**
- ↑/↓ - Navigate through secrets list
- Enter - View selected secret

**Actions:**
- Ctrl+N - Create new secret
- Ctrl+R - Sync with remote
- Ctrl+G - Generate password (simple)
- Ctrl+Shift+G - Generate password (advanced)

---

## 📄 Detail View

### Mode: Normal (normal)
**Navigation:**
- ↑/↓ - Navigate between fields
- Tab - Next field
- Shift+Tab - Previous field
- Esc - Back to search

**Actions:**
- Enter - Copy field value
- Ctrl+C - Copy to clipboard
- Ctrl+E - Edit field value
- Ctrl+Shift+E - Deep edit (edit key + value)
- Ctrl+T - Toggle visibility (password fields)
- Ctrl+N - Add new field
- Ctrl+D - Delete field
- Ctrl+S - Save changes

### Mode: Edit (edit)
**Navigation:**
- (none - focus locked on editing field)

**Actions:**
- Enter - Confirm edit
- Esc - Cancel edit
- Tab - (native input navigation)

### Mode: Deep Edit (deep_edit)
**Navigation:**
- Tab - Switch between key/value inputs
- Shift+Tab - Switch backward

**Actions:**
- Enter - Confirm changes
- Esc - Cancel deep edit
- Ctrl+D - Delete field

### Mode: Add New Field (add_new)
**Navigation:**
- Tab - Switch between key/value inputs
- Shift+Tab - Switch backward

**Actions:**
- Enter - Confirm new field
- Esc - Cancel (delete empty field)
- Ctrl+N - Add another field (if current is valid)

---

## ➕ Create View

### Mode: Create - Navigation Mode (create)
**Navigation:**
- ↑/↓ - Navigate between sections (tags, resource, fields)
- Tab - Next field
- Shift+Tab - Previous field
- Esc - Back to search (with confirmation if dirty)

**Actions:**
- Enter - Activate section / Add tag
- Ctrl+E - Enter editing mode for focused field
- Ctrl+T - Add new tag (when tags section focused)
- Ctrl+N - Add new field
- Ctrl+S - Save resource

### Mode: Create - Tags Interaction (create_tags)
**Navigation:**
- ↑/↓ - Navigate tags
- Tab - Next tag
- Shift+Tab - Previous tag
- Esc - Exit tags section

**Actions:**
- Enter - Select/deselect tag
- Ctrl+T - Add new namespace
- Space - Toggle tag selection

### Mode: Create - Editing (create_editing)
**Navigation:**
- Tab - (native input navigation)

**Actions:**
- Enter - Confirm edit / next field
- Esc - Cancel edit
- Ctrl+G - Generate password (if password field)

### Mode: Create - New Field (create_new_field)
**Navigation:**
- Tab - Switch between key/value
- Shift+Tab - Switch backward

**Actions:**
- Enter - Confirm field
- Esc - Delete empty field / Cancel
- Ctrl+N - Add another field

---

## 🎯 Priority States (порядок важности)

### Phase 1 (Critical - Must have):
1. ✅ search
2. ✅ normal (detail)
3. ✅ edit (detail)
4. ✅ deep_edit (detail)
5. ✅ add_new (detail)
6. ⚠️ create (partial)

### Phase 2 (Important - Should have):
7. ❌ create_tags (not implemented)
8. ❌ create_editing (not implemented)
9. ❌ create_new_field (not implemented)

### Phase 3 (Nice to have):
10. Enhanced visuals (icons, better separation)
11. Contextual tooltips
12. Keyboard shortcuts cheatsheet dialog
