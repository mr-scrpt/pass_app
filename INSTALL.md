# Installation Guide for Pass Keyboard Control

## Prerequisites

Before installing Pass Keyboard Control, make sure you have:

1. **Python 3.8+** installed
2. **pass** (password-store) installed and configured
3. **GPG** key set up with pass
4. **Git** (optional, for synchronization)

### Check Prerequisites

```bash
# Check Python version
python3 --version

# Check if pass is installed
pass --version

# Check if GPG is configured
gpg --list-keys
```

## Installation Methods

### Method 1: Install from Source (Recommended for Users)

```bash
cd /home/mr/Hellkitchen/solution/pass/project

# Install dependencies
pip install -r requirements.txt

# Install Pass Keyboard Control
pip install .

# Run the application
pass-suite
```

### Method 2: Install in Development Mode (Recommended for Developers)

```bash
cd /home/mr/Hellkitchen/solution/pass/project

# Install in editable mode
pip install -e .

# Now you can edit the code and see changes immediately
pass-suite
```

### Method 3: Build and Install Standalone Executable

```bash
cd /home/mr/Hellkitchen/solution/pass/project

# Build executable
./build_executable.sh

# Run directly
./dist/pass-suite

# OR install system-wide
sudo cp dist/pass-suite /usr/local/bin/
pass-suite
```

### Method 4: Build Wheel Package

```bash
cd /home/mr/Hellkitchen/solution/pass/project

# Build wheel
./build_package.sh

# Install the wheel
pip install dist/pass_keyboard_control-*.whl
```

## Post-Installation

### Create Desktop Entry (Linux)

Create `~/.local/share/applications/pass-suite.desktop`:

```ini
[Desktop Entry]
Name=Pass Keyboard Control
Comment=Modern GUI for Unix password manager
Exec=pass-suite
Icon=dialog-password
Terminal=false
Type=Application
Categories=Utility;Security;
Keywords=password;manager;pass;gpg;
```

### Create Symlink (Alternative)

```bash
# If installed with pip
which pass-suite

# If using executable
sudo ln -s /path/to/dist/pass-suite /usr/local/bin/pass-suite
```

## Troubleshooting

### Qt Platform Plugin Error

If you see "could not find or load the Qt platform plugin":

```bash
# Install required Qt libraries
sudo apt-get install libxcb-xinerama0 libxcb-cursor0
```

### Import Errors

If you get import errors:

```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

### Permission Issues

If `pass` commands fail:

```bash
# Check password store permissions
ls -la ~/.password-store

# Check GPG key
gpg --list-keys
pass init <your-gpg-id>
```

## Uninstallation

### If installed with pip

```bash
pip uninstall pass-suite
```

### If installed as executable

```bash
sudo rm /usr/local/bin/pass-suite
rm ~/.local/share/applications/pass-suite.desktop
```

## Distribution to Other Machines

### Option 1: Share Wheel Package

```bash
# On source machine
./build_package.sh

# Copy dist/pass_keyboard_control-*.whl to target machine
# On target machine
pip install pass_keyboard_control-*.whl
```

### Option 2: Share Standalone Executable

```bash
# On source machine
./build_executable.sh

# Copy dist/pass-suite to target machine
# On target machine
chmod +x pass-suite
./pass-suite

# Or install system-wide
sudo cp pass-suite /usr/local/bin/
```

### Option 3: Git Repository

```bash
# On target machine
git clone <your-repo-url>
cd pass-suite
pip install .
```

## System-wide Installation

For system-wide installation (all users):

```bash
# Build executable
./build_executable.sh

# Install to /opt
sudo mkdir -p /opt/pass-suite
sudo cp dist/pass-suite /opt/pass-suite/
sudo ln -s /opt/pass-suite/pass-suite /usr/local/bin/pass-suite

# Create desktop entry
sudo cp pass-suite.desktop /usr/share/applications/
```

## Docker Installation (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    pass \
    gnupg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install .

CMD ["pass-suite"]
```

Build and run:

```bash
docker build -t pass-suite .
docker run -it --rm \
    -v ~/.password-store:/root/.password-store \
    -v ~/.gnupg:/root/.gnupg \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    pass-suite
```
