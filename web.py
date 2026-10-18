import os
import json
from flask import Flask, request, render_template_string, redirect, session, url_for, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv, set_key
load_dotenv()

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
            <span class="font-bold text-gray-800">WP Relay</span>
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
            <h1 class="text-2xl md:text-3xl font-light text-gray-800 mb-2">WP Relay Control Center</h1>
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
                    
                    <div class="pt-6 border-t border-gray-300/50">
                        <label class="block text-sm font-bold text-gray-700 mb-2">Video Override <span class="text-xs font-normal text-gray-500">(PRO)</span></label>
                        <p class="text-xs text-gray-500 mb-3">Upload a video or provide a URL to replace any incoming videos.</p>
                        <div class="flex flex-col md:flex-row gap-4 items-center">
                            <input type="file" name="video_upload" accept="video/*" class="w-full md:w-1/2 text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-white file:text-gray-700 hover:file:bg-gray-100 cursor-pointer neumorphic-inset p-2 rounded-xl">
                            <span class="text-sm text-gray-500 font-bold hidden md:block">OR</span>
                            <input type="text" name="video_url" value="{{ json_data.get('video_swap_url', '') }}" placeholder="Paste Video URL here..." class="w-full md:w-1/2 neumorphic-inset px-4 py-3 rounded-xl outline-none text-gray-700 text-sm">
                        </div>
                        {% if json_data.get('video_swap_path') or json_data.get('video_swap_url') %}
                        <div class="bg-indigo-100/50 p-3 rounded-lg border border-indigo-200 mt-4">
                            <p class="text-xs text-indigo-700 font-bold"><i class="fa-solid fa-check-circle mr-1"></i> Custom video is currently active.</p>
                            <label class="flex items-center mt-2 text-sm text-gray-700">
                                <input type="checkbox" name="remove_video" class="mr-2 rounded"> Check this box to remove custom video.
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


<!-- Feedback Modal -->
<div id="feedbackModal" class="fixed inset-0 bg-black bg-opacity-70 hidden items-center justify-center z-50 p-4 backdrop-blur-sm transition-opacity duration-300" style="display:none;">
    <div class="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl transform transition-all">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-xl font-bold text-white flex items-center gap-2">
                    <svg class="w-7 h-7 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path>
</svg> Help Us Improve
                </h3>
                <button onclick="closeFeedbackModal()" class="text-gray-400 hover:text-white transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <p class="text-gray-300 text-sm mb-6">What feature should we build next?</p>
            <textarea id="feedbackText" rows="4" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder-gray-500"></textarea>
            <button onclick="submitFeedback(this)" class="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl py-3 font-semibold shadow-lg hover:from-blue-500 hover:to-purple-500 transition-all flex items-center justify-center gap-2">
                <span>Send to Developer</span>
            </button>
        </div>
    </div>
</div>
\n<script>\n
const shouldPopupFeedback = {{ 'true' if (json_data is defined and json_data.get('should_popup_feedback')) else 'false' }};

document.addEventListener('DOMContentLoaded', function() {
    if (shouldPopupFeedback && !sessionStorage.getItem('feedbackClosed')) {
        setTimeout(() => {
            const m = document.getElementById('feedbackModal');
            if(m) { m.classList.remove('hidden'); m.style.display = 'flex'; }
        }, 1500);
    }
});

function closeFeedbackModal() {
    const m = document.getElementById('feedbackModal');
    if(m) { m.classList.add('hidden'); m.style.display = 'none'; }
    sessionStorage.setItem('feedbackClosed', 'true');
}

async function submitFeedback(btn) {
    const text = document.getElementById('feedbackText').value.trim();
    if (!text) return;
    
    const originalContent = btn.innerHTML;
    btn.innerHTML = 'Sending...';
    
    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        });
        
        btn.innerHTML = 'Sent!';
        setTimeout(() => { closeFeedbackModal(); }, 1000);
    } catch(e) {
        btn.innerHTML = originalContent;
        alert('Failed to send.');
    }
}
\n</script>\n</body>
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
        
    from database_manager import get_user_data, get_tenants, get_stats, save_user_data
    user_data = get_user_data(chat_id) if chat_id else {}
    
    if chat_id:
        submitted = user_data.get("feedback_submitted_count", 0)
        user_data["should_popup_feedback"] = (submitted < 3)
    
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

