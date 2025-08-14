#!/usr/bin/env python3
import os
import sys
import time
import math
import random
import shutil
import atexit
import signal
import colorsys


# -------- Terminal control helpers --------

def get_terminal_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def move_cursor(x: int, y: int) -> None:
    # 1-based coordinates
    sys.stdout.write(f"\x1b[{max(1, y)};{max(1, x)}H")


def clear_screen() -> None:
    sys.stdout.write("\x1b[2J\x1b[H")


def hide_cursor() -> None:
    sys.stdout.write("\x1b[?25l")


def show_cursor() -> None:
    sys.stdout.write("\x1b[?25h")


def reset_style() -> None:
    sys.stdout.write("\x1b[0m")


def supports_truecolor() -> bool:
    colorterm = os.environ.get("COLORTERM", "").lower()
    term = os.environ.get("TERM", "").lower()
    return ("truecolor" in colorterm) or ("24bit" in colorterm) or ("direct" in term)


def rgb_code(r: int, g: int, b: int, *, foreground: bool = True) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    if supports_truecolor():
        return f"\x1b[{38 if foreground else 48};2;{r};{g};{b}m"
    # Fallback to 256-color approximation
    # Map to 6x6x6 color cube
    r6 = int((r / 255) * 5)
    g6 = int((g / 255) * 5)
    b6 = int((b / 255) * 5)
    idx = 16 + 36 * r6 + 6 * g6 + b6
    return f"\x1b[{38 if foreground else 48};5;{idx}m"


def hsv_to_rgb_bytes(h: float, s: float, v: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def center_x_for_text(text: str, term_width: int) -> int:
    return max(1, (term_width - len(text)) // 2 + 1)


# -------- Effects --------

def matrix_rain(duration_seconds: float = 2.5, fps: int = 35) -> None:
    width, height = get_terminal_size()
    columns = min(width, 160)
    # Initialize drops
    y_positions = [random.randint(-height, 0) for _ in range(columns)]
    speeds = [random.uniform(0.5, 1.5) for _ in range(columns)]

    start_time = time.time()
    frame_delay = 1.0 / max(1, fps)

    glyphs = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@#$%&*+"  # noqa: E501

    while time.time() - start_time < duration_seconds:
        clear_screen()
        for x in range(columns):
            head_y = int(y_positions[x])
            trail = random.randint(6, max(6, height // 3))

            # Draw trail
            for i in range(trail):
                y = head_y - i
                if 1 <= y <= height:
                    char = random.choice(glyphs)
                    # Head brighter, tail fades
                    hue = 0.33  # green
                    sat = 0.9
                    val = max(0.15, 1.0 - (i / (trail + 2)))
                    r, g, b = hsv_to_rgb_bytes(hue, sat, val)
                    sys.stdout.write(rgb_code(r, g, b))
                    move_cursor(x + 1, y)
                    sys.stdout.write(char)

            # Update position
            y_positions[x] += speeds[x] * 2.0
            if y_positions[x] - trail > height:
                y_positions[x] = random.randint(-height // 2, 0)
                speeds[x] = random.uniform(0.6, 1.6)

        reset_style()
        sys.stdout.flush()
        time.sleep(frame_delay)


def gradient_text_line(text: str, y: int, hue_start: float = 0.0, hue_cycle_turns: float = 1.0) -> None:
    width, _ = get_terminal_size()
    start_x = center_x_for_text(text, width)
    n = max(1, len(text))
    for i, ch in enumerate(text):
        hue = hue_start + (i / n) * hue_cycle_turns
        r, g, b = hsv_to_rgb_bytes(hue, 1.0, 1.0)
        move_cursor(start_x + i, y)
        sys.stdout.write(rgb_code(r, g, b) + ch)
    reset_style()


def drop_shadow_text(text: str, y: int) -> None:
    width, _ = get_terminal_size()
    x = center_x_for_text(text, width)
    # Shadow
    move_cursor(x + 2, y + 1)
    sys.stdout.write("\x1b[2m" + rgb_code(25, 25, 35) + text)
    reset_style()


def render_banner_hello_world() -> None:
    clear_screen()
    width, height = get_terminal_size()
    center_y = max(3, height // 2)

    title = "Hello, World!"

    # Shadow then main gradient
    drop_shadow_text(title, center_y)
    gradient_text_line(title, center_y, hue_start=random.random(), hue_cycle_turns=1.0)

    # Subtitle
    subtitle = "你好，世界 · Python ✨"
    move_cursor(center_x_for_text(subtitle, width), center_y + 2)
    hue = random.random()
    r, g, b = hsv_to_rgb_bytes(hue, 0.4, 0.95)
    sys.stdout.write(rgb_code(r, g, b) + "\x1b[1m" + subtitle)
    reset_style()

    sys.stdout.flush()


def confetti(duration_seconds: float = 2.0, fps: int = 30, density: int = 80) -> None:
    width, height = get_terminal_size()
    chars = ["★", "✦", "✧", "•", "♦", "✺", "✶", "✹", "✸", "✷", "✻"]
    frame_delay = 1.0 / max(1, fps)
    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        # Sprinkle a handful of confetti per frame
        drops = max(1, min(density, width * height // 60))
        for _ in range(drops):
            x = random.randint(1, width)
            y = random.randint(1, height)
            hue = random.random()
            r, g, b = hsv_to_rgb_bytes(hue, 0.9, 1.0)
            move_cursor(x, y)
            sys.stdout.write(rgb_code(r, g, b) + random.choice(chars))
        reset_style()
        sys.stdout.flush()
        time.sleep(frame_delay)


# -------- Main flow --------

def cleanup() -> None:
    reset_style()
    show_cursor()


def main() -> None:
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    hide_cursor()
    clear_screen()

    # Intro matrix effect
    matrix_rain(duration_seconds=2.5, fps=35)

    # Show banner
    render_banner_hello_world()

    # Spark some confetti around it
    confetti(duration_seconds=2.0, fps=35, density=90)

    # Hold a moment before exiting
    move_cursor(1, get_terminal_size()[1])
    sys.stdout.write("\n")
    sys.stdout.flush()
    time.sleep(0.8)


if __name__ == "__main__":
    main()