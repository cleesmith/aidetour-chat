# Aidetour Chat Application

**Aidetour Chat** is a personal, multi-provider AI chat application that allows you to interact with various AI language models from different providers—all in one place. Designed for single-user, local use, it gives you the ability to use your own API keys to connect with AI models like OpenAI's GPT-4, Google's **Gemini**, Anthropic's Claude, and others. **What's more, with providers like Ollama and LM Studio, you can use the application completely offline—staying unplugged from the internet while still interacting with powerful AI models.**

## Key Features

- **Multi-Provider Support**: Seamlessly switch between different AI providers and models without leaving the app.
- **User-Friendly Interface**: Enjoy a modern, intuitive chat interface built with NiceGUI, offering a web-like experience on your desktop.
- **Offline Capability**: Use AI models from providers like Ollama and LM Studio entirely offline, ensuring privacy and independence from internet connectivity.
- **Personal API Keys**: Use your own API keys for each provider, ensuring secure and private interactions.
- **Conversation History**: Keep track of your chats with a history log that you can copy, save, or clear at any time. Even save snippets from the chat as AI pairs, ME+AI, not just the AI response as in most chat bots.
- **Customizable Settings**: Adjust parameters like the AI model's temperature to fine-tune responses according to your preferences.
- **Unified Experience**: No more juggling multiple apps or websites to interact with different AI models. While some providers may offer more detailed settings or customization in their own interfaces, Aidetour Chat brings all core functionalities into one place for seamless, efficient use. If you need advanced options, you can still access the providers' tools when precision is necessary.
- **Desktop Application**: Run the app locally on your computer as a standalone desktop application—no need for a web server or internet browser.
- **Open Source and Free**: Aidetour Chat is and will remain open source and free, available on GitHub for transparency and community contributions. Simple installable distributions are provided for easy setup.

## Supported AI Providers

*To use the following providers, the user must add their API keys in Aidetour Chat Settings:*  
- **OpenAI**: Access models like GPT-3.5, GPT-4, and others.  
- **Google**: Interact with Google's Gemini models.  
- **Anthropic**: Use models such as Claude.  
- **Groq**  
- **Mistral AI**  
- **Perplexity AI**

*To use the following providers, they must be installed on the user's local computer:*  
- **Ollama**: Use AI models offline.  
- **LM Studio**: Enjoy offline interactions with AI models.

## Why Choose Aidetour Chat?

- **Privacy First**: All interactions happen locally on your machine, and you control the API keys.  
- **Stay Offline When You Want**: With providers like Ollama and LM Studio, you can use the app without any internet connection.  
- **Unified Experience**: Enjoy a streamlined interface that consolidates essential features from multiple providers into one app. While individual providers' chat interfaces may offer more settings to tweak or change, Aidetour Chat focuses on delivering core functionalities in a single, convenient platform.  
- **Easy to Use**: Designed with simplicity in mind, so you can focus on your conversations, not the technology.  
- **Open Source and Free**: Aidetour Chat is and will remain open source and free, with simple installable distributions for easy setup.  
- **Plain Text Only**: The app ensures all copies and saves are handled as plain text, maintaining simplicity and compatibility. No hassles with html or json, as plain text is the best for editing and writing as it is portable to most word processors, like Word, every text editor, Google Docs, Vellum, and more.

---

Get started with Aidetour Chat and bring all your favorite AI models into a single, convenient interface—even when you're offline!


---

## Project Layout

```
tree -f -I 'build|dist' | sed 's|\./||g' | tr '\240' ' '                        
```

```
.
├── AidetourChat.spec
├── AidetourChatIcon.icns
├── LICENSE
├── README.md
├── aidetour-chat.iss
├── aidetourchat
│   ├── aidetourchat/AidetourChatIcon.ico
│   ├── aidetourchat/__init__.py
│   ├── aidetourchat/aidetour_chat.py
│   └── aidetourchat/images
│       └── aidetourchat/images/Aidetour.png
├── images
│   └── images/Aidetour.png
├── poetry.lock
├── pyproject.toml
├── settings.py
├── setup.py
├── win_pyproject.toml
└── win_setup.py
```