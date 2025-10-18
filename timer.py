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

def play_blocking_sound(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    os.system('mpg123 -q ' + filepath)

def get_work_complete_sound():
    if random.random() < 0.1:  # 10% chance
        return 'are-you-winning-son.mp3'
    else:
        return 'break-time.mp3'

def display_time(seconds, message=""):
    mins, secs = divmod(seconds, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    print(f"    {Colors.BOLD}{Colors.YELLOW}{time_str}{Colors.ENDC} {message}", end='\r', flush=True)

def countdown(total_seconds):
    if not is_interactive:
        while total_seconds >= 0:
            display_time(total_seconds, "")
            time.sleep(1)
            total_seconds -= 1
    else:
        paused = False
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while total_seconds >= 0:
                if paused:
                    display_time(total_seconds, "PAUSED - press p to continue")
                else:
                    display_time(total_seconds, "press p for pause")
                if select.select([sys.stdin], [], [], 1)[0]:
                    key = sys.stdin.read(1)
                    if key == '\x03':
                        raise KeyboardInterrupt
                    if key.lower() == 'p':
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
                if key.lower() == 'p':
                    break
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def ask_continue():
    try:
        response = input("All work sessions complete. Add another run? y/n: ").strip().lower()
        return response == 'y'
    except KeyboardInterrupt:
        return False

# --- Core Functions ---

def run_pomodoro(work_time, break_time, sessions):
    try:
        play_sound('aight-let-s-do-it.mp3')
        work_sessions_done = 0
        user_exited = False
        while work_sessions_done < sessions:
            work_sessions_done += 1
            # --- Work Session ---
            print(f"""
            {Colors.BOLD}{Colors.GREEN}--- Work Session {work_sessions_done} ---{Colors.ENDC}""")
            total_seconds = int(parse_time(work_time))
            countdown(total_seconds)
            play_sound(get_work_complete_sound())
            print() # Print a newline after the timer is done

            if work_sessions_done < sessions:
                # Wait for P to start break
                wait_for_p(f"Work Session {work_sessions_done} complete, press P for a break. Break Overdue:", 'break-time.mp3')

                # --- Break Session ---
                print(f"""
                {Colors.BOLD}{Colors.RED}--- Break {work_sessions_done} ---{Colors.ENDC}""")
                total_seconds = int(parse_time(break_time))
                countdown(total_seconds)
                play_sound('back-to-work.mp3')
                print() # Print a newline after the timer is done

                # Wait for P to start next work
                wait_for_p(f"Break {work_sessions_done} complete. To start the next work session, press P. Work Overdue:", 'back-to-work.mp3')
            else:
                # All sessions complete, ask to add another
                if ask_continue():
                    # Wait for P to start break
                    wait_for_p("Press P for break. Break Overdue:", 'break-time.mp3')

                    # --- Break Session ---
                    print(f"""
                    {Colors.BOLD}{Colors.RED}--- Break {work_sessions_done} ---{Colors.ENDC}""")
                    total_seconds = int(parse_time(break_time))
                    countdown(total_seconds)
                    play_sound('back-to-work.mp3')
                    print() # Print a newline after the timer is done

                    # Wait for P to start next work
                    wait_for_p("Break complete. To start the next work session, press P. Work Overdue:", 'back-to-work.mp3')
                    play_sound('aight-let-s-do-it.mp3')

                    # Increment sessions to do one more
                    sessions += 1
                else:
                    user_exited = True
                    break

        print(f"""
        {Colors.BOLD}{Colors.PURPLE}*** Pomodoro Complete! ***{Colors.ENDC}
        """)
        if user_exited:
            play_blocking_sound('have-a-good-one.mp3')

    except KeyboardInterrupt:
        print(f"""

        {Colors.BOLD}{Colors.RED}Timer Cancelled.{Colors.ENDC}
        """)
        sys.exit(0)

def run_countdown(time_str):
    try:
        print(f"""
        {Colors.BOLD}{Colors.GREEN}--- Countdown Timer ---{Colors.ENDC}""")
        play_sound('bell.mp3')
        total_seconds = int(parse_time(time_str))
        countdown(total_seconds)
        print(f"""

        {Colors.BOLD}{Colors.PURPLE}*** Timer Complete! ***{Colors.ENDC}
        """)
        play_blocking_sound('gong.mp3')

    except KeyboardInterrupt:
        print(f"""

        {Colors.BOLD}{Colors.RED}Timer Cancelled.{Colors.ENDC}
        """)
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="A stylish terminal timer script.")
    subparsers = parser.add_subparsers(dest="command")

    parser_countdown = subparsers.add_parser("tcount", help="A simple countdown timer.")
    parser_countdown.add_argument("time", type=str, help="The time to count down (e.g., 5m for 5 minutes, 30s for 30 seconds).")

    parser_pomodoro = subparsers.add_parser("tpom", help="A Pomodoro timer.")
    parser_pomodoro.add_argument("work", type=str, help="Work session length (e.g., 25m, 1500s).")
    parser_pomodoro.add_argument("break_time", type=str, help="Break session length (e.g., 5m, 300s).")
    parser_pomodoro.add_argument("sessions", type=int, help="Number of work sessions.")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "tcount":
        run_countdown(args.time)
    elif args.command == "tpom":
        run_pomodoro(args.work, args.break_time, args.sessions)

if __name__ == "__main__":
    main()
