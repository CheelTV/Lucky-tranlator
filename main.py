import os
import discord
from discord.ext import commands
from google.cloud import translate_v2 as translate

# --- Configuration de l'API Google Cloud ---
# Assurez-vous que la variable d'environnement GOOGLE_APPLICATION_CREDENTIALS est définie.
translate_client = translate.Client()

# --- Configuration du bot Discord ---
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN') 

if DISCORD_BOT_TOKEN is None:
    print("ERREUR: Le token du bot Discord n'a pas été trouvé dans les variables d'environnement.")
    print("Veuillez définir la variable d'environnement 'DISCORD_BOT_TOKEN' avant de lancer le bot.")
    print("Exemple (Linux/macOS): export DISCORD_BOT_TOKEN='VOTRE_TOKEN_ICI'")
    print("Exemple (Windows CMD): set DISCORD_BOT_TOKEN='VOTRE_TOKEN_ICI'")
    exit(1)

DEFAULT_TARGET_LANGUAGE = 'en'

FLAG_LANGUAGE_MAP = {
    '🇫🇷': 'fr',
    '🇬🇧': 'en',
    '🇺🇸': 'en',
    '🇪🇸': 'es',
    '🇩🇪': 'de',
    '🇮🇹': 'it',
    '🇯🇵': 'ja',
    '🇨🇳': 'zh',
    '🇰🇷': 'ko',
    '🇷🇺': 'ru',
    '🇧🇷': 'pt',
    '🇵🇹': 'pt',
    '🇸🇦': 'ar',
    '🇮🇳': 'hi',
    # Ajoutez d'autres drapeaux si vous le souhaitez
}

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user.name} ({bot.user.id})')
    print('------')

# --- Fonction utilitaire pour envoyer un Embed de traduction ---
async def send_translation_embed(channel, original_text, translated_text, target_language, detected_source_language=None, requested_by=None):
    """Crée et envoie un Embed Discord avec la traduction."""
    embed = discord.Embed(
        title="🌍 Traduction",
        description=f"**Langue Cible :** `{target_language.upper()}`",
        color=discord.Color.blue() # Une couleur sympa pour l'embed
    )

    if requested_by:
        embed.set_author(name=f"Demandé par {requested_by.display_name}", icon_url=requested_by.avatar.url if requested_by.avatar else requested_by.default_avatar_url)

    embed.add_field(name="Texte Original", value=f"```\n{original_text}\n```", inline=False)
    
    # Si la langue source est détectée et différente de la cible, on l'affiche
    if detected_source_language and detected_source_language.lower() != target_language.lower():
        embed.add_field(name=f"Traduit de `{detected_source_language.upper()}`", value=f"```\n{translated_text}\n```", inline=False)
    else:
        embed.add_field(name="Texte Traduit", value=f"```\n{translated_text}\n```", inline=False)
    
    embed.set_footer(text="Propulsé par Google Cloud Translation")
    embed.timestamp = discord.utils.utcnow() # Ajoute l'heure actuelle de la traduction

    await channel.send(embed=embed)


@bot.command(name='translate', help='Traduit le texte donné dans la langue spécifiée. Utilisation: !translate [langue] <texte>')
async def translate_command(ctx, *args):
    """
    Traduit le texte fourni via une commande.
    """
    if not args:
        await ctx.send(f"Veuillez fournir du texte à traduire. Utilisation: `!translate [langue] <texte>`")
        return

    target_language = DEFAULT_TARGET_LANGUAGE
    text_to_translate_parts = []
    
    if len(args[0]) == 2 and args[0].isalpha():
        target_language = args[0].lower()
        text_to_translate_parts = args[1:]
    else:
        text_to_translate_parts = args
    
    text_to_translate = " ".join(text_to_translate_parts)

    if not text_to_translate:
        await ctx.send(f"Veuillez fournir du texte à traduire. Utilisation: `!translate [langue] <texte>`")
        return

    try:
        result = translate_client.translate(text_to_translate, target_language=target_language)
        translated_text = result['translatedText']
        detected_source_language = result.get('detectedSourceLanguage')

        await send_translation_embed(
            ctx.channel,
            text_to_translate,
            translated_text,
            target_language,
            detected_source_language,
            ctx.author # L'auteur de la commande
        )

    except Exception as e:
        print(f"Erreur de traduction via commande: {e}")
        await ctx.send(f"Désolé, une erreur est survenue lors de la traduction.")


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if str(reaction.emoji) in FLAG_LANGUAGE_MAP:
        target_language = FLAG_LANGUAGE_MAP[str(reaction.emoji)]
        original_message = reaction.message
        text_to_translate = original_message.content

        if not text_to_translate or text_to_translate.startswith('!translate'):
            return

        if len(text_to_translate) > 1000:
            await original_message.channel.send("Désolé, le message est trop long pour être traduit par réaction.")
            return

        try:
            print(f"Tentative de traduction par réaction de '{text_to_translate}' vers {target_language}")
            result = translate_client.translate(text_to_translate, target_language=target_language)
            translated_text = result['translatedText']
            detected_source_language = result.get('detectedSourceLanguage')
            
            await send_translation_embed(
                original_message.channel,
                text_to_translate,
                translated_text,
                target_language,
                detected_source_language,
                user # L'utilisateur qui a ajouté la réaction
            )

        except Exception as e:
            print(f"Erreur de traduction par réaction: {e}")
            await original_message.channel.send(f"{user.mention}, désolé, une erreur est survenue lors de la traduction.")


bot.run(DISCORD_BOT_TOKEN)