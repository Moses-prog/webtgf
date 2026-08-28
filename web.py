import os
import json
from flask import Flask, request, render_template_string, redirect, session, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv, set_key

app = Flask(__name__)
app.secret_key = "super_secret_key_for_session"
ENV_FILE = '.env'
JSON_FILE = 'replacements.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Manager Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background-color: #d1d5db; /* Light grey matching inspiration */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
        }
        .neumorphic {
            background: #e5e7eb;
            box-shadow: 8px 8px 16px #c3c4c7, -8px -8px 16px #ffffff;
        }
        .neumorphic-inset {
            background: #e5e7eb;
            box-shadow: inset 4px 4px 8px #c3c4c7, inset -4px -4px 8px #ffffff;
        }
        .neumorphic-card {
            background: #e5e7eb;
            border-radius: 20px;
            box-shadow: 5px 5px 15px #c8cacd, -5px -5px 15px #ffffff;
        }
        .floating-sidebar {
            background: #2a2a2a;
            border-radius: 20px;
            box-shadow: 10px 10px 20px rgba(0,0,0,0.2);
        }
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #b0b0b0; border-radius: 4px; }
    </style>
</head>
<body class="h-screen flex flex-col md:flex-row antialiased text-gray-800 bg-[#d1d5db]">

    {% if not session.get('logged_in') %}
    <!-- LOGIN SCREEN -->
    <div class="m-auto neumorphic-card p-6 md:p-10 w-full max-w-md text-center mx-4 md:mx-auto">
        <div class="mb-6">
            <i class="fa-solid fa-fingerprint text-4xl text-gray-600 mb-2"></i>
            <h2 class="text-2xl font-bold text-gray-800">System Login</h2>
            <p class="text-sm text-gray-500 mt-2">Log in as Admin or Tenant.</p>
        </div>
        <form method="POST" action="/login" class="space-y-4">
            <div class="text-left">
                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Select Role</label>
                <select name="role" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700">
                    <option value="tenant">Tenant (Manage Rules)</option>
                    <option value="admin">Admin (System Config)</option>
                </select>
            </div>
            <div class="text-left">
                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Password</label>
                <input type="password" name="password" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700" placeholder="Type anything for now...">
            </div>
            <button type="submit" class="w-full bg-gray-800 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-gray-700 transition">Enter Dashboard</button>
        </form>
    </div>
    
    {% else %}
    <!-- DASHBOARD LAYOUT -->
    
    <!-- Mobile Header / Navbar -->
    <div class="md:hidden flex items-center justify-between p-4 neumorphic mb-4 shadow-sm z-20">
        <div class="flex items-center space-x-2">
            <i class="fa-solid fa-robot text-blue-500 text-xl"></i>
            <span class="font-bold text-gray-800">Webtgf Manager</span>
        </div>
        <div class="flex space-x-4">
            <a href="/?tab=dashboard" class="{% if tab == 'dashboard' %}text-blue-600{% else %}text-gray-500{% endif %}"><i class="fa-solid fa-wand-magic-sparkles text-xl"></i></a>
            <a href="/?tab=help" class="{% if tab == 'help' %}text-blue-600{% else %}text-gray-500{% endif %}"><i class="fa-solid fa-circle-info text-xl"></i></a>
            {% if session.get('role') == 'admin' %}
            <a href="/?tab=admin" class="{% if tab == 'admin' %}text-blue-600{% else %}text-gray-500{% endif %}"><i class="fa-solid fa-server text-xl"></i></a>
            {% endif %}
            <a href="/logout" class="text-red-400"><i class="fa-solid fa-arrow-right-from-bracket text-xl"></i></a>
        </div>
    </div>
    
    <!-- Desktop Far Left Dark Sidebar -->
    <nav class="hidden md:flex w-16 floating-sidebar flex-col items-center py-8 space-y-8 z-20 text-gray-400 m-4 lg:m-8 mr-0">
        <a href="#" class="text-white bg-gray-700 p-3 rounded-xl shadow-inner"><i class="fa-solid fa-robot"></i></a>
        <a href="/?tab=dashboard" class="{% if tab == 'dashboard' %}text-white{% else %}hover:text-white{% endif %} transition"><i class="fa-solid fa-wand-magic-sparkles"></i></a>
        <a href="/?tab=help" class="{% if tab == 'help' %}text-white{% else %}hover:text-white{% endif %} transition"><i class="fa-solid fa-circle-question"></i></a>
        {% if session.get('role') == 'admin' %}
        <a href="/?tab=admin" class="{% if tab == 'admin' %}text-white{% else %}hover:text-white{% endif %} transition"><i class="fa-solid fa-server"></i></a>
        {% endif %}
        <div class="flex-1"></div>
        <a href="/logout" class="hover:text-red-400 transition" title="Logout"><i class="fa-solid fa-arrow-right-from-bracket"></i></a>
    </nav>
    
    <!-- Desktop Secondary Light Sidebar -->
    <aside class="hidden md:flex w-64 neumorphic rounded-l-3xl -ml-4 pl-8 pr-4 py-8 z-10 flex-col my-4 lg:my-8">
        <!-- Profile -->
        <div class="flex items-center space-x-3 mb-10 pl-2">
            <div class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center shadow-inner overflow-hidden">
                <i class="fa-solid fa-user text-gray-500"></i>
            </div>
            <div>
                <h3 class="text-sm font-bold text-gray-800">{{ session.get('role').capitalize() }} User</h3>
                <p class="text-xs text-gray-500">Active Workspace</p>
            </div>
        </div>

        <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Management</h4>
        <ul class="space-y-1 mb-8">
            <li>
                <a href="/?tab=dashboard" class="flex items-center px-4 py-2 rounded-lg text-sm font-medium {% if tab == 'dashboard' %}bg-white/50 shadow-sm text-gray-900{% else %}text-gray-600 hover:bg-white/30{% endif %}">
                    <i class="fa-solid fa-wand-magic-sparkles w-6"></i> My Bot Rules
                </a>
            </li>
            <li>
                <a href="/?tab=help" class="flex items-center px-4 py-2 rounded-lg text-sm font-medium {% if tab == 'help' %}bg-white/50 shadow-sm text-gray-900{% else %}text-gray-600 hover:bg-white/30{% endif %}">
                    <i class="fa-solid fa-book w-6"></i> Instructions
                </a>
            </li>
            {% if session.get('role') == 'admin' %}
            <li>
                <a href="/?tab=admin" class="flex items-center px-4 py-2 rounded-lg text-sm font-medium {% if tab == 'admin' %}bg-white/50 shadow-sm text-gray-900{% else %}text-gray-600 hover:bg-white/30{% endif %}">
                    <i class="fa-solid fa-server w-6"></i> System Settings
                </a>
            </li>
            {% endif %}
        </ul>
        
        <div class="flex-1"></div>
        <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">System Status</h4>
        <div class="neumorphic-inset p-4 rounded-xl">
            {% if is_online %}
            <div class="flex items-center mb-2">
                <span class="w-3 h-3 rounded-full bg-green-500 mr-3 animate-pulse shadow-[0_0_8px_#22c55e]"></span> 
                <span class="text-sm font-bold text-gray-800">Bot Online</span>
            </div>
            <p class="text-xs text-gray-500">Actively listening for messages in background.</p>
            {% else %}
            <div class="flex items-center mb-2">
                <span class="w-3 h-3 rounded-full bg-red-500 mr-3 shadow-[0_0_8px_#ef4444]"></span> 
                <span class="text-sm font-bold text-gray-800">Bot Offline</span>
            </div>
            <p class="text-xs text-gray-500">The python forwarder script is not running.</p>
            {% endif %}
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 neumorphic md:rounded-r-3xl rounded-none p-4 md:p-8 lg:p-12 overflow-y-auto z-10 border-l border-white/20 md:my-4 lg:my-8 mb-0 pb-12 relative">
        
        <!-- Mobile Status Indicator -->
        <div class="md:hidden absolute top-4 right-4 flex items-center bg-white/50 px-3 py-1 rounded-full shadow-sm">
            {% if is_online %}
            <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> <span class="text-xs font-bold">Online</span>
            {% else %}
            <span class="w-2 h-2 rounded-full bg-red-500 mr-2"></span> <span class="text-xs font-bold">Offline</span>
            {% endif %}
        </div>

        {% if tab == 'help' %}
        <!-- INSTRUCTIONS -->
        <div class="max-w-4xl mx-auto md:mx-0">
            <h1 class="text-2xl md:text-3xl font-light text-gray-800 mb-2">How to use this System</h1>
            <p class="text-gray-500 mb-8 text-sm md:text-base">A quick guide for non-technical users.</p>
            
            <div class="space-y-6">
                <div class="neumorphic-card p-6 md:p-8">
                    <h3 class="text-lg font-bold text-blue-600 mb-2"><i class="fa-solid fa-tower-broadcast mr-2"></i> How Channels Work</h3>
                    <p class="text-sm text-gray-700 leading-relaxed">
                        In the <b>Bot Rules</b> tab, you will see <i>Sources</i> and <i>Targets</i>. <br><br>
                        <b>Sources:</b> These are the channels the bot watches. When a new message is posted here, the bot grabs it immediately. Type them like <code>@crypto_news</code>.<br>
                        <b>Targets:</b> This is where the bot sends the final message after applying your rules. Usually your own channel, like <code>@my_crypto_channel</code>.
                    </p>
                </div>
                
                <div class="neumorphic-card p-6 md:p-8">
                    <h3 class="text-lg font-bold text-purple-600 mb-2"><i class="fa-solid fa-wand-magic-sparkles mr-2"></i> Global Swaps</h3>
                    <p class="text-sm text-gray-700 leading-relaxed">
                        Instead of replacing words one-by-one, use <b>Global Swaps</b> to save time:<br><br>
                        - If you set a <b>Global Link</b>, the bot will find ANY clickable website link in the message and replace it with yours.<br>
                        - If you set a <b>Global Username</b>, the bot will automatically change any mention (like <code>@admin</code> or <code>@creator</code>) to your username.
                    </p>
                </div>
                
                <div class="neumorphic-card p-6 md:p-8">
                    <h3 class="text-lg font-bold text-indigo-600 mb-2"><i class="fa-solid fa-image mr-2"></i> Image Override</h3>
                    <p class="text-sm text-gray-700 leading-relaxed">
                        If you upload an image in the settings, the bot will <b>replace</b> any incoming picture or video with your uploaded image. <br><br>
                        <i>Note: It will ONLY replace images if the original message actually contained a picture/video. If the original message was just text, it will remain just text!</i>
                    </p>
                </div>
            </div>
        </div>
        
        {% elif tab == 'admin' %}
        <!-- ADMIN SETTINGS -->
        <div class="max-w-4xl mx-auto md:mx-0 space-y-8">
            <h1 class="text-2xl md:text-3xl font-light text-gray-800 mb-2">Webtgf Control Center</h1>
            <p class="text-gray-500 mb-8 text-sm md:text-base">Admin only. Manage your platform, tenants, and view analytics.</p>
            
            <!-- Analytics -->
            <div class="neumorphic-card p-4 md:p-8">
                <h2 class="text-lg font-bold text-gray-800 mb-4 border-b border-gray-300/50 pb-2"><i class="fa-solid fa-chart-line mr-2"></i> Analytics</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="neumorphic-inset p-6 rounded-xl text-center">
                        <p class="text-sm text-gray-500 uppercase font-bold tracking-wider mb-2">Total Tenants</p>
                        <p class="text-3xl font-light text-gray-800">{{ tenants|length }}</p>
                    </div>
                    <div class="neumorphic-inset p-6 rounded-xl text-center">
                        <p class="text-sm text-gray-500 uppercase font-bold tracking-wider mb-2">Total Forwards</p>
                        <p class="text-3xl font-light text-gray-800">{{ stats.total }}</p>
                    </div>
                    <div class="neumorphic-inset p-6 rounded-xl text-center">
                        <p class="text-sm text-gray-500 uppercase font-bold tracking-wider mb-2">Today's Activity</p>
                        <p class="text-3xl font-light text-gray-800">{{ stats.today }}</p>
                    </div>
                </div>
            </div>

            <!-- Tenant Management -->
            <div class="neumorphic-card p-4 md:p-8">
                <h2 class="text-lg font-bold text-gray-800 mb-4 border-b border-gray-300/50 pb-2"><i class="fa-solid fa-users mr-2"></i> Tenant Management</h2>
                
                <div class="mb-6">
                    <h3 class="text-sm font-bold text-gray-600 mb-3">Active Tenants:</h3>
                    <div class="flex flex-wrap gap-2">
                        {% for t in tenants %}
                        <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full border border-blue-200">{{ t }}</span>
                        {% else %}
                        <span class="text-sm text-gray-400">No active tenants.</span>
                        {% endfor %}
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <form method="POST" action="/add_tenant" class="neumorphic-inset p-4 rounded-xl space-y-4">
                        <label class="block text-xs font-bold text-gray-500 uppercase">Add Tenant ID</label>
                        <input type="text" name="tenant_id" placeholder="Telegram Chat ID" class="w-full bg-white/50 px-4 py-2 rounded-lg outline-none text-gray-700 text-sm">
                        <button type="submit" class="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-bold shadow hover:bg-blue-700 transition text-sm"><i class="fa-solid fa-plus mr-1"></i> Add</button>
                    </form>
                    <form method="POST" action="/remove_tenant" class="neumorphic-inset p-4 rounded-xl space-y-4">
                        <label class="block text-xs font-bold text-gray-500 uppercase">Remove Tenant ID</label>
                        <input type="text" name="tenant_id" placeholder="Telegram Chat ID" class="w-full bg-white/50 px-4 py-2 rounded-lg outline-none text-gray-700 text-sm">
                        <button type="submit" class="w-full bg-red-500 text-white px-4 py-2 rounded-lg font-bold shadow hover:bg-red-600 transition text-sm"><i class="fa-solid fa-trash mr-1"></i> Remove</button>
                    </form>
                </div>
            </div>

            <!-- API Config -->
            <form method="POST" action="/update_admin" class="neumorphic-card p-4 md:p-8 space-y-6">
                <h2 class="text-lg font-bold text-gray-800 mb-4 border-b border-gray-300/50 pb-2"><i class="fa-solid fa-key mr-2"></i> Admin's API Config</h2>
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Telegram API ID</label>
                    <input type="text" name="api_id" value="{{ env_data.get('API_ID', '') }}" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 font-mono text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Telegram API Hash</label>
                    <input type="password" name="api_hash" value="{{ env_data.get('API_HASH', '') }}" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 font-mono text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Telegram Session String</label>
                    <textarea name="session_string" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 font-mono h-24 text-xs">{{ env_data.get('SESSION_STRING', '') }}</textarea>
                </div>
                <div class="pt-4 border-t border-gray-300/50">
                    <button type="submit" class="w-full md:w-auto bg-gray-800 text-white px-8 py-3 rounded-xl font-bold shadow-md hover:bg-gray-700 transition">Save API Config</button>
                </div>
            </form>
        </div>
        
        {% else %}
        <!-- TENANT DASHBOARD (BOT RULES) -->
        <div class="max-w-5xl mx-auto md:mx-0">
            <h1 class="text-2xl md:text-3xl font-light text-gray-800 mb-2">Bot Rules & Routing</h1>
            <p class="text-gray-500 mb-8 text-sm md:text-base">Easily control what your bot listens to and how it modifies messages.</p>

            <form method="POST" action="/update_tenant" enctype="multipart/form-data" class="space-y-6 md:space-y-8">
                
                <!-- 1. CHANNELS -->
                <div class="neumorphic-card p-5 md:p-8">
                    <h2 class="text-md md:text-lg font-bold text-gray-800 mb-4 border-b border-gray-300/50 pb-2">1. Where should the bot listen and post?</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Listen to these Channels (Sources)</label>
                            <p class="text-xs text-gray-500 mb-2">Separate multiple channels with commas. (e.g. @news, @crypto)</p>
                            <input type="text" name="sources" value="{{ env_data.get('SOURCE_CHANNELS', '') }}" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Forward messages to (Targets)</label>
                            <p class="text-xs text-gray-500 mb-2">Separate multiple channels with commas. (e.g. @my_channel, @group2)</p>
                            <input type="text" name="targets" value="{{ env_data.get('TARGET_CHANNELS', '') }}" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                    </div>
                </div>

                <!-- 2. LINKS & MEDIA -->
                <div class="neumorphic-card p-5 md:p-8">
                    <h2 class="text-md md:text-lg font-bold text-gray-800 mb-4 border-b border-gray-300/50 pb-2">2. Global Links & Media Swapper</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Replace ANY Link With:</label>
                            <p class="text-xs text-gray-500 mb-2">Forces all links in messages to become this URL.</p>
                            <input type="text" name="global_link" value="{{ json_data.get('replace_all_links_with', '') }}" placeholder="https://my-affiliate.com" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Replace ALL Usernames With:</label>
                            <p class="text-xs text-gray-500 mb-2">Instantly changes any @mention to yours.</p>
                            <input type="text" name="global_username" value="{{ json_data.get('replace_all_usernames_with', '') }}" placeholder="@myusername" class="w-full neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                    </div>
                    
                    <div class="mt-6 pt-6 border-t border-gray-300/50">
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Replace Photos/Videos With Custom Image:</label>
                        <p class="text-xs text-gray-500 mb-3">Upload an image to override incoming media, OR paste a URL to an image below.</p>
                        
                        <div class="flex flex-col md:flex-row items-center space-y-3 md:space-y-0 md:space-x-4 mb-3">
                            <input type="file" name="image_upload" accept="image/*" class="w-full md:w-1/2 text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-white file:text-gray-700 hover:file:bg-gray-100 cursor-pointer neumorphic-inset p-2 rounded-xl">
                            <span class="text-sm text-gray-500 font-bold hidden md:block">OR</span>
                            <input type="text" name="image_url" value="{{ json_data.get('image_swap_url', '') }}" placeholder="Paste Image URL here..." class="w-full md:w-1/2 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                        {% if json_data.get('image_swap_path') or json_data.get('image_swap_url') %}
                        <div class="bg-green-100/50 p-3 rounded-lg border border-green-200 mt-4">
                            <p class="text-xs text-green-700 font-bold"><i class="fa-solid fa-check-circle mr-1"></i> Custom image is currently active.</p>
                            <label class="flex items-center mt-2 text-sm text-gray-700">
                                <input type="checkbox" name="remove_image" class="mr-2 rounded"> Check this box to remove custom image.
                            </label>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- 3. DICTIONARY -->
                <div class="neumorphic-card p-5 md:p-8">
                    <h2 class="text-md md:text-lg font-bold text-gray-800 mb-1">3. Word Replacer</h2>
                    <p class="text-sm text-gray-500 mb-6 border-b border-gray-300/50 pb-4">Define specific words or phrases to find and swap.</p>
                    
                    <div id="swaps-container" class="space-y-3 md:space-y-4">
                        <!-- Existing Swaps -->
                        {% for old_text, new_text in json_data.get('text_swaps', {}).items() %}
                        <div class="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-4 group bg-white/30 p-3 md:p-0 rounded-xl md:bg-transparent">
                            <input type="text" name="old_text[]" value="{{ old_text }}" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Find this word...">
                            <i class="fa-solid fa-arrow-down md:fa-arrow-right text-gray-400 text-center block"></i>
                            <input type="text" name="new_text[]" value="{{ new_text }}" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Replace with...">
                            <button type="button" onclick="this.parentElement.remove()" class="text-red-400 hover:text-red-600 px-2 pt-2 md:pt-0 self-end md:self-auto opacity-100 md:opacity-0 md:group-hover:opacity-100 transition text-sm"><i class="fa-solid fa-trash mr-1 md:mr-0"></i><span class="md:hidden">Remove</span></button>
                        </div>
                        {% endfor %}
                        
                        <!-- Empty Row for new entry -->
                        <div class="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-4 group swap-row bg-white/30 p-3 md:p-0 rounded-xl md:bg-transparent">
                            <input type="text" name="old_text[]" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Find this word...">
                            <i class="fa-solid fa-arrow-down md:fa-arrow-right text-gray-400 text-center block"></i>
                            <input type="text" name="new_text[]" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Replace with...">
                            <button type="button" onclick="this.parentElement.remove()" class="text-red-400 hover:text-red-600 px-2 pt-2 md:pt-0 self-end md:self-auto opacity-100 md:opacity-0 md:group-hover:opacity-100 transition text-sm"><i class="fa-solid fa-trash mr-1 md:mr-0"></i><span class="md:hidden">Remove</span></button>
                        </div>
                    </div>
                    
                    <button type="button" onclick="addRow()" class="mt-4 text-sm font-semibold text-gray-600 hover:text-gray-900 flex items-center bg-white/40 px-4 py-3 rounded-lg shadow-sm w-full justify-center md:w-auto md:justify-start">
                        <i class="fa-solid fa-plus mr-2"></i> Add Another Row
                    </button>
                    
                    <script>
                        function addRow() {
                            const container = document.getElementById('swaps-container');
                            const row = document.createElement('div');
                            row.className = 'flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-4 group swap-row mt-4 bg-white/30 p-3 md:p-0 rounded-xl md:bg-transparent';
                            row.innerHTML = `
                                <input type="text" name="old_text[]" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Find this word...">
                                <i class="fa-solid fa-arrow-down md:fa-arrow-right text-gray-400 text-center block"></i>
                                <input type="text" name="new_text[]" class="w-full md:flex-1 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm" placeholder="Replace with...">
                                <button type="button" onclick="this.parentElement.remove()" class="text-red-400 hover:text-red-600 px-2 pt-2 md:pt-0 self-end md:self-auto opacity-100 md:opacity-0 md:group-hover:opacity-100 transition text-sm"><i class="fa-solid fa-trash mr-1 md:mr-0"></i><span class="md:hidden">Remove</span></button>
                            `;
                            container.appendChild(row);
                        }
                    </script>
                </div>

                <div class="pt-4 flex justify-end">
                    <button type="submit" class="w-full md:w-auto bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 rounded-xl font-bold shadow-lg transition transform hover:-translate-y-1">
                        <i class="fa-solid fa-check mr-2"></i> Save & Apply Changes
                    </button>
                </div>
            </form>
        </div>
        {% endif %}
    </main>
    {% endif %}

