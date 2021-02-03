import discord
import time
import sys
import os
import asyncio
from logo import gblogo
from discord.ext import commands
from json_abs import *


# CONSTANTS
CHAR_SUCCESS = "✅"
CHAR_FAILED = "❌"
FILE_SECRET = 'secret.txt'
FILE_WRITETOFILES = 'writetofiles.txt'
FILE_CONFIG = 'config.json'
DISCORD_PREFIX = ';;'


# UTILITY

def corePYIPath(relative_path):
	""" Fixes PyInstaller file issues. """
	try:
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

def readLinesTXT(filename: str) -> list:
	""" Reads lines from a TXT file. """
	# RETURNS: list<str>
	f = open(filename, 'r')
	lines = [line.replace('\n','') for line in f.readlines() if not line.startswith('#') and len(line)>2]
	f.close()
	return lines

def writeLinesTXT(filename: str, data):
	""" Overwrites lines to a TXT file. """
	use_data = data
	if isinstance(use_data, list):
		use_data = ''.join([d + '\n' for d in use_data])
	f = open(filename, 'w')
	f.truncate()
	f.write(use_data)
	f.close()

def formatFilepath(filepath: str) -> str:
	""" Condenses filepath and removes PC username. """
	# RETURNS: str
	path = filepath
	if '/users/' in path.lower():
		repstr = ''
		u_index = 0
		for i in range(0, len(path)):
			if i+7 < len(path):
				if path[i:i+7].lower() == '/users/':
					u_index = i+7
					break
		spliced = path[u_index:]
		spliced = 'NAME' + spliced[spliced.index('/'):]
		repstr = path[:u_index] + spliced
		path = repstr
	if len(path) > 10:
		path = "..." + path[len(path) - 10:]
	return path

def falseInsteadExceptionInt(chk: str) -> bool:
	""" Checks if a string can be converted to an integer. 
		Purposed for exception handling on list comprehension. """
	# RETURNS: bool
	try:
		int(chk)
		return True
	except ValueError:
		return False
	return True

def updateStrNumbers(data: str, sign: str, value: int) -> str:
	""" Changes the values of all numbers in the input string. """
	# PARAMS: sign (str) ['+', '-']
	# RETURNS: str
	if not value or not data:
		return data
	replaces = []
	rep_str = ''
	read_num = False
	for c in data:
		if read_num:
			if falseInsteadExceptionInt(c):
				rep_str += c
			else:
				read_num = False
				rep_int = int(rep_str)
				if sign == '+':
					rep_int += value
				elif sign == '-':
					rep_int -= value
				replaces.append(str(rep_int))
				rep_str = c
		else:
			if not falseInsteadExceptionInt(c):
				rep_str += c
			else:
				read_num = True
				replaces.append(rep_str)
				rep_str = str(c)
	if falseInsteadExceptionInt(rep_str):
		rep_int = int(rep_str)
		if sign == '+':
			rep_int += value
		elif sign == '-':
			rep_int -= value
		rep_str = rep_int
	replaces.append(str(rep_str))
	return "".join(replaces)

def pDiscordAdmin(ctx: commands.Context) -> bool:
	""" Returns True if Discord command user has Administrative privileges 
		in the server this command was executed. """
	# RETURNS: bool
	for member in ctx.guild.members:
		if str(member.id) == str(ctx.author.id):
			for role in member.roles:
				if role.permissions.administrator:
					return True
	return False

async def response(message: discord.Message, react: str, static="", dynamic=""):
	""" Discord Bot responses. """
	r = {
		'SUCCESS': CHAR_SUCCESS,
		'FAILED': CHAR_FAILED
	}
	s = {
		'PERM_ADMIN': "You are not an Administrator of this server!",
		'PERM': "You do not have access to this command!"
	}
	msg = await message.channel.send("**" + message.author.name + "**, " + (dynamic or s[static]))
	await message.add_reaction(r[react])
	return msg


# GLOBALS
intents = discord.Intents.default()
intents.members = True
bot_prefix = DISCORD_PREFIX
client = commands.Bot(command_prefix=bot_prefix, intents=intents)
client.remove_command("help")
secret = readLinesTXT(FILE_SECRET)
secret = secret[0]
write_files = readLinesTXT(FILE_WRITETOFILES)
configs = j_read(FILE_CONFIG)
numchoices = []


# DISCORD
@client.event
async def on_ready():
	print("[discord] Connecting...")
	await client.wait_until_ready()
	print("[discord] Bot ONLINE.")
	print("[discord] Name=" + client.user.name + ", ID=" + str(client.user.id))

