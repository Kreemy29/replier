import os
import sys
import argparse

def view_logs(log_file='logs/app.log', lines=50, follow=False):
    """
    View the latest log entries
    
    Args:
        log_file: Path to log file
        lines: Number of lines to display
        follow: Whether to follow the log file (like tail -f)
    """
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        print("Make sure the server has been started at least once.")
        return

    if follow:
        # Follow the log file (similar to tail -f)
        import time
        from collections import deque
        
        # Show last N lines first
        with open(log_file, 'r') as f:
            last_lines = deque(f, lines)
            for line in last_lines:
                print(line.strip())
        
        # Then follow new entries
        with open(log_file, 'r') as f:
            f.seek(0, 2)  # Go to the end of the file
            print(f"\n--- Following log file (Ctrl+C to stop) ---\n")
            try:
                while True:
                    line = f.readline()
                    if line:
                        print(line.strip())
                    else:
                        time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopped following log file.")
    else:
        # Just display the last N lines
        try:
            with open(log_file, 'r') as f:
                lines_list = f.readlines()
                for line in lines_list[-lines:]:
                    print(line.strip())
        except Exception as e:
            print(f"Error reading log file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View application logs")
    parser.add_argument('-f', '--file', default='logs/app.log', help='Log file path')
    parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to display')
    parser.add_argument('-t', '--tail', action='store_true', help='Follow the log file (like tail -f)')
    
    args = parser.parse_args()
    view_logs(args.file, args.lines, args.tail) 