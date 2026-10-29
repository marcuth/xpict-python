from typing import List


def wrap_text(text: str, max_width: int) -> List[str]:
    """Split ``text`` into lines of at most ``max_width`` characters (approximately)."""
    words = text.split(" ")
    line = ""
    lines: List[str] = []

    for n, word in enumerate(words):
        test_line = line + word + " "

        if len(test_line) > max_width and n > 0:
            lines.append(line)
            line = word + " "
        else:
            line = test_line

    lines.append(line)

    return lines