MINIAPP_HTML_PATH = os.path.join(os.path.dirname(__file__), 'miniapp_template.html')

def get_miniapp_html():
    if os.path.exists(MINIAPP_HTML_PATH):
        with open(MINIAPP_HTML_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Mini App Template Missing</h1>"

# --- AUTHENTICATION & SECURITY VAULT GUARDS ---

import hmac
import hashlib
from urllib.parse import parse_qsl

def verify_telegram_init_data(init_data_str):
    bot_token = os.getenv("BOT_TOKEN")
    if not init_data_str or not bot_token:
        return None
    try:
        parsed_data = dict(parse_qsl(init_data_str, keep_blank_values=True))
        if 'hash' not in parsed_data:
            return None
        received_hash = parsed_data.pop('hash')
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
        if hmac.compare_digest(calc_hash, received_hash):
            user_json = parsed_data.get('user')
            if user_json:
                u = json.loads(user_json)
                return str(u.get('id'))
            return parsed_data.get('query_id')
        return None
    except Exception as e:
        print(f"initData verification error: {e}")
        return None

def make_studio_token(user_id):
    secret = (app.secret_key or "super_secret_key_for_session").encode('utf-8')
    sig = hmac.new(secret, str(user_id).encode('utf-8'), hashlib.sha256).hexdigest()[:24]
    return f"{user_id}:{sig}"

def verify_studio_token(token):
    if not token or ':' not in token:
        return None
    try:
        user_id, sig = token.split(':', 1)
        expected = make_studio_token(user_id)
        if hmac.compare_digest(token, expected):
            return str(user_id)
    except:
        pass
    return None

def get_authenticated_user():
    # 1. Telegram Init Data (Header or query/body param)
    init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('init_data')
    if not init_data and request.is_json:
        init_data = (request.json or {}).get('init_data')
    if init_data:
        tg_user_id = verify_telegram_init_data(init_data)
        if tg_user_id:
            return str(tg_user_id)

    # 2. Studio Token (Header or query/body param)
    token = request.headers.get('X-Studio-Token') or request.args.get('token')
    if not token and request.is_json:
        token = (request.json or {}).get('token')
    if token:
        token_user_id = verify_studio_token(token)
        if token_user_id:
            return str(token_user_id)

    # 3. Flask Session
    if session.get('logged_in') and session.get('chat_id'):
        return str(session.get('chat_id'))
    if session.get('miniapp_user'):
        return str(session.get('miniapp_user'))

    return None

def check_permission(target_user_id):
    auth_user = get_authenticated_user()
    if not auth_user:
        return None, (jsonify({"error": "Unauthorized. Studio is locked.", "locked": True}), 401)
    
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    is_admin = (auth_user == admin_id)
    
    if target_user_id:
        target_str = str(target_user_id)
        if not is_admin and auth_user != target_str:
            return None, (jsonify({"error": "Forbidden: You cannot access or modify another tenant's account.", "locked": False}), 403)
        return target_str, None
            
    return auth_user, None

@app.route('/api/auth_check', methods=['POST'])
def api_auth_check():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user:
        return jsonify({
            "authenticated": True,
            "user_id": auth_user,
            "is_admin": (auth_user == admin_id),
            "token": make_studio_token(auth_user)
        })
    return jsonify({"authenticated": False, "locked": True}), 401

@app.route('/api/unlock_studio', methods=['POST'])
def api_unlock_studio():
    data = request.json or {}
    passcode = str(data.get('passcode', '')).strip()
    target_user_id = str(data.get('user_id', '')).strip()
    
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    from database_manager import get_tenants, get_user_data
    
    # 1. Check Master Admin verification
    admin_data = get_user_data(admin_id)
    admin_pins = [admin_id, "admin"]
    if admin_data.get('deletion_pin'):
        admin_pins.append(str(admin_data.get('deletion_pin')))
    if os.getenv("ADMIN_PIN"):
        admin_pins.append(str(os.getenv("ADMIN_PIN")))
        
    if passcode in admin_pins:
        resolved_user = target_user_id if target_user_id else admin_id
        session['chat_id'] = admin_id
        session['miniapp_user'] = admin_id
        session['logged_in'] = True
        return jsonify({
            "success": True, 
            "token": make_studio_token(admin_id), 
            "user_id": resolved_user, 
            "is_admin": True,
            "message": "Admin authenticated"
        })
        
    # 2. Check if passcode matches a registered Tenant ID directly
    tenants = [str(t) for t in get_tenants()]
    if passcode in tenants:
        session['chat_id'] = passcode
        session['miniapp_user'] = passcode
        session['logged_in'] = True
        return jsonify({
            "success": True, 
            "token": make_studio_token(passcode), 
            "user_id": passcode, 
            "is_admin": False,
            "message": "Tenant authenticated"
        })
        
    # 3. Check if passcode matches a tenant's security deletion_pin
    if target_user_id and target_user_id in tenants:
        ud = get_user_data(target_user_id)
        if ud.get('deletion_pin') and str(ud.get('deletion_pin')) == passcode:
            session['chat_id'] = target_user_id
            session['miniapp_user'] = target_user_id
            session['logged_in'] = True
            return jsonify({
                "success": True, 
                "token": make_studio_token(target_user_id), 
                "user_id": target_user_id, 
                "is_admin": False,
                "message": "Tenant PIN authenticated"
            })
            
    return jsonify({"error": "Invalid Passcode or PIN. Access denied."}), 401

@app.route('/api/lock_studio', methods=['POST'])
def api_lock_studio():
    session.pop('miniapp_user', None)
    return jsonify({"success": True, "locked": True})

@app.route('/api/admin_overview', methods=['GET'])
def api_admin_overview():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    from database_manager import get_tenants, get_stats, get_all_users, get_user_data, get_feature_toggles
    tenants = get_tenants()
    stats = get_stats()
    toggles = get_feature_toggles()

    tenant_details = []
    pro_count = 0
    for t in tenants:
        ud = get_user_data(t)
        is_p = ud.get('is_pro', False) or (str(t) == admin_id)
        if is_p:
            pro_count += 1
        tenant_details.append({
            "tenant_id": str(t),
            "is_pro": is_p,
            "sources_count": len(ud.get('sources', [])),
            "targets_count": len(ud.get('targets', [])),
            "swaps_count": len(ud.get('text_swaps', {})),
            "is_active": ud.get('is_active', False),
            "has_session": bool(ud.get('session_string'))
        })

    free_count = len(tenants) - pro_count

    return jsonify({
        "success": True,
        "is_admin": True,
        "stats": stats,
        "tenants": tenant_details,
        "total_tenants": len(tenants),
        "pro_count": pro_count,
        "free_count": free_count,
        "toggles": toggles,
        "api_id": os.getenv("API_ID", ""),
        "api_hash": os.getenv("API_HASH", ""),
        "has_session": bool(os.getenv("SESSION_STRING")),
        "bot_token_configured": bool(os.getenv("BOT_TOKEN")),
        "bot_token_preview": (os.getenv("BOT_TOKEN")[:10] + "...") if os.getenv("BOT_TOKEN") else "",
        "total_users_in_db": len(get_all_users())
    })

@app.route('/api/admin_manage_tenant', methods=['POST'])
def api_admin_manage_tenant():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    action = data.get('action')
    tenant_id = str(data.get('tenant_id', '')).strip()

    if not tenant_id or action not in ['add', 'remove', 'toggle_pro']:
        return jsonify({"error": "Invalid action or tenant ID"}), 400

    from database_manager import get_tenants, save_tenants, get_user_data, save_user_data
    tenants = [str(t) for t in get_tenants()]

    if action == 'add':
        if tenant_id not in tenants:
            tenants.append(tenant_id)
            save_tenants(tenants)
            # Try to notify new tenant via bot
            bot_token = os.getenv('BOT_TOKEN')
            if bot_token:
                try:
                    import requests
                    requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": tenant_id, "text": "Account Activated!\nThe Administrator has granted you access to the forwarder platform."},
                        timeout=5
                    )
                except: pass
    elif action == 'remove':
        if tenant_id in tenants:
            tenants.remove(tenant_id)
            save_tenants(tenants)
    elif action == 'toggle_pro':
        ud = get_user_data(tenant_id)
        current_pro = ud.get('is_pro', False)
        ud['is_pro'] = not current_pro
        save_user_data(tenant_id, ud)
        return jsonify({"success": True, "tenant_id": tenant_id, "is_pro": ud['is_pro']})

    return jsonify({"success": True, "tenants": tenants})

