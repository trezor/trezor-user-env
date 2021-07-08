from termcolor import colored


def log(text: str, color: str = "blue") -> None:
    print(colored(text, color))
