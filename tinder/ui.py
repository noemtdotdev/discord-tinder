from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
import constants as constants

async def create_tinder_image(avatar_url: str, name: str, age: int, bio: str) -> Image.Image:
    """
    Create a Tinder-style image with the user's avatar, name, age, and bio.
    The avatar will fill the entire background with a zoomed, blurred version.
    Bio text will wrap to 2 lines maximum with ellipsis if needed.

    Args:
        avatar_url (str): URL of the user's avatar.
        name (str): User's name.
        age (int): User's age.
        bio (str): User's bio.

    Returns:
        PIL.Image.Image: The created Tinder-style image.
    """
    card_width, card_height = 600, 800
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch image: HTTP {response.status}")
                avatar_data = await response.read()
        
        original_image = Image.open(io.BytesIO(avatar_data)).convert("RGB")
        
        card = Image.new("RGB", (card_width, card_height), (255, 255, 255))
        
        background = original_image.copy()
        bg_ratio = max(card_width / background.width, card_height / background.height)
        new_size = (int(background.width * bg_ratio), int(background.height * bg_ratio))
        background = background.resize(new_size, Image.LANCZOS)
        
        left = max(0, (background.width - card_width) // 2)
        top = max(0, (background.height - card_height) // 2)
        right = min(background.width, left + card_width)
        bottom = min(background.height, top + card_height)
        background = background.crop((left, top, right, bottom))
        
        background = background.filter(ImageFilter.GaussianBlur(radius=15))
        
        card.paste(background, (0, 0))
        
        avatar_size = (500, 500)
        avatar = original_image.copy()
        
        avatar_ratio = min(avatar_size[0] / avatar.width, avatar_size[1] / avatar.height)
        new_size = (int(avatar.width * avatar_ratio), int(avatar.height * avatar_ratio))
        avatar = avatar.resize(new_size, Image.LANCZOS)
        
        centered_avatar = Image.new("RGB", avatar_size, (0, 0, 0, 0))
        
        paste_x = (avatar_size[0] - avatar.width) // 2
        paste_y = (avatar_size[1] - avatar.height) // 2
        centered_avatar.paste(avatar, (paste_x, paste_y))
        
        card.paste(centered_avatar, (50, 50))
        
    except Exception as e:
        print(f"Error loading avatar: {e}")
        card = Image.new("RGB", (card_width, card_height), (200, 200, 200))
        draw = ImageDraw.Draw(card)
        draw.text((card_width//2, card_height//2), "No Image", fill=(50, 50, 50), anchor="mm")
    
    draw = ImageDraw.Draw(card)
    
    overlay = Image.new("RGBA", (card_width, 280), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    for y in range(280):
        alpha = min(180, int(y * 1.3))
        overlay_draw.line([(0, y), (card_width, y)], fill=(0, 0, 0, alpha))
    
    card.paste(Image.alpha_composite(Image.new("RGBA", (card_width, 280), (0, 0, 0, 0)), overlay), 
              (0, card_height - 280), 
              mask=overlay)
    
    name_font = ImageFont.truetype(constants.FONT_MEDIUM_PATH, 40)
    bio_font = ImageFont.truetype(constants.FONT_PATH, 30)
    
    name_age_text = f"{name}, {age}"
    draw.text((50, 570), name_age_text, font=name_font, fill=(255, 255, 255))
    
    max_width = card_width - 100
    max_lines = 2
    line_spacing = 35
    
    def wrap_text(text, font, max_width, max_lines):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width = font.getlength(test_line)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    
                    if len(lines) >= max_lines:
                        break
                else:
                    lines.append(word)
                    if len(lines) >= max_lines:
                        break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
            
        if len(lines) == max_lines and len(lines) < len(words):
            last_line = lines[-1]
            while font.getlength(last_line + "...") > max_width:
                if " " in last_line:
                    last_line = last_line.rsplit(" ", 1)[0]
                else:
                    last_line = last_line[:-1]
            lines[-1] = last_line + "..."
            
        return lines
    
    wrapped_bio = wrap_text(bio, bio_font, max_width, max_lines)
    
    for i, line in enumerate(wrapped_bio):
        y_position = 620 + i * line_spacing
        draw.text((50, y_position), line, font=bio_font, fill=(255, 255, 255))
    
    return card
