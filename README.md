# Terminal Timer

A minimalistic Pomodoro and countdown timer in terminal, with audio and GUI notifications and interactive controls.

## Features

### Core Functionality
- **Pomodoro Timer**: call 'tpom 45 15 4' to start 4 45-minute work sessions with 15-minute breaks; add 'a' to autostart timers
- **Countdown Timer**: start with tcount 1m or tcount 1 for 1 minute, 1s for 1 second
- **Interactive Controls**: Pause/resume with 'p' key, cancel with Ctrl+C
- **Notifications**: Audio and GUI notifications and reminders
- **Rich UI**: Real-time progress bars and ANSI color-coded terminal output

## Installation

### Prerequisites
1. **Python 3.x** (pre-installed on most Linux distributions)
2. **mpg123** for audio playback
3. **notify-send** for desktop notifications (optional, for Linux)
4. **Terminal**

### Installation

1. **Install required packages**:
   ```bash
   sudo pacman -S mpg123 libnotify
   ```

2. **Download and set up the script**:
   ```bash
   # Create a directory for the timer
   mkdir -p ~/bin/pomotimer
   cd ~/bin/pomotimer
   
   # Copy pomotimer.py and make executable
   chmod +x pomotimer.py
   ```

3. **Add to PATH**:
   Add to your `~/.bashrc`
   ```bash
   export PATH="$PATH:$HOME/bin/pom"
   ```

4. **Set up aliases**:
   Add to your `~/.bashrc`:
   ```bash
   alias 'tpom'='pomotimer tpom'
   alias 'tcount'='pomotimer tcount'
   ```

5. **Source it**:
   ```bash
   source ~/.bashrc
   ```

### Alternative System-Wide Installation
```bash
# Install to /usr/local/bin for system-wide access
sudo cp pomotimer.py /usr/local/bin/pom
sudo chmod +x /usr/local/bin/pom

# Create aliases
echo "alias 'tpom'='pomotimer tpom'" | sudo tee -a /etc/bash.bashrc
echo "alias 'tcount'='pomotimer tcount'" | sudo tee -a /etc/bash.bashrc
```

## Usage

### Pomodoro Timer

**Basic usage:**
```bash
# Using the main script
python3 pomotimer.py tpom 25m 5m 4

# Or with aliases (after setup)
tpom 25m 5m 4

# Or direct timer command
pomotimer tpom 25m 5m 4
```

**Parameters:**
- `25m`: Work session length (25 minutes)
- `5m`: Break length (5 minutes)  
- `4`: Number of work sessions
- `a`: Optional to start pomodoro timers automatically

**Autostart Example:**
```bash
# With autostart - no 'p' input is needed to continue
tpom 25m 5m 4 a
```

### Countdown Timer

**Basic usage:**
```bash
# Using the main script
python3 pomotimer.py tcount 10m

# Or with aliases
tcount 10m

# Or direct timer command
pomotimer tcount 10m
```

**Examples:**
```bash
# 30 minute countdown
tcount 30m

# 2 hour countdown  
tcount 120m

# 45 second countdown
tcount 45s

# 90 second countdown (90 seconds = 1.5 minutes)
tcount 1.5m
```

### Time Formats

- **Minutes**: `25m` or `25` (defaults to minutes)
- **Seconds**: `1500s` or `90s`
- **Decimal minutes**: `1.5m` (90 seconds)
- **Hours**: `2h` (120 minutes)

## Configuration Tips

### Power User Setup
```bash
# Add to ~/.bashrc for power user experience
alias tpom='pomotimer tpom'
alias tcount='pomotimer tcount'
alias work50='tpom 50m 10m 4'    # Custom work session
alias shortbreak='tcount 15m'    # Quick countdown
alias focus='tpom 25m 5m 8 a'    # Long focus session with autostart
```

## Troubleshooting

### Audio Issues
- **No sound**: Ensure `mpg123` is installed: `which mpg123`
- **Permission denied**: Check file permissions on audio files
- **Audio cuts off**: Normal behavior - sounds play asynchronously

### Display Issues
- **No colors**: Ensure your terminal supports ANSI colors
- **Progress bar not working**: Terminal may not support carriage return (\r)

### Permission Issues
- **Script won't execute**: `chmod +x pomotimer.py`
- **PATH not working**: Restart terminal or run `source ~/.bashrc`

### Notification Issues
- **No desktop notifications**: Install `libnotify`

## Contributing

I appreciate any input! Feel free to:
- Report bugs or suggest features
- Submit pull requests for improvements
- Share your experience using the timer

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License. See the [LICENSE.md](LICENSE.md) file for details.

### Source

https://github.com/markplusgood/pomodoro-in-bash