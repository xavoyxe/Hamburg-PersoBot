import asyncio
import json
import sys
import time
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, Button, View, Select
import os
from typing import List
from moduals.perso_crud import Person, PersonenDB
from pathlib import Path
from enum import Enum
from moduals.ini_crud import INIManager
from moduals.logger_crud import LoggingManager
import requests
import aiohttp
import io

variables = INIManager("app_data/ini/variables.ini")


class Vars(str, Enum):
    GUILD = variables.get("DISCORD", "GUILD")
    DATABASE = variables.get("DISCORD", "DATABASE")
    CREATION = variables.get("DISCORD", "CREATION")
    SHOW = variables.get("DISCORD", "SHOW")
    PROF = variables.get("DISCORD", "PROF")
    GENERAL = variables.get("COMMANDS", "GENERAL")
    DELLPERSO = variables.get("COMMANDS", "DELLPERSO")
    STOP = variables.get("COMMANDS", "STOP")
    USERDATA = variables.get("COMMANDS", "USERDATA")
    DynamicSelectPlaceholder = variables.get("VARS", "DynamicSelectPlaceholder")
    BackUps = variables.get("VARS", "BackUps")
    BackUpsFile = variables.get("VARS", "BackUpsFile")
    BackUpsTime = variables.get("VARS", "BackUpsTime")
    CreatePerso = variables.get("CommandNames", "CreatePerso")
    DeletePerso = variables.get("CommandNames", "DeletePerso")
    ShowPerso = variables.get("CommandNames", "ShowPerso")
    PersoDatabase = variables.get("FILES", "PersoDatabase")
    PersoPng = variables.get("FILES", "PersoPng")
    DebugLog = variables.get("FILES", "DebugLog")


LOCKS_FILE = Path("locks.json")


def load_locks():
    if LOCKS_FILE.exists():
        with LOCKS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_locks(locks):
    with LOCKS_FILE.open("w", encoding="utf-8") as f:
        json.dump(locks, f, indent=2)


logger = LoggingManager(Vars.DebugLog.value).get_logger()

try:
    perso_db = PersonenDB(Path("."))
except Exception as e:
    logger.error(e)


class Status(str, Enum):
    ausstehend = "ausstehend"
    angenommen = "angenommen"
    bearbeitung = "bearbeitung"
    abgelehnt = "abgelehnt"


async def send_embed(
        interaction: discord.Interaction = None,
        channel_id: int = None,
        title: str = "",
        description: str = "",
        fields: list = None,
        color: discord.Color = discord.Color.blue(),
        thumbnail_url: str = None,
        image_url: str = None,
        footer_text: str = None,
        footer_icon: str = None,
        author_name: str = None,
        author_url: str = None,
        author_icon: str = None,
        ephemeral: bool = False,
        view: discord.ui.View = None,
        user_id: int = None
):
    try:
        if interaction is None and channel_id is None and user_id is None:
            raise ValueError("Entweder interaction, channel_id oder user_id muss angegeben werden")

        embed = discord.Embed(
            title=title[:256],
            description=description[:4096],
            color=color
        )

        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", "")[:256],
                    value=field.get("value", "")[:1024],
                    inline=field.get("inline", False)
                )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if image_url:
            embed.set_image(url=image_url)

        if footer_text or footer_icon:
            embed.set_footer(
                text=footer_text[:2048] if footer_text else None,
                icon_url=footer_icon if footer_icon else None
            )

        if author_name:
            embed.set_author(
                name=author_name[:256],
                url=author_url if author_url else None,
                icon_url=author_icon if author_icon else None
            )

        if user_id:
            try:
                user = await bot.fetch_user(user_id)
                dm_channel = user.dm_channel or await user.create_dm()

                if view:
                    await dm_channel.send(embed=embed, view=view)
                else:
                    await dm_channel.send(embed=embed)
                logger.info(f"Embed erfolgreich an User {user_id} gesendet")
                return
            except discord.Forbidden:
                if interaction:
                    await interaction.followup.send(
                        "Konnte keine DM senden (Nutzer hat DMs deaktiviert)",
                        ephemeral=True
                    )
                logger.warning(f"Konnte DM an User {user_id} nicht senden (DMs deaktiviert)")
                return
            except Exception as e:
                logger.error(f"Fehler beim DM-Versand an User {user_id}: {str(e)}", exc_info=True)
                if interaction:
                    await interaction.followup.send(
                        "Es gab einen Fehler beim Senden der DM.",
                        ephemeral=True
                    )
                return

        if channel_id:
            try:
                channel = interaction.client.get_channel(channel_id) if interaction else bot.get_channel(channel_id)
                if not channel:
                    raise ValueError(f"Channel mit ID {channel_id} nicht gefunden")

                if view:
                    await channel.send(embed=embed, view=view)
                else:
                    await channel.send(embed=embed)
                logger.info(f"Embed erfolgreich in Channel {channel_id} gesendet")
            except Exception as e:
                logger.error(f"Fehler beim Senden in Channel {channel_id}: {str(e)}", exc_info=True)
                if interaction:
                    await interaction.followup.send(
                        f"Es gab einen Fehler beim Senden in Channel {channel_id}.",
                        ephemeral=True
                    )
                return

        if interaction:
            try:
                kwargs = {
                    "embed": embed,
                    "ephemeral": ephemeral
                }
                if view:
                    kwargs["view"] = view

                if interaction.response.is_done():
                    await interaction.followup.send(**kwargs)
                else:
                    await interaction.response.send_message(**kwargs)
                logger.info("Embed erfolgreich als Interaktionsantwort gesendet")
            except Exception as e:
                logger.error(f"Fehler beim Senden der Interaktionsantwort: {str(e)}", exc_info=True)
                try:
                    await interaction.followup.send(
                        "Es gab einen Fehler beim Senden der Antwort.",
                        ephemeral=True
                    )
                except:
                    pass

    except Exception as e:
        logger.critical(f"Kritischer Fehler in send_embed: {str(e)}", exc_info=True)
        if interaction:
            try:
                await interaction.followup.send(
                    "Es gab einen kritischen Fehler beim Verarbeiten der Anfrage.",
                    ephemeral=True
                )
            except:
                pass


