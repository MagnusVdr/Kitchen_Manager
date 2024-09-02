import usb.core
import usb.util
from PIL import Image, ImageDraw, ImageFont

x = 1
path = 'C:\\Users\\supor\\AppData\\Local\\Microsoft\\Windows\\Fonts\\'
font = 'digital-7.mono.ttf'
font2 = 'FiraCode-Bold.ttf'
font3 = 'BebasNeue-Regular.ttf'


def create_large_number_image(number, output_path, font_path=path+font2,
                              font_size=220 * x):
    # Create an image with white background
    width, height = 400 * x, 270 * x  # Adjust size as needed
    image = Image.new('1', (width, height), color=1)  # 1-bit pixels, black and white
    draw = ImageDraw.Draw(image)

    # Load font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text size and position using textbbox
    position = (-10 * x, -50 * x)

    # Draw text
    draw.text(position, number, fill=0, font=font)

    # Save image
    image.save(output_path)


def stretch_image_vertically(input_path, output_path, stretch_factor=3):
    # Open the image
    image = Image.open(input_path)

    # Get the current size
    width, height = image.size

    # Calculate the new height
    new_height = int(height * stretch_factor)

    # Resize the image
    stretched_image = image.resize((width, new_height), Image.Resampling.LANCZOS)

    # Save the stretched image
    stretched_image.save(output_path)


def image_to_bytes(image_path):
    image = Image.open(image_path)
    image = image.convert('1')

    width, height = image.size
    image_data = []

    for y in range(height):
        row = []
        for x in range(0, width, 8):
            byte = 0
            for bit in range(8):
                if x + bit < width and image.getpixel((x + bit, y)) == 0:
                    byte |= 128 >> bit  # Changed from 1 << bit to 128 >> bit
            row.append(byte)
        image_data.append(bytes(row))

    return width, height, image_data


def image_print(ep, image_path):
    width, height, image_data = image_to_bytes(image_path)
    # ESC * m nL nH xL xH data
    esc = b'\x1D\x76\x30\x00'
    size_data = bytes([width % 256, width // 256, height % 256, height // 256])

    ep.write(esc + size_data)

    for row in image_data:
        ep.write(bytes(row))


def init_printer():
    dev = usb.core.find(idVendor=0x28E9, idProduct=0x0289)
    if dev is None:
        raise ValueError('Printer not found')

    # Set configuration
    dev.set_configuration()

    # Get an endpoint instance
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    ep = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
    )

    if ep is None:
        raise ValueError('Endpoint not found')

    return ep, dev


def set_text_mode(ep):
    # Initialize text mode
    ep.write(b'\x1B\x40')  # ESC @ - Initialize printer
    ep.write(b'\x1B\x74\x00')  # ESC t 0 - Select character code table
    ep.write(b'\x1B\x52\x00')  # ESC R 0 - Select international character set


def print_text(text, size=1):
    print("hey" + text)
    ep, dev = init_printer()
    try:
        set_text_mode(ep)
        if size == 1:
            print("Aga siin")
            ep.write(b'\x1B\x21\x00')  # ESC ! 0
            ep.write(text.encode() + b'\n')

        elif size == 2:
            ep.write(b'\x1B\x21\x30')  # ESC ! 48
            ep.write(text.encode() + b'\n')
    finally:
        usb.util.dispose_resources(dev)


def print_image(numb):
    ep, dev = init_printer()
    try:
        create_large_number_image(numb, 'number_image.bmp')
        stretch_image_vertically('number_image.bmp', 'stretched_number_image.bmp', stretch_factor=7)
        image_print(ep, 'stretched_number_image.bmp')
    finally:
        usb.util.dispose_resources(dev)


def print_order():
    print_text('Sinu tellimus on:', size=2)
    for item, count in {"kana": 1, "kala": 2}.items():
        print_text(f"{item} x{count}")
    print_text('sinu tellimuse number:', size=2)
    print_image(f"{str(78).zfill(3)}")
    print_text('hei')


if __name__ == "__main__":

    print_order()
