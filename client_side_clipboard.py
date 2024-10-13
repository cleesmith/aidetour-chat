# https://nicegui.io/documentation/clipboard#client-side_clipboard
from nicegui import ui, app, native
import asyncio
import webview

text = f"navigator and no click button ...\n Line 1\nLine 2\nthe end."

async def copy_chat():
    await ui.context.client.connected()  # Essential: Wait for the client connection

    # Best practice: Use a self-executing anonymous function (IIFE)
    await ui.run_javascript(f'''
        (() => {{
            navigator.clipboard.writeText({repr(text)});
            console.log("Text copied to clipboard:", {repr(text)}); // For debugging
        }})();
    ''')

    print(f"copy_chat (server-side): {text}")


@ui.page('/')
async def index():
    await copy_chat()

    text = f"clicked button ...\n Line 1\nLine 2\nthe end."
    ui.button('Write').on('click', js_handler=f'''
        () => navigator.clipboard.writeText({repr(text)})
    ''')

    async def get_text(clip):
        print(clip)

    ui.button('Read').on('click', js_handler='''
        async () => emitEvent("clipboard", await navigator.clipboard.readText())
    ''')
    ui.on('clipboard', lambda e: get_text(e.args))


    # text = f"navigator and no click button ...\n Line 1\nLine 2\nthe end."
    # async def copy_chat():
    #     # await ui.context.client.connected()
    #     # text = f"no click button ...\n Line 1\nLine 2\nthe end."
    #     # await ui.run_javascript(f"navigator.clipboard.writeText({repr(text)})")
    #     await ui.run_javascript(f'''
    #         () => navigator.clipboard.writeText({repr(text)})
    #     ''')
    #     print(f"copy_chat: {text}")

    # # await asyncio.sleep(2)
    # await ui.context.client.connected()
    # await copy_chat()


    # text = f"pywebview and no click button ...\n Line 1\nLine 2\nthe end."
    # js_code = f"""
    #         navigator.clipboard.writeText('{text}').then(function() {{
    #             console.log('Copied to clipboard: ', '{text}');
    #         }}).catch(function(err) {{
    #             console.error('Failed to copy: ', err);
    #         }});
    #     """
    # await app.native.main_window.evaluate_js(js_code)

# pywebview
ui.run(native=True, reload=False, show_welcome_message=False)

# web browser:
# ui.run(native=False, reload=False, show_welcome_message=False)


'''
You're right, requiring users to install system packages like xsel or xclip (which pyperclip relies on under the hood on Linux) can be inconvenient. Here are alternative approaches to handle clipboard operations on Linux without external dependencies within your NiceGUI app:

1. Using gtk if Available:

If your users have GTK (GNOME Toolkit) already installed (which is common on many Linux desktops), you can use it directly from Python. This avoids the pyperclip dependency and its underlying requirements:

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

async def copy_to_clipboard_gtk(text):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(text, -1)  # -1 sets the length automatically
    print("Clipboard copy attempted (using GTK)")

# Example usage (in your copy_chat function or elsewhere):
await copy_to_clipboard_gtk("This text will be copied")
content_copy
Use code with caution.
Python

2. Bundling xclip or xsel with Your Application:

If GTK is not a reliable option, you can bundle a statically compiled version of xclip or xsel with your application. This way, you won't need users to install anything. Here's a general outline:

Download Source: Download the source code for xclip or xsel.

Static Compilation: Compile the utility statically (so it doesn't have external library dependencies). This often involves using flags like -static during compilation. The exact steps will depend on the utility and your build environment.

Bundle the Binary: Include the statically compiled binary in your application's distribution.

Call the Binary: Use Python's subprocess module to execute the binary and copy the text:

import subprocess

async def copy_to_clipboard_binary(text):
    try:
        process = subprocess.Popen(['xclip', '-in', '-selection', 'clipboard'], stdin=subprocess.PIPE) # Or xsel
        process.communicate(text.encode())  # Send text to stdin
        print("Clipboard copy attempted (using bundled binary)")
    except FileNotFoundError:
        print("xclip/xsel binary not found.") # Handle the error
    except Exception as e:
        print(f"Error copying to clipboard: {e}")


# ... usage within your copy_chat function (similar to GTK example)
content_copy
Use code with caution.
Python

3. Using wl-copy for Wayland (if applicable):

If you anticipate users on Wayland desktops, wl-copy is the appropriate clipboard utility. You would bundle and use it similarly to xclip or xsel in the previous example.

Recommendation:

If GTK is readily available on your target systems, it's the easiest and most recommended approach. Bundling a static binary provides more control and avoids external dependencies, but it requires more setup. Consider which option best balances ease of implementation and user experience for your specific situation. Always handle potential errors (like the binary not being found) gracefully.
'''