class DynamicModal(discord.ui.Modal):
    def __init__(self, fields: List[str], *args, **kwargs):
        self.logger = logger
        super().__init__(*args, **kwargs)
        self.fields = fields
        self.data = {}
        self.user_inputs = []
        self.interaction = None
        self.discord_userid = None

        try:
            for field in fields:
                text_input = discord.ui.TextInput(
                    label=field,
                    style=discord.TextStyle.short,
                    required=True
                )
                self.user_inputs.append(text_input)
                self.add_item(text_input)
            self.logger.debug(f"DynamicModal mit Feldern {fields} initialisiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des DynamicModal: {str(e)}", exc_info=True)
            raise

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.data = {field: input_item.value for field, input_item in zip(self.fields, self.user_inputs)}
            await interaction.response.defer()
            self.interaction = interaction
            self.discord_userid = interaction.user.id
            self.logger.info(f"Modal submitted von User {self.discord_userid} mit Daten: {self.data}")
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Modal-Submits: {str(e)}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "Es gab einen Fehler beim Verarbeiten deiner Eingabe.",
                    ephemeral=True
                )
            except:
                pass
            raise

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        self.logger.error(f"Modal-Fehler: {str(error)}", exc_info=True)
        try:
            await interaction.response.send_message(
                "Es gab einen unerwarteten Fehler. Bitte versuche es später erneut.",
                ephemeral=True
            )
        except:
            pass


class DynamicSelect(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption]):
        self.logger = logger
        try:
            super().__init__(
                placeholder="Wähle eine Option...",
                min_values=1,
                max_values=1,
                options=options
            )
            self.logger.debug(f"DynamicSelect mit {len(options)} Optionen initialisiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des DynamicSelect: {str(e)}", exc_info=True)
            raise

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.selected_value = self.values[0]
            await interaction.response.defer()
            await interaction.delete_original_response()
            self.logger.info(f"Select-Option '{self.view.selected_value}' von User {interaction.user.id} gewählt")
            self.view.stop()
        except Exception as e:
            self.logger.error(f"Fehler im Select-Callback: {str(e)}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "Es gab einen Fehler bei der Auswahl. Bitte versuche es erneut.",
                    ephemeral=True
                )
            except:
                pass
            raise


class DropdownView(discord.ui.View):
    def __init__(self, options: List[discord.SelectOption]):
        self.logger = logger
        super().__init__()
        self.selected_value = None
        try:
            self.add_item(DynamicSelect(options))
            self.logger.debug(f"DropdownView mit {len(options)} Optionen initialisiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des DropdownView: {str(e)}", exc_info=True)
            raise

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        self.logger.error(
            f"View-Fehler bei Item {item}: {str(error)}",
            exc_info=True
        )
        try:
            await interaction.response.send_message(
                "Es gab einen unerwarteten Fehler. Bitte versuche es später erneut.",
                ephemeral=True
            )
        except:
            pass


WEBHOOK_URL = "https://discord.com/api/webhooks/1400072969354612831/u1IAWbZ8pfrlGfzmRTOR7tzaLXQ6dfNLaT__pLiYAo1Wb-tOAYYjN0QuEe_Z7oyveuTx"


def send_webhook_log(content: str):
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        logger.error(f"Fehler beim Senden des Webhook-Logs: {str(e)}")


