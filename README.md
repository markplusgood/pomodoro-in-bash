# Terminal Timer

A terminal-based Pomodoro and simple countdown timers, complete with sound effects and interactive controls.

## Features

- **Pomodoro Timer**: Work/break sessions with custom durations
- **Countdown Timer**: Simple countdown with time input (minutes/seconds)
- **Interactive Controls**: Pause/resume with 'p' key, cancel with Ctrl+C
- **Sound Effects**: Audio notifications for session starts, completions, transitions, and reminders
- **Colorful Output**: ANSI color codes for enhanced terminal experience
- **Cross-Platform**: Works on Linux/macOS with mpg123 for audio, yes that includes Omarchy

## Installation

1. **Clone or download** the repository to your local machine.

2. **Install dependencies**:
   - Python 3.x
   - `mpg123` for audio playback: `sudo apt-get install mpg123` (Ubuntu/Debian) or `brew install mpg123` (macOS) or `pacman -Syu mpg123` (Omarchy)

3. **Make scripts executable**:
   ```bash
   chmod +x pom.py tpom tcount
   ```

4. **Add the script directory to your PATH for global access**:
   Add `path/to/timer/scripts` to your `PATH="$PATH:/...:$PATH` in the .bashrc or .bash_profile.

## Usage

### Pomodoro Timer

Run a Pomodoro session with work and break intervals:

```bash
# Using the main script
python3 pom.py tpom 25m 5m 4

# Or directly
timer tpom 25 5m 4
```

- `25m`: Work session length (25 minutes)
- `5m`: Break length (5 minutes)
- `4`: Number of work sessions

### Countdown Timer

Start a simple countdown:

```bash
# Using the main script
python3 pom.py tcount 10m

# Or directly
timer tcount 10m
```
- `10m`: Countdown duration (10 minutes)

#### Add aliases to skip typing 'timer' every time

Add this to your .bashrc or .bash_profile

```
alias 'tpom'='timer tpom'
alias 'tcount'='timer tcount'
```

### Time Formats

- Minutes: `25m` or `25` (assumes minutes)
- Seconds: `1500s`

### Interactive Controls

- **Pause/Resume**: Press `p` during countdown
- **Cancel**: Press `Ctrl+C` to exit
- **Continue**: Press `p` to proceed between sessions

## Sound Files

The script uses the following audio files (included in the repository):
- `aight-let-s-do-it.mp3`: Session start
- `break-time.mp3`: Work complete
- `back-to-work.mp3`: Break complete
- `bell.mp3`: Countdown start
- `gong.mp3`: Countdown complete
- `have-a-good-one.mp3`: Session end
- `are-you-winning-son.mp3`: Random work complete (10% chance)

## Contributing

We welcome contributions! Feel free to:

- Report bugs or suggest features
- Submit pull requests for improvements
- Share your experience using the timer
- Help improve documentation

Please open an issue or submit a PR on GitHub.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License. See the [LICENSE.md](LICENSE.md) file for details.
### Source

https://github.com/markplusgood/pomodoro-in-bash
