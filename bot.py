from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ואז לפני השורה של bot.run(TOKEN), פשוט תכתוב:
keep_alive()
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select, UserSelect
import asyncio
from datetime import datetime, timedelta
import os
import io
# תיקון קטן כאן כדי להבטיח עבודה חלקה עם Pillow
from PIL import Image, ImageDraw, ImageOps, ImageFont 

# --- הגדרות רולים והרשאות ---
ADMIN_ROLES = ["server owner", "DEV Server Discord", "co | owner", "『בעל השרת』", "server bot"]
RENAME_ROLES = ["server owner", "co | owner", "『בעל השרת』", "DEV Server Discord", "Staff Team", "『צוות השרת』", "『גישות』", "Management", "『?רול חדיד』"]
AUTHORIZED_ROLES = ["server owner", "co | owner", "גישות", "בעל השרת", "Staff", "Admin", "Staff Team"]
FILTER_ROLE_NAME = "MEMBER FANATICS" 
CATEGORY_NAME = "Tickets" 
LOGS_CHANNEL_NAME = "『🛠️』logs-system"
WELCOME_CHANNEL_NAME = "『👋』welcome" # שם חדר הוולקם
RULES_CHANNEL_NAME = "「📜」חוקי・השרת" # שם חדר החוקים לתיוג

# שמות החדרים המעודכנים
TICKET_LOGS_CHANNEL = "logs-ticket" 
LEADERBOARD_CHANNEL = "top-ticket-logs" 

# משתנה לשמירת כמות הטיקטים של הצוות
ticket_counts = {}

# --- פונקציה ליצירת תמונת Welcome בשחור לבן עם כתב ענק ---
async def create_welcome_card(member):
    # הגדרת צבעים לשחור ולבן
    COLOR_BLACK = (10, 10, 10, 255)
    COLOR_WHITE = (255, 255, 255, 255)

    # יצירת רקע שחור (הגדלתי מעט את הגובה ל-420 כדי להכיל כתב ענק)
    base = Image.new('RGBA', (1100, 420), COLOR_BLACK)
    draw = ImageDraw.Draw(base)

    # פסים לבנים דקים למעלה ולמטה למראה יוקרתי
    draw.rectangle([0, 0, 1100, 15], fill=COLOR_WHITE)
    draw.rectangle([0, 405, 1100, 420], fill=COLOR_WHITE)

    try:
        # טעינת תמונת הפרופיל
        avatar_asset = member.display_avatar.with_format("png")
        avatar_data = await avatar_asset.read()
        avatar_image = Image.open(io.BytesIO(avatar_data)).convert("RGBA")

        # הפיכת תמונת הפרופיל לשחור-לבן שתתאים לעיצוב
        avatar_image = ImageOps.grayscale(avatar_image).convert("RGBA")

        avatar_size = 280 # הגדלת התמונה
        avatar_image = avatar_image.resize((avatar_size, avatar_size))

        # חיתוך לעיגול
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        output_avatar = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
        output_avatar.putalpha(mask)

        # מסגרת לבנה עבה סביב הפרופיל
        draw.ellipse([45, 65, 45+avatar_size+15, 65+avatar_size+15], outline=COLOR_WHITE, width=12)

        # הדבקה
        base.paste(output_avatar, (52, 72), output_avatar)
    except Exception as e:
        print(f"Error loading avatar: {e}")

    # טעינת פונטים - גדלים ענקיים
    try:
        font_path = "arial.ttf" 
        if not os.path.exists(font_path):
             if os.name == 'nt': font_path = "C:\\Windows\\Fonts\\arialbd.ttf" # משתמש ב-Bold אם אפשר
             else: font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" 

        # פונטים ענקיים במיוחד
        title_font = ImageFont.truetype(font_path, 130) # כותרת ענקית
        name_font = ImageFont.truetype(font_path, 85)   # שם משתמש גדול
        sub_font = ImageFont.truetype(font_path, 50)    # מונה חברים
    except:
        title_font = name_font = sub_font = ImageFont.load_default()

    text_start_x = 380

    # כתיבת הטקסט בלבן על שחור
    draw.text((text_start_x, 60), "WELCOME!", fill=COLOR_WHITE, font=title_font)
    draw.text((text_start_x, 210), f"{member.display_name}", fill=COLOR_WHITE, font=name_font)
    draw.text((text_start_x, 310), f"MEMBER #{member.guild.member_count}", fill=COLOR_WHITE, font=sub_font)

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# פונקציית עזר לשליפת המבצע מיומן הביקורת
async def get_audit_log_entry(guild, action):
    await asyncio.sleep(1) 
    async for entry in guild.audit_logs(limit=1, action=action):
        return entry
    return None

# פונקציה לעדכון טבלת המובילים
async def update_leaderboard(guild):
    channel = discord.utils.get(guild.text_channels, name=LEADERBOARD_CHANNEL)
    if not channel:
        return

    sorted_staff = sorted(ticket_counts.items(), key=lambda item: item[1], reverse=True)

    embed = discord.Embed(title="🏆 טבלת מובילי הצוות - לקיחת טיקטים", color=0xf1c40f, timestamp=datetime.now())
    description = "הצוות שלקח הכי הרבה פניות ועזר לקהילה:\n\n"

    for index, (staff_id, count) in enumerate(sorted_staff[:10], start=1):
        mention = f"<@{staff_id}>"
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"**#{index}**"
        description += f"{medal} {mention} — **{count}** טיקטים\n"

    if not sorted_staff:
        description = "אין נתונים עדיין. הצוות צריך להתחיל לקחת טיקטים!"

    embed.description = description
    embed.set_footer(text="Maccabi Support | Leaderboard")

    async for msg in channel.history(limit=10):
        if msg.author == guild.me and msg.embeds and msg.embeds[0].title == "🏆 טבלת מובילי הצוות - לקיחת טיקטים":
            await msg.edit(embed=embed)
            return

    await channel.send(embed=embed)