class ApprovalButtons(discord.ui.View):
    def __init__(self, user_id: int, uuid: str, a, is_fake: bool = False):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.uuid = uuid
        self.logger = logger
        self.id_a = a
        self.is_fake = is_fake
        self.logger.info(f"ApprovalButtons initialisiert für User {user_id} mit UUID {uuid} (Gefälscht: {is_fake})")

    async def handle_error(self, interaction: discord.Interaction, error: Exception, action: str):
        self.logger.error(f"Fehler bei {action}: {str(error)}", exc_info=True)
        try:
            await interaction.followup.send(
                f"Ein Fehler ist während der {action} aufgetreten. Bitte versuche es später erneut.",
                ephemeral=True
            )
        except:
            pass

    @discord.ui.button(label="Annehmen", style=discord.ButtonStyle.success, emoji="✅", custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)

            try:
                if hasattr(self, 'id_a') and self.id_a:
                    message = await interaction.channel.fetch_message(self.id_a)
                    await message.delete()
                    self.logger.debug(f"Antragsnachricht {self.id_a} gelöscht")

                if interaction.message:
                    await interaction.message.delete()
                    self.logger.debug("Button-Nachricht gelöscht")

            except discord.NotFound:
                self.logger.warning("Eine der Nachrichten wurde bereits gelöscht")
            except discord.Forbidden:
                self.logger.error("Keine Berechtigung zum Löschen der Nachrichten")
            except Exception as e:
                self.logger.error(f"Fehler beim Löschen: {str(e)}")

            try:
                antrag = perso_db.get_perso_by_uuid(uuid_str=self.uuid)
                if not antrag:
                    raise ValueError(f"Antrag {self.uuid} nicht gefunden")

                antrag["status"] = Status.angenommen.value
                perso_db.update_perso(discord_id=str(self.user_id), uuid_str=self.uuid, new_data=antrag)
                
                doc_type = "🚨 Gefälschter Ausweis" if self.is_fake else "✅ Ausweisantrag"
                self.logger.info(f"Antrag {self.uuid} angenommen (Gefälscht: {self.is_fake})")

                fields = [
                    {"name": "Vorname & Nachname", "value": antrag["vollstaendiger_name"], "inline": False},
                    {"name": "Geburtsdatum", "value": antrag["geburtsdatum"], "inline": False},
                    {"name": "Geburtsort / Nationalität", "value": antrag["geburtsort_nationalitaet"], "inline": False},
                    {"name": "Größe", "value": antrag["groesse"], "inline": False},
                    {"name": "Geschlecht", "value": antrag["geschlecht"], "inline": False},
                    {"name": "Typ", "value": "G" if self.is_fake else "O", "inline": False},
                    {"name": "Timestamp", "value": antrag["time"], "inline": False},
                    {"name": "Status", "value": antrag["status"], "inline": False},
                ]

                title_user = f"{'🚨 Gefälschter Ausweis' if self.is_fake else '✅ Ausweisantrag'} angenommen"
                desc_user = f"Dein {'gefälschter ' if self.is_fake else ''}Ausweis wurde genehmigt und kann nun im RP verwendet werden."
                
                await asyncio.gather(
                    send_embed(
                        user_id=self.user_id,
                        title=title_user,
                        description=desc_user,
                        fields=fields,
                        color=discord.Color.orange() if self.is_fake else discord.Color.green()
                    ),
                    send_embed(
                        channel_id=1392541223205605547,
                        title=f"{doc_type} angenommen - {antrag['vollstaendiger_name']}",
                        description=f"Antrag von <@{self.user_id}> wurde genehmigt.",
                        fields=fields,
                        color=discord.Color.orange() if self.is_fake else discord.Color.green()
                    )
                )

                await interaction.followup.send("✅ Antrag erfolgreich angenommen!", ephemeral=True)

                doc_emoji = "🚨" if self.is_fake else "✅"
                send_webhook_log(f"{doc_emoji} <@{interaction.user.id}> hat {'gefälschten ' if self.is_fake else ''}Ausweis von <@{self.user_id}> mit UUID `{self.uuid}` **angenommen**.")

            except Exception as e:
                await interaction.followup.send(
                    "⚠️ Fehler bei der Antragsbearbeitung! Bitte manuell prüfen.",
                    ephemeral=True
                )
                raise

        except Exception as e:
            self.logger.error(f"Kritischer Fehler im Annahme-Prozess: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ Ein schwerwiegender Fehler ist aufgetreten!",
                    ephemeral=True
                )
            except:
                pass
            raise

    @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.danger, emoji="❌", custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            form_fields = ["Ablehnungs Grund"]
            modal = DynamicModal(form_fields, title="Ablehnungsgrund")
            await interaction.response.send_modal(modal)
            self.logger.debug(f"Modal für Ablehnung von Antrag {self.uuid} angezeigt")

            await modal.wait()

            if not modal.data:
                self.logger.warning(f"Modal für Antrag {self.uuid} wurde abgebrochen")
                return

            try:
                message = await interaction.channel.fetch_message(self.id_a)
                await message.delete()
                await interaction.message.delete()
                self.logger.debug(f"Nachricht für Antrag {self.uuid} gelöscht")
            except discord.NotFound:
                self.logger.warning(f"Nachricht für Antrag {self.uuid} bereits gelöscht")
            except Exception as e:
                self.logger.error(f"Fehler beim Löschen der Nachricht: {str(e)}")

            try:
                antrag = perso_db.get_perso_by_uuid(uuid_str=self.uuid)
                if not antrag:
                    raise ValueError(f"Antrag mit UUID {self.uuid} nicht gefunden")

                antrag["status"] = "abgelehnt"

                fields = [
                    {"name": "Vorname & Nachname", "value": antrag["vollstaendiger_name"], "inline": False},
                    {"name": "Geburtsdatum", "value": antrag["geburtsdatum"], "inline": False},
                    {"name": "Geburtsort / Nationalität", "value": antrag["geburtsort_nationalitaet"], "inline": False},
                    {"name": "Größe", "value": antrag["groesse"], "inline": False},
                    {"name": "Geschlecht", "value": antrag["geschlecht"], "inline": False},
                    {"name": "Timestamp", "value": antrag["time"], "inline": False},
                    {"name": "Status", "value": antrag["status"], "inline": False},
                    {"name": "Ablehnungs Grund", "value": modal.data["Ablehnungs Grund"], "inline": False},
                ]

                doc_type_title = "Gefälschter Ausweisantrag" if self.is_fake else "Ausweisantrag"
                
                await send_embed(
                    user_id=self.user_id,
                    title=f"{doc_type_title} wurde abgelehnt",
                    description="Dein Antrag wurde abgelehnt. Du kannst einen neuen Antrag stellen.",
                    fields=fields,
                    color=discord.Color.red(),
                )

                perso_db.delete_perso(discord_id=str(self.user_id), uuid_str=self.uuid)
                self.logger.info(f"Antrag {self.uuid} wurde abgelehnt mit Grund: {modal.data['Ablehnungs Grund']}")

                await interaction.followup.send("Antrag wurde abgelehnt!", ephemeral=True)
                self.logger.info(f"Benachrichtigung an User {self.user_id} gesendet")

                send_webhook_log(f"❌ <@{interaction.user.id}> hat {'gefälschten ' if self.is_fake else ''}Ausweis von <@{self.user_id}> mit UUID `{self.uuid}` **abgelehnt**.")

            except Exception as e:
                await self.handle_error(interaction, e, "Ablehnung des Antrags")
                raise

        except Exception as e:
            await self.handle_error(interaction, e, "Ablehnungs-Prozess")
            raise

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        await self.handle_error(interaction, error, f"Button-Interaktion ({item.label})")


class DocumentTypeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.selected_type = None
        self.logger = logger

    @discord.ui.button(label="Normaler Ausweis", style=discord.ButtonStyle.primary, emoji="📄")
    async def normal_doc(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_type = "normal"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Gefälschter Ausweis", style=discord.ButtonStyle.danger, emoji="🚨")
    async def fake_doc(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_type = "fake"
        await interaction.response.defer()
        self.stop()


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="$", intents=intents)
        self.registered_commands = []
        self.logger = logger
        self._dev_guild = discord.Object(id=1273251270903337000)

    async def _ensure_bot_in_guild(self):
        try:
            guild = await self.fetch_guild(self._dev_guild.id)
            self.logger.info(f"Bot ist auf Server: {guild.name} (ID: {guild.id})")
            return True
        except discord.Forbidden:
            self.logger.error("Bot hat keinen Zugriff auf den Server")
            return False
        except discord.NotFound:
            self.logger.error("Server nicht gefunden - Bot ist nicht auf diesem Server")
            return False

    async def setup_hook(self):
        self.logger.info("Starte Bot-Initialisierung...")

        if not await self._ensure_bot_in_guild():
            self.logger.warning("Sync für Dev-Server wird übersprungen")

        commands_list = list(self.tree.walk_commands())
        self.logger.debug(f"Gefundene Commands: {len(commands_list)}")

        try:
            self.tree.copy_global_to(guild=self._dev_guild)
            synced = await self.tree.sync(guild=self._dev_guild)

            self.logger.info(f"Erfolgreich synchronisiert: {len(synced)} Commands")
            for cmd in synced:
                self.logger.debug(f"-> /{cmd.name} (ID: {cmd.id})")

        except discord.Forbidden as e:
            if e.code == 50001:
                self.logger.error("FEHLER: Bot Invite-Link muss 'applications.commands' Scope enthalten!")
            elif e.code == 50013:
                self.logger.error("FEHLER: Fehlende Berechtigungen auf dem Server!")
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler: {type(e).__name__} - {str(e)}")

    async def on_message(self, message):
        try:
            if message.author == self.user:
                return

            if message.author.id in [949997415027605514, 919586564764479490]:
                await self.process_commands(message)
                self.logger.debug(f"Command von Nutzer {message.author.id} verarbeitet")
            else:
                return
        except Exception as e:
            self.logger.error(f"Fehler in on_message: {str(e)}", exc_info=True)

    async def on_error(self, event, *args, **kwargs):
        self.logger.error(f"Fehler in Event {event}: {str(args[0]) if args else 'Unbekannter Fehler'}", exc_info=True)

    async def on_command_error(self, context, exception):
        self.logger.error(f"Command-Fehler: {str(exception)}", exc_info=True)
        if isinstance(exception, commands.CommandNotFound):
            return
        await context.send(f"⚠️ Ein Fehler ist aufgetreten: {str(exception)}")


bot = MyBot()


@bot.event
async def on_ready():
    bot.logger.info(f'Eingeloggt als {bot.user} (ID: {bot.user.id})')
    bot.logger.info(f'Bot ist bereit auf {len(bot.guilds)} Servern')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="deine Befehle"))


