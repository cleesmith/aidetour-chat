from nicegui import app, ui, events
import sys
import json
import base64
from collections import defaultdict
from icecream import ic
from cryptography.fernet import Fernet

ic.configureOutput(includeContext=True, contextAbsPath=True)

# this should be used only once outside of the app, then
# used as the storage_secret and to encrypt/decrypt 'browser session cookie'
# key = Fernet.generate_key()
# ic(key)

# similar to novelcrafter, all settings must go in a 'browser session cookie' 
# note: users of the same browser on the same device get the same cookie,
#       without auth/signin coding.
# 
# see: https://nicegui.io/documentation/storage#storage
# app.storage.browser: 
# Unlike the previous types, this dictionary is stored directly as the 
# browser session cookie, shared among all browser tabs for the same user. 
# However, app.storage.user is generally preferred due to its advantages in reducing 
# data payload, enhancing security, and offering larger storage capacity. 
# By default, NiceGUI holds a unique identifier for the browser session in 
# app.storage.browser['id']. This storage is only available within 
# page builder functions and requires the storage_secret parameter in ui.run() 
# to sign the browser session cookie.

APP_SETTINGS = {
    'host': '127.0.0.1',
    'port': 8000,
    'dark_mode': True
}

PROVIDER_SETTINGS = [
    {"name": "Anthropic", "settings": {"api_key": "", "max_tokens": 4096, "timeout": 30}},
    {"name": "Google", "settings": {"api_key": "", "timeout": 30}},
    {"name": "Groq", "settings": {"api_key": "", "timeout": 30}},
    {"name": "LMStudio", "settings": {"api_key": "", "base_url": "http://localhost:5506/v1", "timeout": 30}},
    {"name": "Ollama", "settings": {"api_key": "", "base_url": "http://localhost:11434", "timeout": 30}},
    {"name": "OpenAI", "settings": {"api_key": "", "timeout": 30}},
    {"name": "OpenRouter", "settings": {"api_key": "", "base_url": "https://openrouter.ai/api/v1", "timeout": 30}},
    {"name": "Perplexity", "settings": {"api_key": "", "base_url": "https://api.perplexity.ai", "timeout": 30}},
]

