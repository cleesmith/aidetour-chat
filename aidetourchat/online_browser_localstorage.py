from nicegui import app, ui, events
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
    {"name": "Anthropic", "defaults": {"api_key": "", "max_tokens": 4096, "timeout": 30}},
    {"name": "Google", "defaults": {"api_key": "", "timeout": 30}},
    {"name": "Groq", "defaults": {"api_key": "", "timeout": 30}},
    {"name": "LMStudio", "defaults": {"api_key": "", "base_url": "http://localhost:5506/v1", "timeout": 30}},
    {"name": "Ollama", "defaults": {"api_key": "", "base_url": "http://localhost:11434", "timeout": 30}},
    {"name": "OpenAI", "defaults": {"api_key": "", "timeout": 30}},
    {"name": "OpenRouter", "defaults": {"api_key": "", "base_url": "https://openrouter.ai/api/v1", "timeout": 30}},
    {"name": "Perplexity", "defaults": {"api_key": "", "base_url": "https://api.perplexity.ai", "timeout": 30}},
]

@ui.page('/', response_timeout=999)
async def _main_page() -> None:
    global APP_SETTINGS, PROVIDER_SETTINGS

    with ui.dialog().props('full-width') as dialog:
        with ui.card():
            content = ui.markdown()

    def read_settings_from_storage():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app_settings = app.storage.browser.get('app_settings')
        provider_settings = app.storage.browser.get('provider_settings')
        if app_settings is None or provider_settings is None:
            return False
        APP_SETTINGS.update(app_settings)
        PROVIDER_SETTINGS.update(provider_settings)
        ic(APP_SETTINGS, PROVIDER_SETTINGS)
        return True

    def set_app_setting(key, value):
        global APP_SETTINGS
        APP_SETTINGS[key] = value
        app.storage.browser['app_settings'] = APP_SETTINGS
        ic(app.storage.browser)

    def set_provider_setting(provider_name, key, value):
        global PROVIDER_SETTINGS
        ic(provider_name, key, value)
        # PROVIDER_SETTINGS = app.storage.user.get('provider_settings', {})
        # if provider not in PROVIDER_SETTINGS:
        #     PROVIDER_SETTINGS[provider] = {}
        # PROVIDER_SETTINGS[provider][key] = value
        for provider in PROVIDER_SETTINGS:
                if provider["name"] == provider_name:
                    provider["defaults"][key] = value
                    break
        app.storage.user['provider_settings'] = PROVIDER_SETTINGS

    def get_provider_setting(provider, key):
        global PROVIDER_SETTINGS
        provider_settings = app.storage.user.get('provider_settings', {})
        if provider in provider_settings and key in provider_settings[provider]:
            return provider_settings[provider][key]
        return None

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

    def initialize_default_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app.storage.browser.pop('app_settings', None)
        set_app_setting('host', '127.0.0.1')
        set_app_setting('port', 8000)
        set_app_setting('dark_mode', True)

        app.storage.browser.pop('provider_settings', None)
        for provider in PROVIDER_SETTINGS:
            ic(provider)
            name = provider['name']
            defaults = provider['defaults']
            set_provider_setting(name, 'api_key', "")
            if 'base_url' in defaults:
                set_provider_setting(name, 'base_url', defaults['base_url'])
            if 'timeout' in defaults:
                set_provider_setting(name, 'timeout', defaults['timeout'])
            if 'max_tokens' in defaults:
                set_provider_setting(name, 'max_tokens', defaults['max_tokens'])

    def download_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        # app_settings, provider_settings = read_settings_from_storage()
        settings = {
            'app_settings': APP_SETTINGS,
            'provider_settings': PROVIDER_SETTINGS
        }
        content = json.dumps(settings, indent=4)

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

    def download_conversation():
        content = "Sample AI conversation..."

        ui.download(content.encode('utf-8'), 'cls.txt')

        # b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        # ui.run_javascript(f"""
        #     const content = atob("{b64_content}");
        #     const blob = new Blob([content], {{type: 'text/plain'}});
        #     const url = URL.createObjectURL(blob);
        #     const a = document.createElement('a');
        #     a.href = url;
        #     a.download = 'ai_conversation.txt';
        #     document.body.appendChild(a);
        #     a.click();
        #     document.body.removeChild(a);
        #     URL.revokeObjectURL(url);
        # """)

    ic(app.storage.browser['id'])
    ic(type(app.storage.browser))
    ic(app.storage.browser)

    app.storage.browser.pop('app_settings', None)
    app.storage.browser.pop('provider_settings', None)

    # ic(type(APP_SETTINGS), type(PROVIDER_SETTINGS), type(PROVIDER_SETTINGS[0]))
    # ic(APP_SETTINGS, PROVIDER_SETTINGS)

    found = read_settings_from_storage()
    ic(found)
    ic(APP_SETTINGS, PROVIDER_SETTINGS)
    ic(app.storage.browser)

    # initialize_default_settings()
    # ic(app.storage.browser)
    # ic(APP_SETTINGS, PROVIDER_SETTINGS)

    ui.button('Download Settings', on_click=download_settings)
    ui.button('Download Conversation', on_click=download_conversation)

    ui.upload(on_upload=upload_settings).props('accept=.json').classes('max-w-full')


    def edit_provider_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        provider_settings = app.storage.user.get('provider_settings', [])
        
        for provider in PROVIDER_SETTINGS:
            name = provider['name']  # Define 'name' before using it
            defaults = provider['defaults']  # Define 'defaults' before using it
            
            current_settings = next(
                (item for item in provider_settings if item['name'] == name),
                defaults
            )

            with ui.dialog() as dialog:
                with ui.card():
                    ui.label(f'Edit settings for {name}')
                    for key, value in defaults.items():
                        current_value = current_settings.get(key, value)
                        ui.input(f'{key}', value=current_value, on_change=lambda e, key=key, name=name: set_provider_setting(name, key, e.value))
                    ui.button('Close', on_click=dialog.close)
            dialog.open()

    ui.button('Edit Provider Settings', on_click=edit_provider_settings)


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


