from passlib.context import CryptContext
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# 验证码生成
def generate_captcha():
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
    image = Image.new('RGB', (120, 40), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    draw.text((10, 10), code, font=font, fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return code, buffer