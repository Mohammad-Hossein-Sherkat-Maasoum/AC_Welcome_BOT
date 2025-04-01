import discord
import aiohttp
from io import BytesIO
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
from keep_alive import keep_alive  # اجرای سرور Flask برای Railway

# اجرای سرور Flask
keep_alive()

# دریافت توکن از متغیر محیطی
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1071754085361008690  # Server ID
WELCOME_CHANNEL_ID = 1072197211766657024  # Welcome channel ID

# مسیر فایل‌های مورد نیاز
WELCOME_IMAGE_PATH = "welcome_image.jpg"
DEFAULT_AVATAR_PATH = "default_avatar.jpg"
EXTRA_IMAGE_PATH = "extra_image.png"
FONT_PATH = os.path.join(os.getcwd(), "Vazir-Bold.ttf")

if not os.path.exists(FONT_PATH):
    print("⚠️ فایل فونت پیدا نشد!")

# تنظیم Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ساخت کلاینت بات
discord_client = discord.Client(intents=intents)

async def get_user_avatar(user):
    """دریافت آواتار کاربر یا استفاده از آواتار پیش‌فرض."""
    try:
        if user.avatar:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.avatar.url)) as resp:
                    if resp.status == 200:
                        return Image.open(BytesIO(await resp.read())).convert("RGBA")
        return None
    except Exception as e:
        print(f"⚠️ خطا در دریافت آواتار: {e}")
        return None

async def create_welcome_image(user):
    """ساخت تصویر خوش‌آمدگویی."""
    try:
        user_avatar = await get_user_avatar(user)
        default_avatar = Image.open(DEFAULT_AVATAR_PATH).convert("RGBA").resize((155, 155))

        base_image = Image.open(WELCOME_IMAGE_PATH).convert("RGBA").resize((600, 400))
        canvas = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        canvas.paste(base_image, (0, 0))
        
        if user_avatar:
            user_avatar = user_avatar.resize((115, 115))
            canvas.paste(user_avatar, (60, 50), user_avatar)
        canvas.paste(default_avatar, (base_image.width - default_avatar.width - 40, 30), default_avatar)

        draw = ImageDraw.Draw(canvas)
        font = ImageFont.truetype(FONT_PATH, 35)

        # متن خوش‌آمدگویی
        text = f"سلام {user.name} خوش اومدی!\nاز الآن عضو کُلایدر آرمی هستی!"
        reshaped_text = get_display(reshape(text))

        # تقسیم متن به خطوط
        lines = reshaped_text.split('\n')
        total_text_height = sum([draw.textbbox((0, 0, 0, 0), line, font=font)[3] for line in lines]) + (len(lines) - 1) * 10

        # رسم متن
        current_y = (base_image.height - total_text_height) // 2 + 20
        for line in lines:
            text_width = draw.textbbox((0, 0, 0, 0), line, font=font)[2]
            text_x = (base_image.width - text_width) // 2
            draw.text((text_x, current_y), line, font=font, fill="white")
            current_y += 45

        if os.path.exists(EXTRA_IMAGE_PATH):
            extra_image = Image.open(EXTRA_IMAGE_PATH).convert("RGBA").resize((100, 100))
            canvas.paste(extra_image, ((base_image.width - 100) // 2, current_y - 15), extra_image)
        
        output_path = f"welcome_{user.id}.png"
        canvas.save(output_path, "PNG")
        return output_path
    except Exception as e:
        print(f"⚠️ خطا در ساخت تصویر: {e}")
        return None

@discord_client.event
async def on_ready():
    print(f"✅ {discord_client.user} آنلاین شد!")

@discord_client.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    channel = discord_client.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        print("❌ کانال خوش‌آمدگویی پیدا نشد!")
        return
    welcome_image_path = await create_welcome_image(member)
    if welcome_image_path and os.path.exists(welcome_image_path):
        await channel.send(f"🎉 {member.mention} خوش اومدی!", file=discord.File(welcome_image_path))
        os.remove(welcome_image_path)
    else:
        await channel.send(f"🎉 {member.mention} خوش اومدی! (خطا در ساخت تصویر)")

if TOKEN:
    discord_client.run(TOKEN)
else:
    print("❌ توکن تنظیم نشده! لطفاً `DISCORD_TOKEN` را ست کن.")
