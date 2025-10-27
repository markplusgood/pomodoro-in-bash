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
import os.path
import random

is_interactive = sys.stdin.isatty()

sound_processes = []

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
    if time_str.endswith('s'):
        return float(time_str[:-1])
    elif time_str.endswith('m'):
        return float(time_str[:-1]) * 60
    else:
        # assume minutes if no suffix
        return float(time_str) * 60

def play_sound(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    p = subprocess.Popen(['mpg123', '-q', filepath])
    sound_processes.append(p)

def play_detached_sound(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    subprocess.Popen(['mpg123', '-q', filepath], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def notify(message):
    subprocess.run(['notify-send', '--expire-time=3000', message])

def get_work_complete_sound():
    if random.random() < 0.1:  # 10% chance
        return 'media/are-you-winning-son.mp3'
    else:
        return 'media/break-time.mp3'

def display_time(initial_total, remaining_seconds, message=""):
    mins, secs = divmod(remaining_seconds, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    if initial_total > 0:
        progress = int(((initial_total - remaining_seconds) / initial_total) * 100)
        width = 20
        filled = int((progress / 100.0) * width)
        bar = '|' * filled + ' ' * (width - filled)
        print(f"\x1b[2K    {Colors.BOLD}{Colors.YELLOW}{time_str}{Colors.ENDC} [{bar}] {progress}% {message}", end='\r', flush=True)
    else:
        print(f"\x1b[2K    {Colors.BOLD}{Colors.YELLOW}{time_str}{Colors.ENDC} {message}", end='\r', flush=True)

def countdown(total_seconds):
    initial_total = total_seconds
    if not is_interactive:
        while total_seconds >= 0:
            display_time(initial_total, total_seconds, "")
            time.sleep(1)
            total_seconds -= 1
    else:
        paused = False
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while total_seconds >= 0:
                if paused:
                    display_time(initial_total, total_seconds, f"PAUSED - {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} to continue")
                else:
                    display_time(initial_total, total_seconds, f"{Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} for pause")
                if select.select([sys.stdin], [], [], 1)[0]:
                    key = sys.stdin.read(1)
                    if key == '\x03':
                        raise KeyboardInterrupt
                    # Check for 'p' in English and other layouts (e.g., 'з' in Russian)
                    if key.lower() in ['p', 'з']:
                        paused = not paused
                else:
                    if not paused:
                        total_seconds -= 1
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def wait_for_p(message, sound_filename=None):
    if not is_interactive:
        return
    start_time = time.time()
    last_sound_time = start_time
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            current_time = time.time()
            if sound_filename and (current_time - last_sound_time) >= 120:
                play_sound(sound_filename)
                last_sound_time = current_time
            overdue = int(current_time - start_time)
            hours, secs = divmod(overdue, 3600)
            mins, secs = divmod(secs, 60)
            overdue_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            print(f"{message} {overdue_str}", end='\r', flush=True)
            if select.select([sys.stdin], [], [], 1)[0]:
                key = sys.stdin.read(1)
                if key == '\x03':
                    raise KeyboardInterrupt
                # Check for 'p' in English and other layouts (e.g., 'з' in Russian)
                if key.lower() in ['p', 'з']:
                    break
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def ask_continue():
    while True:
        try:
            response = input("All work sessions complete. Add another run? y/n: ").strip().lower()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        except KeyboardInterrupt:
            return False

# --- Core Functions ---

def run_pomodoro(work_time, break_time, sessions, autostart=False):
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

            if work_sessions_done < sessions:
                # Wait for P to start break
                if not autostart:
                    wait_for_p(f"Work Session {work_sessions_done} complete, {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC} for a break. Break Overdue:", 'media/break-time.mp3')

                # --- Break Session ---
                print(f"""
                {Colors.BOLD}{Colors.RED}--- Break {work_sessions_done} ---
                {Colors.ENDC}""")
                total_seconds = int(parse_time(break_time))
                countdown(total_seconds)
                play_sound('media/back-to-work.mp3')
                notify(f"Break {work_sessions_done} complete. Time for work!")
                print() # Print a newline after the timer is done

                # Wait for P to start next work
                if not autostart:
                    wait_for_p(f"Break {work_sessions_done} complete. To start the next work session, {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC}. Work Overdue:", 'media/back-to-work.mp3')
            else:
                # --- Final Break Session ---
                print(f"""
                {Colors.BOLD}{Colors.RED}--- Break {work_sessions_done} ---
                {Colors.ENDC}""")
                total_seconds = int(parse_time(break_time))
                countdown(total_seconds)
                play_sound('media/back-to-work.mp3')
                notify("Break complete. Time for work!")
                print() # Print a newline after the timer is done

                # All sessions complete, ask to add another run
                if ask_continue():
                    # Wait for P to start next work
                    if not autostart:
                        wait_for_p(f"Break complete. To start the next work session, {Colors.BOLD}{Colors.BLUE}press P{Colors.ENDC}. Work Overdue:", 'media/back-to-work.mp3')
                    play_sound('media/aight-let-s-do-it.mp3')
                    notify("Let's get to work!")
                    # Increment sessions to do one more
                    sessions += 1
                else:
                    user_exited = True
                    break

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

        countdown(total_seconds)

        print(f"""



        {Colors.BOLD}{Colors.PURPLE}*** Timer Complete! ***
        {Colors.ENDC}

        """)
        play_detached_sound('media/gong.mp3')

        notify("Timer Complete!")

    except KeyboardInterrupt:
        print(f"""

        {Colors.BOLD}{Colors.RED}Timer Cancelled.{Colors.ENDC}
        """)
        sys.exit(0)

def main():
    # original logic
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
        print(f"DEBUG: sys.argv = {sys.argv}")
        print(f"DEBUG: args.autostart = {args.autostart}")
        autostart = args.autostart == 'a'
        print(f"DEBUG: autostart = {autostart}")
        run_pomodoro(args.work, args.break_time, args.sessions, autostart)

if __name__ == "__main__":
    main()