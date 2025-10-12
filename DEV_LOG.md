# Development Log: pass-cli-suite

## ✅ Done

1.  **Backend (`pass_backend.py`) - Fully Complete & Verified**:
    *   Implemented all commands (`list`, `show`, `create`, `edit`, `delete`) using the real `pass` utility.
    *   Fixed bugs related to non-existent password stores and symlinks.
    *   Verified all testable commands via the terminal.

---

## 🚀 UI Redesign Plan

**New Concept**: The UI will be redesigned from a two-panel tree view into a single-view, search-oriented application.

**Key Features**:
1.  **Layout**: A search bar at the top, with a list of results below.
2.  **Search**: The list will filter in real-time as the user types in the search bar.
3.  **Details View**: Selecting a result will switch to a form-like view displaying the secret's details.
4.  **Form Fields**: Each detail (secret, metadata) will be in a read-only input field with "show/hide" and "copy to clipboard" buttons.

---

## ✅ Done

14. **UI - View Switching Architecture**:
    *   Implemented a `QStackedWidget` to manage views.
    *   On `Enter`, the client now correctly fetches secret data from the backend and switches to a placeholder details view.

---

## ➡️ Next Step

*   **UI (`pass_client.py`) - Step 4: Build Details Form**:
    *   Create a dynamic form widget for the details view.
    *   When data is received, this form will generate rows for each piece of data (secret, metadata).
    *   Each row will contain a read-only `QLineEdit`, a show/hide (eyeball) button, and a copy-to-clipboard button.
    *   The main secret field will be masked by default.

---

## 🚀 Future UI Steps

1.  **Data & Search**: Load all secrets into a flat list and implement the real-time search functionality.
2.  **Views Switching**: Implement a `QStackedWidget` to switch between the search/list view and the details view.
3.  **Details Form**: Build the dynamic details form with non-editable fields, show/hide buttons, and copy buttons.
4.  **Integration**: Connect all backend commands (`show`, `create`, `edit`, `delete`) to the UI elements.
