# cd aidetour-chat
# python setup.py build = works, but weird Terminal console window appears = fail!
# python setup.py build bdist_mac = works as expected
# finder: double-click on build/aidetourchat-1.0.app
# poetry run python setup.py build bdist_mac = works as expected

import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "os", "sys", "nicegui", "uvicorn", "fastapi", "httpx", "tinydb",
        "multiprocessing", "signal", "traceback", "uuid", "re", "time", "datetime",
        "asyncio", "collections", "pyperclip", "starlette", "openai",
        "google.generativeai", "anthropic", "groq", "mistralai", "ollama", "socks"
    ],
    "include_files": [
        ("aidetourchat/images/", "images/")
    ],
}

setup(
    name="AidetourChat",
    version="1.0",
    description="Aidetour Chat app",
    options={"build_exe": build_exe_options},
    executables=[Executable("aidetourchat/aidetour_chat.py")]
)

# ... after:
# python setup.py build bdist_dmg
# ... to update the app icon in the .dmg:
# cp AidetourChatIcon.icns build/dist/aidetourchat-1.0.app/Contents/Resources
# cd build/dist
# hdiutil create -volname "AidetourChat" -srcfolder aidetourchat-1.0.app -ov -format UDZO aidetourchat-1.0.dmg



# # dependencies required by your application
# build_exe_options = {
#     "packages": [
#         "os", "sys", "nicegui", "uvicorn", "fastapi", "httpx", "tinydb",
#         "multiprocessing", "signal", "traceback", "uuid", "re", "time", "datetime",
#         "asyncio", "collections", "pyperclip", "starlette", "openai",
#         "google.generativeai", "anthropic", "groq", "mistralai", "ollama", "socks"
#     ],
#     "include_files": [
#         ("aidetourchat/images/", "images/")  # include images folder
#     ],
# }

# executables = [
#     Executable(
#         "aidetourchat/aidetour_chat.py",
#         base=None,
#         target_name="AidetourChat",
#         icon="AidetourChatIcon.icns",
#     )
# ]

# setup(
#     name="AidetourChat",
#     version="1.0",
#     description="Aidetour Chat app",
#     options={"build_exe": build_exe_options},
#     # executables=[Executable("aidetourchat/aidetour_chat.py", base=None)]
#     executables=executables,
# )


# import sys
# from cx_Freeze import setup, Executable

# build_exe_options = {
#     "packages": [
#         "os", "sys", "nicegui", "uvicorn", "fastapi", "httpx", "tinydb",
#         "multiprocessing", "signal", "traceback", "uuid", "re", "time", "datetime",
#         "asyncio", "collections", "pyperclip", "starlette", "openai",
#         "google.generativeai", "anthropic", "groq", "mistralai", "ollama", "socks"
#     ],
#     "include_files": ["images/"],
# }

# # Base should be None for non-Windows platforms
# base = None

# # Mac-specific app bundle options
# bdist_mac_options = {
#     "iconfile": "AidetourChatIcon.icns",
#     "bundle_name": "AidetourChat",  # Name of your app without .app extension
#     # "custom_info_plist": "custom_Info.plist",  # Optional: Custom Info.plist file if needed
#     # "include_resources": [("path/to/resource", "resource_in_app")],  # Include additional resources
# }

# executables = [
#     Executable(
#         "aidetourchat/aidetour_chat.py",
#         base=base,
#         target_name="AidetourChat",
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

