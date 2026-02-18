import os
from PIL import Image, ImageDraw


def create_favicon_image(size=64):
    # Render at 4x then downscale for antialiasing
    render_size = size * 4
    width = render_size
    height = render_size

    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    color1 = '#2563eb'
    color2 = '#0ea5e9'

    scale = render_size / 64.0

    # Keyboard body
    padding = int(8 * scale)
    top = int(16 * scale)
    bottom = int(48 * scale)
    radius = int(6 * scale)
    dc.rounded_rectangle(
        [padding, top, width - padding, bottom],
        radius=radius,
        fill=color1,
        outline=color2,
        width=int(2 * scale)
    )

    # Keys
    key_size = int(6 * scale)
    spacing = int(2 * scale)
    start_x = int(14 * scale)

    # Row 1
    y1 = int(22 * scale)
    for i in range(4):
        x = start_x + i * (key_size + spacing)
        dc.rectangle([x, y1, x + key_size, y1 + key_size], fill='white')

    # Row 2
    y2 = int(30 * scale)
    for i in range(4):
        x = start_x + i * (key_size + spacing)
        dc.rectangle([x, y2, x + key_size, y2 + key_size], fill='white')

    return image.resize((size, size), Image.LANCZOS)


def main():
    favicon_sizes = [16, 32, 48, 64]
    favicon_images = [create_favicon_image(size) for size in favicon_sizes]

    favicon_output = os.path.join('static', 'favicon.ico')
    favicon_images[0].save(
        favicon_output,
        format='ICO',
        sizes=[(s, s) for s in favicon_sizes],
        append_images=favicon_images[1:]
    )
    print(f"[OK] Favicon generated: {favicon_output}")

    png_path = os.path.join('static', 'favicon.png')
    favicon_images[-1].save(png_path, format='PNG')
    print(f"[OK] Favicon PNG generated: {png_path}")

    exe_sizes = [16, 32, 48, 64, 128, 256]
    exe_images = [create_favicon_image(size) for size in exe_sizes]

    exe_icon_path = os.path.join('scripts', 'app.ico')
    exe_images[0].save(
        exe_icon_path,
        format='ICO',
        sizes=[(s, s) for s in exe_sizes],
        append_images=exe_images[1:]
    )
    print(f"[OK] Executable icon generated: {exe_icon_path}")


if __name__ == '__main__':
    main()
