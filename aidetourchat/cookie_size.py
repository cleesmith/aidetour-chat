import json

APP_SETTINGS = {
    'host': '127.0.0.1',
    'port': 8000,
    'dark_mode': True
}

PROVIDER_SETTINGS = {
    "Anthropic": {"api_key": "a" * 128, "max_tokens": 4096, "timeout": 30},
    "Google": {"api_key": "a" * 128, "timeout": 30},
    "Groq": {"api_key": "a" * 128, "timeout": 30},
    "LMStudio": {"api_key": "a" * 128, "base_url": "http://localhost:5506/v1", "timeout": 30},
    "Ollama": {"api_key": "a" * 128, "base_url": "http://localhost:11434", "timeout": 30},
    "OpenAI": {"api_key": "a" * 128, "timeout": 30},
    "OpenRouter": {"api_key": "a" * 128, "base_url": "https://openrouter.ai/api/v1", "timeout": 30},
    "Perplexity": {"api_key": "a" * 128, "base_url": "https://api.perplexity.ai", "timeout": 30},
}

# Convert dictionaries to JSON strings
app_settings_json = json.dumps(APP_SETTINGS)
provider_settings_json = json.dumps(PROVIDER_SETTINGS)

# Calculate size in bytes
app_settings_size = len(app_settings_json.encode('utf-8'))
provider_settings_size = len(provider_settings_json.encode('utf-8'))
total_size = app_settings_size + provider_settings_size

print(f"APP_SETTINGS size: {app_settings_size} bytes")
print(f"PROVIDER_SETTINGS size: {provider_settings_size} bytes")
print(f"Total size: {total_size} bytes")

# encrypt/decrypt browser session cookie data:
from cryptography.fernet import Fernet
# generate a key (should be done only once, and store it securely outside of the app!)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

settings_json = json.dumps(APP_SETTINGS)
encrypted_data1 = cipher_suite.encrypt(settings_json.encode()).decode()
settings_json = json.dumps(PROVIDER_SETTINGS)
encrypted_data2 = cipher_suite.encrypt(settings_json.encode()).decode()

# Calculate size in bytes
app_settings_size = len(encrypted_data1)
provider_settings_size = len(encrypted_data2)
total_size = app_settings_size + provider_settings_size

print(f"\nEncrypted:")
print(f"APP_SETTINGS size: {app_settings_size} bytes")
print(f"PROVIDER_SETTINGS size: {provider_settings_size} bytes")
print(f"Total size: {total_size} bytes")

