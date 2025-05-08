from rich.console import Console

class RichConsole:
    def __init__(self):
        self.console = Console()

    def info(self, message):
        self.write("green", message = message)

    def write(self, color: str, message: str):
        self.console.print(f"[{color}]{message}")

    def log(self, color: str, message: str):
        self.write(color, message)
if __name__ == "__main__":
    RichConsole().write("blue", "OI")