@app.route('/api/admin_toggle_feature', methods=['POST'])
def api_admin_toggle_feature():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    feature = data.get('feature')
    val = bool(data.get('value', False))
    if not feature:
        return jsonify({"error": "Missing feature name"}), 400

    from database_manager import get_feature_toggles, save_feature_toggles
    toggles = get_feature_toggles() or {}
    toggles[feature] = val
    save_feature_toggles(toggles)
    return jsonify({"success": True, "toggles": toggles})

@app.route('/api/admin_broadcast', methods=['POST'])
def api_admin_broadcast():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    msg_text = str(data.get('message', '')).strip()
    btn_text = str(data.get('button_text', '')).strip()
    btn_url = str(data.get('button_url', '')).strip()

    if not msg_text:
        return jsonify({"error": "Message cannot be empty"}), 400

    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        return jsonify({"error": "BOT_TOKEN not configured"}), 500

    from database_manager import get_tenants
    tenants = get_tenants()
    import requests, time

    payload_base = {
        "text": msg_text,
        "parse_mode": "HTML"
    }

    if btn_text and btn_url:
        if not btn_url.startswith(('http://', 'https://', 't.me/')):
            btn_url = 'https://' + btn_url
        payload_base["reply_markup"] = {
            "inline_keyboard": [
                [{"text": btn_text, "url": btn_url}]
            ]
        }

    sent = 0
    for t in tenants:
        try:
            p = {**payload_base, "chat_id": t}
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json=p,
                timeout=8
            )
            if r.status_code == 200:
                sent += 1
            time.sleep(0.05)
        except:
            pass

    return jsonify({"success": True, "sent": sent, "total": len(tenants)})

