import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import asyncio
from datetime import datetime

# --- הגדרות רולים והרשאות ---
# רולים לפקודות ניהול (setup, clear)
ADMIN_ROLES = ["server owner", "DEV Server Discord", "co | owner", "『בעל השרת』", "server bot"]

# רולים לפקודת שינוי שם (rename) - כולל את המנהלים + הצוות שביקשת
RENAME_ROLES = ADMIN_ROLES + ["Staff Team", "Management"]

# הגדרות כלליות
AUTHORIZED_ROLES = ["server owner", "co | owner", "גישות", "בעל השרת", "Staff", "Admin", "Staff Team"]
CATEGORY_NAME = "Tickets" 
LOGS_CHANNEL_NAME = "logs-system"
# ---------------------

class RenameModal(Modal, title='📝 שינוי שם הטיקט'):
    name = TextInput(label='שם חדש לערוץ', placeholder='הקלד שם (נקי ללא אימוג\'י)...', min_length=2, max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.edit(name=f"{self.name.value}")
        embed = discord.Embed(description=f"השם של הטיקט שונה ל: `{self.name.value}`", color=0x000000)
        await interaction.response.send_message(embed=embed)

class ConfirmCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="אשר סגירה ✅", style=discord.ButtonStyle.success, custom_id="confirm_close_fixed")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("רק צוות יכול לאשר סגירה!", ephemeral=True)
            
        await interaction.response.send_message("הסגירה אושרה. סוגר את הטיקט בעוד **5**...")
        message = await interaction.original_response()
        for i in range(4, 0, -1):
            await asyncio.sleep(1)
            await message.edit(content=f"סוגר את הטיקט בעוד **{i}**...")
        await asyncio.sleep(1)
        await interaction.channel.delete()

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
            if len(found_message.embeds[0].fields) == 0:
                return await interaction.response.send_message("הטיקט כבר נמצא במצב המתנה!", ephemeral=True)
            
            embed = found_message.embeds[0]
            embed.clear_fields()
            embed.color = 0xffffff
            await found_message.edit(embed=embed, view=TicketControlView())
            await interaction.response.send_message("הטיקט שוחרר והוחזר למצב המתנה.", ephemeral=True)
        else:
            await interaction.response.send_message("לא נמצאה הודעת הטיקט המקורית.", ephemeral=True)

    @discord.ui.button(label="שנה שם 📝", style=discord.ButtonStyle.success, custom_id="staff_rename_fixed", row=1)
    async def rename_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # בדיקה אם המשתמש יכול לשנות שם (לפי הרשימה המורחבת)
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in RENAME_ROLES):
            return await interaction.response.send_message("אין לך הרשאה לשנות שם!", ephemeral=True)
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.danger, custom_id="staff_close_now_fixed", row=2)
    async def close_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)
        await interaction.response.send_message("סוגר את הטיקט בעוד **5**...")
        message = await interaction.original_response()
        for i in range(4, 0, -1):
            await asyncio.sleep(1)
            await message.edit(content=f"סוגר את הטיקט בעוד **{i}**...")
        await asyncio.sleep(1)
        await interaction.channel.delete()

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לבקש לסגור 🚩", style=discord.ButtonStyle.danger, custom_id="req_close_fixed")
    async def request_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="בקשת סגירה",
            description=f"המשתמש {interaction.user.mention} ביקש לסגור את הטיקט.\nאיש צוות, נא לאשר את הסגירה.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, view=ConfirmCloseView())

    @discord.ui.button(label="לקחת טיקט ✅", style=discord.ButtonStyle.success, custom_id="claim_fixed")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("אין לך הרשאה!", ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.clear_fields()
        embed.add_field(name="מצב הטיקט:", value=f"בטיפול ע\"י {interaction.user.mention}", inline=False)
        embed.color = 0x5865F2
        
        new_view = TicketControlView()
        for child in new_view.children:
            if child.custom_id == "claim_fixed":
                child.disabled = True
        
        await interaction.message.edit(embed=embed, view=new_view)
        await interaction.response.send_message(f"הטיקט נלקח על ידי {interaction.user.mention}", ephemeral=True)

    @discord.ui.button(label="אפשרויות צוות 🛠️", style=discord.ButtonStyle.primary, custom_id="staff_opts_fixed")
    async def staff_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(discord.utils.get(interaction.user.roles, name=r) for r in AUTHORIZED_ROLES):
            return await interaction.response.send_message("גישה לצוות בלבד.", ephemeral=True)
        
        staff_embed = discord.Embed(
            title="🛠️ פאנל ניהול צוות", 
            description="==================================\n**בחר את הפעולה הרצויה לניהול הפנייה:**\n==================================", 
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=staff_embed, view=StaffOptionsView(), ephemeral=True)

class TicketTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="💬", description="פתיחת פנייה בנושאים כלליים"),
            discord.SelectOption(label="בחינה לצוות", emoji="📝", description="הגשת מועמדות לצוות השרת"),
            discord.SelectOption(label="דיווח על באג", emoji="🐞", description="דיווח על תקלות טכניות")
        ]
        super().__init__(placeholder="...בחר את נושא הפנייה", options=options, custom_id="ticket_type_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_name = self.values[0]
        
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        staff_role = discord.utils.get(guild.roles, name="Staff Team")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)

        for r_name in AUTHORIZED_ROLES:
            role = discord.utils.get(guild.roles, name=r_name)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            f'{category_name}-{user.name}', 
            overwrites=overwrites, 
            category=category
        )
        
        inner_embed = discord.Embed(
            title="טיקט נפתח", 
            description=f"----------------------------------\n**נושא הפנייה:** {category_name}\nנא להמתין לצוות בסבלנות וכתבו את שאלתכם.", 
            color=0xffffff
        )
        inner_embed.set_footer(text="Maccabi Support | מערכת הפניות")
        
        staff_mention = staff_role.mention if staff_role else "@Staff Team"
        await channel.send(f"{user.mention} {staff_mention} שלום, פנייתך התקבלה.", embed=inner_embed, view=TicketControlView())
        await interaction.response.edit_message(content=f"הטיקט נפתח בהצלחה: {channel.mention}", embed=None, view=None)

