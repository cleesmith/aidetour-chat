from fastapi.responses import JSONResponse
from datetime import timedelta, datetime, timezone
from nicegui import app, ui, events
import sys
import json
import base64
from icecream import ic


ic.configureOutput(includeContext=True, contextAbsPath=True)

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

    # Function to override cookie settings for max_age and expires
    def set_custom_cookies(response: JSONResponse):
        global APP_SETTINGS, PROVIDER_SETTINGS
        # Serialize the settings to JSON for the cookie
        app_settings_value = json.dumps(APP_SETTINGS)
        provider_settings_value = json.dumps(PROVIDER_SETTINGS)
        # Define custom max_age and expires (e.g., 1 day)
        max_age = 60 * 60 * 24  # 1 day in seconds
        expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)  # Ensure expires is in UTC
        # Set custom cookies for APP_SETTINGS and PROVIDER_SETTINGS
        response.set_cookie(
            key="APP_SETTINGS",
            value=app_settings_value,
            max_age=max_age,
            expires=expires,
            httponly=True,
            samesite="lax"
        )
        response.set_cookie(
            key="PROVIDER_SETTINGS",
            value=provider_settings_value,
            max_age=max_age,
            expires=expires,
            httponly=True,
            samesite="lax"
        )
        ic(response)
        return response

    # Update settings and override cookie max_age and expires
    def set_app_storage_browser_settings():
        global APP_SETTINGS, PROVIDER_SETTINGS

        # Store the settings in the browser (which automatically updates cookies)
        app.storage.browser['APP_SETTINGS'] = APP_SETTINGS
        app.storage.browser['PROVIDER_SETTINGS'] = PROVIDER_SETTINGS

        # Now override the cookie settings for max_age and expires
        response = JSONResponse(content={"message": "Settings saved with custom cookie settings!"})
        return set_custom_cookies(response)

    # Use this function when you need to save settings and override the cookies
    def set_app_setting(key, value):
        global APP_SETTINGS
        APP_SETTINGS[key] = value
        set_app_storage_browser_settings()

    def set_provider_setting(provider_name, key, value):
        global PROVIDER_SETTINGS
        PROVIDER_SETTINGS[provider_name][key] = value
        set_app_storage_browser_settings()


    # empty/clear 'browser session cookie':
    # app.storage.browser.pop('app_settings', None)
    # app.storage.browser.pop('provider_settings', None)
    # app.storage.browser.pop('APP_SETTINGS', None)
    # app.storage.browser.pop('PROVIDER_SETTINGS', None)

    ic(app.storage.browser)

    what = set_app_storage_browser_settings()
    ic(what)

    ic(app.storage.browser)


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