@client.command(pass_context=True)
async def newcounter(ctx, name):
	global numchoices
	""" Registers a TXT file as a counter. """
	# SCOPE: Admins
	if pDiscordAdmin(ctx): # User is Admin
		if name: # Input 'name' string is valid
			if name not in configs['counters']: # Input 'name' not already a Counter
				if write_files: # There exists at least 1 writetofile
					resp = 'Adding new Counter `' + name + '`...\n'
					resp += 'Which **file(s)** will this Counter interact with?\n'
					resp += 'Choose the file number. If multiple files, seperate numbers with commas.\n'
					resp += '*Example Usage*: \'select 1, 5, 6\'\n'
					f_choice = 1
					choices = []
					for wf in write_files:
						choices.append({'id': f_choice, 'path': wf})
						f_choice += 1
					for ch in choices:
						resp += '[' + str(ch['id']) + '] `' + formatFilepath(ch['path']) + '`\n'
					aresp = await response(message=ctx.message, react='SUCCESS', dynamic=resp)
					numchoices = []
					def check(message):
						global numchoices
						numchoices = message.content.replace('select ','').split(',')
						numchoices = [int(ch) for ch in numchoices if falseInsteadExceptionInt(ch)]
						check1 = message.content.startswith('select')
						check2 = message.author.id == ctx.author.id
						check3 = any(num for num in numchoices if num in list(range(1,f_choice+1)))
						return check1 and check2 and check3
					message = None
					try:
						message = await client.wait_for('message', timeout=30.0, check=check)
					except asyncio.TimeoutError:
						await aresp.edit(content='User timed out.')
					else:
						selections = [{'id': sl['id'], 'path': sl['path']} for sl in choices if sl['id'] in numchoices]
						if selections: # There exists at least 1 valid choice
							configs['counters'].append({'name': name, 'files': [sel['path'] for sel in selections]})
							j_overwrite(FILE_CONFIG, configs)
							resp = 'Counter set!\n'
							resp += 'Name: `' + name + '`\n'
							resp += 'Files to Write to: \n' + ''.join(['`' + formatFilepath(wf['path']) + '`\n' for wf in selections])
							resp += 'Make sure your TXT files include a number!\n'
							await response(message=message, react='SUCCESS', dynamic=resp)
						else:
							await response(message=message, react='FAILED', dynamic='Invalid selection!')
				else:
					await response(message=ctx.message, react='FAILED', dynamic='No files specificed to write to! Add some in *writetofiles.txt*!')
			else:
				await response(message=ctx.message, react='FAILED', dynamic='Counter `' + name + "` already exists!")
		else:
			await response(message=ctx.message, react='FAILED', dynamic='Invalid Counter name!')
	else:
		await response(message=ctx.message, react='FAILED', static='PERM_ADMIN')

@client.command(pass_context=True)
async def change(ctx, name, pmvalue):
	""" Updates a Counter value. """
	# PARAMS: pmvalue (str) [Example: '+5', '-1']
	# SCOPE: Anyone
	if name in [cf['name'] for cf in configs['counters']]: # Counter exists
		allowed = ['+', '-']
		if len(pmvalue) >= 2: # Valid pmvalue
			if pmvalue[0] in allowed and falseInsteadExceptionInt(pmvalue[1:]): # Valid pmvalue
				cnt = 0
				for wf in configs['counters']:
					if wf['name'] == name:
						for fl in wf['files']:
							data = readLinesTXT(fl)
							changed = [updateStrNumbers(line, pmvalue[0], int(pmvalue[1:])) for line in data]
							writeLinesTXT(fl, changed)
							cnt += 1
				await response(message=ctx.message, react='SUCCESS', dynamic='Updated `' + pmvalue + '` for *' + \
					str(cnt) + '* files.')
			else:
				await response(message=ctx.message, react='FAILED', dynamic='Invalid value change!')
		else:
			await response(message=ctx.message, react='FAILED', dynamic='Invalid value change!')
	else:
		await response(message=ctx.message, react='FAILED', dynamic='Invalid Counter name!')
	


# MAIN
def mainLong():
	print(gblogo())

	print("OBS DISCORD COUNTER")
	print("BY GUNNERBONES")
	print("="*60)

	print(">>>>WELCOME>>>>")
	print("This Discord Bot takes in user input from Discord to update")
	print("counters stored in TXT files connected to OBS locally.")
	print("This Bot is meant to be run with OBS, OBS Studio, or SLOBS.")
	print()

	print(">>>>SETUP>>>>")
	print("Checking writetofiles.txt...")
	if write_files:
		print("Found %s files!", len(write_files))
		time.sleep(1)
		print("Checking secret.txt...")
		if secret:
			print("Secret found.")
			time.sleep(1)
			print()

			print(">>>>USAGE>>>>")
			print(";;newcounter (name) - Create a Counter that links to TXT files.")
			print(";;change (name) (+/-value) - Increment/Decrement a Counter and all associated TXT files.")
			print()

			print(">>>>READY?>>>>")
			print("Type something to proceed.")
			inp = input(": ")
			if not inp:
				sys.exit()
		else:
			print("No Bot secret found in secret.txt! Exiting in 5s.")
			time.sleep(5)
			sys.exit()
	else:
		print("No files listed! Specify paths in writetofiles.txt.")
		print("Exiting in 5s...")
		time.sleep(5)
		sys.exit()
	try:
		client.run(secret)
	except discord.errors.LoginFailure:
		print("[ERROR] Invalid Bot secret! Exiting in 5s.")
		time.sleep(5)
		sys.exit()

def mainShort():
	print(gblogo())

	print("\tOBS DISCORD COUNTER")
	print("\tBY GUNNERBONES")
	print("="*60)
	if not write_files:
		print("[ERROR] No files listed! Specify paths in writetofiles.txt.")
		print("Exiting in 5s...")
		time.sleep(5)
		sys.exit()
	try:
		client.run(secret)
	except discord.errors.LoginFailure:
		print("[ERROR] Invalid Bot secret! Exiting in 5s.")
		time.sleep(5)
		sys.exit()


if __name__ == "__main__":
	mainShort()
