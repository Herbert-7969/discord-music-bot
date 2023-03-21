import os
import discord
import spotipy
import spotipy.util as util
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice

# Set up the environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up the Spotify API client
scope = ["user-read-playback-state", "user-modify-playback-state"]
token = util.prompt_for_user_token(os.getenv("SPOTIPY_USERNAME"), scope,
                                   client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                                   client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                                   redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"))
sp = spotipy.Spotify(auth=token)

# Set up the Discord client and slash commands
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)

# Global variables
QUEUE = []
PLAYING = False
PAUSED = False

# Helper functions
def add_to_queue(track):
    QUEUE.append(track)

def skip():
    global PLAYING
    global QUEUE
    if len(QUEUE) > 0:
        track = QUEUE.pop(0)
        play(track)
    else:
        PLAYING = False
        sp.pause_playback()

def play(track):
    global PLAYING
    global PAUSED
    if not PLAYING:
        PLAYING = True
        PAUSED = False
        sp.start_playback(uris=[track['uri']])
    else:
        PAUSED = False
        sp.add_to_queue(track['uri'])

def pause():
    global PAUSED
    if not PAUSED:
        PAUSED = True
        sp.pause_playback()

def resume():
    global PAUSED
    if PAUSED:
        PAUSED = False
        sp.start_playback()

# Command functions
@slash.slash(name="play", description="Play a track on Spotify",
             options=[
                 create_option(
                     name="query",
                     description="The search query to look up on Spotify",
                     option_type=3,
                     required=True
                 )
             ])
async def play_track(ctx, query):
    global QUEUE
    results = sp.search(q=query, type='track', limit=1)
    track = results['tracks']['items'][0]
    add_to_queue(track)
    if not PLAYING:
        play(track)
    else:
        await ctx.send(f"Added {track['name']} to the queue.")

@slash.slash(name="queue", description="View the current queue")
async def view_queue(ctx):
    global QUEUE
    if len(QUEUE) == 0:
        await ctx.send("The queue is currently empty.")
    else:
        message = "Current queue:\n"
        for i, track in enumerate(QUEUE):
            message += f"{i+1}. {track['name']} by {track['artists'][0]['name']}\n"
        await ctx.send(message)

@slash.slash(name="skip", description="Skip the currently playing track")
async def skip_track(ctx):
    global PLAYING
    global QUEUE
    if not PLAYING:
        await ctx.send("There is nothing playing to skip.")
    else:
        skip()
        await ctx.send("Skipping to the next track in the queue.")

@slash.slash(name="stop", description="Stop the music and clear the queue")
async def stop_music(ctx):
    global PLAYING
    global QUEUE
    PLAYING = False
    QUEUE = []
    sp.pause_playback()
    await ctx.send("Music stopped and queue cleared.")

@slash.slash(name="pause", description="Pause the currently playing song")
async def pause(ctx: SlashContext):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("Song paused!")
    else:
        await ctx.send("No song is playing right now.")

@slash.slash(name="resume", description="Resume the currently paused song")
async def resume(ctx: SlashContext):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("Song resumed!")
    else:
        await ctx.send("The song is not paused or playing right now.")

@slash.slash(name="skip", description="Skip the currently playing song")
async def skip(ctx: SlashContext):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("Song skipped!")
    else:
        await ctx.send("No song is playing right now.")

@slash.slash(name="queue", description="View the current song queue")
async def queue(ctx: SlashContext):
    queue_list = ""
    for index, song in enumerate(queue):
        queue_list += f"{index + 1}. {song['title']} ({song['duration']})\n"
    if queue_list:
        embed = discord.Embed(title="Song Queue", description=queue_list, color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        await ctx.send("The song queue is empty.")

@slash.slash(name="help", description="Get a list of available commands")
async def help(ctx: SlashContext):
    help_message = """
    **Available Commands**
    /play [song name] - Play a song from Spotify
    /stop - Stop the currently playing song
    /pause - Pause the currently playing song
    /resume - Resume the currently paused song
    /skip - Skip the currently playing song
    /queue - View the current song queue
    /help - Get a list of available commands
    """
    embed = discord.Embed(title="Music Bot Help", description=help_message, color=discord.Color.green())
    await ctx.send(embed=embed)

# Run the Discord client
client.run(TOKEN)

