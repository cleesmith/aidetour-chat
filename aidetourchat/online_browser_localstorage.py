from nicegui import app, ui, events
import json
import base64
from collections import defaultdict

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
        APP_SETTINGS = app.storage.user.get('app_settings', {})
        PROVIDER_SETTINGS = app.storage.user.get('provider_settings', {})

    def set_app_setting(key, value):
        global APP_SETTINGS, PROVIDER_SETTINGS
        # APP_SETTINGS = app.storage.user.get('app_settings', {})
        APP_SETTINGS[key] = value
        app.storage.user['app_settings'] = APP_SETTINGS

    def set_provider_setting(provider_name, key, value):
        global APP_SETTINGS, PROVIDER_SETTINGS
        print("set_provider_setting:")
        print(provider_name, key, value)
        print()
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
        global APP_SETTINGS, PROVIDER_SETTINGS
        provider_settings = app.storage.user.get('provider_settings', {})
        if provider in provider_settings and key in provider_settings[provider]:
            return provider_settings[provider][key]
        return None

    def upload_settings(e: events.UploadEventArguments):
        global APP_SETTINGS, PROVIDER_SETTINGS
        text = e.content.read().decode('utf-8')
        settings = json.loads(text)
        print(f"\nsettings:\n{settings}\n")
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
        set_app_setting('host', '127.0.0.1')
        set_app_setting('port', 8000)
        set_app_setting('dark_mode', True)

        # PROVIDER_SETTINGS = defaultdict(dict)
        print(f"initialize_default_settings: PROVIDER_SETTINGS:\n{PROVIDER_SETTINGS}")
        for provider in PROVIDER_SETTINGS:
            print(f"provider={provider}")
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

    print('before: read_settings_from_storage:')
    print('APP_SETTINGS', APP_SETTINGS)
    print('PROVIDER_SETTINGS', PROVIDER_SETTINGS)
    print()
    # read_settings_from_storage()
    # print('before: read_settings_from_storage:')
    # print('APP_SETTINGS', APP_SETTINGS)
    # print('PROVIDER_SETTINGS', PROVIDER_SETTINGS)
    # print()

    print("app.storage.user:")
    print(app.storage.user)

    print('before: initialize_default_settings:')
    print('APP_SETTINGS', APP_SETTINGS)
    print('PROVIDER_SETTINGS', PROVIDER_SETTINGS)
    print()
    initialize_default_settings()
    print('after: initialize_default_settings:')
    print('APP_SETTINGS', APP_SETTINGS)
    print('PROVIDER_SETTINGS', PROVIDER_SETTINGS)
    print()

    ui.button('Download Settings', on_click=download_settings)
    ui.button('Download Conversation', on_click=download_conversation)

    ui.upload(on_upload=upload_settings).props('accept=.json').classes('max-w-full')


    def edit_provider_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS
        provider_settings = app.storage.user.get('provider_settings', {})
        for provider in PROVIDER_SETTINGS:
            name = provider['name']
            defaults = provider['defaults']
            current_settings = provider_settings.get(name, defaults)

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
        storage_secret='clsxxx',
    )