</body>
</html>
"""

@app.route('/')
def index():
    tab = request.args.get('tab', 'dashboard')
    chat_id = session.get('chat_id')
    role = session.get('role')
    
    # Check Online Status via Heartbeat
    import time
    is_online = False
    try:
        with open('status.json', 'r') as f:
            status_data = json.load(f)
            if time.time() - status_data.get('last_seen', 0) < 20:
                is_online = True
    except:
        pass
        
    if not session.get('logged_in'):
        return render_template_string(HTML_TEMPLATE, env_data={}, json_data={}, tab=tab, is_online=is_online)
        
    from database_manager import get_user_data, get_tenants, get_stats
    user_data = get_user_data(chat_id) if chat_id else {}
    
    env_data = {
        'API_ID': user_data.get('api_id', ''),
        'API_HASH': user_data.get('api_hash', ''),
        'SESSION_STRING': user_data.get('session_string', ''),
        'SOURCE_CHANNELS': ", ".join(user_data.get('sources', [])),
        'TARGET_CHANNELS': ", ".join(user_data.get('targets', []))
    }
    
    json_data = user_data
    
    tenants = []
    stats = {"total": 0, "today": 0}
    if role == 'admin':
        tenants = get_tenants()
        stats = get_stats()
        import datetime
        if stats.get("date") != str(datetime.date.today()):
            stats["today"] = 0
                
    return render_template_string(HTML_TEMPLATE, env_data=env_data, json_data=json_data, tab=tab, is_online=is_online, tenants=tenants, stats=stats)

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role', 'tenant')
    password = request.form.get('password', '')
    
    if role == 'admin':
        if password != os.getenv('ADMIN_ID', '5628105961'):
            return "Invalid Admin ID", 401
        session['chat_id'] = password
    else:
        from database_manager import get_tenants
        if password not in get_tenants():
            return "Tenant ID not found. Make sure the Admin has added your Telegram ID.", 401
        session['chat_id'] = password
        
    session['logged_in'] = True
    session['role'] = role
    return redirect(url_for('index', tab='dashboard' if role == 'tenant' else 'admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add_tenant', methods=['POST'])
def add_tenant():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    
    tenant_id = request.form.get('tenant_id', '').strip()
    if tenant_id:
        from database_manager import get_tenants, save_tenants
        tenants = get_tenants()
        if tenant_id not in tenants:
            tenants.append(tenant_id)
            save_tenants(tenants)
    return redirect(url_for('index', tab='admin'))

@app.route('/remove_tenant', methods=['POST'])
def remove_tenant():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    
    tenant_id = request.form.get('tenant_id', '').strip()
    if tenant_id:
        from database_manager import get_tenants, save_tenants
        tenants = get_tenants()
        if tenant_id in tenants:
            tenants.remove(tenant_id)
            save_tenants(tenants)
    return redirect(url_for('index', tab='admin'))

@app.route('/update_admin', methods=['POST'])
def update_admin():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
        
    chat_id = session.get('chat_id')
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(chat_id)
    user_data['api_id'] = request.form.get('api_id', '')
    user_data['api_hash'] = request.form.get('api_hash', '')
    user_data['session_string'] = request.form.get('session_string', '')
    save_user_data(chat_id, user_data)
    
    return redirect(url_for('index', tab='admin'))

@app.route('/update_tenant', methods=['POST'])
def update_tenant():
    if not session.get('logged_in'):
        return "Unauthorized", 401

    chat_id = session.get('chat_id')
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(chat_id)
    
    # Save routing
    sources_str = request.form.get('sources', '')
    targets_str = request.form.get('targets', '')
    user_data['sources'] = [x.strip() for x in sources_str.split(',') if x.strip()]
    user_data['targets'] = [x.strip() for x in targets_str.split(',') if x.strip()]
    
    # Save text swaps
    old_texts = request.form.getlist('old_text[]')
    new_texts = request.form.getlist('new_text[]')
    text_swaps = {}
    for old, new in zip(old_texts, new_texts):
        if old.strip():
            text_swaps[old] = new
    user_data['text_swaps'] = text_swaps
            
    # Handle Image Upload or URL
    if 'remove_image' in request.form:
        user_data['image_swap_path'] = ''
        user_data['image_swap_url'] = ''
    else:
        url_input = request.form.get('image_url', '').strip()
        if url_input:
            user_data['image_swap_url'] = url_input
            user_data['image_swap_path'] = '' 
        
        if 'image_upload' in request.files:
            file = request.files['image_upload']
            if file.filename:
                filename = secure_filename(file.filename)
                os.makedirs(os.path.join('database', 'images'), exist_ok=True)
                filepath = os.path.join('database', 'images', f"{chat_id}.jpg")
                file.save(filepath)
                user_data['image_swap_path'] = filepath
                user_data['image_swap_url'] = ''
            
    user_data["replace_all_usernames_with"] = request.form.get('global_username', '')
    user_data["replace_all_links_with"] = request.form.get('global_link', '')
    
    save_user_data(chat_id, user_data)
        
    return redirect(url_for('index', tab='dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
