from nicegui import app, ui, events
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime, timezone
import sys
import json
import base64
import asyncio
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
async def _main_page(request: Request) -> None:
    global APP_SETTINGS, PROVIDER_SETTINGS
    ic()
    # ic(request)
    # ic(request.session)
    # ic(request.state)
    # ic(request.headers)
    # ic(request.client)  # Shows client's IP address and port
    # ic(request.query_params)  # Print query parameters
    # ic(request.method)  # Print HTTP method (GET, POST, etc.)
    # ic(request.url)  # Print the full URL requested
    # ic('vars(request):')
    # ic(vars(request))
    # ic(dir(request))  # List all attributes and methods of request object
    ic(request.cookies)

    def get_settings_from_cookies(request) -> None:
        global APP_SETTINGS, PROVIDER_SETTINGS
        # get cookies from the request
        app_settings_cookie = request.cookies.get('APP_SETTINGS')
        ic('get_settings_from_cookies:', app_settings_cookie)
        provider_settings_cookie = request.cookies.get('PROVIDER_SETTINGS')
        if app_settings_cookie is not None:
            APP_SETTINGS = json.loads(app_settings_cookie)
            ic(APP_SETTINGS)
        if provider_settings_cookie is not None:
            PROVIDER_SETTINGS = json.loads(provider_settings_cookie)

    def update_app_settings(key, value):
        global APP_SETTINGS
        APP_SETTINGS[key] = value
        ui.run_javascript(f'''setAppSettingsCookie("{APP_SETTINGS['host']}", "{APP_SETTINGS['port']}")''')
        ic('update_app_settings:', APP_SETTINGS)

    # empty/clear 'browser session cookie':
    # app.storage.browser.pop('app_settings', None)
    # app.storage.browser.pop('provider_settings', None)
    # app.storage.browser.pop('APP_SETTINGS', None)
    # app.storage.browser.pop('PROVIDER_SETTINGS', None)
    # ic(app.storage.browser)

    get_settings_from_cookies(request)
    ic(request)
    ic(APP_SETTINGS)
    APP_SETTINGS = json.loads(APP_SETTINGS)

    ic(APP_SETTINGS.get('host', ''))

    # await asyncio.sleep(1.0)
    ui.input('Host', value=APP_SETTINGS.get('host', ''), on_change=lambda e: update_app_settings('host', e.value))
    ui.input('Port', value=APP_SETTINGS.get('port', 0), on_change=lambda e: update_app_settings('port', e.value))

    # set cookies client-side dynamically with a longer max_age
    ui.add_body_html('''
    <script>
        function extendCookieMaxAge(name, days) {
            // Get the current cookie value
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) == ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) == 0) {
                    // cookie exists, extend its max-age
                    var value = c.substring(nameEQ.length, c.length);
                    var maxAge = days * 24 * 60 * 60; // Convert days to seconds
                    var expires = "; max-age=" + maxAge;
                    document.cookie = name + "=" + value + expires + "; path=/; SameSite=Lax";
                    console.log("Extended cookie: ", document.cookie);
                    return;
                }
            }
        }

        function extendSettingsCookies() {
            // Extend APP_SETTINGS and PROVIDER_SETTINGS cookies by 1 year (365 days)
            extendCookieMaxAge('APP_SETTINGS', 365);
            extendCookieMaxAge('PROVIDER_SETTINGS', 365);
        }

        function setCookie(name, value, days) {
            var expires = "";
            if (days) {
                // var date = new Date();
                // date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));  // Convert days to milliseconds
                // expires = "; max-age=" + date.toUTCString();
                var maxAge = days * 24 * 60 * 60;  // Convert days to seconds
                expires = "; max-age=" + maxAge;
            }
            document.cookie = name + "=" + (value || "") + expires + "; path=/; samesite=lax";
        }

        function setAppSettingsCookie(host, port) {
            var appSettingsValue = JSON.stringify({
                'host': host,
                'port': port
            });
            setCookie('APP_SETTINGS', appSettingsValue, 400);
        }

        function setProviderSettingsCookie() {
            var providerSettingsValue = JSON.stringify({
                "OpenAI": {"api_key": "", "timeout": 30},
                "Anthropic": {"api_key": "", "max_tokens": 4096, "timeout": 30}
            });
            setCookie('PROVIDER_SETTINGS', providerSettingsValue, 400);
        }

        /*
        document.querySelector('[name="Host"]').addEventListener('change', function(e) {
            var host = e.target.value;
            var port = document.querySelector('[name="Port"]').value;
            setAppSettingsCookie(host, port);
        });

        document.querySelector('[name="Port"]').addEventListener('change', function(e) {
            var port = e.target.value;
            var host = document.querySelector('[name="Host"]').value;
            setAppSettingsCookie(host, port);
        });
        */

        const observer = new MutationObserver((mutations, observer) => {
            if (document.querySelector('[name="Host"]') && document.querySelector('[name="Port"]')) {
                setTimeout(() => {
                    // Initially set the cookies when the desired elements are detected
                    setAppSettingsCookie(document.querySelector('[name="Host"]').value, document.querySelector('[name="Port"]').value);
                    setProviderSettingsCookie();
                }, 300); // 300ms sleep
                observer.disconnect(); // stop observing after running the function
            }
        });

        observer.observe(document, {
            childList: true,
            subtree: true
        });
    </script>
    ''')

    ui.run_javascript('extendSettingsCookies();')

    # set cookies server-side
    # ui.run_javascript('''
    #     // Set initial cookies for APP_SETTINGS and PROVIDER_SETTINGS
    #     setAppSettingsCookie(document.querySelector('[name="Host"]').value, document.querySelector('[name="Port"]').value);
    #     setProviderSettingsCookie();
    # ''')


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