@bot.tree.command(name="ausweis-erstellen", description="Erstelle einen normalen oder gefälschten Personalausweis")
async def create_perso(interaction: discord.Interaction):
    locks = load_locks()
    user_id = str(interaction.user.id)
    now = time.time()
    if user_id in locks and now < locks[user_id]:
        remaining = int((locks[user_id] - now) // 86400)
        embed = discord.Embed(
            title="⛔ Du wurdest gelockt",
            description=f"Verbleibende Zeit: **{remaining}** Tag(e)",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    if interaction.channel_id != 1429029371657846894:
        return await interaction.response.send_message(
            "Dieser Befehl kann nur im <#1429029371657846894> Channel verwendet werden.",
            ephemeral=True
        )
    
    type_view = DocumentTypeSelectView()
    embed = discord.Embed(
        title="Ausweis-Typ wählen",
        description="Wähle aus, welche Art von Ausweis du erstellen möchtest:",
        color=discord.Color.blue()
    )
    embed.add_field(name="📄 Normaler Ausweis", value="Offizieller Personalausweis", inline=False)
    embed.add_field(name="🚨 Gefälschter Ausweis", value="Gefälschter Ausweis (für RP-Zwecke)", inline=False)
    
    await interaction.response.send_message(embed=embed, view=type_view, ephemeral=True)
    await type_view.wait()
    
    if not type_view.selected_type:
        return await interaction.followup.send("❌ Keine Auswahl getroffen.", ephemeral=True)
    
    is_fake = type_view.selected_type == "fake"
    
    # Custom Modal erstellen
    modal_title = "🚨 Gefälschte Ausweisdaten" if is_fake else "📄 Persönliche Daten"
    
    class AusweisModal(discord.ui.Modal):
        def __init__(self, title: str):
            super().__init__(title=title, timeout=300)
            
            warning_text = "⚠️ This form will be submitted to HAM Personalausweis. Do not share passwords or other sensitive information."
            
            self.vorname = discord.ui.TextInput(
                label="Vorname & Nachname",
                placeholder="Max Mustermann",
                required=True,
                style=discord.TextStyle.short
            )
            self.geburtsdatum = discord.ui.TextInput(
                label="Geburtsdatum",
                placeholder="01.01.2000",
                required=True,
                style=discord.TextStyle.short
            )
            self.geburtsort = discord.ui.TextInput(
                label="Geburtsort / Nationalität",
                placeholder="Berlin / Deutsch",
                required=True,
                style=discord.TextStyle.short
            )
            self.groesse = discord.ui.TextInput(
                label="Größe",
                placeholder="180cm",
                required=True,
                style=discord.TextStyle.short
            )
            self.geschlecht = discord.ui.TextInput(
                label="Geschlecht",
                placeholder="Männlich / Weiblich",
                required=True,
                style=discord.TextStyle.short
            )
            
            self.add_item(self.vorname)
            self.add_item(self.geburtsdatum)
            self.add_item(self.geburtsort)
            self.add_item(self.groesse)
            self.add_item(self.geschlecht)
            
            self.data = {}
            self.discord_userid = None
            
        async def on_submit(self, inter: discord.Interaction):
            self.data = {
                "Vorname & Nachname": self.vorname.value,
                "Geburtsdatum": self.geburtsdatum.value,
                "Geburtsort / Nationalität": self.geburtsort.value,
                "Größe": self.groesse.value,
                "Geschlecht": self.geschlecht.value
            }
            self.discord_userid = inter.user.id
            await inter.response.defer()
            self.stop()
    
    modal = AusweisModal(title=modal_title)
    
    # Button View für Modal-Öffnung
    class OpenModalButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            
        @discord.ui.button(label="Formular öffnen", style=discord.ButtonStyle.primary, emoji="📝")
        async def open_modal(self, inter: discord.Interaction, button: discord.ui.Button):
            await inter.response.send_modal(modal)
            self.stop()
    
    view = OpenModalButton()
    await interaction.followup.send("Klicke auf den Button, um das Formular zu öffnen:", view=view, ephemeral=True)
    await modal.wait()

    discord_userid = str(modal.discord_userid)
    data = modal.data

    count = perso_db.count_persos(discord_id=discord_userid)
    if count >= 2:
        await send_embed(
            interaction=interaction,
            title="Ungültige Anfrage",
            description="Du hast schon 2 Ausweise erstellt\nLösche erst einen bevor du wieder einen erstellen kannst!",
            color=discord.Color.red(),
            ephemeral=True
        )
    else:
        perso = Person(
            vollstaendiger_name=data["Vorname & Nachname"],
            geburtsdatum=data["Geburtsdatum"],
            geburtsort_nationalitaet=data["Geburtsort / Nationalität"],
            groesse=data["Größe"],
            geschlecht=data["Geschlecht"],
            status=Status.ausstehend.value,
        )
        
        # Typ hinzufügen (falls Person-Klasse das unterstützt)
        if hasattr(perso, 'typ'):
            perso.typ = "G" if is_fake else "O"

        uuid = perso_db.add_perso(discord_id=discord_userid, person=perso)

        fields = [
            {"name": "Vorname & Nachname", "value": data["Vorname & Nachname"], "inline": False},
            {"name": "Geburtsdatum", "value": data["Geburtsdatum"], "inline": False},
            {"name": "Geburtsort / Nationalität", "value": data["Geburtsort / Nationalität"], "inline": False},
            {"name": "Größe", "value": data["Größe"], "inline": False},
            {"name": "Geschlecht", "value": data["Geschlecht"], "inline": False},
            {"name": "Typ", "value": "G" if is_fake else "O", "inline": False},
        ]

        doc_type = "🚨 Gefälschter Ausweis" if is_fake else "📄 Ausweis"
        
        await send_embed(
            interaction=interaction,
            title="Anfrage Bestätigt und weitergeleitet",
            description=f"Dein {'gefälschter ' if is_fake else ''}Ausweis wurde zur Prüfung eingereicht!\nDu wirst benachrichtigt, sobald er angenommen oder abgelehnt wurde.",
            color=discord.Color.orange() if is_fake else discord.Color.green(),
            ephemeral=True
        )

        usr = interaction.user

        a = await bot.get_channel(1392541330265083987).send('<@1400148859988213791>')
        a = a.id
        view = ApprovalButtons(user_id=int(discord_userid), uuid=uuid, a=a, is_fake=is_fake)

        await send_embed(
            channel_id=1392541330265083987,
            author_name=usr.name,
            author_icon=usr.display_avatar.url,
            title=f"{doc_type} - Neuer Antrag",
            description=f"{'🚨 GEFÄLSCHTER AUSWEIS - ' if is_fake else ''}Ein neuer Ausweisantrag wartet auf Genehmigung.",
            fields=fields,
            color=discord.Color.orange() if is_fake else discord.Color.blue(),
            footer_text=f"Antrag von [{usr.display_name}] > [{discord_userid}]",
            view=view
        )


@bot.tree.command(name="ausweis-löschen", description="Lösche einen deiner Ausweise")
async def delete_perso(interaction: discord.Interaction):
    if interaction.channel_id != 1429029371657846894:
        await interaction.response.send_message(
            "Dieser Befehl kann nur im <#1429029371657846894> Channel verwendet werden.", 
            ephemeral=True
        )
        return
    user = interaction.user
    user_id = user.id
    personen = perso_db.get_persos_by_discordid(discord_id=str(user_id))

    if not personen:
        return await interaction.response.send_message(
            "Du hast keine Ausweise zum Löschen",
            ephemeral=True
        )

    options = [
        discord.SelectOption(
            label=f'Ausweis {perso.get("nick", idx+1)}',
            value=str(perso["uuid"]),
            description=f'Erstellt am {perso.get("time", "Unbekannt")}'
        )
        for idx, perso in enumerate(personen[:25])
    ]

    view = DropdownView(options)
    await interaction.response.send_message(
        "Wähle einen Ausweis zum Löschen:",
        view=view,
        ephemeral=True
    )
    await view.wait()

    if view.selected_value:
        perso_db.delete_perso(uuid_str=str(view.selected_value), discord_id=str(user_id))
        await interaction.followup.send(
            "✅ Ausweis wurde gelöscht",
            ephemeral=True
        )


@bot.tree.command(name="ausweis-ansehen", description="Zeige einen Ausweis an (eigenen oder von anderen)")
@app_commands.describe(user="Der User, dessen Ausweis angezeigt werden soll")
async def show_perso(interaction: discord.Interaction, user: discord.Member):
    try:
        if interaction.channel_id != 1429029510891835514:
            await interaction.response.send_message(
                "Dieser Befehl kann nur im <#1429029510891835514> Channel verwendet werden.", 
                ephemeral=True
            )
            return

        member_user_id = user.id
        requester_id = interaction.user.id
        personen = perso_db.get_persos_by_discordid(discord_id=str(member_user_id))

        if not personen:
            return await interaction.response.send_message(
                "Die Person hat keinen Ausweis",
                ephemeral=True
            )

        options = [
            discord.SelectOption(
                label=f"Ausweis #{idx + 1} - {perso.get('nick', 'Unbekannt')}",
                value=str(perso['uuid']),
                description=f"Erstellt am {perso.get('time', 'Unbekannt')}"
            )
            for idx, perso in enumerate(personen[:25])
        ]

        embed = discord.Embed(
            title=f"Ausweise von {user.display_name}",
            description="Wähle einen Ausweis zur Anzeige:",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Insgesamt {len(personen)} Ausweise")

        view = DropdownView(options)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        await view.wait()

        if not view.selected_value:
            return

        selected_perso = next(p for p in personen if str(p['uuid']) == view.selected_value)

        if member_user_id != requester_id:
            confirmation_embed = discord.Embed(
                title="Freigabe erforderlich",
                description=f"{user.mention}, möchtest du diesen Ausweis freigeben?",
                color=discord.Color.orange()
            )

            confirmation_embed.add_field(
                name="Ausweisinformationen",
                value=f"**Name:** {selected_perso.get('vollstaendiger_name', 'N/A')}\n"
                      f"**Erstellt am:** {selected_perso.get('time', 'N/A')}",
                inline=False
            )

            confirmation_embed.set_footer(text=f"Angefragt von {interaction.user.display_name}")

            class ConfirmationView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60.0)
                    self.confirmed = None

                @discord.ui.button(label="Freigeben", style=discord.ButtonStyle.green)
                async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
                    self.confirmed = True
                    await inter.response.defer()
                    await inter.message.delete()
                    self.stop()

                @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.red)
                async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
                    self.confirmed = False
                    await inter.message.delete()
                    await inter.followup.send(
                        "Freigabe wurde abgelehnt.",
                        ephemeral=True
                    )
                    self.stop()

            confirmation_view = ConfirmationView()
            await user.send(embed=confirmation_embed, view=confirmation_view)

            await confirmation_view.wait()

            if not confirmation_view.confirmed:
                await interaction.followup.send(
                    f"{user.display_name} hat die Freigabe des Ausweises abgelehnt.",
                    ephemeral=True
                )
                return

        detail_embed = discord.Embed(
            title=f"Ausweis von {user.display_name}",
            color=discord.Color.green()
        )
        detail_embed.set_thumbnail(url=user.display_avatar.url)

        fields = [
            ("Vollständiger Name", selected_perso.get("vollstaendiger_name", "N/A"), False),
            ("Geburtsdatum", selected_perso.get("geburtsdatum", "N/A"), True),
            ("Geburtsort", selected_perso.get("geburtsort_nationalitaet", "N/A"), True),
            ("Größe", selected_perso.get("groesse", "N/A"), True),
            ("Geschlecht", selected_perso.get("geschlecht", "N/A"), True),
            ("Typ", selected_perso.get("typ", "O"), True),
            ("Erstellt am", selected_perso.get("time", "N/A"), False)
        ]

        for name, value, inline in fields:
            detail_embed.add_field(name=name, value=value, inline=inline)

        if member_user_id != requester_id:
            detail_embed.set_footer(text=f"Freigegeben von {user.display_name}")

        try:
            await interaction.edit_original_response(
                embed=detail_embed,
                view=None
            )
        except discord.NotFound:
            await interaction.followup.send(
                embed=detail_embed,
                ephemeral=True
            )

    except Exception as e:
        logger.error(f"Fehler in show-perso: {e}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Ein Fehler ist aufgetreten beim Anzeigen des Ausweises",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Ein Fehler ist aufgetreten beim Anzeigen des Ausweises",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Fehler beim Senden der Fehlermeldung: {e}", exc_info=True)


@bot.command()
async def userdata(ctx, *, params: str):
    try:
        allowed_users = {949997415027605514, 919586564764479490, 1400148859988213791}

        if ctx.author.id not in allowed_users:
            return

        args = {}
        for pair in params.split():
            if '=' not in pair:
                continue
            key, value = pair.split('=', 1)
            args[key.lower()] = value.strip()

        if 'id' not in args:
            raise ValueError("ID ist erforderlich (Verwendung: !userdata id=123456789)")

        user_id = args["id"]
        user_data = perso_db.get_persos_by_discordid(discord_id=user_id)

        if not user_data:
            return await ctx.send(f"Keine Daten für ID {user_id} gefunden")

        formatted_data = json.dumps(
            user_data,
            indent=2,
            ensure_ascii=False,
            default=str
        )
        if len(formatted_data) <= 2000:
            await ctx.send(f"```json\n{formatted_data}\n```")
        else:
            parts = [formatted_data[i:i + 2000] for i in range(0, len(formatted_data), 2000)]
            for part in parts:
                await ctx.send(f"```json\n{part}\n```")

    except ValueError as e:
        await ctx.send(f"⚠️ {str(e)}")
    except json.JSONDecodeError:
        await ctx.send("⚠️ Fehler beim Formatieren der Daten")
    except Exception as e:
        await ctx.send(f"❌ Unerwarteter Fehler: {str(e)}")


@bot.command(name='stop')
async def stop(ctx):
    try:
        allowed_users = {949997415027605514, 919586564764479490}

        if ctx.author.id not in allowed_users:
            return

        confirm_msg = await ctx.send(
            "⚠️ **WARNUNG: Bot wird gestoppt!**\n"
            "Reagiere mit ✅ innerhalb von 30 Sekunden zum Bestätigen."
        )
        await confirm_msg.add_reaction("✅")

        def check(reaction, user):
            return (
                    user == ctx.author
                    and str(reaction.emoji) == '✅'
                    and reaction.message.id == confirm_msg.id
            )

        try:
            await bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("Stop abgebrochen (Timeout)")

        print(f"Bot wird gestoppt von {ctx.author} (ID: {ctx.author.id})")
        await ctx.send("⏹️ Bot wird gestoppt...")
        await bot.close()
        sys.exit(0)

    except Exception as e:
        await ctx.send(f"❌ Fehler beim Stoppen: {str(e)}")
        print(f"Stop-Fehler: {e}")


@bot.command(name="get-channel")
async def get_channel(ctx, *, args=None):
    try:
        allowed_users = {949997415027605514, 919586564764479490}
        if ctx.author.id not in allowed_users:
            return await ctx.send("❌ Keine Berechtigung.")

        params = dict(a.split("=", 1) for a in (args or "").split() if "=" in a)
        guild_id = int(params.get("guild"))
        source_ch_id = int(params.get("id"))
        mirror = str(params.get("mirror", "false")).lower() in {"1", "true", "yes", "y"}
        target_ch_id = int(params["target"]) if "target" in params else None

        guild = bot.get_guild(guild_id)
        if not guild:
            return await ctx.send(f"❌ Guild {guild_id} nicht gefunden.")
        source_ch = guild.get_channel(source_ch_id)
        if not source_ch or not isinstance(source_ch, (discord.TextChannel, discord.Thread)):
            return await ctx.send(f"❌ Channel {source_ch_id} nicht gefunden/kein Textkanal.")

        target_ch = None
        if mirror:
            target_ch = (guild.get_channel(target_ch_id) if target_ch_id
                         else ctx.channel)
            if not target_ch:
                return await ctx.send("❌ Ziel-Channel ungültig.")

        collected = []
        async for msg in source_ch.history(limit=None, oldest_first=True):
            if not msg.embeds:
                continue
            for emb in msg.embeds:
                try:
                    emb_dict = emb.to_dict()
                except Exception:
                    emb_dict = {
                        "title": emb.title, 
                        "description": emb.description,
                        "url": emb.url, 
                        "color": emb.color.value if emb.color else None,
                        "timestamp": str(emb.timestamp) if emb.timestamp else None
                    }
                collected.append({
                    "message_id": msg.id,
                    "created_at": msg.created_at.isoformat(),
                    "author_id": msg.author.id,
                    "author_tag": str(msg.author),
                    "embed": emb_dict,
                })

        if not collected:
            return await ctx.send("📭 Keine Embeds gefunden.")

        if mirror:
            await ctx.send(f"🔁 Starte Spiegelung von {len(collected)} Embed(s) → {target_ch.mention} …")
            for i, item in enumerate(collected, 1):
                try:
                    e = discord.Embed.from_dict(item["embed"])
                    await target_ch.send(embed=e)
                except Exception as ex:
                    await asyncio.sleep(1)
                    await target_ch.send(f"⚠️ Embed #{i} konnte nicht gespiegelt werden: `{ex}`")
                if i % 5 == 0:
                    await asyncio.sleep(1.2)
            return await ctx.send("✅ Spiegelung abgeschlossen.")

        buf = io.BytesIO()
        buf.write(json.dumps(collected, ensure_ascii=False, indent=2).encode("utf-8"))
        buf.seek(0)
        fname = f"embeds_g{guild_id}_c{source_ch_id}.json"
        await ctx.send(
            content=f"✅ {len(collected)} Embed(s) exportiert.",
            file=discord.File(buf, filename=fname)
        )

    except Exception as e:
        await ctx.send(f"❌ Fehler: {e}")


@bot.command()
async def dellperso(ctx, *, params: str):
    try:
        allowed_users = {949997415027605514, 919586564764479490, 1400148859988213791}

        if ctx.author.id not in allowed_users:
            return

        args = {}
        for pair in params.split():
            if '=' not in pair:
                continue
            key, value = pair.split('=', 1)
            args[key.lower()] = value.strip()

        if 'uuid' not in args:
            raise ValueError("UUID ist erforderlich (Verwendung: !dellperso uuid=12345678 id=USERID)")
        if 'id' not in args:
            raise ValueError("User-ID ist erforderlich (Verwendung: !dellperso uuid=12345678 id=USERID)")

        deleted_data = perso_db.delete_perso(
            discord_id=args["id"],
            uuid_str=args["uuid"]
        )

        if not deleted_data:
            return await ctx.send(f"❌ Kein Ausweis mit UUID {args['uuid']} für User {args['id']} gefunden")

        embed = discord.Embed(
            title="✅ Ausweis gelöscht",
            description="Folgender Ausweis wurde entfernt:",
            color=discord.Color.green()
        )

        embed.add_field(name="UUID", value=args["uuid"], inline=False)
        embed.add_field(name="User-ID", value=args["id"], inline=False)

        await ctx.send(embed=embed)

    except ValueError as e:
        await ctx.send(f"⚠️ Fehler: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Kritischer Fehler: {str(e)}")
        print(f"Fehler in dellperso: {e}")


@bot.tree.command(name="report", description="Sende einen Bugreport an das Dev-Team")
@app_commands.describe(message="Beschreibe den Bug oder das Problem")
async def report_bug(interaction: discord.Interaction, message: str):
    username = interaction.user.name
    webhook_url = "https://maker.ifttt.com/trigger/bugreport/with/key/jn0D3A447nffQoxXu4C6AkeklimS3o1wgqh-4kYfWz-"

    payload = {
        "value1": username,
        "value2": message
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if response.status == 200:
                await interaction.response.send_message(
                    "✅ Bugreport erfolgreich gesendet.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Fehler beim Senden des Bugreports.", ephemeral=True)


if __name__ == "__main__":
    print("Starte Bot...")
    bot.run("")