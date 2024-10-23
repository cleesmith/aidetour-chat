from nicegui import app, ui, events
import sys
import json
import base64
from icecream import ic
from cryptography.fernet import Fernet

ic.configureOutput(includeContext=True, contextAbsPath=True)

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

PROVIDER_SETTINGS = {
    "Anthropic": {"api_key": "", "max_tokens": 4096, "timeout": 30},
    "Google": {"api_key": "", "timeout": 30},
    "Groq": {"api_key": "", "timeout": 30},
    "LMStudio": {"api_key": "", "base_url": "http://localhost:5506/v1", "timeout": 30},
    "Ollama": {"api_key": "", "base_url": "http://localhost:11434", "timeout": 30},
    "OpenAI": {"api_key": "", "timeout": 30},
    "OpenRouter": {"api_key": "", "base_url": "https://openrouter.ai/api/v1", "timeout": 30},
    "Perplexity": {"api_key": "", "base_url": "https://api.perplexity.ai", "timeout": 30},
}

@ui.page('/', response_timeout=999)
async def _main_page() -> None:
    global APP_SETTINGS, PROVIDER_SETTINGS

    # getter's and setters:

    def get_app_storage_browser_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app_settings = app.storage.browser.get('APP_SETTINGS', None)
        provider_settings = app.storage.browser.get('PROVIDER_SETTINGS', None)
        if app_settings is None or provider_settings is None:
            # i.e. globals will be the default settings not from cookie
            return False
        APP_SETTINGS = app.storage.browser.get('APP_SETTINGS')
        PROVIDER_SETTINGS = app.storage.browser.get('PROVIDER_SETTINGS')
        return True

    def set_app_storage_browser_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        app.storage.browser['APP_SETTINGS'] = APP_SETTINGS
        app.storage.browser['PROVIDER_SETTINGS'] = PROVIDER_SETTINGS

    def get_app_setting(key):
        return APP_SETTINGS.get(key, "")

    def set_app_setting(key, value):
        global APP_SETTINGS
        # always set the global as the current/master settings:
        APP_SETTINGS[key] = value
        app.storage.browser['APP_SETTINGS'] = APP_SETTINGS

    def get_provider_setting(provider_name, key):
        return PROVIDER_SETTINGS.get(provider_name, {}).get(key, "")

    def set_provider_setting(provider_name, key, value):
        global PROVIDER_SETTINGS
        PROVIDER_SETTINGS[provider_name][key] = value
        app.storage.browser['PROVIDER_SETTINGS'] = PROVIDER_SETTINGS

    def download_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        settings = {
            'APP_SETTINGS': APP_SETTINGS,
            'PROVIDER_SETTINGS': PROVIDER_SETTINGS
        }
        content = json.dumps(settings)
        ui.download(content.encode('utf-8'), 'clsSettings.json')

    def upload_settings(e: events.UploadEventArguments):
        global APP_SETTINGS, PROVIDER_SETTINGS
        text = e.content.read().decode('utf-8')
        settings = json.loads(text)
        if 'APP_SETTINGS' in settings:
            APP_SETTINGS = settings['APP_SETTINGS']
        if 'PROVIDER_SETTINGS' in settings:
            PROVIDER_SETTINGS = settings['PROVIDER_SETTINGS']
        set_app_storage_browser_settings()

    ic(app.storage.browser['id'])

    # empty/clear 'browser session cookie':
    # app.storage.browser.pop('app_settings', None)
    # app.storage.browser.pop('provider_settings', None)
    # app.storage.browser.pop('APP_SETTINGS', None)
    # app.storage.browser.pop('PROVIDER_SETTINGS', None)

    found = get_app_storage_browser_settings()
    ic('get_app_storage_browser_settings', found, app.storage.browser)

    if not found:
        set_app_storage_browser_settings()
        ic(app.storage.browser)

    # set_provider_setting('OpenRouter', 'timeout', 999)
    # ic('set_provider_setting', app.storage.browser)

    # or_timeout = get_provider_setting('OpenRouter', 'timeout')
    # ic(or_timeout)
    # h = get_app_setting('host')
    # ic(h)

    # ui=gui
    ui.button('Download Settings', on_click=download_settings)
    ui.upload(on_upload=upload_settings).props('accept=.json').classes('max-w-full')

    # for provider in PROVIDER_SETTINGS:
    for provider_name, settings in PROVIDER_SETTINGS.items():
        with ui.expansion(provider_name).classes('w-full mb-2'):
            with ui.column().classes('w-full'):
                inputs = {}
                inputs['api_key'] = ui.input(
                    label='API Key', 
                    password=True, 
                    password_toggle_button=True, 
                    value=get_provider_setting(provider_name, 'api_key')) \
                .classes('w-full mb-2') \
                .props("spellcheck=false") \
                .props("autocomplete=off") \
                .props("autocorrect=off")

                inputs['timeout'] = ui.input(
                    label='Timeout', 
                    value=get_provider_setting(provider_name, 'timeout')) \
                .classes('w-full mb-2') \
                .props("spellcheck=false") \
                .props("autocomplete=off") \
                .props("autocorrect=off")

                if provider_name in ['Ollama', 'OpenRouter', 'Perplexity', 'LMStudio']:
                    inputs['base_url'] = ui.input(
                        label='Base URL', 
                        value=get_provider_setting(provider_name, 'base_url')) \
                    .classes('w-full mb-2') \
                    .props("spellcheck=false") \
                    .props("autocomplete=off") \
                    .props("autocorrect=off")

                if provider_name == 'Anthropic':
                    inputs['max_tokens'] = ui.input(
                        label='Max Tokens', 
                        value=get_provider_setting(provider_name, 'max_tokens')) \
                    .classes('w-full mb-2') \
                    .props("spellcheck=false") \
                    .props("autocomplete=off") \
                    .props("autocorrect=off")

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
# this should be used only once outside of the app, then
# used as the storage_secret and to encrypt/decrypt 'browser session cookie'
# key = Fernet.generate_key()
# ic(key)

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

