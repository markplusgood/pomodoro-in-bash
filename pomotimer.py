#!/usr/bin/env python3
import argparse
import atexit
import time
import sys
import select
import subprocess
import tty
import termios
import os
import random
import shutil

sound_processes = []
autostart_mode = False

def cleanup_sounds():
    for p in sound_processes:
        p.terminate()

atexit.register(cleanup_sounds)

# --- UI & Style Constants ---
class Colors:
    PURPLE = '\x1b[95m'
    BLUE = '\x1b[94m'
    GREEN = '\x1b[92m'
    YELLOW = '\x1b[93m'
    RED = '\x1b[91m'
    BOLD = '\x1b[1m'
    ENDC = '\x1b[0m'

def parse_time(time_str):
    try:
        time_str = time_str.strip()
        if not time_str:
            raise ValueError("Time string cannot be empty")
            
        if time_str.endswith('s'):
            value = float(time_str[:-1])
        elif time_str.endswith('m'):
            value = float(time_str[:-1]) * 60
        else:
            # assume minutes if no suffix
            value = float(time_str) * 60
            
        if value <= 0:
            raise ValueError("Time value must be positive")
            
        return value
    except (ValueError, IndexError) as e:
        print(f"{Colors.RED}Error: Invalid time format '{time_str}'. Use format like '5m', '30s', or '25' (minutes).{Colors.ENDC}")
        sys.exit(1)

