# 📋 Planify Widget

A native GTK4 + Libadwaita desktop companion for **Planify** that lets you manage tasks directly from your desktop.

## ✨ Features
- View, add, edit and complete Planify tasks
- Search and filter tasks
- Desktop widget mode
- Progress tracking
- Live synchronization with the Planify database
- GTK4 + Libadwaita native interface

## 🚀 Installation

### Prerequisites
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 sqlite3
```

### Clone
```bash
git clone https://github.com/YOUR_USERNAME/planify-widget.git
cd planify-widget
python3 app.py
```

## 📂 Project Structure
```text
planify-widget/
├── app.py
├── config.py
├── database.py
├── controllers/
├── ui/
├── styles.css
├── scripts/
└── flatpak/
```

## 🏗 Architecture
MVC Architecture

View (GTK4 UI)
↓
Controller
↓
Database
↓
Planify SQLite Database

## 📊 Current Status

| Feature | Status |
|---------|--------|
| Database Integration | ✅ |
| GTK4 UI | ✅ |
| Task CRUD | ✅ |
| Search & Filter | ✅ |
| Live Sync | ✅ |
| Widget Mode | ✅ |
| Flatpak Packaging | 🚧 |
| DBus Integration | 📋 Planned |

## 🗺 Roadmap
### Phase 1
- Database integration
- Task loading
- Statistics

### Phase 2
- GTK4 interface
- Task cards
- Controller layer

### Phase 3
- CRUD operations

### Phase 4
- Rich task cards

### Phase 5
- Search and filtering

### Phase 6
- Live synchronization

### Phase 7
- Desktop widget mode

### Phase 8
- Packaging

### Phase 9
- DBus integration

## 🤝 Contributing
1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

## 📄 License
GPL v3