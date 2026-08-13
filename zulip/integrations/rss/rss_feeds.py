def parse_feed_file_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]