def play_sound(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    try:
        if not os.path.isfile(filepath):
            print(f"{Colors.YELLOW}Warning: Sound file not found: {filepath}{Colors.ENDC}")
            return
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Cannot access sound file {filepath}: {e}{Colors.ENDC}")
        return
    
    try:
        p = subprocess.Popen(['mpg123', '-q', filepath],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        sound_processes.append(p)
    except FileNotFoundError:
        print(f"{Colors.YELLOW}Warning: mpg123 not found. Install with: sudo pacman -S mpg123{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Failed to play sound {filepath}: {e}{Colors.ENDC}")

def play_detached_sound(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    try:
        if not os.path.isfile(filepath):
            return  # Silently skip missing files in detached mode
    except Exception:
        return
    
    try:
        subprocess.Popen(['mpg123', '-q', filepath],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)
    except (FileNotFoundError, Exception):
        pass  # Silently fail in detached mode

def notify(message):
    try:
        result = subprocess.run(['notify-send', '--app-name=pomotimer', '--expire-time=3000', message],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{Colors.YELLOW}Note: Desktop notifications may not be available{Colors.ENDC}")
    except FileNotFoundError:
        print(f"{Colors.YELLOW}Note: notify-send not found. Desktop notifications disabled{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.YELLOW}Note: Failed to send notification: {e}{Colors.ENDC}")

def dismiss_timer_notifications():
    """
    Dismiss all notifications from the pomotimer app only.
    Uses makoctl to list notifications and dismiss only those with app-name=pomotimer.
    """
    try:
        # Get list of current notifications
        result = subprocess.run(['makoctl', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            return
        
        # Parse the output to find pomotimer notification IDs
        lines = result.stdout.strip().split('\n')
        pomotimer_ids = []
        
        for i, line in enumerate(lines):
            if line.startswith('Notification ') and i + 1 < len(lines):
                if 'App name: pomotimer' in lines[i + 1]:
                    # Extract notification ID from "Notification 123: ..."
                    notification_id = line.split()[1].rstrip(':')
                    pomotimer_ids.append(notification_id)
        
        # Dismiss each pomotimer notification
        for notification_id in pomotimer_ids:
            subprocess.run(['makoctl', 'dismiss', '-n', notification_id], 
                         capture_output=True, text=True)
                         
    except (FileNotFoundError, Exception):
        pass  # Silently fail if makoctl not available or other errors occur

def get_work_complete_sound():
    if random.random() < 0.2:  # 20% chance
        return 'media/are-you-winning-son.mp3'
    else:
        return 'media/break-time.mp3'

def display_time(initial_total, remaining_seconds, message="", show_autostart_status=True, use_cursor_saving=False):
    global autostart_mode
    mins, secs = divmod(remaining_seconds, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    autostart_str = ""
    if show_autostart_status:
        status = f"{Colors.GREEN}ON{Colors.ENDC}" if autostart_mode else f"{Colors.RED}OFF{Colors.ENDC}"
        autostart_str = f" | Auto:{status}"

    full_str = ""
    if initial_total > 0:
        progress = int(((initial_total - remaining_seconds) / initial_total) * 100)
        width = 20
        filled = int((progress / 100.0) * width)
        bar = '▌' * filled + ' ' * (width - filled)
        full_str = f"    {Colors.BOLD}{Colors.YELLOW}{time_str}{Colors.ENDC} [{bar}] {progress}% {message}{autostart_str}"
    else:
        full_str = f"    {Colors.BOLD}{Colors.YELLOW}{time_str}{Colors.ENDC} {message}{autostart_str}"

    # Handle terminal width to prevent line wrapping issues
    terminal_width = shutil.get_terminal_size().columns
    if len(full_str) > terminal_width:
        full_str = full_str[:terminal_width-3] + "..."

    if use_cursor_saving:
        sys.stdout.write('\x1b[u\x1b[J' + full_str)
        sys.stdout.flush()
    else:
        sys.stdout.write(f'\x1b[2K{full_str}\r')
        sys.stdout.flush()

def countdown(total_seconds, show_autostart_status=True):
    global autostart_mode
    initial_total = total_seconds
    paused = False
    
    # Check if we can use terminal control
    try:
        old_settings = termios.tcgetattr(sys.stdin)
        use_terminal_control = True
    except (termios.error, OSError):
        use_terminal_control = False
    
    if use_terminal_control:
        try:
            tty.setraw(sys.stdin.fileno())

            # Start on a new line and save cursor position
            sys.stdout.write('\n')
            sys.stdout.write('\x1b[s')
            sys.stdout.flush()

            while total_seconds >= 0:
                if paused:
                    display_time(initial_total, total_seconds, f"PAUSED - {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} to continue", show_autostart_status, use_cursor_saving=True)
                else:
                    display_time(initial_total, total_seconds, f"{Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} for pause", show_autostart_status, use_cursor_saving=True)
                
                if select.select([sys.stdin], [], [], 1)[0]:
                    key = sys.stdin.read(1)
                    if key == '\x03':
                        raise KeyboardInterrupt
                    # Check for 'p' in English and other layouts (e.g., 'з' in Russian)
                    if key.lower() in ['p', 'з']:
                        paused = not paused
                    elif key.lower() == 'a' and show_autostart_status:
                        autostart_mode = not autostart_mode
                else:
                    if not paused:
                        total_seconds -= 1
        finally:
            if use_terminal_control:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    else:
        # Fallback for non-terminal environments
        while total_seconds >= 0:
            display_time(initial_total, total_seconds, "", show_autostart_status, use_cursor_saving=False)
            time.sleep(1)
            total_seconds -= 1

def wait_for_p(message, sound_filename=None, interval=120):
    """
    Wait for user to press 'p' key while displaying a message and optional periodic notifications.

    Args:
        message: The message to display with elapsed time
        sound_filename: Optional sound file to play at intervals
        interval: Seconds between sound/GUI notifications (default 120, but 60 for tcount overdue)
    """
    start_time = time.time()
    last_sound_time = start_time

    # Check if we can use terminal control
    try:
        old_settings = termios.tcgetattr(sys.stdin)
        use_terminal_control = True
    except (termios.error, OSError):
        use_terminal_control = False

    if not use_terminal_control:
        # If no terminal control available, just return immediately
        return

    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            current_time = time.time()
            if sound_filename and (current_time - last_sound_time) >= interval:
                play_sound(sound_filename)
                last_sound_time = current_time
                # Send critical notification that lasts until dismissed (no expire-time)
                try:
                    subprocess.run(['notify-send', '--app-name=pomotimer', '--urgency=critical', f"Timer overdue by {int((current_time - start_time) // 60)} minutes"],
                                   capture_output=True, text=True)
                except (FileNotFoundError, Exception):
                    pass  # Silently fail if notify-send not available
            overdue = int(current_time - start_time)
            hours, rem = divmod(overdue, 3600)
            mins, secs = divmod(rem, 60)
            overdue_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            
            # Handle terminal width - allow wrapping to second line for overdue timer
            display_content = f"{message} {overdue_str}"
            terminal_width = shutil.get_terminal_size().columns
            
            # Calculate how many lines the content will span
            lines_needed = (len(display_content) + terminal_width - 1) // terminal_width
            
            # Clear all lines that might contain content
            for _ in range(lines_needed):
                sys.stdout.write('\x1b[2K\x1b[1A')  # Clear line and move up
            sys.stdout.write('\x1b[1B')  # Move back down to original position
            
            # Display the content (allow natural wrapping)
            sys.stdout.write(f'{display_content}\r')
            sys.stdout.flush()
            if select.select([sys.stdin], [], [], 1)[0]:
                key = sys.stdin.read(1)
                if key == '\x03':
                    raise KeyboardInterrupt
                # Check for 'p' in English and other layouts (e.g., 'з' in Russian)
                if key.lower() in ['p', 'з']:
                    dismiss_timer_notifications()
                    break
    finally:
        if use_terminal_control:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def ask_continue():
    # Check if we can use terminal control
    try:
        old_settings = termios.tcgetattr(sys.stdin)
    except (termios.error, OSError):
        return False
    
    try:
        tty.setraw(sys.stdin.fileno())
        print("All work sessions complete. Add another run? y/n: ", end='', flush=True)
        
        while True:
            if select.select([sys.stdin], [], [], 1)[0]:
                key = sys.stdin.read(1).lower()
                
                if key == 'y':
                    print('y')
                    return True
                elif key == 'n':
                    print('n')
                    return False
                elif key == '\x03':
                    print('^C')
                    raise KeyboardInterrupt
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print()

# --- Core Functions ---

def run_pomodoro(work_time, break_time, sessions):
    global autostart_mode
    try:
        play_sound('media/aight-let-s-do-it.mp3')
        notify("New pomodoro session started. Let's get to work!")
        work_sessions_done = 0
        user_exited = False
        while work_sessions_done < sessions:
            work_sessions_done += 1
            # --- Work Session ---
            print(f"""
            {Colors.BOLD}{Colors.GREEN}--- Work Session {work_sessions_done} ---
            {Colors.ENDC}""")
            total_seconds = int(parse_time(work_time))
            countdown(total_seconds)
            play_sound(get_work_complete_sound())
            notify(f"Work session {work_sessions_done} complete. Time for a break!")
            print() # Print a newline after the timer is done

            run_break = False
            continuing_after_final = False
            if work_sessions_done < sessions:
                run_break = True
            else:
                if ask_continue():
                    sessions += 1
                    run_break = True
                    continuing_after_final = True
                else:
                    user_exited = True
                    break

            if run_break:
                # For break: don't wait if autostart OR if user just chose to continue
                if not (autostart_mode or continuing_after_final):
                    wait_for_p(f"""Work Session {work_sessions_done} complete, {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} for a break. Break Overdue:""", 'media/break-time.mp3')

                # --- Break Session ---
                print(f"""
                {Colors.BOLD}{Colors.RED}--- Break {work_sessions_done} ---
                {Colors.ENDC}""")
                total_seconds = int(parse_time(break_time))
                countdown(total_seconds)
                play_sound('media/back-to-work.mp3')
                notify(f"""Break {work_sessions_done} complete. Time for work!""")
                print() # Print a newline after the timer is done

                # For work sessions: only skip waiting if autostart (respect the 'a' parameter)
                if not autostart_mode:
                    wait_for_p(f"""Break {work_sessions_done} complete. To start the next work session, {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC}. Work Overdue:""", 'media/back-to-work.mp3')

        print(f"""
        {Colors.BOLD}{Colors.PURPLE}*** Pomodoro Complete! ***
        {Colors.ENDC}""")
        if user_exited:
            play_detached_sound('media/have-a-good-one.mp3')

    except KeyboardInterrupt:
        print(f"""

        {Colors.BOLD}{Colors.RED}Timer Cancelled.{Colors.ENDC}
        """)
        sys.exit(0)

def run_countdown(time_str):

    try:

        print(f"""

        {Colors.BOLD}{Colors.GREEN}--- Countdown Timer ---
        {Colors.ENDC}""")

        play_sound('media/bell.mp3')

        notify("Countdown timer started")

        total_seconds = int(parse_time(time_str))

        countdown(total_seconds, show_autostart_status=False)

        print(f"""



        {Colors.BOLD}{Colors.PURPLE}*** Timer Complete! ***
        {Colors.ENDC}

        """)
        play_detached_sound('media/gong.mp3')

        # Send critical notification for timer completion (persistent, no auto-expire)
        try:
            subprocess.run(['notify-send', '--app-name=pomotimer', '--urgency=critical', "Timer Complete!"],
                           capture_output=True, text=True)
        except (FileNotFoundError, Exception):
            pass  # Silently fail if notify-send not available

        # Enter overdue tracking phase with 1-minute notification intervals
        wait_for_p(f"Timer Complete! {Colors.BOLD}{Colors.BLUE}Press P{Colors.ENDC} to exit. Overdue:", 'media/gong.mp3', 60)

    except KeyboardInterrupt:
        print(f"""

        {Colors.BOLD}{Colors.RED}Timer Cancelled.{Colors.ENDC}
        """)
        sys.exit(0)

def main():
    global autostart_mode
    parser = argparse.ArgumentParser(description="A stylish terminal timer script.")
    subparsers = parser.add_subparsers(dest="command")

    parser_countdown = subparsers.add_parser("tcount", help="A simple countdown timer.")
    parser_countdown.add_argument("time", type=str, help="The time to count down (e.g., 5 or 5m for 5 minutes, 30s for 30 seconds).")

    parser_pomodoro = subparsers.add_parser("tpom", help="A Pomodoro timer.")
    parser_pomodoro.add_argument("work", type=str, help="Work session length (e.g., 25 or 25m, 1500s).")
    parser_pomodoro.add_argument("break_time", type=str, help="Break session length (e.g., 5 or 5m, 300s).")
    parser_pomodoro.add_argument("sessions", type=int, help="Number of work sessions.")
    parser_pomodoro.add_argument("autostart", type=str, nargs='?', default=None, help="Optional: type 'a' to autostart next session without confirmation.")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "tcount":
        run_countdown(args.time)
    elif args.command == "tpom":
        # Validate autostart parameter
        if args.autostart is not None and args.autostart != '' and args.autostart != 'a':
            print(f"{Colors.RED}Error: Invalid autostart parameter '{args.autostart}'.{Colors.ENDC}")
            print()
            parser_pomodoro.print_help(sys.stderr)
            print()
            print(f"{Colors.YELLOW}Usage example:{Colors.ENDC}")
            print(f"  {Colors.BOLD}python pomotimer.py tpom 25 5 4{Colors.ENDC}    # Regular pomodoro")
            print(f"  {Colors.BOLD}python pomotimer.py tpom 25 5 4 a{Colors.ENDC}  # Autostart enabled")
            print()
            sys.exit(1)
        
        # Treat empty string as None (no autostart)
        autostart_mode = args.autostart == 'a'
        run_pomodoro(args.work, args.break_time, args.sessions)

if __name__ == "__main__":
    main()