@app.route('/api/admin_ai_generate_broadcast', methods=['POST'])
def api_admin_ai_generate_broadcast():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    user_prompt = str(data.get('prompt', '')).strip()
    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        return jsonify({"error": "GEMINI_API_KEY not found in environment"}), 500

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        prompt = (
            f"You are an expert community manager for a Telegram channel forwarder bot. "
            f"Write an engaging, professional broadcast announcement based on these instructions: {user_prompt}. "
            f"Format with clean paragraphs and bullet points. Output ONLY the announcement text itself. "
            f"Do not include intro or outro commentary."
        )

        models_to_try = ['gemini-2.5-flash', 'gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-1.5-flash']
        generated_text = None
        last_err = None

        for m in models_to_try:
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                if resp and resp.text:
                    generated_text = resp.text.strip()
                    break
            except Exception as e:
                last_err = e

        if not generated_text:
            return jsonify({"error": f"AI generation failed: {last_err}"}), 500

        return jsonify({"success": True, "generated_message": generated_text})
    except Exception as e:
        return jsonify({"error": f"AI generator error: {e}"}), 500

@app.route('/api/admin_update_api_config', methods=['POST'])
def api_admin_update_api_config():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    api_id = str(data.get('api_id', '')).strip()
    api_hash = str(data.get('api_hash', '')).strip()
    session_string = str(data.get('session_string', '')).strip()
    bot_token = str(data.get('bot_token', '')).strip()

    if api_id:
        os.environ['API_ID'] = api_id
        set_key(ENV_FILE, 'API_ID', api_id)
    if api_hash:
        os.environ['API_HASH'] = api_hash
        set_key(ENV_FILE, 'API_HASH', api_hash)
    if session_string:
        os.environ['SESSION_STRING'] = session_string
        set_key(ENV_FILE, 'SESSION_STRING', session_string)
    if bot_token:
        os.environ['BOT_TOKEN'] = bot_token
        set_key(ENV_FILE, 'BOT_TOKEN', bot_token)

    return jsonify({"success": True})

