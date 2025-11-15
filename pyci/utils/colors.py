class Colors:
    RESET = "\033[0m"

    BOLD = "\033[1m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.RESET}"
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.RESET}"
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.RESET}"
    @staticmethod
    def blue(text): return f"{Colors.BLUE}{text}{Colors.RESET}"
    @staticmethod
    def bold(text): return f"{Colors.BOLD}{text}{Colors.RESET}"
