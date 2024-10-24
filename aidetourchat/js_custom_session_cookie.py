from nicegui import app, ui, events
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime, timezone
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
async def _main_page(request: Request) -> None:
    global APP_SETTINGS, PROVIDER_SETTINGS
    ic()
    ic(request)
    ic(request.session)
    ic(request.state)
    ic(request.headers)
    ic(request.client)  # Shows client's IP address and port
    ic(request.query_params)  # Print query parameters
    ic(request.method)  # Print HTTP method (GET, POST, etc.)
    ic(request.url)  # Print the full URL requested
    ic(request.cookies)
    ic('vars(request):')
    ic(vars(request))
    ic(dir(request))  # List all attributes and methods of request object

    # Server-side: Function to retrieve settings from cookies
    def get_settings_from_cookies(request: Request):
        global APP_SETTINGS, PROVIDER_SETTINGS
        app_settings_cookie = request.cookies.get('APP_SETTINGS')
        provider_settings_cookie = request.cookies.get('PROVIDER_SETTINGS')

        if app_settings_cookie:
            APP_SETTINGS = json.loads(app_settings_cookie)
        if provider_settings_cookie:
            PROVIDER_SETTINGS = json.loads(provider_settings_cookie)

        return APP_SETTINGS, PROVIDER_SETTINGS

    # Function to set custom cookies for settings with essentially "forever" max_age
    def set_custom_cookies():
        global APP_SETTINGS, PROVIDER_SETTINGS

        # Serialize the settings to JSON for the cookie
        app_settings_value = json.dumps(APP_SETTINGS)
        provider_settings_value = json.dumps(PROVIDER_SETTINGS)

        # Create the response object
        response = JSONResponse(content={"message": "Settings saved with custom cookie settings"})

        # Define custom max_age for essentially "forever" (e.g., 10 years)
        max_age = 60 * 60 * 24 * 365 * 10  # 10 years in seconds
        expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)

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

        return response

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

    APP_SETTINGS, PROVIDER_SETTINGS = get_settings_from_cookies(request)
    ic(request)
    ic(APP_SETTINGS)

    # Display current settings for the user to update
    ui.input('Host', value=APP_SETTINGS.get('host', ''), on_change=lambda e: update_app_settings('host', e.value))
    ui.input('Port', value=APP_SETTINGS.get('port', 0), on_change=lambda e: update_app_settings('port', e.value))

    # Inject JavaScript to set cookies client-side dynamically with a long max_age
    ui.add_body_html('''
    <script>
        // extend existing cookie max-age by 1 year
        function extendCookieMaxAge(name, days) {
            // Get the current cookie value
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) == ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) == 0) {
                    // Cookie exists, extend its max-age
                    var value = c.substring(nameEQ.length, c.length);
                    var maxAge = days * 24 * 60 * 60; // Convert days to seconds
                    var expires = "; max-age=" + maxAge;
                    document.cookie = name + "=" + value + expires + "; path=/; SameSite=Lax";
                    console.log("Extended cookie: ", document.cookie);
                    return;
                }
            }
        }

        // extend the max-age of specific settings cookies
        function extendSettingsCookies() {
            // Extend APP_SETTINGS and PROVIDER_SETTINGS cookies by 1 year (365 days)
            extendCookieMaxAge('APP_SETTINGS', 365);
            extendCookieMaxAge('PROVIDER_SETTINGS', 365);
        }

        // set cookies with a long max_age (essentially forever)
        function setCookie(name, value, days) {
            var expires = "";
            if (days) {
                // var date = new Date();
                // date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));  // Convert days to milliseconds
                // expires = "; max-age=" + date.toUTCString();
                var maxAge = days * 24 * 60 * 60;  // Convert days to seconds
                expires = "; max-age=" + maxAge;
            }
            console.log(expires);
            document.cookie = name + "=" + (value || "") + expires + "; path=/; samesite=lax";
            console.log(document.cookie);
        }


        // set cookies for APP_SETTINGS with a very long expiration (e.g., 10 years)
        function setAppSettingsCookie(host, port) {
            var appSettingsValue = JSON.stringify({
                'host': host,
                'port': port
            });
            setCookie('APP_SETTINGS', appSettingsValue, 400);
        }

        // set cookies for PROVIDER_SETTINGS with a very long expiration (e.g., 10 years)
        function setProviderSettingsCookie() {
            var providerSettingsValue = JSON.stringify({
                "OpenAI": {"api_key": "", "timeout": 30},
                "Anthropic": {"api_key": "", "max_tokens": 4096, "timeout": 30}
            });
            setCookie('PROVIDER_SETTINGS', providerSettingsValue, 400);
        }

        // dynamically update the app settings cookie based on user input
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

        // initially set the cookies when the page loads
        setAppSettingsCookie(document.querySelector('[name="Host"]').value, document.querySelector('[name="Port"]').value);
        setProviderSettingsCookie();
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