@app.route('/api/admin_test_bot_token', methods=['POST'])
def api_admin_test_bot_token():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    candidate_token = str(data.get('bot_token', '')).strip() or os.getenv('BOT_TOKEN', '').strip()
    if not candidate_token:
        return jsonify({"success": False, "error": "No bot token provided"}), 400

    try:
        import requests
        r = requests.get(f"https://api.telegram.org/bot{candidate_token}/getMe", timeout=8)
        d = r.json()
        if d.get("ok"):
            res = d.get("result", {})
            return jsonify({
                "success": True,
                "valid": True,
                "bot_id": res.get("id"),
                "username": res.get("username"),
                "first_name": res.get("first_name")
            })
        else:
            return jsonify({
                "success": False,
                "valid": False,
                "error": d.get("description", "Unauthorized")
            })
    except Exception as e:
        return jsonify({"success": False, "valid": False, "error": str(e)})

@app.route('/api/admin_channel_info', methods=['GET'])
def api_admin_channel_info():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    import channel_engine
    bot_st = channel_engine.get_bot_status()
    auto_cfg = channel_engine.get_autopilot_config()
    return jsonify({
        "success": True,
        "bot_status": bot_st,
        "autopilot": auto_cfg,
        "categories": channel_engine.TOPIC_CATEGORIES,
        "default_channel": channel_engine.DEFAULT_CHANNEL,
        "bot_username": channel_engine.DEFAULT_BOT_USERNAME
    })