@ui.page('/', response_timeout=999)
async def _main_page() -> None:
    global APP_SETTINGS, PROVIDER_SETTINGS

    def initialize_default_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app.storage.browser['APP_SETTINGS'] = APP_SETTINGS
        app.storage.browser['PROVIDER_SETTINGS'] = PROVIDER_SETTINGS

    def read_settings_from_storage():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app_settings = app.storage.browser.get('APP_SETTINGS', None)
        provider_settings = app.storage.browser.get('PROVIDER_SETTINGS', None)
        if app_settings is None or provider_settings is None:
            return False
        APP_SETTINGS = app.storage.browser.get('APP_SETTINGS')
        PROVIDER_SETTINGS = app.storage.browser.get('PROVIDER_SETTINGS')
        return True

    def get_app_setting(key):
        global APP_SETTINGS
        ic(key, APP_SETTINGS)
        value = APP_SETTINGS[key]
        return value

    def set_app_setting(key, value):
        global APP_SETTINGS
        ic(key, value)
        APP_SETTINGS[key] = value
        app.storage.browser['APP_SETTINGS'] = APP_SETTINGS

    def get_provider_setting(provider_name, key):
        global PROVIDER_SETTINGS
        ic(provider_name, key)
        for provider in PROVIDER_SETTINGS:
            ic(provider, provider["name"])
            if provider["name"] == provider_name:
                value = provider["settings"][key]
                return value
        return None

    def set_provider_setting(provider_name, key, value):
        global PROVIDER_SETTINGS
        for provider in PROVIDER_SETTINGS:
            if provider["name"] == provider_name:
                provider["settings"][key] = value
                break
        app.storage.browser['PROVIDER_SETTINGS'] = PROVIDER_SETTINGS
        ic(PROVIDER_SETTINGS)

    def download_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        settings = {
            'app_settings': APP_SETTINGS,
            'provider_settings': PROVIDER_SETTINGS
        }
        content = json.dumps(settings)
        ui.download(content.encode('utf-8'), 'clsSettings.json')
        # b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        # ui.run_javascript(f"""
        #     const content = atob("{b64_content}");
        #     const blob = new Blob([content], {{type: 'application/json'}});
        #     const url = URL.createObjectURL(blob);
        #     const a = document.createElement('a');
        #     a.href = url;
        #     a.download = 'settings.json';
        #     document.body.appendChild(a);
        #     a.click();
        #     document.body.removeChild(a);
        #     URL.revokeObjectURL(url);
        # """)

    def upload_settings(e: events.UploadEventArguments):
        global APP_SETTINGS, PROVIDER_SETTINGS
        text = e.content.read().decode('utf-8')
        settings = json.loads(text)
        ic(settings)
        if 'app_settings' in settings:
            app_settings = settings['app_settings']
            for key, value in app_settings.items():
                set_app_setting(key, value)
        if 'provider_settings' in settings:
            provider_settings = settings['provider_settings']
            for name, provider in provider_settings.items():
                for key, value in provider.items():
                    set_provider_setting(name, key, value)
        content.set_content(text)
        dialog.open()

    ic(app.storage.browser['id'])
    ic(type(app.storage.browser))
    ic(app.storage.browser)

    # empty/clear browser session cookie:
    # app.storage.browser.pop('app_settings', None)
    # app.storage.browser.pop('provider_settings', None)
    # app.storage.browser.pop('APP_SETTINGS', None)
    # app.storage.browser.pop('PROVIDER_SETTINGS', None)

    found = read_settings_from_storage()
    ic('read_settings_from_storage', found)
    # ic(APP_SETTINGS, PROVIDER_SETTINGS)
    ic(app.storage.browser)

    if not found:
        initialize_default_settings()
        ic(app.storage.browser)

    # set_provider_setting('OpenRouter', 'timeout', 999)
    # ic(app.storage.browser)

    or_timeout = get_provider_setting('OpenRouter', 'timeout')
    ic(or_timeout)
    h = get_app_setting('host')
    ic(h)

    # gui/ui
    ui.button('Download Settings', on_click=download_settings)
    ui.upload(on_upload=upload_settings).props('accept=.json').classes('max-w-full')
    log = ui.log(max_lines=1500).classes('w-full h-full')

    # ias = ic(APP_SETTINGS)
    # log.push(ias)
    app_settings_str = json.dumps(APP_SETTINGS, indent=2) # readable
    log.push("APP_SETTINGS:")
    log.push(app_settings_str)
    log.push(" ")
    provider_settings_str = json.dumps(PROVIDER_SETTINGS, indent=2)
    log.push("PROVIDER_SETTINGS:")
    log.push(provider_settings_str)

if __name__ == '__main__':
    ui.run(
        host="127.0.0.1",
        port=8010,
        title="AidetourChat",
        reload=False,
        show_welcome_message=False,
        show=True,
        dark=True,
        storage_secret='clsxxx',
    )


# from nicegui import app
# encrypt/decrypt browser session cookie data:
# from cryptography.fernet import Fernet

# # generate a key (should be done only once, and store it securely outside of the app!)
# key = Fernet.generate_key()
# cipher_suite = Fernet(key)

# # encrypt the data before storing it
# app_setting = "spud!"
# encrypted_data = cipher_suite.encrypt(app_setting.encode()).decode()

# # store the encrypted data in the browser
# app.storage.browser['app_settings'] = encrypted_data

# # later on, retrieve and decrypt the data
# encrypted_data = app.storage.browser['app_settings']
# decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()

# # use the decrypted data
# print(decrypted_data)  # Outputs: spud!


