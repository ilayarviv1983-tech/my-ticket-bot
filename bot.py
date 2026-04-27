import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import asyncio
import os  # חשוב בשביל השרת

# --- הגדרות מערכת ---
TOKEN = os.getenv('DISCORD_TOKEN') # זה מאפשר לשרת לקרוא את הטוקן בצורה מאובטחת
AUTHORIZED_ROLES = ["server owner", "co | owner", "גישות", "בעל השרת", "Staff", "Admin", "Staff Team"]
# ---------------------

class RenameModal(Modal, title='📝 שינוי שם הטיקט'):
    name = TextInput(label='שם חדש לערוץ', placeholder='הקלד שם...', min_length=2, max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.edit(name=f"📩-{self.name.value}")
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
        
        async for msg in interaction.channel.history(limit=20):
            if msg.embeds and msg.embeds[0].title == "טיקט נפתח":
                embed = msg.embeds[0]
                embed.clear_fields()
                embed.color = 0xffffff
                await msg.edit(embed=embed, view=TicketControlView())
                break
        await interaction.response.send_message("הטיקט שוחרר והוחזר למצב המתנה.", ephemeral=True)

    @discord.ui.button(label="שנה שם 📝", style=discord.ButtonStyle.secondary, custom_id="staff_rename_fixed", row=1)
    async def rename_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameModal())

    # סגור טיקט מופיע מתחת לשנה שם (שורה 2)
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
        
        for child in self.children:
            if child.custom_id == "claim_fixed":
                child.disabled = True
        
        await interaction.message.edit(embed=embed, view=self)
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
            discord.SelectOption(label="דיווח על באג", emoji="🐛", description="דיווח על תקלות טכניות"),
            discord.SelectOption(label="בחינה לצוות", emoji="📝", description="הגשת מועמדות לצוות השרת")
        ]
        super().__init__(placeholder="...בחר את נושא הפנייה", options=options, custom_id="ticket_type_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_name = self.values[0]
        
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

        channel = await guild.create_text_channel(f'{category_name}-{user.name}', overwrites=overwrites)
        
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
    
    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(TicketControlView())
        self.add_view(StaffOptionsView())
        self.add_view(ConfirmCloseView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"--- הבוט {self.user.name} פועל ומחובר! ---")

bot = MyBot()

@bot.tree.command(name="setup", description="הגדרת פאנל הטיקטים")
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="**פתיחת טיקט בשרת**",
        description=(
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "**צריכים עזרה בנוגע לשרת, או כל דבר אחר?**\n"
            "**לחצו על פתיחת טיקט**\n\n"
            "**זמן מענה משוער:** דקות בודדות."
        ),
        color=0x2b2d31
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    embed.set_footer(text="כל הזכויות שמורות ל- [MF]")

    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.followup.send("המערכת הותקנה בהצלחה!")

bot.run(TOKEN)