@app.route('/api/admin_channel_generate', methods=['POST'])
def api_admin_channel_generate():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    category = str(data.get('category', '')).strip() or None
    prompt = str(data.get('custom_prompt', '')).strip() or None

    try:
        import channel_engine
        res = channel_engine.generate_channel_post(category_id=category, custom_prompt=prompt)
        return jsonify({
            "success": True,
            "text": res["text"],
            "buttons": res["buttons"],
            "model_used": res["model_used"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin_channel_post', methods=['POST'])
def api_admin_channel_post():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    msg_text = str(data.get('message', '')).strip()
    if not msg_text:
        return jsonify({"error": "Message text cannot be empty"}), 400

    target_channel = str(data.get('channel', '@webtgfv1')).strip() or '@webtgfv1'
    buttons = data.get('buttons', [])
    pin = bool(data.get('pin', False))
    silent = bool(data.get('disable_notification', False))

    try:
        import channel_engine
        res = channel_engine.publish_to_channel(
            text=msg_text,
            buttons=buttons,
            pin=pin,
            target_channel=target_channel,
            disable_notification=silent
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin_channel_autopilot', methods=['POST'])
def api_admin_channel_autopilot():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    import channel_engine
    cfg = channel_engine.get_autopilot_config()

    if 'enabled' in data:
        cfg['enabled'] = bool(data['enabled'])
    if 'frequency_hours' in data:
        try:
            cfg['frequency_hours'] = max(1, int(data['frequency_hours']))
        except Exception:
            pass

    channel_engine.save_autopilot_config(cfg)
    return jsonify({"success": True, "autopilot": cfg})

@app.route('/api/admin_channel_autopilot_trigger', methods=['POST'])
def api_admin_channel_autopilot_trigger():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    import channel_engine, time
    try:
        cfg = channel_engine.get_autopilot_config()
        idx = cfg.get("topic_index", 0) % len(channel_engine.TOPIC_CATEGORIES)
        category = channel_engine.TOPIC_CATEGORIES[idx]

        post_data = channel_engine.generate_channel_post(category_id=category["id"])
        should_pin = category["id"] in ["anti_ban", "pro_features"]
        result = channel_engine.publish_to_channel(
            text=post_data["text"],
            buttons=post_data["buttons"],
            pin=should_pin,
            target_channel=channel_engine.DEFAULT_CHANNEL
        )
        cfg["topic_index"] = (idx + 1) % len(channel_engine.TOPIC_CATEGORIES)
        cfg["last_posted_at"] = int(time.time())
        channel_engine.save_autopilot_config(cfg)
        return jsonify({"success": True, "result": result, "category": category["title"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin_channel_delete_post', methods=['POST'])
def api_admin_channel_delete_post():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.json or {}
    message_id = data.get('message_id')
    channel = data.get('channel', '@webtgfv1')
    if not message_id:
        return jsonify({"error": "Missing message_id"}), 400

    try:
        import channel_engine
        res = channel_engine.delete_channel_message(message_id, target_channel=channel)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin_logs', methods=['GET'])
def api_admin_logs():
    auth_user = get_authenticated_user()
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if auth_user != admin_id:
        return jsonify({"error": "Admin privileges required"}), 403

    logs = []
    log_file = 'forwarder.log'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                logs = [l.strip() for l in lines[-60:] if l.strip()]
        except Exception as e:
            logs = [f"Error reading log file: {e}"]
    else:
        logs = ["Log file does not exist yet."]

    return jsonify({"success": True, "logs": logs})

def check_feature_access(user_id, feature_key=None, requires_pro=True):
    ADMIN_ID = str(os.getenv("ADMIN_ID", "5628105961"))
    if str(user_id) == ADMIN_ID:
        return None
    from database_manager import get_user_data, get_feature_toggles
    user_data = get_user_data(user_id)
    is_pro = user_data.get('is_pro', False)
    toggles = get_feature_toggles() or {}

    # 1. Check Admin Lock Toggle
    if feature_key:
        if feature_key in ['cta_buttons_unlocked', 'video_swap_unlocked']:
            is_unlocked = toggles.get(feature_key, True)
        else:
            is_unlocked = toggles.get(feature_key, False)
        if not is_unlocked:
            return jsonify({"error": "This feature is currently locked by the Admin."}), 403

    # 2. Check PRO requirement
    if requires_pro and not is_pro:
        return jsonify({"error": "This is a PRO feature. Contact administrator @apklord55 to upgrade."}), 403

    return None

# --- SYNCHRONIZED NATIVE BOT BACKEND API ROUTES ---

@app.route('/api/user_status', methods=['GET'])
def api_user_status():
    requested_user = request.args.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err
        
    try:
        user_id = int(user_id)
    except:
        return jsonify({"error": "Invalid user_id"}), 400
        
    ADMIN_ID = os.getenv("ADMIN_ID", "")
    is_admin = (str(user_id) == str(ADMIN_ID))
    from database_manager import get_user_data, get_feature_toggles
    user_data = get_user_data(user_id)
    toggles = get_feature_toggles() or {}
    
    has_session = bool(user_data.get('session_string'))
    is_pro = user_data.get('is_pro', False)
    if is_admin:
        is_pro = True
        
    submitted = user_data.get("feedback_submitted_count", 0)
    should_popup = (submitted < 3)
        
    return jsonify({
        "is_admin": is_admin,
        "should_popup_feedback": should_popup,
        "is_pro": is_pro,
        "has_session": has_session,
        "feature_toggles": toggles,
        "sources_count": len(user_data.get('sources', [])),
        "targets_count": len(user_data.get('targets', [])),
        "sources": user_data.get('sources', []),
        "targets": user_data.get('targets', []),
        "text_swaps": user_data.get('text_swaps', {}),
        "replace_all_links_with": user_data.get('replace_all_links_with', ''),
        "exclude_link_keywords": user_data.get('exclude_link_keywords', ''),
        "replace_all_usernames_with": user_data.get('replace_all_usernames_with', ''),
        "image_override_enabled": user_data.get('image_override_enabled', True),
        "image_swap_url": user_data.get('image_swap_url', ''),
        "video_override_enabled": user_data.get('video_override_enabled', True),
        "video_swap_url": user_data.get('video_swap_url', ''),
        "ai_watermark_mode": user_data.get('ai_watermark_mode', 'off'),
        "ai_watermark_target": user_data.get('ai_watermark_target', ''),
        "ai_watermark_replace": user_data.get('ai_watermark_replace', ''),
        "cta_buttons": user_data.get('cta_buttons', []),
        "smart_delay_enabled": user_data.get('smart_delay_enabled', False),
        "drip_interval": user_data.get('drip_interval', 0),
        "sleep_mode": user_data.get('sleep_mode', {"enabled": False, "start_time": "22:00", "end_time": "08:00", "timezone_offset": 0}),
        "mirror_delete": user_data.get('mirror_delete', False),
        "auto_delete_limit": user_data.get('auto_delete_limit', 0),
        "strip_payment_details": user_data.get('strip_payment_details', False),
        "disable_voicenotes": user_data.get('disable_voicenotes', False)
    })

def validate_channel_input(x):
    import re
    x = x.strip()
    if not x: return None, "Empty input"
    if x.startswith('-100') and x[4:].isdigit(): return x, None
    if x.lstrip('-').isdigit(): return x, None
    if x.startswith('@') and len(x) > 3: return x, None
    if 't.me/c/' in x:
        m = re.search(r't\.me/c/(\d+)', x)
        if m: return f"-100{m.group(1)}", None
    if 't.me/' in x:
        m = re.search(r't\.me/([^/\?]+)', x)
        if m:
            u = m.group(1)
            if u in ['joinchat'] or u.startswith('+'):
                return None, "Private invite links (joinchat/+) are not supported. Use a public @username or numeric -100 ID."
            return f"@{u}", None
    return None, "Invalid format. Enter a valid @username or -100 ID."

@app.route('/api/manage_channel', methods=['POST'])
def api_manage_channel():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    channel_type = data.get('type')
    action = data.get('action')
    channel_id = data.get('channel_id')
    if not all([channel_type, action, channel_id]):
        return jsonify({"error": "Missing params"}), 400
    if action == 'add':
        parsed_id, err = validate_channel_input(channel_id)
        if err: return jsonify({"error": err}), 400
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
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    action = data.get('action')
    old_word = data.get('old_word')
    new_word = data.get('new_word')
    if not all([action, old_word]):
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
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    key = data.get('key')
    val = data.get('val')
    if not key:
        return jsonify({"error": "Missing key"}), 400

    if key == 'mirror_delete' and val:
        lock_err = check_feature_access(user_id, 'deletion_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data[key] = bool(val)
    save_user_data(user_id, user_data)
    return jsonify({"success": True, "val": bool(val)})

@app.route('/api/save_branding', methods=['POST'])
def api_save_branding():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data['replace_all_links_with'] = data.get('global_link', '').strip()
    user_data['exclude_link_keywords'] = data.get('exclude_keywords', '').strip()
    user_data['replace_all_usernames_with'] = data.get('global_username', '').strip()
    save_user_data(user_id, user_data)
    return jsonify({"success": True})

@app.route('/api/manage_cta', methods=['POST'])
def api_manage_cta():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    lock_err = check_feature_access(user_id, 'cta_buttons_unlocked', requires_pro=True)
    if lock_err:
        return lock_err

    action = data.get('action')
    if not action:
        return jsonify({"error": "Missing action"}), 400
    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    btns = user_data.get('cta_buttons', [])
    if action == 'add':
        btn_text = data.get('text', '').strip()
        btn_url = data.get('url', '').strip()
        if not btn_text or not btn_url:
            return jsonify({"error": "Missing text or url"}), 400
        if not btn_url.startswith(('http://', 'https://', 't.me/')):
            btn_url = 'https://' + btn_url
        btns.append({"text": btn_text, "url": btn_url})
    elif action == 'remove':
        idx = data.get('index')
        if idx is not None and 0 <= idx < len(btns):
            btns.pop(idx)
    elif action == 'clear':
        btns = []
    user_data['cta_buttons'] = btns
    save_user_data(user_id, user_data)
    return jsonify({"success": True, "cta_buttons": btns})

@app.route('/api/save_media_url', methods=['POST'])
def api_save_media_url():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    m_type = data.get('type')
    url = data.get('url', '').strip()
    if not m_type:
        return jsonify({"error": "Missing type"}), 400

    if m_type == 'video':
        lock_err = check_feature_access(user_id, 'video_swap_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    if m_type == 'image':
        user_data['image_swap_url'] = url
        user_data['image_swap_path'] = ''
    elif m_type == 'video':
        user_data['video_swap_url'] = url
        user_data['video_swap_path'] = ''
    save_user_data(user_id, user_data)
    return jsonify({"success": True})

@app.route('/api/save_watermark', methods=['POST'])
def api_save_watermark():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    if data.get('mode') and data.get('mode') != 'off':
        lock_err = check_feature_access(user_id, 'ai_watermark_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data['ai_watermark_mode'] = data.get('mode', 'off')
    user_data['ai_watermark_target'] = data.get('target', '').strip()
    user_data['ai_watermark_replace'] = data.get('replace', '').strip()
    save_user_data(user_id, user_data)
    return jsonify({"success": True})

@app.route('/api/set_drip', methods=['POST'])
def api_set_drip():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    interval = data.get('interval', 0)
    if int(interval) > 0:
        lock_err = check_feature_access(user_id, 'drip_posting_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data['drip_interval'] = int(interval)
    if int(interval) == 0:
        user_data['drip_queue'] = []
    save_user_data(user_id, user_data)
    return jsonify({"success": True, "interval": int(interval)})

@app.route('/api/save_sleep_mode', methods=['POST'])
def api_save_sleep_mode():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    if data.get('enabled'):
        lock_err = check_feature_access(user_id, 'sleep_mode_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data['sleep_mode'] = {
        "enabled": bool(data.get('enabled', False)),
        "start_time": data.get('start_time', '22:00'),
        "end_time": data.get('end_time', '08:00'),
        "timezone_offset": float(data.get('timezone_offset', 0))
    }
    save_user_data(user_id, user_data)
    return jsonify({"success": True})

@app.route('/api/save_auto_delete', methods=['POST'])
def api_save_auto_delete():
    data = request.json or {}
    requested_user = data.get('user_id')
    user_id, err = check_permission(requested_user)
    if err:
        return err

    limit = data.get('limit', 0)
    if int(limit) > 0:
        lock_err = check_feature_access(user_id, 'deletion_unlocked', requires_pro=True)
        if lock_err:
            return lock_err

    from database_manager import get_user_data, save_user_data
    user_data = get_user_data(user_id)
    user_data['auto_delete_limit'] = int(limit)
    save_user_data(user_id, user_data)
    return jsonify({"success": True, "limit": int(limit)})

@app.route('/miniapp')
def miniapp():
    # Only resolve server user ID if caller is already authenticated
    auth_user = get_authenticated_user() or ""
    html = get_miniapp_html()
    html = html.replace('let SERVER_USER_ID = "";', f'let SERVER_USER_ID = "{auth_user}";')
    return html

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json or {}
    requested_user = data.get('user_id')
    chat_id, err = check_permission(requested_user)
    if err:
        return err

    text = data.get('text', '')
    if text and chat_id:
        from database_manager import get_user_data, save_user_data
        ud = get_user_data(chat_id)
        submitted = ud.get('feedback_submitted_count', 0)
        ud['feedback_submitted_count'] = submitted + 1
        save_user_data(chat_id, ud)
        import requests, os
        admin_id = os.getenv('ADMIN_ID')
        bot_token = os.getenv('BOT_TOKEN')
        if admin_id and bot_token:
            url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
            payload = {'chat_id': admin_id, 'text': f'Feature Request!\n\nFrom: {chat_id}\n\nMessage:\n{text}'}
            try: requests.post(url, json=payload, timeout=15)
            except: pass
    return jsonify({'success': True})

def start_autopilot_worker():
    # If running under Werkzeug reloader, only run in the main child process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        return

    def loop():
        import time
        time.sleep(30)  # initial delay after startup to let server settle
        while True:
            try:
                import channel_engine
                channel_engine.run_autopilot_tick()
            except Exception as e:
                print(f"[AUTOPILOT WORKER ERROR] {e}")
            time.sleep(300) # check every 5 minutes

    import threading
    t = threading.Thread(target=loop, daemon=True)
    t.start()

start_autopilot_worker()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

