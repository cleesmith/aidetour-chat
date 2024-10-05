# python setup.py build

import sys
from cx_Freeze import setup, Executable

# Dependencies required by your application
build_exe_options = {
    "packages": [
        "os", "sys", "nicegui", "uvicorn", "fastapi", "httpx", "tinydb",
        "multiprocessing", "signal", "traceback", "uuid", "re", "time", "datetime",
        "asyncio", "collections", "pyperclip", "starlette", "webview", "openai",
        "google.generativeai", "anthropic", "groq", "mistralai", "ollama", "socks"
    ],
    "include_files": ["images/"],  # Add any static files here
}

# Setting the base to None for non-Windows platforms.
# For macOS GUI apps, base is set to None.
base = None

setup(
    name="AidetourChat",
    version="1.0",
    description="Aidetour Chat app",
    options={"build_exe": build_exe_options},
    executables=[Executable("aidetour_chat.py", base=base)],
)


# import sys
# from cx_Freeze import setup, Executable

# build_exe_options = {
#     "packages": [
#         "os", "sys", "nicegui", "uvicorn", "fastapi", "httpx", "tinydb",
#         "multiprocessing", "signal", "traceback", "uuid", "re", "time", "datetime",
#         "asyncio", "collections", "pyperclip", "starlette", "webview", "openai",
#         "google.generativeai", "anthropic", "groq", "mistralai", "ollama"
#     ],
#     "include_files": ["images/"],
#     "includes": ["nicegui.functions.clipboard"], 
# }

# # Base should be None for non-Windows platforms
# base = None

# # Mac-specific app bundle options
# bdist_mac_options = {
#     "iconfile": "Funnel.icns",
#     "bundle_name": "AidetourChat",  # Name of your app without .app extension
#     # "custom_info_plist": "custom_Info.plist",  # Optional: Custom Info.plist file if needed
#     # "include_resources": [("path/to/resource", "resource_in_app")],  # Include additional resources
# }

# executables = [
#     Executable(
#         "aidetour_chat.py",
#         base=base,
#         target_name="AidetourChat",  # The name of your macOS app
#     )
# ]

# setup(
#     name="AidetourChat",
#     version="1.0.0",
#     description="Aidetour Chat is a personal, multi-provider AI chat application that allows you to interact with various AI language models from different providers—all in one place.",
#     long_description="Aidetour Chat enables seamless interaction with multiple AI providers, bringing them into a single, convenient interface for personal use.",
#     author="Clee Smith",
#     author_email="cleesmith2006@gmail.com",
#     url="https://github.com/cleesmith/aidetour-chat",
#     license="MIT",
#     keywords="AI, chat, multi-provider, language models, personal AI",
#     project_urls={
#         "Source": "https://github.com/cleesmith/aidetour-chat",
#         "Documentation": "https://github.com/cleesmith/aidetour-chat/wiki",
#     },
#     options={
#         "bdist_mac": bdist_mac_options,
#     },
#     executables=executables,
# )

