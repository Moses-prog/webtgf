import os
import json
from flask import Flask, request, render_template_string, redirect, session, url_for, jsonify
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
    
/* Bottom Navigation */
body { padding-bottom: 80px; }

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: var(--card-bg);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 10px 0;
    padding-bottom: calc(10px + env(safe-area-inset-bottom));
    z-index: 900;
}

.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 500;
    gap: 4px;
    cursor: pointer;
    transition: 0.2s;
    width: 60px;
    -webkit-tap-highlight-color: transparent;
}

.nav-item:active {
    opacity: 0.7;
    transform: scale(0.95);
}

.nav-item.active {
    color: var(--primary-color);
}

.nav-item svg {
    width: 24px;
    height: 24px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}

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

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WebTGF</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-main: #111827;
            --text-muted: #6b7280;
            --border-color: #e5e7eb;
            --accent: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #000000;
                --card-bg: #1c1c1e;
                --text-main: #ffffff;
                --text-muted: #8e8e93;
                --border-color: #2c2c2e;
                --accent: #0a84ff;
                --success: #30d158;
                --warning: #ffd60a;
            }
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            min-height: 100vh;
            padding-bottom: 40px;
        }
        
        /* Icons */
        svg { width: 22px; height: 22px; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; fill: none; }
        
        /* Header */
        .header { display: flex; flex-direction: column; align-items: center; padding: 32px 20px 24px; }
        .avatar-frame {
            position: relative;
            width: 86px; height: 86px;
            border-radius: 50%;
            background: var(--text-muted); /* Grey for FREE */
            padding: 3px; 
            margin-bottom: 16px;
            display: flex;
            transition: all 0.3s ease;
        }
        
        .avatar-frame.pro {
            background: linear-gradient(135deg, #ff4500, #ff8c00, #ff003c, #ff4500);
            background-size: 300% 300%;
            animation: proGlow 3s ease infinite;
        }
        
        @keyframes proGlow {
            0% { background-position: 0% 50%; box-shadow: 0 0 15px rgba(255, 69, 0, 0.4); }
            50% { background-position: 100% 50%; box-shadow: 0 0 25px rgba(255, 0, 60, 0.7); }
            100% { background-position: 0% 50%; box-shadow: 0 0 15px rgba(255, 69, 0, 0.4); }
        }
        .avatar-inner {
            width: 100%; height: 100%;
            border-radius: 50%;
            background: var(--bg-color);
            padding: 3px;
            display: flex; align-items: center; justify-content: center;
        }
        .avatar-image {
            width: 100%; height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background: var(--border-color);
            display: flex; align-items: center; justify-content: center;
        }
        .avatar-image svg { width: 36px; height: 36px; color: var(--text-muted); }
        .tier-diamond {
            position: absolute;
            top: -6px; right: -6px;
            background: var(--bg-color);
            border-radius: 50%; padding: 4px;
            display: none; /* Shown via JS if PRO */
        }
        .tier-diamond svg { width: 16px; height: 16px; color: #ff4500; fill: #ff4500; }
        
        .bot-name { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
        .bot-username { font-size: 15px; color: var(--text-muted); margin-bottom: 16px; }
        
        .status-badges { display: flex; gap: 8px; }
        .badge {
            padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;
            display: flex; align-items: center; gap: 4px;
        }
        .badge svg { width: 14px; height: 14px; }
        
        .badge.pro { background: rgba(10, 132, 255, 0.15); color: var(--accent); }
        .badge.free { background: rgba(142, 142, 147, 0.15); color: var(--text-muted); }
        .badge.connected { background: rgba(48, 209, 88, 0.15); color: var(--success); }
        .badge.disconnected { background: rgba(255, 69, 58, 0.15); color: #ff453a; }

        /* Sections */
        .section-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; padding: 18px 16px 8px; }
        
        /* Lists */
        .list-group { background: var(--card-bg); margin: 0 16px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); }
        .list-item { 
            display: flex; align-items: center; padding: 16px; 
            border-bottom: 1px solid var(--border-color); 
            gap: 16px; 
        }
        .list-item:last-child { border-bottom: none; }
        
        .icon-box { 
            width: 32px; height: 32px; border-radius: 8px; 
            display: flex; align-items: center; justify-content: center; 
            flex-shrink: 0; color: var(--text-main);
        }
        
        .item-text { flex: 1; }
        .item-title { font-size: 16px; font-weight: 500; margin-bottom: 2px; }
        .item-subtitle { font-size: 13px; color: var(--text-muted); }
        
        .item-right { color: var(--text-muted); font-size: 14px; display: flex; align-items: center; }
        .item-right svg { width: 18px; height: 18px; color: var(--border-color); }

        .chip { background: var(--border-color); color: var(--text-muted); font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; }

        /* Buttons */
        .primary-btn { 
            margin: 24px 16px 10px; background: var(--accent); color: white; border: none; 
            padding: 16px; font-size: 16px; font-weight: 600; border-radius: 12px; 
            cursor: pointer; width: calc(100% - 32px); transition: opacity 0.2s; 
            display: flex; justify-content: center; align-items: center; gap: 8px;
        }
        .primary-btn:active { opacity: 0.8; }
        .footer { text-align: center; font-size: 13px; color: var(--text-muted); padding: 20px; }
        
        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 0 16px 8px; }
        .stat-card { background: var(--card-bg); padding: 16px; border-radius: 12px; border: 1px solid var(--border-color); }
        .stat-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
        .stat-label { font-size: 12px; color: var(--text-muted); font-weight: 500; text-transform: uppercase; }

        /* Loading state */
        .skeleton { background: var(--border-color); border-radius: 4px; animation: pulse 1.5s infinite; color: transparent !important; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        
        /* Modal Popup */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 100;
            display: none; opacity: 0; transition: opacity 0.3s;
            backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
        }
        .modal {
            position: fixed; bottom: -100%; left: 0; width: 100%; max-height: 85vh;
            background: var(--bg-color); border-radius: 24px 24px 0 0;
            z-index: 101; transition: bottom 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            display: flex; flex-direction: column;
            box-shadow: 0 -5px 25px rgba(0,0,0,0.15);
        }
        .modal.active { bottom: 0; }
        .modal-overlay.active { display: block; opacity: 1; }
        
        .modal-drag { width: 40px; height: 5px; background: var(--border-color); border-radius: 3px; margin: 12px auto; }
        .modal-header { padding: 8px 20px 20px; border-bottom: 1px solid var(--border-color); }
        .modal-header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .modal-title { font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 8px; }
        .modal-subtitle { font-size: 14px; color: var(--text-muted); }

        .modal-close { background: none; border: none; color: var(--text-muted); padding: 4px; cursor: pointer; }
        .modal-close svg { width: 24px; height: 24px; }
        
        .modal-body { overflow-y: auto; padding: 16px; flex: 1; }
        
        .channel-row { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--card-bg); margin-bottom: 12px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
        .channel-name { font-size: 15px; font-family: monospace; font-weight: 600; color: var(--text-main); word-break: break-all; }
        .btn-remove { background: rgba(255, 69, 58, 0.1); color: #ff453a; border: none; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; }
        .btn-remove:active { background: #ff453a; color: white; }
        .btn-remove svg { width: 16px; height: 16px; }
        
        .add-channel-row { display: flex; flex-direction: column; padding: 20px 20px calc(24px + env(safe-area-inset-bottom, 16px)) 20px; gap: 12px; background: var(--card-bg); border-top: 1px solid var(--border-color); }
        .add-input { flex: 1; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-main); padding: 14px 16px; border-radius: 12px; font-size: 16px; outline: none; transition: border-color 0.2s; }
        .add-input:focus { border-color: var(--accent); }
        .btn-add { background: var(--accent); color: white; border: none; padding: 14px 24px; border-radius: 12px; font-weight: 700; font-size: 16px; cursor: pointer; transition: transform 0.1s, opacity 0.2s; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); width: 100%; }\n        .btn-add:active { transform: scale(0.98); opacity: 0.9; }
        .btn-add:active { opacity: 0.8; }
        
        .empty-state { padding: 40px 20px; text-align: center; color: var(--text-muted); font-size: 15px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
        .empty-icon { width: 64px; height: 64px; color: var(--border-color); background: var(--card-bg); border-radius: 50%; padding: 16px; margin-bottom: 8px; }
        .empty-title { font-weight: 600; color: var(--text-main); font-size: 18px; }
        
        /* iOS Switch */
        .switch { position: relative; display: inline-block; width: 50px; height: 28px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--border-color); transition: .3s; border-radius: 30px; }
        .slider:before { position: absolute; content: ""; height: 24px; width: 24px; left: 2px; bottom: 2px; background-color: white; transition: .3s; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        input:checked + .slider { background-color: #34c759; }
        input:checked + .slider:before { transform: translateX(22px); }
        
        .stat-card { cursor: pointer; transition: transform 0.1s; }
        .stat-card:active { transform: scale(0.98); }
    
/* Bottom Navigation */
body { padding-bottom: 80px; }

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: var(--card-bg);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 10px 0;
    padding-bottom: calc(10px + env(safe-area-inset-bottom));
    z-index: 900;
}

.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 500;
    gap: 4px;
    cursor: pointer;
    transition: 0.2s;
    width: 60px;
    -webkit-tap-highlight-color: transparent;
}

.nav-item:active {
    opacity: 0.7;
    transform: scale(0.95);
}

.nav-item.active {
    color: var(--primary-color);
}

.nav-item svg {
    width: 24px;
    height: 24px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}

</style>
</head>
<body>
    <div class="header">
        <div class="avatar-frame" id="avatar-frame">
            <div class="avatar-inner">
                <div class="avatar-image" id="user-avatar-container">
                    <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
            </div>
            <div class="tier-diamond" id="tier-diamond">
                <svg viewBox="0 0 24 24"><path d="M6 3h12l4 6-10 13L2 9z"></path><path d="M11 3l-4 6 5 13"></path><path d="M13 3l4 6-5 13"></path><path d="M2 9h20"></path></svg>
            </div>
        </div>
        <div class="bot-name" id="user-greeting">Hi, User!</div>
        <div class="bot-username">WebTGF Dashboard</div>
        
        <div class="status-badges">
            <div id="tier-badge" class="badge free skeleton">Tier</div>
            <div id="conn-badge" class="badge disconnected skeleton">Status</div>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card" onclick="openModal('sources')">
            <div id="stat-sources" class="stat-value skeleton">0</div>
            <div class="stat-label">Active Sources &rarr;</div>
        </div>
        <div class="stat-card" onclick="openModal('targets')">
            <div id="stat-targets" class="stat-value skeleton">0</div>
            <div class="stat-label">Active Targets &rarr;</div>
        </div>
                <div class="stat-card" style="grid-column: span 2;" onclick="openModal('replacements')">
            <div id="stat-replacements" class="stat-value skeleton">0</div>
            <div class="stat-label">Word Replacements &rarr;</div>
        </div>
    </div>

    
    
    <div class="section-label">Core Features</div>
    <div class="list-group">
        <div class="list-item" onclick="openModal('settings')">
            <div class="icon-box"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg></div>
            <div class="item-text">
                <div class="item-title">Filters & Settings</div>
                <div class="item-subtitle">Configure anti-payment & audio/voice block</div>
            </div>
            <span class="chip">PRO</span>
        </div>
        <div class="list-item">
            <div class="icon-box"><svg viewBox="0 0 24 24"><path d="M21 3H3v18h18V3zM12 8v8m-4-4h8"></path></svg></div>
            <div class="item-text">
                <div class="item-title">Auto Forwarding</div>
                <div class="item-subtitle">Copy messages across channels</div>
            </div>
            <span class="chip">Active</span>
        </div>
        <div class="list-item">
            <div class="icon-box"><svg viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg></div>
            <div class="item-text">
                <div class="item-title">Message Modifier</div>
                <div class="item-subtitle">Replace words, links and usernames</div>
            </div>
            <span class="chip">Active</span>
        </div>
    </div>

    <div class="section-label">Pro Features</div>
    <div class="list-group">
        <div class="list-item">
            <div class="icon-box"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg></div>
            <div class="item-text">
                <div class="item-title">AI Watermark Engine</div>
                <div class="item-subtitle">Automatically brand images</div>
            </div>
            <span class="chip">PRO</span>
        </div>
        <div class="list-item">
            <div class="icon-box"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg></div>
            <div class="item-text">
                <div class="item-title">Drip Posting</div>
                <div class="item-subtitle">Auto-post on a delayed schedule</div>
            </div>
            <span class="chip">PRO</span>
        </div>
    </div>

    <button class="primary-btn" onclick="Telegram.WebApp.close()">
        <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        Close Dashboard
    </button>
    <div class="footer">WebTGF Dashboard &bull; Version 2.0</div>

    <!-- BOTTOM NAVIGATION -->
    <div class="bottom-nav">
        <div class="nav-item active">
            <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            <span class="nav-label">Home</span>
        </div>
        <div class="nav-item">
            <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
            <span class="nav-label">Tools</span>
        </div>
        <div class="nav-item" onclick="openModal('settings')">
            <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            <span class="nav-label">Settings</span>
        </div>
    </div>



    <!-- MODAL POPUP -->
    <div class="modal-overlay" id="modal-overlay" onclick="closeModal()"></div>
    <div class="modal" id="manager-modal">
        <div class="modal-drag"></div>
        <div class="modal-header">
            <div class="modal-header-top">
                <div class="modal-title" id="modal-title">
                    <svg viewBox="0 0 24 24" id="modal-icon"><path d="M21 3H3v18h18V3zM12 8v8m-4-4h8"></path></svg>
                    Manage Channels
                </div>
                <button class="modal-close" onclick="closeModal()"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
            </div>
            <div class="modal-subtitle" id="modal-subtitle">Add or remove channels from your routing list.</div>
        </div>
        <div class="modal-body" id="modal-list">
            <div class="empty-state">Loading...</div>
        </div>
        
        <div id="modal-settings-content" style="display:none; padding: 20px; overflow-y: auto; flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--bg-color); border-radius: 12px; margin-bottom: 12px; border: 1px solid var(--border-color);">
                <div>
                    <div style="font-weight: 700; color: var(--text-main); font-size: 16px; margin-bottom: 4px;">Anti-Payment Stripper</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Deletes Banks & Crypto details</div>
                </div>
                <label class="switch">
                    <input type="checkbox" id="toggle-strip" onchange="toggleSetting('strip_payment_details', this.checked)">
                    <span class="slider"></span>
                </label>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--bg-color); border-radius: 12px; border: 1px solid var(--border-color);">
                <div>
                    <div style="font-weight: 700; color: var(--text-main); font-size: 16px; margin-bottom: 4px;">Skip Audio/Voice</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Blocks audio files & voice notes</div>
                </div>
                <label class="switch">
                    <input type="checkbox" id="toggle-voice" onchange="toggleSetting('disable_voicenotes', this.checked)">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        
        <div class="add-channel-row" id="modal-add-row">
            <input type="text" id="modal-input" class="add-input" placeholder="@channel or ID">
            <input type="text" id="modal-input-2" class="add-input" placeholder="Replace with..." style="display:none;">
            <button class="btn-add" onclick="submitModalAdd()">Add</button>
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        // Theme matching
        document.documentElement.style.setProperty('--bg-color', tg.backgroundColor || '#181818');
        
        // Set User info
        const userName = tg.initDataUnsafe?.user?.first_name || tg.initDataUnsafe?.user?.username || 'User';
        document.getElementById('user-greeting').innerText = `Hi, ${userName}!`;
        

        
        const photoUrl = tg.initDataUnsafe?.user?.photo_url;
        if (photoUrl) {
            document.getElementById('user-avatar-container').innerHTML = `<img src="${photoUrl}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
        }
        
        // Fetch Real-time status
        async function fetchStatus() {
            try {
                // If opening outside Telegram (for dev), use a dummy user
                const userId = tg.initDataUnsafe?.user?.id || '123456';
                
                const response = await fetch('/api/user_status?user_id=' + userId);
                const data = await response.json();
                
                // Update Badges
                const tierBadge = document.getElementById('tier-badge');
                tierBadge.classList.remove('skeleton', 'free', 'pro');
                if (data.is_pro || data.is_admin) {
                    tierBadge.classList.add('pro');
                    tierBadge.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 3h12l4 6-10 13L2 9z"></path><path d="M11 3l-4 6 5 13"></path><path d="M13 3l4 6-5 13"></path><path d="M2 9h20"></path></svg> PRO';
                    document.getElementById('tier-diamond').style.display = 'block';
                    document.getElementById('avatar-frame').classList.add('pro');
                } else {
                    tierBadge.classList.add('free');
                    tierBadge.innerHTML = 'FREE';
                }
                
                
                window.globalSources = data.sources || [];
                window.globalTargets = data.targets || [];
                window.globalSwaps = data.text_swaps || {};
                
                document.getElementById('stat-sources').innerText = data.sources_count;
                document.getElementById('stat-targets').innerText = data.targets_count;
                document.getElementById('stat-replacements').innerText = Object.keys(window.globalSwaps).length;
                document.getElementById('stat-replacements').classList.remove('skeleton');
                document.getElementById('stat-sources').classList.remove('skeleton');
                document.getElementById('stat-targets').classList.remove('skeleton');
                
                if(document.getElementById('toggle-strip')) document.getElementById('toggle-strip').checked = data.strip_payment_details;
                if(document.getElementById('toggle-voice')) document.getElementById('toggle-voice').checked = data.disable_voicenotes;
                
                const connBadge = document.getElementById('conn-badge');
                connBadge.classList.remove('skeleton', 'connected', 'disconnected');
                if (data.has_session) {
                    connBadge.classList.add('connected');
                    connBadge.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg> Connected';
                } else {
                    connBadge.classList.add('disconnected');
                    connBadge.innerHTML = '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Disconnected';
                }
                

                
            } catch (err) {
                console.error("Error fetching status:", err);
                document.getElementById('tier-badge').classList.remove('skeleton');
                document.getElementById('tier-badge').innerText = 'ERROR';
                document.getElementById('conn-badge').classList.remove('skeleton');
                document.getElementById('conn-badge').innerText = 'ERROR';
            }
        }
        
        
        let currentModalType = '';
        
        function openModal(type) {
            currentModalType = type;
            
            document.getElementById('modal-list').style.display = 'block';
            document.getElementById('modal-add-row').style.display = 'flex';
            if (document.getElementById('modal-settings-content')) {
                document.getElementById('modal-settings-content').style.display = 'none';
            }
            if (type === 'sources') {
                document.getElementById('modal-title').innerHTML = '<svg viewBox="0 0 24 24"><path d="M21 3H3v18h18V3zM12 8v8m-4-4h8"></path></svg> Source Channels';
                document.getElementById('modal-subtitle').innerText = 'Messages posted here will be forwarded.';
            } else if (type === 'targets') {
                document.getElementById('modal-title').innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg> Target Channels';
                document.getElementById('modal-subtitle').innerText = 'Messages will be forwarded to these groups.';
                document.getElementById('modal-input-2').style.display = 'none';
                document.getElementById('modal-input').placeholder = '@channel or ID';
            } else if (type === 'replacements') {
                document.getElementById('modal-title').innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg> Word Swaps';
                document.getElementById('modal-subtitle').innerText = 'Auto-replace words, links, and text in messages.';
                document.getElementById('modal-input').placeholder = 'Find what...';
                document.getElementById('modal-input-2').placeholder = 'Replace with...';
                document.getElementById('modal-input-2').style.display = 'block';
            } else if (type === 'settings') {
                document.getElementById('modal-title').innerHTML = '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg> Filters & Settings';
                document.getElementById('modal-subtitle').innerText = 'Configure your automated rules.';
                document.getElementById('modal-list').style.display = 'none';
                document.getElementById('modal-add-row').style.display = 'none';
                if (document.getElementById('modal-settings-content')) {
                    document.getElementById('modal-settings-content').style.display = 'block';
                }
            }
            
            document.getElementById('modal-overlay').classList.add('active');
            
            // tiny delay for animation
            setTimeout(() => {
                document.getElementById('manager-modal').classList.add('active');
            }, 10);
            
            renderModalList();
        }
        
        function closeModal() {
            document.getElementById('manager-modal').classList.remove('active');
            setTimeout(() => {
                document.getElementById('modal-overlay').classList.remove('active');
            }, 300);
        }
        
        function renderModalList() {
            const container = document.getElementById('modal-list');
            
            if (currentModalType === 'replacements') {
                const swaps = window.globalSwaps || {};
                const keys = Object.keys(swaps);
                if (keys.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon"><svg viewBox="0 0 24 24"><path d="M21 3H3v18h18V3zM12 8v8m-4-4h8"></path></svg></div>
                            <div class="empty-title">No Word Swaps</div>
                            <div>Enter a word to find and replace below.</div>
                        </div>`;
                    return;
                }
                
                container.innerHTML = keys.map(k => `
                    <div class="channel-row">
                        <div class="channel-name" style="flex:1;"><span style="color:var(--text-muted)">Find:</span> ${k}<br><span style="color:var(--text-muted)">Replace:</span> ${swaps[k]}</div>
                        <button class="btn-remove" onclick="manageSwap('remove', '${k}')">
                            <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                        </button>
                    </div>
                `).join('');
                return;
            }

            const list = currentModalType === 'sources' ? window.globalSources : window.globalTargets;
            if (!list || list.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon"><svg viewBox="0 0 24 24"><path d="M21 3H3v18h18V3zM12 8v8m-4-4h8"></path></svg></div>
                        <div class="empty-title">No ${currentModalType}</div>
                        <div>Add a channel ID or @username below to get started.</div>
                    </div>`;
                return;
            }
            
            container.innerHTML = list.map(item => `
                <div class="channel-row">
                    <div class="channel-name">${item}</div>
                    <button class="btn-remove" onclick="manageChannel('${currentModalType}', 'remove', '${item}')">
                        <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>
            `).join('');
        }
        
        function submitModalAdd() {
            const inputEl = document.getElementById('modal-input');
            const val = inputEl.value.trim();
            if(!val) return;
            
            if (currentModalType === 'replacements') {
                const inputEl2 = document.getElementById('modal-input-2');
                const val2 = inputEl2.value.trim();
                manageSwap('add', val, val2);
                inputEl.value = '';
                inputEl2.value = '';
            } else {
                manageChannel(currentModalType, 'add', val);
                inputEl.value = '';
            }
        }
        
        async function manageSwap(action, oldWord, newWord = null) {
            const userId = tg.initDataUnsafe?.user?.id || '123456';
            try {
                tg.HapticFeedback.impactOccurred('medium');
                const response = await fetch('/api/manage_swap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, action: action, old_word: oldWord, new_word: newWord })
                });
                const data = await response.json();
                if (data.success) {
                    window.globalSwaps = data.swaps;
                    document.getElementById('stat-replacements').innerText = Object.keys(data.swaps).length;
                    renderModalList();
                } else {
                    tg.showAlert(data.error || "Failed to update word swap.");
                }
            } catch (err) {
                tg.showAlert("Network error.");
            }
        }

        async function manageChannel(type, action, channelId) {
            const userId = tg.initDataUnsafe?.user?.id || '123456';
            
            try {
                tg.HapticFeedback.impactOccurred('medium');
                const response = await fetch('/api/manage_channel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        type: type,
                        action: action,
                        channel_id: channelId
                    })
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('modal-list').style.display = 'block';
            document.getElementById('modal-add-row').style.display = 'flex';
            if (document.getElementById('modal-settings-content')) {
                document.getElementById('modal-settings-content').style.display = 'none';
            }
            if (type === 'sources') {
                        window.globalSources = data.list;
                        document.getElementById('stat-sources').innerText = data.list.length;
                    } else {
                        window.globalTargets = data.list;
                        document.getElementById('stat-targets').innerText = data.list.length;
                    }
                    renderModalList();
                } else {
                    tg.showAlert(data.error || "Failed to update channel.");
                }
            } catch (err) {
                tg.showAlert("Network error.");
            }
        }
        
        
        async function toggleSetting(key, val) {
            const userId = tg.initDataUnsafe?.user?.id || '123456';
            tg.HapticFeedback.impactOccurred('light');
            try {
                await fetch('/api/toggle_setting', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, key: key, val: val })
                });
            } catch (err) {
                tg.showAlert("Failed to save setting.");
            }
        }
        
        fetchStatus();

    </script>
</body>
</html>'''

@app.route('/api/user_status', methods=['GET'])
def api_user_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
        
    try:
        user_id = int(user_id)
    except:
        return jsonify({"error": "Invalid user_id"}), 400
        
    import os
    from database_manager import get_user_data
    
    ADMIN_ID = os.getenv("ADMIN_ID", "")
    is_admin = (str(user_id) == str(ADMIN_ID))
    user_data = get_user_data(user_id)
    
    has_session = bool(user_data.get('session_string'))
    is_pro = user_data.get('is_pro', False)
    
    if is_admin:
        is_pro = True
        
    return jsonify({
        "is_admin": is_admin,
        "is_pro": is_pro,
        "has_session": has_session,
        "sources_count": len(user_data.get('sources', [])),
        "targets_count": len(user_data.get('targets', [])),
        "sources": user_data.get('sources', []),
        "targets": user_data.get('targets', []),
        "text_swaps": user_data.get('text_swaps', {}),
        "strip_payment_details": user_data.get('strip_payment_details', False),
        "disable_voicenotes": user_data.get('disable_voicenotes', False)
    })


def validate_channel_input(x):
    import re
    x = x.strip()
    if not x: return None, "Empty input"
    
    # Is it a standard numeric ID?
    if x.startswith('-100') and x[4:].isdigit():
        return x, None
    if x.lstrip('-').isdigit():
        return x, None
        
    # Is it an @username?
    if x.startswith('@') and len(x) > 3:
        return x, None
        
    # Is it a t.me link?
    if 't.me/c/' in x:
        match = re.search(r't\.me/c/(\d+)', x)
        if match:
            return f"-100{match.group(1)}", None
            
    if 't.me/' in x:
        match = re.search(r't\.me/([^/\?]+)', x)
        if match:
            username = match.group(1)
            if username in ['joinchat'] or username.startswith('+'):
                return None, "Private invite links (joinchat/+) are not supported. Please use a public @username or the numeric -100 Channel ID."
            return f"@{username}", None
            
    return None, "Invalid format. Please enter a valid @username, -100 ID, or public t.me link."

@app.route('/api/manage_channel', methods=['POST'])
def api_manage_channel():
    data = request.json
    user_id = data.get('user_id')
    channel_type = data.get('type') # 'sources' or 'targets'
    action = data.get('action') # 'add' or 'remove'
    channel_id = data.get('channel_id')
    
    if not all([user_id, channel_type, action, channel_id]):
        return jsonify({"error": "Missing params"}), 400
        
    if action == 'add':
        parsed_id, err = validate_channel_input(channel_id)
        if err:
            return jsonify({"error": err}), 400
        channel_id = parsed_id
        
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    
    if channel_type not in ['sources', 'targets']:
        return jsonify({"error": "Invalid type"}), 400
        
    current_list = user_data.get(channel_type, [])
    
    if action == 'add':
        if channel_id not in current_list:
            current_list.append(channel_id)
    elif action == 'remove':
        if channel_id in current_list:
            current_list.remove(channel_id)
            
    user_data[channel_type] = current_list
    save_user_data(user_id, user_data)
    
    return jsonify({"success": True, "list": current_list})


@app.route('/api/manage_swap', methods=['POST'])
def api_manage_swap():
    data = request.json
    user_id = data.get('user_id')
    action = data.get('action') # 'add' or 'remove'
    old_word = data.get('old_word')
    new_word = data.get('new_word')
    
    if not all([user_id, action, old_word]):
        return jsonify({"error": "Missing params"}), 400
        
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    text_swaps = user_data.get('text_swaps', {})
    
    if action == 'add':
        if not new_word:
            return jsonify({"error": "Missing replacement word"}), 400
        text_swaps[old_word] = new_word
    elif action == 'remove':
        if old_word in text_swaps:
            del text_swaps[old_word]
            
    user_data['text_swaps'] = text_swaps
    save_user_data(user_id, user_data)
    
    return jsonify({"success": True, "swaps": text_swaps})


@app.route('/api/toggle_setting', methods=['POST'])
def api_toggle_setting():
    data = request.json
    user_id = data.get('user_id')
    key = data.get('key')
    val = data.get('val')
    
    if not user_id or not key:
        return jsonify({"error": "Missing params"}), 400
        
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data[key] = bool(val)
    save_user_data(user_id, user_data)
    
    return jsonify({"success": True, "val": bool(val)})

@app.route('/miniapp')
def miniapp():
    return html_content

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


