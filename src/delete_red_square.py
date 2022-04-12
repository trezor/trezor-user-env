import sys

from PIL import Image


def replace_red_square(screenshot_location: str) -> None:
    """Gets rid of red square in top right corner - a sign of debug link.

    Replaces all the red pixels in that corner with the surrounding color.
    Modifies the screenshot in place.
    """
    img = Image.open(screenshot_location)
    pixel_data = img.load()
    width, height = img.size

    # Square is 8 pixels squared, make it little more to be safe
    square_size = 10

    # Color to be replaced
    red_color = (255, 0, 0, 255)

    # Find surrounding color outside the square
    replacement_color = pixel_data[width - square_size - 1, square_size + 1]

    for y in range(height):
        for x in range(width):
            if x > width - square_size and y < square_size:
                if pixel_data[x, y] == red_color:
                    pixel_data[x, y] = replacement_color

    img.save(screenshot_location, "PNG")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Input location as the first parameter")
        print("Usage: python delete_red_square.py <screenshot_location>")
        sys.exit(1)

    screenshot_location = sys.argv[1]

    replace_red_square(screenshot_location)