# --- מחלקות ה-UI ---

class RenameModal(Modal, title='📝 שינוי שם הטיקט'):
    name = TextInput(label='שם חדש לערוץ', placeholder='הקלד שם (נקי ללא אימוג\'י)...', min_length=2, max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.edit(name=f"{self.name.value}")
        embed = discord.Embed(description=f"השם של הטיקט שונה ל: `{self.name.value}`", color=0x000000)
        await interaction.response.send_message(embed=embed)

class CloseReasonModal(Modal, title='🔒 סיבת סגירת הטיקט'):
    reason = TextInput(
        label='מה סיבת הסגירה?',
        placeholder='הקלד את הסיבה כאן...',
        style=discord.TextStyle.paragraph,
        min_length=2,
        max_length=100,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_parts = interaction.channel.name.split('-')
        user_name = user_parts[-1] if len(user_parts) > 1 else "Unknown"

        transcript_content = f"Transcript for Ticket: {interaction.channel.name}\n"
        transcript_content += f"Opened by: {user_name}\n"
        transcript_content += f"Closed by: {interaction.user.display_name}\n"
        transcript_content += f"Reason: {self.reason.value}\n"
        transcript_content += "-"*50 + "\n\n"

        async for message in interaction.channel.history(limit=None, oldest_first=True):
            time = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content if message.content else "[No Text Content / Image]"
            transcript_content += f"[{time}] {message.author.display_name}: {content}\n"

        file = discord.File(io.BytesIO(transcript_content.encode()), filename=f"transcript-{interaction.channel.name}.txt")

        log_channel = discord.utils.get(interaction.guild.text_channels, name=TICKET_LOGS_CHANNEL)
        if log_channel:
            log_embed = discord.Embed(title="📂 דוח סגירת טיקט מלא", color=0xff0000, timestamp=datetime.now())
            log_embed.add_field(name="שם הטיקט:", value=f"`{interaction.channel.name}`", inline=True)
            log_embed.add_field(name="פותח הטיקט:", value=f"`{user_name}`", inline=True)
            log_embed.add_field(name="נסגר ע\"י:", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="סיבת סגירה:", value=self.reason.value, inline=False)
            await log_channel.send(log_embed, file=file)

        dm_embed = discord.Embed(title="הטיקט שלך נסגר", color=0xff0000, timestamp=datetime.now())
        dm_embed.add_field(name="שרת:", value=interaction.guild.name, inline=False)
        dm_embed.add_field(name="נסגר על ידי:", value=interaction.user.display_name, inline=False)
        dm_embed.add_field(name="סיבת סגירה:", value=self.reason.value, inline=False)
        dm_embed.set_footer(text="Maccabi Support")

        ticket_opener = discord.utils.get(interaction.guild.members, name=user_name)
        try:
            if ticket_opener:
                await ticket_opener.send(embed=dm_embed)
        except:
            pass 

        await interaction.response.send_message(f"הסיבה תועדה והלוגים נשמרו. סוגר בעוד **5**...")
        message = await interaction.original_response()

        for i in range(4, 0, -1):
            await asyncio.sleep(1)
            await message.edit(content=f"סוגר את הטיקט בעוד **{i}**...")

        await asyncio.sleep(1)
        await interaction.channel.delete()

class AddUserView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_users = []

    @discord.ui.select(cls=UserSelect, placeholder="חפש משתמש", custom_id="add_multiple_users_select", min_values=1, max_values=25)
    async def select_callback(self, interaction: discord.Interaction, select: UserSelect):
        self.selected_users = select.values

        has_plus = any(child.custom_id == "add_more_users_btn" for child in self.children)

        if not has_plus:
            plus_button = Button(label="➕", style=discord.ButtonStyle.secondary, custom_id="add_more_users_btn")

            async def plus_callback(inter: discord.Interaction):
                await inter.response.defer()

            plus_button.callback = plus_callback
            self.add_item(plus_button)

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="אישור הוספה ✅", style=discord.ButtonStyle.success, custom_id="confirm_add_user_btn")
    async def confirm_callback(self, interaction: discord.Interaction, button: Button):
        if not self.selected_users:
            return await interaction.response.send_message("אנא בחר לפחות משתמש אחד קודם!", ephemeral=True)

        added_mentions = []
        unauthorized_users = []
        filter_role = discord.utils.get(interaction.guild.roles, name=FILTER_ROLE_NAME)

        for user in self.selected_users:
            if filter_role in user.roles:
                await interaction.channel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)
                added_mentions.append(user.mention)
            else:
                unauthorized_users.append(user.display_name)

        if added_mentions:
            embed = discord.Embed(title="👤 משתמשים נוספו לטיקט", color=0xf1c40f) 
            embed.add_field(name="המשתמשים שנוספו:", value=", ".join(added_mentions), inline=False)
            embed.add_field(name="בוצע על ידי:", value=interaction.user.mention, inline=False)
            embed.set_footer(text="Maccabi Support | ניהול משתמשים")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("לא נוספו משתמשים חדשים.", ephemeral=True)

        if unauthorized_users:
            error_msg = f"לא ניתן להוסיף את: {', '.join(unauthorized_users)} (אין להם את הרול `{FILTER_ROLE_NAME}`)"
            await interaction.followup.send(error_msg, ephemeral=True)

class ConfirmCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="כן ✅", style=discord.ButtonStyle.success, custom_id="confirm_close_yes")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("רק צוות יכול לאשר סגירה!", ephemeral=True)

        modal = CloseReasonModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="לא ❌", style=discord.ButtonStyle.danger, custom_id="confirm_close_no")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("סגירת הטיקט בוטלה.", ephemeral=True)

class StaffOptionsView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="שחרר טיקט 🔄", style=discord.ButtonStyle.primary, custom_id="staff_unclaim_fixed", row=1)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)

        found_message = None
        async for msg in interaction.channel.history(limit=20):
            if msg.embeds and msg.embeds[0].title == "טיקט נפתח":
                found_message = msg
                break

        if found_message:
            current_embed = found_message.embeds[0]
            if not any("בטיפול ע\"י" in field.value for field in current_embed.fields):
                return await interaction.response.send_message("הטיקט כבר נמצא במצב המתנה!", ephemeral=True)

            embed = discord.Embed(title="טיקט נפתח", color=0xffffff)
            embed.add_field(name="-------------------------------------------", value=f"**נושא הפנייה:** {interaction.channel.name.split('-')[0]}\nנא להמתין לצוות בסבלנות וכתבו את שאלתכם.\n\n**Maccabi Support | מערכת הפניות**", inline=False)
            await found_message.edit(embed=embed, view=TicketControlView())
            await interaction.response.send_message("הטיקט שוחרר והוחזר למצב המתנה.", ephemeral=True)

    @discord.ui.button(label="שנה שם 📝", style=discord.ButtonStyle.success, custom_id="staff_rename_fixed", row=1)
    async def rename_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in RENAME_ROLES):
            return await interaction.response.send_message("אין לך הרשאה לשנות שם!", ephemeral=True)
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="הוסף משתמש + 🟡", style=discord.ButtonStyle.secondary, custom_id="staff_add_user_fixed", row=2)
    async def add_user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)

        embed = discord.Embed(title="הוספת משתמש לטיקט", description="בחר את המשתמשים שברצונך לצרף לשיחה הנוכחית.", color=0xf1c40f)
        await interaction.response.send_message(embed=embed, view=AddUserView(), ephemeral=True)

    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.danger, custom_id="staff_close_now_confirm", row=2)
    async def close_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)

        confirm_embed = discord.Embed(title="⚠️ אישור סגירה", description="האם אתה בטוח שברצונך לסגור את הטיקט?", color=0xffff00)

        view = ConfirmCloseView()
        no_reason_btn = Button(label="ללא סיבה ❌", style=discord.ButtonStyle.secondary, custom_id="close_no_reason_final")

        async def no_reason_callback(inter: discord.Interaction):
            if not any(discord.utils.get(inter.user.roles, name=r) for r in AUTHORIZED_ROLES):
                return await inter.response.send_message("אין לך הרשאה!", ephemeral=True)

            await inter.response.send_message("סוגר את הטיקט (ללא לוגים וללא הודעה בפרטי)...")
            await asyncio.sleep(1)
            await inter.channel.delete()

        no_reason_btn.callback = no_reason_callback
        view.add_item(no_reason_btn)

        await interaction.response.send_message(embed=confirm_embed, view=view)

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לבקש לסגור 🚩", style=discord.ButtonStyle.danger, custom_id="req_close_fixed")
    async def request_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="בקשת סגירה", description=f"המשתמש {interaction.user.mention} ביקש לסגור את הטיקט.", color=0xff0000)
        await interaction.response.send_message(embed=embed, view=ConfirmCloseView())

    @discord.ui.button(label="לקחת טיקט ✅", style=discord.ButtonStyle.success, custom_id="claim_fixed")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)

        staff_id = str(interaction.user.id)
        ticket_counts[staff_id] = ticket_counts.get(staff_id, 0) + 1

        embed = interaction.message.embeds[0]
        embed.clear_fields()
        embed.add_field(name="-------------------------------------------", value=f"**בטיפול ע\"י:** {interaction.user.mention}\n\n**Maccabi Support | מערכת הפניות**", inline=False)
        embed.color = 0x5865F2

        new_view = TicketControlView()
        for child in new_view.children:
            if child.custom_id == "claim_fixed": child.disabled = True

        await interaction.message.edit(embed=embed, view=new_view)
        await interaction.response.send_message(f"הטיקט נלקח על ידי {interaction.user.mention}", ephemeral=True)
        await update_leaderboard(interaction.guild)

    @discord.ui.button(label="אפשרויות צוות 🛠️", style=discord.ButtonStyle.primary, custom_id="staff_opts_fixed")
    async def staff_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("גישה לצוות בלבד.", ephemeral=True)
        staff_embed = discord.Embed(title="🛠️ פאנל ניהול צוות", description="==============================\n**בחר את הפעולה הרצויה לניהול הפנייה:**\n==============================", color=0x2b2d31)
        await interaction.response.send_message(embed=staff_embed, view=StaffOptionsView(), ephemeral=True)

class TicketTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="💬", description="פתיחת פנייה בנושאים כלליים"),
            discord.SelectOption(label="בחינה לצוות", emoji="📝", description="הגשת מועמדות לצוות השרת"),
            discord.SelectOption(label="דיווח על באג", emoji="🐞", description="דיווח על תקלות טכניות")
        ]
        super().__init__(placeholder="בחר את נושא הפנייה...", options=options, custom_id="ticket_type_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        staff_role = discord.utils.get(guild.roles, name="Staff Team")
        staff_mention = staff_role.mention if staff_role else "@Staff Team"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for r_name in AUTHORIZED_ROLES:
            role = discord.utils.get(guild.roles, name=r_name)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(f'{self.values[0]}-{user.name}', overwrites=overwrites, category=category)

        inner_embed = discord.Embed(title="טיקט נפתח", color=0xffffff)
        inner_embed.add_field(name="-------------------------------------------", value=f"**נושא הפנייה:** {self.values[0]}\nנא להמתין לצוות בסבלנות וכתבו את שאלתכם.\n\n**Maccabi Support | מערכת הפניות**", inline=False)

        await channel.send(f"{interaction.user.mention} {staff_mention} שלום, פנייתך התקבלה.", embed=inner_embed, view=TicketControlView())
        await interaction.response.edit_message(content=f"הטיקט נפתח בהצלחה: {channel.mention}", embed=None, view=None)

class OpenTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="פתיחת טיקט", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_fixed")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        select_view = View()
        select_view.add_item(TicketTypeSelect())
        embed = discord.Embed(title="בחר קטגוריית פנייה", description="אנא בחר מהרשימה למטה את הנושא המתאים ביותר לפנייתך.", color=0x2b2d31)
        await interaction.response.send_message(embed=embed, view=select_view, ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(TicketControlView())
        self.add_view(StaffOptionsView())
        self.add_view(ConfirmCloseView())
        self.add_view(AddUserView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"--- הבוט {self.user.name} פועל ומחובר! ---")

    async def on_member_join(self, member):
        guild = member.guild
        channel = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME)
        rules_channel = discord.utils.get(guild.text_channels, name=RULES_CHANNEL_NAME)
        rules_mention = rules_channel.mention if rules_channel else f"`{RULES_CHANNEL_NAME}`"

        auto_role = discord.utils.get(guild.roles, name=FILTER_ROLE_NAME)
        if auto_role:
            try:
                await member.add_roles(auto_role)
            except Exception as e:
                print(f"Could not add auto-role to {member.name}: {e}")

        if channel:
            embed = discord.Embed(
                title="👋 ברוך הבא לקהילה שלנו!",
                description=f"שלום {member.mention}, אנחנו שמחים שהצטרפת אלינו!",
                color=0x000000, 
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📜 מה עושים עכשיו?", 
                value=f"בבקשה לקרוא את חוקי השרת בחדר {rules_mention} כדי להימנע מאי נעימויוט.", 
                inline=False
            )
            embed.set_image(url=member.display_avatar.url)
            embed.set_footer(text=f"Maccabi Support | Member #{guild.member_count}", icon_url=guild.icon.url if guild.icon else None)
            await channel.send(content=f"ברוך הבא {member.mention}! ✨", embed=embed)

        try:
            dm_embed = discord.Embed(
                title=f"ברוך הבא לשרת {guild.name}! 🌟",
                description=f"היי {member.name},\nשמחים שהצטרפת למשפחה שלנו! אנחנו כאן לכל שאלה או עזרה שתצטרך.",
                color=0xf1c40f,
                timestamp=datetime.now()
            )
            dm_embed.add_field(name="📍 איפה מתחילים?", value=f"מומלץ לעבור על החוקים בשרת ולהתעדכן בחדשות.", inline=False)
            dm_embed.add_field(name="📩 תמיכה", value="אם תצטרך עזרה מהצוות, תוכל תמיד לפתוח טיקט במחלקה המתאימה.", inline=False)
            dm_embed.set_thumbnail(url=guild.icon.url if guild.icon else member.display_avatar.url)
            dm_embed.set_footer(text="נשמח לראות אותך פעיל בקהילה!")
            await member.send(embed=dm_embed)
        except Exception as e:
            print(f"Could not send DM to {member.name}: {e}")

    # --- מערכת הלוגים המלאה (Logs System) ---

    async def on_message_delete(self, message):
        if message.author.bot: return
        channel = discord.utils.get(message.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if channel:
            embed = discord.Embed(title="🗑️ הודעה נמחקה", color=0xff0000, timestamp=datetime.now())
            embed.add_field(name="כותב ההודעה:", value=message.author.mention, inline=True)
            embed.add_field(name="ערוץ:", value=message.channel.mention, inline=True)
            embed.add_field(name="תוכן:", value=message.content or "ללא טקסט (ייתכן תמונה)", inline=False)
            await channel.send(embed=embed)

    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        channel = discord.utils.get(before.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if channel:
            embed = discord.Embed(title="📝 הודעה נערכה", color=0xffff00, timestamp=datetime.now())
            embed.add_field(name="כותב ההודעה:", value=before.author.mention, inline=True)
            embed.add_field(name="לפני:", value=before.content, inline=False)
            embed.add_field(name="אחרי:", value=after.content, inline=False)
            await channel.send(embed=embed)

    async def on_guild_channel_update(self, before, after):
        # סינון: אם הערוץ שייך לקטגוריית הטיקטים, אל תשלח לוג
        if after.category and after.category.name == CATEGORY_NAME: return

        channel_logs = discord.utils.get(before.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if not channel_logs: return

        entry = await get_audit_log_entry(before.guild, discord.AuditLogAction.channel_update)
        user_mention = entry.user.mention if entry else "לא ידוע"

        # לוג שינוי שם
        if before.name != after.name:
            embed = discord.Embed(title="🏷️ שם ערוץ שונה", color=0x3498db, timestamp=datetime.now())
            embed.add_field(name="ערוץ:", value=after.mention)
            embed.add_field(name="לפני:", value=before.name)
            embed.add_field(name="אחרי:", value=after.name)
            embed.add_field(name="בוצע ע\"י:", value=user_mention)
            await channel_logs.send(embed=embed)

        # לוג הזזת ערוץ
        elif before.position != after.position:
            embed = discord.Embed(title="↕️ הזזת ערוץ", color=0x3498db, timestamp=datetime.now())
            embed.add_field(name="הערוץ:", value=after.mention, inline=True)
            embed.add_field(name="בוצע ע\"י:", value=user_mention, inline=True)
            await channel_logs.send(embed=embed)

    async def on_guild_channel_create(self, channel):
        if channel.category and channel.category.name == CATEGORY_NAME: return
        logs = discord.utils.get(channel.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if logs:
            entry = await get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_create)
            embed = discord.Embed(title="🆕 ערוץ נוצר", color=0x2ecc71, timestamp=datetime.now())
            embed.add_field(name="שם הערוץ:", value=channel.name)
            embed.add_field(name="נוצר ע\"י:", value=entry.user.mention if entry else "לא ידוע")
            await logs.send(embed=embed)

    async def on_guild_channel_delete(self, channel):
        if channel.category and channel.category.name == CATEGORY_NAME: return
        logs = discord.utils.get(channel.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if logs:
            entry = await get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_delete)
            embed = discord.Embed(title="🔥 ערוץ נמחק", color=0xe74c3c, timestamp=datetime.now())
            embed.add_field(name="שם הערוץ:", value=channel.name)
            embed.add_field(name="נמחק ע\"י:", value=entry.user.mention if entry else "לא ידוע")
            await logs.send(embed=embed)

    async def on_member_update(self, before, after):
        logs = discord.utils.get(before.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if not logs: return

        # לוג שינוי כינוי (Nickname)
        if before.display_name != after.display_name:
            embed = discord.Embed(title="👤 שינוי כינוי / שם", color=0x9b59b6, timestamp=datetime.now())
            embed.add_field(name="משתמש:", value=after.mention)
            embed.add_field(name="לפני:", value=before.display_name)
            embed.add_field(name="אחרי:", value=after.display_name)
            await logs.send(embed=embed)

        # לוג הוספת/הסרת רולים
        if before.roles != after.roles:
            entry = await get_audit_log_entry(before.guild, discord.AuditLogAction.member_role_update)
            executor = entry.user.mention if entry else "לא ידוע"

            if len(before.roles) < len(after.roles):
                added_role = next(role for role in after.roles if role not in before.roles)
                embed = discord.Embed(title="✅ רול ניתן", color=0x2ecc71, timestamp=datetime.now())
                embed.add_field(name="למשתמש:", value=after.mention)
                embed.add_field(name="הרול:", value=added_role.mention)
                embed.add_field(name="ניתן ע\"י:", value=executor)
                await logs.send(embed=embed)
            else:
                removed_role = next(role for role in before.roles if role not in after.roles)
                embed = discord.Embed(title="❌ רול הוסר", color=0xe74c3c, timestamp=datetime.now())
                embed.add_field(name="מהמשתמש:", value=after.mention)
                embed.add_field(name="הרול:", value=removed_role.mention)
                embed.add_field(name="הוסר ע\"י:", value=executor)
                await logs.send(embed=embed)

    async def on_guild_role_create(self, role):
        logs = discord.utils.get(role.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if logs:
            entry = await get_audit_log_entry(role.guild, discord.AuditLogAction.role_create)
            embed = discord.Embed(title="🆕 רול חדש נוצר", color=0x2ecc71, timestamp=datetime.now())
            embed.add_field(name="שם הרול:", value=role.name)
            embed.add_field(name="נוצר ע\"י:", value=entry.user.mention if entry else "לא ידוע")
            await logs.send(embed=embed)

    async def on_guild_role_delete(self, role):
        logs = discord.utils.get(role.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if logs:
            entry = await get_audit_log_entry(role.guild, discord.AuditLogAction.role_delete)
            embed = discord.Embed(title="🔥 רול נמחק", color=0xe74c3c, timestamp=datetime.now())
            embed.add_field(name="שם הרול:", value=role.name)
            embed.add_field(name="נמחק ע\"י:", value=entry.user.mention if entry else "לא ידוע")
            await logs.send(embed=embed)

bot = MyBot()

# --- פקודות Slash ---

@bot.tree.command(name="testwelcome", description="בדיקת הודעת ברוך הבא (בחדר welcome בלבד)")
async def testwelcome(interaction: discord.Interaction):
    if interaction.channel.name != WELCOME_CHANNEL_NAME:
        return await interaction.response.send_message(f"ניתן להשתמש בפקודה זו רק בחדר {WELCOME_CHANNEL_NAME}", ephemeral=True)

    await interaction.response.defer()

    member = interaction.user
    rules_channel = discord.utils.get(interaction.guild.text_channels, name=RULES_CHANNEL_NAME)
    rules_mention = rules_channel.mention if rules_channel else f"`{RULES_CHANNEL_NAME}`"

    embed = discord.Embed(
        title="👋 ברוך הבא לקהילה שלנו!",
        description=f"שלום {member.mention}, אנחנו שמחים שהצטרפת אלינו!",
        color=0x000000,
        timestamp=datetime.now()
    )
    embed.add_field(
        name="📜 מה עושים עכשיו?", 
        value=f"בבקשה לקרוא את חוקי השרת בחדר {rules_mention} כדי להימנע מאי נעימויות.", 
        inline=False
    )

    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=f"Maccabi Support | Test Mode", icon_url=member.guild.icon.url if member.guild.icon else None)

    await interaction.followup.send(content=f"ברוך הבא {member.mention}! (בדיקת מערכת) ✨", embed=embed)

@bot.tree.command(name="setup", description="הגדרת פאנל הטיקטים")
async def setup(interaction: discord.Interaction):
    if not any(r.name == "server owner" for r in interaction.user.roles):
        return await interaction.response.send_message("רק הבעלים יכול להשתמש בפקודה זו!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="**פתיחת טיקט בשרת**", description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n**צריכים עזרה? לחצו על פתיחת טיקט**", color=0x2b2d31)

    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    embed.set_footer(text="כל הזכויות שמורות ל- [MF]")
    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.followup.send("המערכת הותקנה!")

@bot.tree.command(name="clear", description="מחיקת כמות מסוימת של הודעות מהצ'אט")
@app_commands.describe(amount="כמות ההודעות למחיקה")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("אין לך הרשאה למחוק הודעות!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"נמחקו בהצלחה `{len(deleted)}` הודעות.", ephemeral=True)

@bot.tree.command(name="rename", description="שינוי שם של חדר בשרת")
@app_commands.describe(new_name="השם החדש לחדר")
async def rename(interaction: discord.Interaction, new_name: str):
    if not any(discord.utils.get(interaction.user.roles, name=r) for r in RENAME_ROLES):
        return await interaction.response.send_message("אין לך הרשאה לשנות שם לחדרים!", ephemeral=True)

    await interaction.channel.edit(name=new_name)
    embed = discord.Embed(description=f"שם החדר שונה בהצלחה ל: `{new_name}`", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="timeout", description="מתן טיימאוט למשתמש בשרת")
@app_commands.describe(member="המשתמש שברצונך להשתיק", minutes="כמות דקות (לדוגמה: 10)", reason="סיבת הטיימאוט")
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "לא צוינה סיבה"):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("אין לך הרשאות מתאימות לביצוע פעולה זו!", ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        return await interaction.response.send_message("אינך יכול לתת טיימאוט למשתמש עם רול גבוה ממך או שווה לך!", ephemeral=True)

    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)

        embed = discord.Embed(title="🔇 משתמש הושתק (Timeout)", color=0xffa500, timestamp=datetime.now())
        embed.add_field(name="משתמש:", value=member.mention, inline=True)
        embed.add_field(name="זמן:", value=f"{minutes} דקות", inline=True)
        embed.add_field(name="בוצע ע\"י:", value=interaction.user.mention, inline=True)
        embed.add_field(name="סיבה:", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"שגיאה בביצוע הפעולה: {e}", ephemeral=True)
        
# --- Advanced Giveaway System ---
import random
import asyncio
from datetime import datetime, timedelta

class GiveawayView(View):
    def __init__(self, end_time, winners_count, role_id, host_id):
        super().__init__(timeout=None)
        self.participants = set()
        self.end_time = end_time
        self.winners_count = winners_count
        self.role_id = role_id
        self.host_id = host_id

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(self.role_id)

        if role and role not in interaction.user.roles:
            return await interaction.response.send_message("אין לך את הרול הנדרש כדי להשתתף!", ephemeral=True)

        if interaction.user.id in self.participants:
            return await interaction.response.send_message("אתה כבר רשום להגרלה 🎉", ephemeral=True)

        self.participants.add(interaction.user.id)

        await interaction.response.send_message("נכנסת להגרלה, בהצלחה! 🎉", ephemeral=True)
        await self.update_embed(interaction.message)

    @discord.ui.button(label="❌ Leave Giveaway", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id not in self.participants:
            return await interaction.response.send_message("אתה לא רשום להגרלה.", ephemeral=True)

        self.participants.remove(interaction.user.id)

        await interaction.response.send_message("יצאת מההגרלה.", ephemeral=True)
        await self.update_embed(interaction.message)

    async def update_embed(self, message):
        embed = message.embeds[0]
        embed.set_field_at(2, name="**__Participants __**", value=str(len(self.participants)), inline=False)
        await message.edit(embed=embed, view=self)


async def run_giveaway(message, view: GiveawayView):
    while True:
        now = datetime.utcnow()
        remaining = view.end_time - now

        if remaining.total_seconds() <= 0:
            break

        total_seconds = int(remaining.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            time_text = f"{days}d {hours}h"
        elif hours > 0:
            time_text = f"{hours}h {minutes}m"
        else:
            time_text = f"{minutes}m"

        embed = message.embeds[0]
        embed.set_field_at(1, name="**__Time Remaining __**", value=time_text, inline=False)

        await message.edit(embed=embed)
        await asyncio.sleep(60)

    participants = list(view.participants)
    embed = message.embeds[0]
    prize_name = embed.description.replace("**", "")

    if len(participants) == 0:
        embed.title = "❌ Giveaway Ended"
        embed.description = "לא היו מספיק משתתפים."
        await message.edit(embed=embed, view=None)
        return

    winners = random.sample(participants, min(view.winners_count, len(participants)))
    winners_mentions = ", ".join([f"<@{w}>" for w in winners])

    embed.title = "🎉 Giveaway Ended 🎉"
    embed.description = f"**הפרס:** {prize_name}"
    embed.clear_fields()
    embed.add_field(name="**__Winners🏆 __**", value=winners_mentions, inline=False)
    
    await message.edit(embed=embed, view=None)

    # פאנל הכרזה על זוכים: התיוג מופיע רק בתוך הפאנל (description)
    winner_embed = discord.Embed(
        title="זוכה ההגרלה הוא:",
        description=f"{winners_mentions} זכה בהגרלה על {prize_name} ! 🥳",
        color=0xFFA500 
    )
    # שליחת הפאנל ללא תוכן (content) חיצוני כדי למנוע תיוג כפול
    await message.channel.send(embed=winner_embed)


@bot.tree.command(name="giveaway", description="יצירת הגרלה חדשה")
@app_commands.describe(
    prize="What is the giveaway for?",
    days="Number of days",
    hours="Number of hours",
    minutes="Number of minutes",
    winners="Number of winners",
    role="Role required to join"
)
async def giveaway(interaction: discord.Interaction, prize: str, winners: int, role: discord.Role, days: int = 0, hours: int = 0, minutes: int = 0):

    if not any(r.name in ["server owner", "co | owner"] for r in interaction.user.roles):
        return await interaction.response.send_message("אין לך הרשאות לבצע פקודה זו!", ephemeral=True)

    total_duration_minutes = (days * 1440) + (hours * 60) + minutes
    if total_duration_minutes <= 0:
        return await interaction.response.send_message("חובה להזין זמן תקין להגרלה!", ephemeral=True)

    end_time = datetime.utcnow() + timedelta(minutes=total_duration_minutes)
    
    display_end_time = end_time + timedelta(hours=3)
    end_date_str = display_end_time.strftime("%d/%m/%Y at %H:%M")

    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=f"**{prize}**",
        color=0x5865F2
    )

    embed.add_field(name="**__Hosted by __**", value=interaction.user.mention, inline=False)
    embed.add_field(name="**__Time Remaining __**", value=f"Calculating...", inline=False)
    embed.add_field(name="**__Participants __**", value="0", inline=False)
    embed.add_field(name="**__Winners🏆 __**", value=str(winners), inline=False)
    embed.add_field(name="**__Required Role __**", value=role.mention, inline=False)
    embed.add_field(name="**__End Date __**", value=end_date_str, inline=False)

    embed.set_footer(text="Click the buttons below to join or leave!")

    view = GiveawayView(end_time, winners, role.id, interaction.user.id)

    await interaction.response.send_message("יוצר הגרלה...", ephemeral=True)
    message = await interaction.channel.send(embed=embed, view=view)

    bot.loop.create_task(run_giveaway(message, view))
    
    import collections

# --- הגדרות מערכת Anti-Spam ---
# משתנה לשמירת היסטוריית ההודעות בזיכרון (מתאפס בכל הפעלה)
user_message_data = {}

# רשימת הרולים שחסינים מהמערכות
WHITELIST_ROLES = ["server owner", "DEV Server Discord", "co | owner", "『בעל השרת』", "server bot", "Management"]

@bot.event
async def on_message(message):

    # התעלמות מהודעות של הבוט עצמו

    if message.author.bot:

        return



    # בדיקה אם המשתמש חסין לפי הרולים שלו

    is_whitelisted = any(role.name in WHITELIST_ROLES for role in message.author.roles)



    # --- מערכת Anti-Link (זיהוי קישורים לשרתים אחרים) ---

    if not is_whitelisted:

        # מחפש קישורי דיסקורד (discord.gg או discord.com/invite)

        if "discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower():

            await message.delete() # מחיקת הקישור אוטומטית

           

            link_embed = discord.Embed(

                title=f"**__נמחק אוטומטית הקישור ששלחת {message.author.display_name}__**",

                description=(

                    "זוהה ששלחת קישור, בפעם הבאה שתשלח קישור תקבל טיימאוט!\n"

                    "כל עבירה על חוקי השרת תגרום לענישה!"

                ),

                color=0xFF0000 # אדום

            )

            link_embed.set_thumbnail(url=message.author.display_avatar.url)

            return await message.channel.send(content=message.author.mention, embed=link_embed)



    # --- מערכת Anti-Spam (5 הודעות בפחות מ-2 שניות) ---

    if not is_whitelisted:

        user_id = message.author.id

        now = datetime.utcnow()



        if user_id not in user_message_data:

            user_message_data[user_id] = []



        # מוסיף את זמן ההודעה הנוכחית ומנקה הודעות ישנות מהרשימה (מעל 2 שניות)

        user_message_data[user_id].append(now)

        user_message_data[user_id] = [t for t in user_message_data[user_id] if (now - t).total_seconds() < 2]



        # בדיקה אם נשלחו 5 הודעות ומעלה

        if len(user_message_data[user_id]) >= 5:

            try:

                # מתן טיימאוט ל-5 דקות

                duration = timedelta(minutes=5)

                await message.author.timeout(duration, reason="Spamming in chat")

               

                spam_embed = discord.Embed(

                    title=f"**__קיבלת טיימאוט {message.author.display_name}__**",

                    description=(

                        "זוהה ספאם בצאט, קיבלת טיימאוט ל-5 דקות!\n"

                        "פעם הבאה שתעבור על החוקים תענש שוב."

                    ),

                    color=0xFFA500 # כתום-צהוב

                )

                spam_embed.set_thumbnail(url=message.author.display_avatar.url)

               

                # איפוס המונה למשתמש לאחר הענישה

                user_message_data[user_id] = []

               

                await message.channel.send(content=message.author.mention, embed=spam_embed)

            except Exception as e:

                print(f"Error giving timeout: {e}")



    # חשוב: מאפשר לפקודות אחרות של הבוט להמשיך לעבוד

    await bot.process_commands(message)
    
    # --- Poll System ---

class PollView(View):
    def __init__(self, options, end_time):
        super().__init__(timeout=None)
        self.votes = {}  # user_id -> option_index
        self.options = options
        self.end_time = end_time
        self.counts = [0] * len(options)

        for i, option in enumerate(options):
            button = Button(label=option, style=discord.ButtonStyle.primary)

            async def callback(interaction: discord.Interaction, index=i):
                await self.handle_vote(interaction, index)

            button.callback = callback
            self.add_item(button)

        remove_btn = Button(label="❌ Remove Vote", style=discord.ButtonStyle.danger)
        remove_btn.callback = self.remove_vote
        self.add_item(remove_btn)

    async def handle_vote(self, interaction, index):
        user_id = interaction.user.id

        if datetime.utcnow() >= self.end_time:
            return await interaction.response.send_message("This poll has ended.", ephemeral=True)

        if user_id in self.votes:
            old_index = self.votes[user_id]
            self.counts[old_index] -= 1

        self.votes[user_id] = index
        self.counts[index] += 1

        await interaction.response.send_message("Your vote has been recorded ✅", ephemeral=True)
        await self.update_embed(interaction.message)

    async def remove_vote(self, interaction):
        user_id = interaction.user.id

        if user_id not in self.votes:
            return await interaction.response.send_message("You haven't voted yet.", ephemeral=True)

        index = self.votes[user_id]
        self.counts[index] -= 1
        del self.votes[user_id]

        await interaction.response.send_message("Your vote has been removed ❌", ephemeral=True)
        await self.update_embed(interaction.message)

    async def update_embed(self, message):
        embed = message.embeds[0]

        desc = ""
        for i, option in enumerate(self.options):
            desc += f"**{option}** — {self.counts[i]} votes\n"

        embed.description = desc
        await message.edit(embed=embed, view=self)


async def run_poll(message, view: PollView):
    while True:
        if datetime.utcnow() >= view.end_time:
            break
        await asyncio.sleep(10)

    embed = message.embeds[0]
    embed.title = "📊 Poll Ended"
    embed.set_footer(text="Voting closed")

    await message.edit(embed=embed, view=None)


@bot.tree.command(name="poll", description="Create a poll")
@app_commands.describe(
    question="The poll question",
    option1="Option 1",
    option2="Option 2",
    option3="Option 3",
    option4="Option 4",
    option5="Option 5",
    option6="Option 6",
    time="Duration number",
    unit="minutes / hours / days"
)
@app_commands.choices(unit=[
    app_commands.Choice(name="Minutes", value="minutes"),
    app_commands.Choice(name="Hours", value="hours"),
    app_commands.Choice(name="Days", value="days"),
])
async def poll(
    interaction: discord.Interaction,
    question: str,
    option1: str,
    option2: str,
    time: int,
    unit: app_commands.Choice[str],
    option3: str = None,
    option4: str = None,
    option5: str = None,
    option6: str = None
):

    await interaction.response.defer()

    options = [option1, option2]

    for opt in [option3, option4, option5, option6]:
        if opt:
            options.append(opt)

    if unit.value == "minutes":
        delta = timedelta(minutes=time)
    elif unit.value == "hours":
        delta = timedelta(hours=time)
    else:
        delta = timedelta(days=time)

    end_time = datetime.utcnow() + delta

    embed = discord.Embed(
        title="📊 NEW POL",
        description="",
        color=0x5865F2
    )

    embed.add_field(name="Question", value=question, inline=False)

    desc = ""
    for opt in options:
        desc += f"**{opt}** — 0 votes\n"

    embed.description = desc

    embed.set_footer(text=f"Ends in {time} {unit.value}")

    view = PollView(options, end_time)

    message = await interaction.channel.send(embed=embed, view=view)

    bot.loop.create_task(run_poll(message, view))
    
bot.run(os.environ.get("TOKEN"))