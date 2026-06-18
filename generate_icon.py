# generate_icon.py — запустить ОДИН раз для создания иконки
from PIL import Image, ImageDraw

def create_icon():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Синий круг
    draw.ellipse([8, 8, 56, 56], fill=(30, 100, 220))
    
    # Белая буква J
    draw.text((24, 16), "J", fill=(255, 255, 255))
    
    img.save("jarvis_icon.png")
    print("Иконка создана: jarvis_icon.png")

if __name__ == "__main__":
    create_icon()