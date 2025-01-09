import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import json

class DiscordBotMaker(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.commands = []
        self.events = []
        self.advanced_commands = []  # Store advanced commands separately
        self.language = tk.StringVar(value="python")  # Default language
        self.create_widgets()

    def create_widgets(self):
        # Create notebook for different sections
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Add language selection at the top
        lang_frame = ttk.Frame(self)
        lang_frame.pack(fill='x', pady=5, before=self.notebook)
        
        ttk.Label(lang_frame, text="Bot Language:").pack(side='left')
        ttk.Radiobutton(lang_frame, text="Python", value="python", 
                       variable=self.language).pack(side='left', padx=5)
        ttk.Radiobutton(lang_frame, text="JavaScript (Node.js)", value="nodejs", 
                       variable=self.language).pack(side='left', padx=5)

        # Basic Settings Tab
        basic_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(basic_frame, text='Basic Settings')

        # Bot configuration
        ttk.Label(basic_frame, text="Bot Configuration", font=('Segoe UI', 12, 'bold')).pack()
        
        settings_frame = ttk.LabelFrame(basic_frame, text="Settings", padding=5)
        settings_frame.pack(fill='x', pady=5)

        # Token entry
        ttk.Label(settings_frame, text="Bot Token:").pack()
        self.token_entry = ttk.Entry(settings_frame, width=50)
        self.token_entry.pack(fill='x', pady=2)

        # Status options
        ttk.Label(settings_frame, text="Bot Status:").pack()
        self.status_var = tk.StringVar(value="online")
        for status in ["online", "idle", "dnd", "invisible"]:
            ttk.Radiobutton(settings_frame, text=status, value=status, 
                          variable=self.status_var).pack(side='left', padx=5)

        # Activity frame
        activity_frame = ttk.LabelFrame(basic_frame, text="Activity", padding=5)
        activity_frame.pack(fill='x', pady=5)
        
        self.activity_type = tk.StringVar(value="playing")
        ttk.OptionMenu(activity_frame, self.activity_type, "playing", 
                      "playing", "watching", "listening", "streaming").pack(side='left')
        
        self.activity_text = ttk.Entry(activity_frame, width=40)
        self.activity_text.insert(0, "with Python")
        self.activity_text.pack(side='left', padx=5, fill='x', expand=True)

        # Commands Tab
        commands_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(commands_frame, text='Commands')

        # Command tools
        tools_frame = ttk.Frame(commands_frame)
        tools_frame.pack(fill='x')
        
        ttk.Button(tools_frame, text="Add Simple Command", 
                  command=self.add_command).pack(side='left', padx=2)
        ttk.Button(tools_frame, text="Add Advanced Command", 
                  command=self.add_advanced_command).pack(side='left', padx=2)
        ttk.Button(tools_frame, text="Add Slash Command", 
                  command=self.add_slash_command).pack(side='left', padx=2)

        # Commands list
        self.commands_frame = ttk.Frame(commands_frame)
        self.commands_frame.pack(fill='both', expand=True)

        # Events Tab
        events_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(events_frame, text='Events')

        # Event handlers
        events_list = [
            "on_member_join", "on_member_remove", "on_message_delete",
            "on_reaction_add", "on_voice_state_update", "on_guild_join"
        ]
        
        for event in events_list:
            event_frame = ttk.Frame(events_frame)
            event_frame.pack(fill='x', pady=2)
            
            enabled = tk.BooleanVar()
            ttk.Checkbutton(event_frame, text=event, 
                          variable=enabled).pack(side='left')
            
            response = ttk.Entry(event_frame, width=50)
            response.pack(side='left', fill='x', expand=True, padx=5)
            
            self.events.append((event, enabled, response))

        # Features Tab
        features_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(features_frame, text='Features')

        # Feature toggles
        features = [
            ("Welcome Messages", "Send welcome messages to new members"),
            ("Auto Role", "Automatically assign roles to new members"),
            ("Message Filter", "Filter inappropriate content"),
            ("Logging", "Log server events to a channel"),
            ("Music Player", "Enable music playback commands"),
            ("Level System", "Track user activity and levels"),
            ("Custom Reactions", "Create custom reaction responses"),
            ("Polls", "Enable poll creation"),
            ("Moderation", "Enable moderation commands"),
            ("Economy", "Enable virtual currency system")
        ]

        self.feature_vars = {}
        for feature, description in features:
            frame = ttk.Frame(features_frame)
            frame.pack(fill='x', pady=2)
            
            var = tk.BooleanVar()
            self.feature_vars[feature] = var
            ttk.Checkbutton(frame, text=feature, variable=var).pack(side='left')
            ttk.Label(frame, text=description, foreground='gray').pack(side='left', padx=5)

        # Generate Button
        generate_frame = ttk.Frame(self)
        generate_frame.pack(fill='x', pady=10)
        
        ttk.Button(generate_frame, text="⚙️ Generate Advanced Bot", 
                  command=self.generate_advanced_bot).pack(side='right', padx=5)
        ttk.Button(generate_frame, text="📋 Copy Code", 
                  command=self.copy_code).pack(side='right', padx=5)
        ttk.Button(generate_frame, text="💾 Save Configuration", 
                  command=self.save_config).pack(side='right', padx=5)

        # Code Output
        code_frame = ttk.LabelFrame(self, text="Generated Code", padding=5)
        code_frame.pack(fill='both', expand=True)
        
        self.code_output = tk.Text(code_frame,
                                 wrap='none',
                                 bg=self.theme['text_bg'],
                                 fg=self.theme['text_fg'],
                                 font=('Consolas', 11))
        self.code_output.pack(fill='both', expand=True)

        # Add new tabs
        self.add_roles_tab()
        self.add_permissions_tab()
        self.add_embeds_tab()
        self.add_scheduler_tab()
        self.add_automod_tab()
        self.add_custom_commands_tab()
        self.add_integrations_tab()

    def add_command(self):
        command_frame = ttk.Frame(self.commands_frame)
        command_frame.pack()

        ttk.Label(command_frame, text="Command:").pack(side='left')
        command_entry = ttk.Entry(command_frame, width=20)
        command_entry.pack(side='left')

        ttk.Label(command_frame, text="Response:").pack(side='left')
        response_entry = ttk.Entry(command_frame, width=40)
        response_entry.pack(side='left')

        self.commands.append((command_entry, response_entry))

    def add_advanced_command(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Advanced Command")
        dialog.geometry("500x400")
        
        name_var = tk.StringVar()
        desc_var = tk.StringVar()
        
        ttk.Label(dialog, text="Command Name:").pack()
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(fill='x', padx=5)
        
        ttk.Label(dialog, text="Description:").pack()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var)
        desc_entry.pack(fill='x', padx=5)
        
        ttk.Label(dialog, text="Arguments:").pack()
        args_text = tk.Text(dialog, height=4)
        args_text.pack(fill='x', padx=5)
        
        ttk.Label(dialog, text="Command Code:").pack()
        code_text = tk.Text(dialog, height=10)
        code_text.pack(fill='both', expand=True, padx=5)
        
        def save_command():
            self.advanced_commands.append({
                'name': name_var.get(),
                'description': desc_var.get(),
                'arguments': args_text.get('1.0', tk.END).strip(),
                'code': code_text.get('1.0', tk.END).strip()
            })
            dialog.destroy()
        
        ttk.Button(dialog, text="Save Command", command=save_command).pack(pady=5)

    def add_slash_command(self):
        # Similar to add_advanced_command but for slash commands
        pass

    def save_config(self):
        config = {
            'token': self.token_entry.get(),
            'status': self.status_var.get(),
            'activity': {
                'type': self.activity_type.get(),
                'text': self.activity_text.get()
            },
            'features': {k: v.get() for k, v in self.feature_vars.items()},
            'events': [(e, en.get(), r.get()) for e, en, r in self.events]
        }
        
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def copy_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.code_output.get('1.0', tk.END))
        messagebox.showinfo("Success", "Code copied to clipboard!")

    def generate_advanced_bot(self):
        try:
            # Ask for save location
            save_dir = filedialog.askdirectory(title="Select folder to save bot files")
            if not save_dir:
                return
            
            config = {
                'basic': self.get_basic_config(),
                'commands': self.get_commands_config(),
                'events': self.get_events_config(),
                'features': self.get_features_config()
            }

            lang = self.language.get()
            
            # Create bot folder structure
            if lang == "python":
                self.setup_python_project(save_dir, config)
            elif lang == "nodejs":
                self.setup_nodejs_project(save_dir, config)
            
            messagebox.showinfo("Success", f"Bot files generated in:\n{save_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate bot code: {str(e)}")

    def setup_python_project(self, save_dir, config):
        # Create main bot file
        bot_code = self.generate_python_bot(config)
        with open(f"{save_dir}/bot.py", 'w') as f:
            f.write(bot_code)
        
        # Create requirements.txt
        requirements = """discord.py>=2.0.0
python-dotenv>=0.19.0
asyncio>=3.4.3
aiohttp>=3.8.0"""
        with open(f"{save_dir}/requirements.txt", 'w') as f:
            f.write(requirements)
        
        # Create .env file
        with open(f"{save_dir}/.env", 'w') as f:
            f.write(f"DISCORD_TOKEN={config['basic']['token']}")
        
        # Create cogs folder for advanced features
        if any(config['features'].values()):
            import os
            cogs_dir = f"{save_dir}/cogs"
            os.makedirs(cogs_dir, exist_ok=True)
            
            if config['features'].get('Music Player'):
                with open(f"{cogs_dir}/music.py", 'w') as f:
                    f.write(self.generate_music_cog())
            
            if config['features'].get('Economy'):
                with open(f"{cogs_dir}/economy.py", 'w') as f:
                    f.write(self.generate_economy_cog())

    def setup_nodejs_project(self, save_dir, config):
        # Create main bot file
        bot_code = self.generate_nodejs_bot(config)
        with open(f"{save_dir}/index.js", 'w') as f:
            f.write(bot_code)
        
        # Create package.json
        package_json = """{
  "name": "discord-bot",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "discord.js": "^14.0.0",
    "dotenv": "^16.0.0"
  }
}"""
        with open(f"{save_dir}/package.json", 'w') as f:
            f.write(package_json)
        
        # Create .env file
        with open(f"{save_dir}/.env", 'w') as f:
            f.write(f"DISCORD_TOKEN={config['basic']['token']}")
        
        # Create modules folder for advanced features
        if any(config['features'].values()):
            import os
            modules_dir = f"{save_dir}/modules"
            os.makedirs(modules_dir, exist_ok=True)
            
            if config['features'].get('Music Player'):
                with open(f"{modules_dir}/music.js", 'w') as f:
                    f.write(self.generate_music_module_js())
            
            if config['features'].get('Economy'):
                with open(f"{modules_dir}/economy.js", 'w') as f:
                    f.write(self.generate_economy_module_js())

    # Add helper methods for generating feature-specific code
    def generate_music_cog(self):
        return """import discord
from discord.ext import commands
import wavelink

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def play(self, ctx, *, query):
        # Music player implementation
        pass

async def setup(bot):
    await bot.add_cog(Music(bot))
"""

    def generate_economy_cog(self):
        return """import discord
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def balance(self, ctx):
        # Economy system implementation
        pass

async def setup(bot):
    await bot.add_cog(Economy(bot))
"""

    def generate_music_module_js(self):
        return """const { AudioPlayer, createAudioResource } = require('@discordjs/voice');

class MusicPlayer {
    constructor() {
        this.player = new AudioPlayer();
    }
    
    // Music player implementation
}

module.exports = MusicPlayer;
"""

    def generate_economy_module_js(self):
        return """class EconomySystem {
    constructor() {
        this.balances = new Map();
    }
    
    // Economy system implementation
}

module.exports = EconomySystem;
"""

    def get_basic_config(self):
        return {
            'token': self.token_entry.get(),
            'status': self.status_var.get(),
            'activity': {
                'type': self.activity_type.get(),
                'text': self.activity_text.get()
            }
        }

    def get_commands_config(self):
        commands_list = []
        
        # Add simple commands
        for cmd_entry, resp_entry in self.commands:
            commands_list.append({
                'type': 'simple',
                'name': cmd_entry.get(),
                'response': resp_entry.get()
            })
        
        # Add advanced commands
        for cmd in self.advanced_commands:
            commands_list.append({
                'type': 'advanced',
                **cmd  # Unpack stored command data
            })
            
        return commands_list

    def get_events_config(self):
        return [{
            'name': event,
            'enabled': enabled.get(),
            'response': response.get()
        } for event, enabled, response in self.events]

    def get_features_config(self):
        return {k: v.get() for k, v in self.feature_vars.items()}

    def get_roles_config(self):
        return {
            'hierarchy_enabled': True,  # Add your role configuration getters
            'auto_roles': [],
            'role_colors': {},
            'role_rewards': {}
        }

    def get_permissions_config(self):
        return {
            'manage_messages': True,  # Add your permission configuration getters
            'kick_members': False,
            'ban_members': False
        }

    def get_embeds_config(self):
        return {
            'color': getattr(self, 'embed_color', '#0099ff'),
            'fields': []  # Add your embed fields configuration
        }

    def get_scheduler_config(self):
        return {
            'tasks': []  # Add your scheduled tasks configuration
        }

    def get_automod_config(self):
        return {
            'enabled': True,  # Add your automod configuration
            'rules': {}
        }

    def get_integrations_config(self):
        return {
            'youtube': False,  # Add your integrations configuration
            'twitch': False,
            'github': False
        }

    def generate_bot_code(self, config):
        lang = self.language.get()
        
        if lang == "python":
            return self.generate_python_bot(config)
        elif lang == "nodejs":
            return self.generate_nodejs_bot(config)

    def generate_python_bot(self, config):
        requirements = """discord.py>=2.0.0
python-dotenv>=0.19.0
asyncio>=3.4.3
aiohttp>=3.8.0"""

        if messagebox.askyesno("Requirements", "Would you like to edit requirements.txt?"):
            self.open_in_code_editor("requirements.txt", requirements)

        bot_code = """import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
"""

        # Add event handlers
        for event in config['events']:
            if event['enabled']:
                bot_code += f"""
@bot.event
async def {event['name']}(*args):
    {event['response']}
"""

        # Add commands
        for cmd in config['commands']:
            if cmd['type'] == 'simple':
                bot_code += f"""
@bot.command(name="{cmd['name']}")
async def {cmd['name']}(ctx):
    await ctx.send("{cmd['response']}")
"""
            elif cmd['type'] == 'advanced':
                bot_code += f"""
@bot.command(name="{cmd['name']}")
async def {cmd['name']}(ctx, {cmd['arguments']}):
    {cmd['code']}
"""

        bot_code += """
# Run the bot
bot.run(TOKEN)
"""
        return bot_code

    def generate_nodejs_bot(self, config):
        package_json = """{
  "name": "discord-bot",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "discord.js": "^14.0.0",
    "dotenv": "^16.0.0"
  }
}"""

        if messagebox.askyesno("Package.json", "Would you like to edit package.json?"):
            self.open_in_code_editor("package.json", package_json)

        bot_code = """const { Client, GatewayIntentBits, Events } = require('discord.js');
const dotenv = require('dotenv');

dotenv.config();
const TOKEN = process.env.DISCORD_TOKEN;

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ]
});
"""

        # Add event handlers
        for event in config['events']:
            if event['enabled']:
                bot_code += f"""
client.on('{event['name']}', async (...args) => {{
    {event['response']}
}});
"""

        # Add commands
        bot_code += """
client.on('messageCreate', async message => {
    if (!message.content.startsWith('!')) return;

    const args = message.content.slice(1).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    switch (command) {
"""

        for cmd in config['commands']:
            if cmd['type'] == 'simple':
                bot_code += f"""
        case '{cmd['name']}':
            await message.channel.send('{cmd['response']}');
            break;
"""
            elif cmd['type'] == 'advanced':
                bot_code += f"""
        case '{cmd['name']}':
            {cmd['code']}
            break;
"""

        bot_code += """
    }
});

client.login(TOKEN);
"""
        return bot_code

    def open_in_code_editor(self, filename, content):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            initialfile=filename,
            filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(content)
            messagebox.showinfo("Success", f"File saved as {file_path}\nYou can now open it in the Code Editor tab.")

    # ... Additional getter methods for other configurations ...

    def add_roles_tab(self):
        roles_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(roles_frame, text='Roles')

        # Role management features
        features = [
            ("Role Hierarchy", "Set up role hierarchy system"),
            ("Auto Roles", "Configure automatic role assignment rules"),
            ("Role Colors", "Custom role color management"),
            ("Role Rewards", "Set up role-based reward system"),
            ("Role Menu", "Create role selection menus"),
        ]
        
        for feature, desc in features:
            frame = ttk.Frame(roles_frame)
            frame.pack(fill='x', pady=2)
            ttk.Checkbutton(frame, text=feature).pack(side='left')
            ttk.Label(frame, text=desc, foreground='gray').pack(side='left', padx=5)

    def add_permissions_tab(self):
        perm_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(perm_frame, text='Permissions')

        # Permission settings
        perms = [
            "Manage Messages", "Manage Channels", "Kick Members",
            "Ban Members", "Manage Roles", "View Audit Log",
            "Manage Webhooks", "Manage Emojis", "Manage Server"
        ]
        
        for perm in perms:
            frame = ttk.Frame(perm_frame)
            frame.pack(fill='x', pady=2)
            ttk.Checkbutton(frame, text=perm).pack(side='left')

    def add_embeds_tab(self):
        embeds_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(embeds_frame, text='Embeds')

        # Embed designer
        ttk.Label(embeds_frame, text="Embed Designer", font=('Segoe UI', 12, 'bold')).pack()
        
        # Color picker
        color_frame = ttk.Frame(embeds_frame)
        color_frame.pack(fill='x', pady=5)
        ttk.Label(color_frame, text="Color:").pack(side='left')
        ttk.Button(color_frame, text="Pick Color", 
                  command=self.pick_embed_color).pack(side='left', padx=5)

        # Fields
        fields_frame = ttk.LabelFrame(embeds_frame, text="Fields", padding=5)
        fields_frame.pack(fill='x', pady=5)
        ttk.Button(fields_frame, text="Add Field").pack()

    def add_scheduler_tab(self):
        scheduler_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(scheduler_frame, text='Scheduler')

        # Task scheduler
        tasks_frame = ttk.LabelFrame(scheduler_frame, text="Scheduled Tasks", padding=5)
        tasks_frame.pack(fill='x', pady=5)

        # Add task button
        ttk.Button(tasks_frame, text="Add Task", 
                  command=self.add_scheduled_task).pack()

    def add_automod_tab(self):
        automod_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(automod_frame, text='AutoMod')

        # AutoMod rules
        rules = [
            ("Spam Detection", "Detect and handle spam messages"),
            ("Link Filter", "Control link sharing"),
            ("Word Filter", "Filter inappropriate words"),
            ("Raid Protection", "Prevent server raids"),
            ("Mention Limits", "Control mention spam"),
            ("Slow Mode", "Enable channel slow mode"),
            ("Anti-Phishing", "Detect and remove phishing links"),
            ("Caps Lock", "Control excessive caps usage"),
            ("Emoji Spam", "Control emoji spam"),
            ("Invite Links", "Control Discord invite sharing")
        ]

        for rule, desc in rules:
            frame = ttk.Frame(automod_frame)
            frame.pack(fill='x', pady=2)
            ttk.Checkbutton(frame, text=rule).pack(side='left')
            ttk.Label(frame, text=desc, foreground='gray').pack(side='left', padx=5)

    def add_custom_commands_tab(self):
        custom_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(custom_frame, text='Custom Commands')

        # Command types
        command_types = [
            "Text Response", "Random Response", "Image Response",
            "Embed Response", "Role Management", "Channel Management",
            "User Info", "Server Info", "Custom API Call", "Message Management"
        ]

        for cmd_type in command_types:
            frame = ttk.Frame(custom_frame)
            frame.pack(fill='x', pady=2)
            ttk.Button(frame, text=f"Add {cmd_type}").pack(side='left', padx=2)

    def add_integrations_tab(self):
        integrations_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(integrations_frame, text='Integrations')

        # Integration options
        integrations = [
            ("YouTube", "YouTube notifications and commands"),
            ("Twitch", "Twitch stream notifications"),
            ("Twitter", "Tweet notifications"),
            ("Reddit", "Subreddit updates"),
            ("GitHub", "Repository updates"),
            ("Custom API", "Custom API integration"),
            ("Webhook", "Discord webhook integration"),
            ("Database", "Database connection"),
            ("Weather API", "Weather information"),
            ("Translation", "Message translation")
        ]

        for integration, desc in integrations:
            frame = ttk.Frame(integrations_frame)
            frame.pack(fill='x', pady=2)
            ttk.Checkbutton(frame, text=integration).pack(side='left')
            ttk.Label(frame, text=desc, foreground='gray').pack(side='left', padx=5)

    def pick_embed_color(self):
        color = colorchooser.askcolor(title="Choose Embed Color")
        if color[1]:
            # Store the color for embed generation
            self.embed_color = color[1]

    def add_scheduled_task(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Scheduled Task")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Task Name:").pack()
        name_entry = ttk.Entry(dialog)
        name_entry.pack(fill='x', padx=5)

        ttk.Label(dialog, text="Schedule:").pack()
        schedule_frame = ttk.Frame(dialog)
        schedule_frame.pack(fill='x')

        # Time picker
        hour_var = tk.StringVar(value="00")
        minute_var = tk.StringVar(value="00")
        ttk.Spinbox(schedule_frame, from_=0, to=23, width=3, 
                   textvariable=hour_var).pack(side='left')
        ttk.Label(schedule_frame, text=":").pack(side='left')
        ttk.Spinbox(schedule_frame, from_=0, to=59, width=3, 
                   textvariable=minute_var).pack(side='left')