class TicketTypeView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(TicketTypeSelect())

class OpenTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="פתיחת טיקט", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_fixed")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        selection_embed = discord.Embed(
            title="**__בחר קטגוריית פנייה__**",
            description="> אנא בחר מהרשימה למטה את הנושא המתאים ביותר לפנייתך כדי שנוכל לעזור לך במהירות.",
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=selection_embed, view=TicketTypeView(), ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.last_move_time = 0

    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(TicketControlView())
        self.add_view(StaffOptionsView())
        self.add_view(ConfirmCloseView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"--- הבוט {self.user.name} פועל ומחובר! ---")

    async def on_guild_channel_update(self, before, after):
        if after.category and after.category.name == CATEGORY_NAME: return
        logs_channel = discord.utils.get(after.guild.text_channels, name=LOGS_CHANNEL_NAME)
        if not logs_channel: return
        
        embed = discord.Embed(title="⚙️ עדכון ערוץ", color=0x3498db)
        
        if before.position != after.position:
            current_time = datetime.now().timestamp()
            if current_time - self.last_move_time < 2:
                return
            self.last_move_time = current_time
            embed.title = "↕️ הזזת חדר"
            embed.add_field(name="החדר שהוזז", value=after.mention, inline=False)
        elif before.name != after.name or before.topic != after.topic:
            if before.name != after.name:
                embed.add_field(name="שינוי שם חדר", value=f"מ-`{before.name}` ל-`{after.name}`")
            if before.topic != after.topic:
                embed.add_field(name="שינוי נושא חדר", value=f"מ-`{before.topic}` ל-`{after.topic}`")
        else:
            return

        await asyncio.sleep(0.5)
        author = "לא ידוע"
        async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_update):
            if entry.target.id == after.id:
                author = entry.user.mention
                break
        
        embed.add_field(name="בוצע ע\"י", value=author, inline=False)
        await logs_channel.send(embed=embed)

bot = MyBot()

# --- פקודות סלאש עם הרשאות מעודכנות ---

@bot.tree.command(name="rename", description="שינוי שם הטיקט (לצוות מורשה בלבד)")
async def rename(interaction: discord.Interaction, new_name: str):
    # בדיקה לפי רשימת RENAME_ROLES
    if not any(discord.utils.get(interaction.user.roles, name=r) for r in RENAME_ROLES):
        return await interaction.response.send_message("אין לך הרשאה להשתמש בפקודה זו!", ephemeral=True)
    await interaction.channel.edit(name=new_name)
    await interaction.response.send_message(embed=discord.Embed(description=f"שם הערוץ שונה ל: **{new_name}**", color=0x00ff00))

@bot.tree.command(name="clear", description="מחיקת הודעות (להנהלה בלבד)")
@app_commands.describe(amount="כמות הודעות למחיקה")
async def clear(interaction: discord.Interaction, amount: int):
    # בדיקה לפי רשימת ADMIN_ROLES
    if not any(discord.utils.get(interaction.user.roles, name=r) for r in ADMIN_ROLES):
        return await interaction.response.send_message("אין לך הרשאה למחיקת הודעות!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"נמחקו בהצלחה **{len(deleted)}** הודעות.", ephemeral=True)

@bot.tree.command(name="setup", description="הגדרת פאנל הטיקטים (להנהלה בלבד)")
async def setup(interaction: discord.Interaction):
    # בדיקה לפי רשימת ADMIN_ROLES
    if not any(discord.utils.get(interaction.user.roles, name=r) for r in ADMIN_ROLES):
        return await interaction.response.send_message("אין לך הרשאה להגדרת המערכת!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="**פתיחת טיקט בשרת**", description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n**צריכים עזרה? לחצו על פתיחת טיקט**", color=0x2b2d31)
    if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="כל הזכויות שמורות ל- [MF]")
    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.followup.send("המערכת הותקנה!")

# משיכת הטוקן בצורה בטוחה
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("Error: DISCORD_TOKEN not found!")