from multiprocessing import freeze_support  # noqa

freeze_support()  # noqa

import os
import sys
import signal
import traceback
import uuid
import re
import time
import datetime
import asyncio
from collections import defaultdict

import httpx

import pyperclip

from tinydb import TinyDB, Query

from fastapi.responses import RedirectResponse
from fastapi import HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.responses import RedirectResponse

from nicegui import app, ui
from nicegui import __version__ as nv
import webview # pip install pywebview

from openai import OpenAI

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.generativeai.types import HarmBlockThreshold

import anthropic

from groq import Groq
from groq import AsyncGroq

import mistralai
from mistralai.client import MistralClient

import ollama
from ollama import Client as OllamaClient

from openai import __version__ as oav
from anthropic import __version__ as av
from google.generativeai import __version__ as ggv
from groq import __version__ as gv
# from mistralai import __version__ as mv
# from ollama import __version__ as ov

from importlib.metadata import version, PackageNotFoundError
try:
	mv = version('mistralai')
except PackageNotFoundError:
	mv = 'unknown'
try:
	ov = version('ollama')
except PackageNotFoundError:
	ov = 'unknown'
try:
	pwv = version('pywebview')
except PackageNotFoundError:
	pwv = 'unknown'
try:
	uvv = version('uvicorn')
except PackageNotFoundError:
	uvv = 'unknown'
try:
	fav = version('fastapi')
except PackageNotFoundError:
	fav = 'unknown'
try:
	pipv = version('pip')
except PackageNotFoundError:
	pipv = 'unknown'


HOST = '127.0.0.1' # note: using 'localhost' prioritizes IPv6, so IP = ::1, well on macOS
PORT = 8000
WIDTH = 810
HEIGHT = 840

ACTIVE_SESSION = None
CHAT_HISTORY = ""
SEND_BUTTON = None
THINKING_LABEL = None
ABORT_STREAM = None
ABORT = False
MESSAGE_CONTAINER = None
SPLASHED = False
TOTAL_MODELS = 0
PROVIDER = ""
MODEL = ""
TEMP = None
DARKNESS = None
CURRENT_PRIMARY_COLOR = '#4CAF50' # green-ish

PROVIDERS = [
	"Aidetour",
	"Anthropic",
	"Google",
	"Groq",
	"LMStudio",
	"Mistral",
	"Ollama",
	"OpenAI",
	"OpenRouter",
	"Perplexity",
]

PROVIDER_MODELS = {}

PROVIDERS_SETTINGS = [
	{"name": "Anthropic", "defaults": {"api_key": "", "max_tokens": 4096, "timeout": 30}},
	{"name": "Google", "defaults": {"api_key": "", "timeout": 30}},
	{"name": "Groq", "defaults": {"api_key": "", "timeout": 30}},
	{"name": "LMStudio", "defaults": {"api_key": "", "base_url": "http://localhost:5506/v1", "timeout": 30}},
	{"name": "Mistral", "defaults": {"api_key": "", "timeout": 30}},
	{"name": "Ollama", "defaults": {"api_key": "", "base_url": "http://localhost:11434", "timeout": 30}},
	{"name": "OpenAI", "defaults": {"api_key": "", "timeout": 30}},
	{"name": "OpenRouter", "defaults": {"api_key": "", "base_url": "https://openrouter.ai/api/v1", "timeout": 30}},
	{"name": "Perplexity", "defaults": {"api_key": "", "base_url": "https://api.perplexity.ai", "timeout": 30}},
]

APP_DB_SETTINGS = {}
PROVIDER_DB_SETTINGS = defaultdict(dict)

# notes: these 'app.' settings don't work: 
#   1.  just before or after 'ui.run'
#   2.  nor in: main()
#   3.  nor in:
#           @ui.page('/', response_timeout=999)
#           async def _main_page(request: Request) -> None:

app.add_static_files('/images', 'images')
app.native.settings['ALLOW_DOWNLOADS'] = True

# app.native.window_args["title"] = f"Aidetour Chat on http://{HOST}:{PORT}"

# see: https://pywebview.flowrl.com/guide/api.html#webview-create-window
# and: https://developer.mozilla.org/en-US/docs/Web/CSS/user-select
# allows text selection with mouse/pad, but not using: native=True:
app.native.window_args["text_select"] = True # allows user to hand select text
app.native.window_args["easy_drag"] = False


def set_abort(value):
	global ABORT
	ABORT = value

def convert_to_int(s: str, default: int) -> int:
	try:
		return int(s)
	except ValueError:
		return default
	except Exception:
		return default

def read_settings_from_db():
	global APP_DB_SETTINGS, PROVIDER_DB_SETTINGS
	db = TinyDB('Aidetour_Chat_Settings.json')
	all_docs = db.all()
	APP_DB_SETTINGS = {}
	PROVIDER_DB_SETTINGS = defaultdict(dict)
	for doc in all_docs:
		if doc['type'] == 'app_setting':
			APP_DB_SETTINGS[doc['key']] = doc['value']
		elif doc['type'] == 'provider_setting':
			PROVIDER_DB_SETTINGS[doc['provider']][doc['key']] = doc['value']
	db.close()

def get_app_setting(key):
	default_values = {
		'host': '127.0.0.1',
		'port': 8000,
		'window_width': 810,
		'window_height': 840,
		'dark_mode': True
	}
	if key in APP_DB_SETTINGS:
		return APP_DB_SETTINGS[key]
	if key == 'dark_mode':
		return default_values[key]
	return default_values.get(key, "")

def set_app_setting(key, value):
	db = TinyDB('Aidetour_Chat_Settings.json')
	Settings = Query()
	if db.search((Settings.type == 'app_setting') & (Settings.key == key)):
		db.update({'value': value}, (Settings.type == 'app_setting') & (Settings.key == key))
	else:
		db.insert({'type': 'app_setting', 'key': key, 'value': value})
	db.close()

def get_provider_setting(provider, key):
	if provider in PROVIDER_DB_SETTINGS and key in PROVIDER_DB_SETTINGS[provider]:
		setting = PROVIDER_DB_SETTINGS[provider][key]
		if setting == "": setting = None
		return setting
	provider_defaults = next((p['defaults'] for p in PROVIDERS_SETTINGS if p['name'] == provider), {})
	return provider_defaults.get(key, None) # "")

def set_provider_setting(provider, key, value):
	db = TinyDB('Aidetour_Chat_Settings.json')
	Settings = Query()
	if db.search((Settings.type == 'provider_setting') & (Settings.provider == provider) & (Settings.key == key)):
		db.update({'value': value}, (Settings.type == 'provider_setting') & (Settings.provider == provider) & (Settings.key == key))
	else:
		db.insert({'type': 'provider_setting', 'provider': provider, 'key': key, 'value': value})
	db.close()

# ************************************************************
# ALL backend API happens below in model listers and streamers:
# ************************************************************

# **********************
# provider model listers:
# **********************

async def aidetour_models():
	PROVIDER_MODELS["Aidetour"] = [
		"Insert a Note",
		"Info",
		"ReadMe",
	]
	return len(PROVIDER_MODELS["Aidetour"])

async def anthropic_models():
	provider_api_key = get_provider_setting('Anthropic', 'api_key')
	if provider_api_key is None or provider_api_key.strip() == "":
		PROVIDERS.remove("Anthropic") if "Anthropic" in PROVIDERS else None
		return 0
	# hardcoded coz they don't provide a 'list models' endpoint <= WHY?
	PROVIDER_MODELS["Anthropic"] = [
		"claude-3-5-sonnet-20240620",
		"claude-3-opus-20240229",
		"claude-3-sonnet-20240229",
		"claude-3-haiku-20240307",
	]
	return len(PROVIDER_MODELS["Anthropic"])

async def perplexity_models():
	provider_api_key = get_provider_setting('Perplexity', 'api_key')
	if provider_api_key is None or provider_api_key.strip() == "":
		PROVIDERS.remove("Perplexity") if "Perplexity" in PROVIDERS else None
		return 0
	# hardcoded coz they don't provide a 'list models' endpoint <= WHY?
	PROVIDER_MODELS["Perplexity"] = [
		"llama-3.1-70b-instruct", # context length: 131,072  
		"llama-3.1-8b-instruct", # context length: 131,072  
		"llama-3.1-sonar-huge-128k-online", # context length: 127,072  
		"llama-3.1-sonar-large-128k-chat", # context length: 127,072  
		"llama-3.1-sonar-large-128k-online", # context length: 127,072  
		"llama-3.1-sonar-small-128k-chat", # context length: 127,072  
		"llama-3.1-sonar-small-128k-online", # context length: 127,072
	]
	return len(PROVIDER_MODELS["Perplexity"])

async def groq_models():
	try:
		provider_api_key = get_provider_setting('Groq', 'api_key')
		if provider_api_key is None or provider_api_key.strip() == "":
			PROVIDERS.remove("Groq") if "Groq" in PROVIDERS else None
			return 0
		client = Groq(
			api_key=provider_api_key,
			max_retries=0, 
			timeout=30.0,
		)
		models = client.models.list()
		model_ids = [model.id for model in models.data if 'whisper' not in model.id.lower()]
		sorted_models = sorted(model_ids)
		PROVIDER_MODELS["Groq"] = sorted_models
		return len(PROVIDER_MODELS["Groq"])
	except Exception as e:
		PROVIDERS.remove("Groq") if "Groq" in PROVIDERS else None
		return 0

async def google_models():
	try:
		provider_api_key = get_provider_setting('Google', 'api_key')
		if provider_api_key is None or provider_api_key.strip() == "":
			PROVIDERS.remove("Google") if "Google" in PROVIDERS else None
			return 0 # ignore when no api key
		genai.configure(api_key=provider_api_key)
		chat_models = []
		for model in genai.list_models(request_options={"timeout": 10}):
			chat_models.append(model.name)
		sorted_models = sorted(chat_models)
		PROVIDER_MODELS["Google"] = sorted_models
		return len(PROVIDER_MODELS["Google"])
	except Exception as e:
		PROVIDERS.remove("Google") if "Google" in PROVIDERS else None
		return 0

async def openai_models():
	try:
		provider_api_key = get_provider_setting('OpenAI', 'api_key')
		if provider_api_key is None or provider_api_key.strip() == "":
			PROVIDERS.remove("OpenAI") if "OpenAI" in PROVIDERS else None
			return 0
		client = OpenAI(
			api_key=provider_api_key,
			max_retries=0, 
			timeout=30.0,
		)
		models = client.models.list()
		chat_models = [model for model in models.data if model.id.startswith("gpt")]
		sorted_chat_models = sorted(chat_models, key=lambda x: x.created, reverse=True)
		openai_model_ids = [model.id for model in sorted_chat_models if "gpt" in model.id]
		PROVIDER_MODELS["OpenAI"] = openai_model_ids
		return len(PROVIDER_MODELS["OpenAI"])
	except Exception as e:
		PROVIDERS.remove("OpenAI") if "OpenAI" in PROVIDERS else None
		return 0

async def mistral_models():
	try:
		provider_api_key = get_provider_setting('Mistral', 'api_key')
		if provider_api_key is None or provider_api_key.strip() == "":
			PROVIDERS.remove("Mistral") if "Mistral" in PROVIDERS else None
			return 0
		client = MistralClient(api_key=provider_api_key)
		list_models_response = client.list_models()
		model_ids = [model.id for model in list_models_response.data]
		sorted_models = sorted(model_ids)
		PROVIDER_MODELS["Mistral"] = sorted_models
		return len(PROVIDER_MODELS["Mistral"])
	except Exception as e:
		PROVIDERS.remove("Mistral") if "Mistral" in PROVIDERS else None
		return 0

async def openrouter_models():
	try:
		provider_api_key = get_provider_setting('OpenRouter', 'api_key')
		if provider_api_key is None or provider_api_key.strip() == "":
			PROVIDERS.remove("OpenRouter") if "OpenRouter" in PROVIDERS else None
			return 0
		client = OpenAI(
			base_url="https://openrouter.ai/api/v1",
			api_key=provider_api_key,
			max_retries=0,
			timeout=30.0
		)
		models = client.models.list()
		model_ids = [model.id for model in models.data]
		sorted_models = sorted(model_ids)
		PROVIDER_MODELS["OpenRouter"] = sorted_models
		return len(PROVIDER_MODELS["OpenRouter"])
	except Exception as e:
		PROVIDERS.remove("OpenRouter") if "OpenRouter" in PROVIDERS else None
		return 0

async def lm_studio_models():
	global PROVIDER_MODELS
	try:
		# api_key isn't required, so try to connect = very fast
		client = OpenAI(base_url="http://localhost:5506/v1", 
			api_key="lm-studio", 
			max_retries=0, 
			timeout=10
		)
		models = client.models.list()
		chat_models = [model.id for model in models.data if model.id]
		# usually 1 or too few to bother sorting them
		PROVIDER_MODELS["LMStudio"] = chat_models
		return len(PROVIDER_MODELS["LMStudio"])
	except Exception as e:
		PROVIDERS.remove("LMStudio") if "LMStudio" in PROVIDERS else None
		return 0 # isn't running which is ok

async def ollama_models():
	global PROVIDERS
	try:
		# api_key isn't required, so try to connect = very fast
		data = ollama.list()
		chat_models = [model['name'] for model in data['models']]
		# usually too few to bother sorting them
		PROVIDER_MODELS["Ollama"] = chat_models
		return len(PROVIDER_MODELS["Ollama"])
	except Exception as e:
		PROVIDERS.remove("Ollama") if "Ollama" in PROVIDERS else None
		return 0 # isn't running which is ok


# *********************************
# model streamers for each provider:
# *********************************
'''
1. Anthropic
	https://docs.anthropic.com/en/api/messages
	temp = 1.0  0.0-1.0
2. Google
	https://ai.google.dev/gemini-api/docs/models/generative-models#model-parameters
	temp = 0.0  0.0-2.0
	also: https://ai.google.dev/gemini-api/docs/text-generation?lang=python
3. Groq
	https://console.groq.com/docs/api-reference#chat-create
	temp = 1  0-2
4. Mistral
	https://docs.mistral.ai/api/#tag/chat/operation/chat_completion_v1_chat_completions_post
	temp = 0.7  0-1.5
5. OpenAI
	https://platform.openai.com/docs/api-reference/chat/create
	temp = 1  0-2
6. OpenRouter
	https://openrouter.ai/docs/parameters
	temp = 1.0  0.0-2.0
7. Perplexity
	https://docs.perplexity.ai/api-reference/chat-completions
	temp = 0.2  0.0-2.0
'''


async def OpenRouterResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = OpenAI(
		  base_url="https://openrouter.ai/api/v1",
		  api_key=get_provider_setting('OpenRouter', 'api_key'), 
		  max_retries=0,
		  timeout=30.0
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
		}
		if TEMP is not None: params["temperature"] = TEMP
		stream = client.chat.completions.create(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.choices[0].delta.content
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nOpenRouter's response for model: {MODEL}\n{e}"


async def PerplexityResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = OpenAI(
			base_url="https://api.perplexity.ai",
			api_key=get_provider_setting('Perplexity', 'api_key'), 
			max_retries=0,
			timeout=30.0
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
		}
		if TEMP is not None: params["temperature"] = TEMP
		stream = client.chat.completions.create(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.choices[0].delta.content
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nPerplexity's response for model: {MODEL}\n{e}"


async def MistralResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = MistralClient(
			api_key=get_provider_setting('Mistral', 'api_key'), 
			max_retries=0, 
			timeout=60
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
		}
		if TEMP is not None: params["temperature"] = TEMP
		stream = client.chat_stream(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.choices[0].delta.content
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nMistral's response for model: {MODEL}\n{e}"


async def OpenAIResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = OpenAI(api_key=get_provider_setting('OpenAI', 'api_key'))
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
		}
		if TEMP is not None: params["temperature"] = TEMP
		stream = client.chat.completions.create(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.choices[0].delta.content
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nOpen AI's response for model: {MODEL}\n{e}"


async def GoogleResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		genai.configure(api_key=get_provider_setting('Google', 'api_key'))
		model = genai.GenerativeModel(
			model_name=MODEL,
		)
		# safety_settings = {
		#   'HARM_CATEGORY_HATE_SPEECH': HarmBlockThreshold.BLOCK_NONE,
		#   'HARM_CATEGORY_HARASSMENT': HarmBlockThreshold.BLOCK_NONE,
		#   'HARM_CATEGORY_SEXUALLY_EXPLICIT': HarmBlockThreshold.BLOCK_NONE,
		#   'HARM_CATEGORY_DANGEROUS': HarmBlockThreshold.BLOCK_NONE,
		# }
		# params = {
		#     "safety_settings": safety_settings,
		# }
		params = {}
		if TEMP is not None:
			params["generation_config"] = {
				"temperature": TEMP,
			}
		# request_options={"timeout": 30},
		timeout = get_provider_setting('Google', 'timeout')
		if timeout is not None:
			params["request_options"] = {"timeout": timeout}
		stream = model.generate_content(
			prompt,
			stream=True,
			**params
		)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				# not valid: stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.text
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nGoogle's response for model: {MODEL}\n{e}"


async def AnthropicResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = anthropic.Anthropic(
			api_key=get_provider_setting('Anthropic', 'api_key'),
			timeout=30,
			max_retries=0,
		)
		params = {
			"messages": [{"role": "user", "content": prompt}],
			"model": MODEL,
			"max_tokens": get_provider_setting('Anthropic', 'max_tokens'), # error if this is missing <= why?
			}
		if TEMP is not None: params["temperature"] = TEMP
		with client.messages.stream(**params) as stream:
			for content in stream.text_stream:
				if ABORT:
					set_abort(False)
					yield f"\n... response stopped by button click."
					stream.close()  # properly close the generator
					break  # exit the generator cleanly
				if isinstance(content, str):
					cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
					yield cleaned_content
				else:
					yield "" # handle None or any unexpected type by yielding an empty string

	except Exception as e:
		yield f"Error:\nAnthropic's response for model: {MODEL}\n{e}"


async def GroqResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = AsyncGroq(
			api_key=get_provider_setting('Groq', 'api_key'), 
			max_retries=0, 
			timeout=30.0,
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
			"stop": None,
		}
		if TEMP is not None: params["temperature"] = TEMP
		try:
			stream = await client.chat.completions.create(**params)
			async for chunk in stream:
				if ABORT:
					set_abort(False)
					yield f"\n... response stopped by button click."
					await stream.close()  # properly close the generator
					break  # exit the generator cleanly
				content = chunk.choices[0].delta.content
				if isinstance(content, str):
					cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
					yield cleaned_content
				else:
					yield " "  # handle None or any unexpected type by yielding an empty string
		except GeneratorExit:
			await stream.close()  # ensure the generator is closed even on GeneratorExit
			return  # exit gracefully after handling GeneratorExit
	except Exception as e:
		yield f"Error:\nGroq's response for model: {MODEL}\n{e}"


async def LMStudioResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = OpenAI(base_url="http://localhost:5506/v1", 
			api_key="lm-studio", 
			max_retries=0, 
			timeout=60.0,
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
		}
		if TEMP is not None: params["temperature"] = TEMP
		stream = client.chat.completions.create(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk.choices[0].delta.content
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nLM Studio's response for model: {MODEL}\n{e}"


async def OllamaResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	try:
		client = OllamaClient(
			host='http://localhost:11434',
			timeout=30,
		)
		params = {
			"model": MODEL,
			"messages": [{"role": "user", "content": prompt}],
			"stream": True,
		}
		if TEMP is not None: 
			params["options"] = {"temperature": TEMP}
		stream = client.chat(**params)
		for chunk in stream:
			if ABORT:
				set_abort(False)
				yield f"\n... response stopped by button click."
				stream.close()  # properly close the generator
				break  # exit the generator cleanly
			content = chunk['message']['content']
			if isinstance(content, str):
				cleaned_content = content.replace("**", "") # no ugly Markdown in plain text
				yield cleaned_content
			else:
				yield ""  # handle None or any unexpected type by yielding an empty string
	except Exception as e:
		yield f"Error:\nOllama's response for model: {MODEL}\n{e}"

# **********************************
# end of backend provider API stuff.
# **********************************

# aidetour stuff:
async def AidetourResponseStreamer(prompt):
	if MODEL is None: yield ""; return # sometimes model list is empty
	if MODEL == "Info":
		TOTAL_MODELS = sum(len(models) for models in PROVIDER_MODELS.values())
		# ignore the extra aidetour pretend stuff:
		total_ai_providers = len(PROVIDERS) - 1
		ignored = len(PROVIDER_MODELS["Aidetour"])
		total_ai_models = TOTAL_MODELS - ignored
		yield f"Client IP: {ui.context.client.ip}\n"
		yield f"Host: {HOST}\n"
		yield f"Port: {PORT}\n\n"
		yield f"*** AI Providers and their LLM Models ***\n"
		yield f"In total there are {total_ai_models} models available from {total_ai_providers} providers.\n"
		for index, provider in enumerate(PROVIDERS, start=0):
			if provider == "Aidetour":
				continue
			models = PROVIDER_MODELS.get(provider, [])
			model_count = len(models)
			yield f"\n(#{index}). {provider}  models: {model_count} ...\n"
			for m, model in enumerate(models, start=1):
				yield f"{m}. {model}\n"
		pvi = sys.version_info
		python_version = f"{pvi.major}.{pvi.minor}.{pvi.micro}"
		nicegui_version = nv
		anthropic_version = av
		genai_version = ggv
		groq_version = gv
		mistralai_version = mv
		ollama_version = ov
		openai_version = oav
		yield f"\n\n--- Software Versions ---\n"
		yield f"Aidetour: 1.0.0\n"
		yield f"Python: {python_version}\n"
		yield f"pip: {pipv}\n"
		yield f"NiceGUI: {nicegui_version}\n"
		yield f"FastAPI: {fav}\n"
		yield f"Uvicorn: {uvv}\n"
		yield f"PyWebView: {pwv}\n"
		yield f"\n--- AI Provider's SDK versions ---\n"
		yield f"1. Anthropic: {anthropic_version}\n"
		yield f"2. Google Generativeai: {genai_version}\n"
		yield f"3. Groq: {groq_version}\n"
		yield f"4. MistralAI: {mistralai_version}\n"
		yield f"5. Ollama: {ollama_version}\n"
		yield f"6. OpenAI: {openai_version}\n"
		yield f"* note: many providers are somewhat OpenAI API compatible\n"
	else:
		import random
		import string
		yield f"The following is a README, documentation, and stream tester all-in-one.\n"
		yield f"I wish all of the AI chatters in the universe 🪐:\n"
		yield f"- were like me 🤓\n"
		yield f"- maintained a simple plain text chat history file, for both human and AI\n"
		yield f"- denoted the ME: and the AI: in their chat history (ok, some of them do this already)\n"
		yield f"- denoted which Provider and Model are being used, so we know who we are chatting with\n"
		yield f"- timestamped the chat with a human readable date and time\n"
		yield f"- would allow us to 'Insert a Note' with a timestamp into the chat history\n"
		yield f"- were easy to scroll ⬇️ to the bottom and ⬆️ to the top\n"
		yield f"- could CLEAR to forget and start a new chat (ok, they all do this already)\n"
		yield f"- could COPY an entire chat to the clipboard\n"
		yield f"- could SAVE an entire chat as a plain text file ... none of them; just say no to JSON, Markdown, and Word (no way!)\n"
		yield f"- would allow us to use your cursor/pointer to select text in this box to copy/paste just what you need  (ok, most of them do this already)\n"
		yield f"- would remove those annoying '**' like I do (again, just say no Markdown)\n"
		yield f"- could continue the same chat across several AI models; me wonders if they learn from each other 🤫\n"
		yield f"- used NiceGUI 👨🏽‍🚀 and worked in many web 🕸️ browsers\n"
		yield f" \n"
		yield f"\nWater's 🌊 fine, let's test the stream:\n"
		for i in range(10):
			# fixme = less sleep!!
			await asyncio.sleep(0.2)
			random_word = "".join(
				random.choices(string.ascii_lowercase, k=random.randint(1, 13))
			)
			yield f" A{random_word}E-{i+1} "  # either front/end space works
		yield f" \n"
		yield f"\nYou are 'go at throttle up' 🚀\n"
		yield f"Enjoy! ☮️\n\n"
		yield f"p.s. click on CLEAR to get rid of this, I await your return! 🙉\n"

# map the PROVIDERS to their corresponding streamer
STREAMER_MAP = {
	"Aidetour": AidetourResponseStreamer,
	"Anthropic": AnthropicResponseStreamer,
	"Google": GoogleResponseStreamer,
	"Groq": GroqResponseStreamer,
	"Mistral": MistralResponseStreamer,
	"OpenAI": OpenAIResponseStreamer,
	"OpenRouter": OpenRouterResponseStreamer,
	"Perplexity": PerplexityResponseStreamer,
	"LMStudio": LMStudioResponseStreamer,
	"Ollama": OllamaResponseStreamer,
}

async def run_streamer(provider, prompt):
	streamer_function = STREAMER_MAP.get(provider)
	if streamer_function is None:
		yield f"No streamer found for provider: {provider}"
		return
	async for chunk in streamer_function(prompt):
		if ABORT:
			set_abort(False)
			await asyncio.sleep(1.0)
			return  # exit the generator cleanly?
		yield chunk


@ui.page("/busy")
async def busy_page():
	ui.separator()
	ui.label(
		"Aidetour Chat is currently in use by another user or running in an existing session."
	)
	ui.separator()
	ui.label(
		"You must end the other session or shutdown the app, then try again."
	).classes("text-red")
	ui.separator()

def append_splash_text(model_log, providers_models, new_text: str):
	providers_models.append(new_text)
	model_log.set_content('<br>'.join(providers_models))

async def make_a_splash():
	global splash_popup, model_log
	with ui.dialog() as splash_popup:
		splash_popup.props("persistent")
		splash_popup.classes("blur(4px)")
		with splash_popup, ui.card().classes("w-96"):
			ui.image("/images/Aidetour.png").classes("w-64 h-64 mx-auto")
			ui.label("Welcome to Aidetour Chat").classes("text-2xl font-bold text-center mt-2")
			with ui.row().classes("justify-center mt-2"):
				ui.spinner('grid', size='sm')
				ui.label("Please standby . . .").classes("text-red text-sm text-center mt-2 ml-2")
			model_log = ui.html().classes("text-sm mt-2").style('white-space: pre-wrap')
			providers_models = []
	splash_popup.open()
	return splash_popup, model_log, providers_models


@ui.page('/', response_timeout=999)
async def _main_page(request: Request) -> None:
	global ACTIVE_SESSION, CHAT_HISTORY, MESSAGE_CONTAINER
	global SEND_BUTTON, THINKING_LABEL, TEMP
	global SPLASHED, PROVIDER, MODEL, TOTAL_MODELS, provider_select
	global APP_DB_SETTINGS, PROVIDER_DB_SETTINGS

	if ACTIVE_SESSION:
		return RedirectResponse('/busy')
	
	ACTIVE_SESSION = True

	read_settings_from_db()

	CURRENT_PRIMARY_COLOR = APP_DB_SETTINGS.get('primary_color', '#4CAF50') # green
	ui.colors(primary=str(CURRENT_PRIMARY_COLOR))

	DARKNESS = ui.dark_mode()
	dm = APP_DB_SETTINGS.get('dark_mode', True)
	DARKNESS.set_value(dm)

	splash, model_log, providers_models = await make_a_splash()
	model_count = await aidetour_models()

	PROVIDER = "Aidetour"
	MODEL = PROVIDER_MODELS.get(PROVIDER, ['Aidetour'])[0]

	# using ui.run_javascript is only possible after a client is connected
	# ... doesn't help: "TimeoutError: JavaScript did not respond within 1.0 s"
	await ui.context.client.connected()

	def update_model_choices():
		global PROVIDER, MODEL
		selected_provider = provider_select.value
		available_models = PROVIDER_MODELS.get(selected_provider, [])
		model_select.options = available_models
		model_select.value = available_models[0] if available_models else ''
		model_select.update()

	def update_temp(e):
		global TEMP
		TEMP = e # .sanitize() is not needed as rounding happens when focus is change

	async def windowInnerHeight():
		window_innerHeight = await ui.run_javascript(f"window.innerHeight")
		return window_innerHeight

	async def windowInnerWidth():
		window_innerWidth = await ui.run_javascript(f"window.innerWidth")
		return window_innerWidth

	async def copy_me_ai_chat_pair(me_message, response_message):
		# TL;DR = this error happens a lot when using: ui.run_javascript
		#   "TimeoutError: JavaScript did not respond within 1.0 s"
		# ... in testing the following does not fix it:
		#   await ui.context.client.connected()
		#   await asyncio.sleep(0.5)
		# why? 
		# ... because the error mostly happens due to not finding the html element, and this:
		#   text = await ui.run_javascript(f"getElement('c{me_message.id}').innerText")
		#   ... the nicegui-way does not find the element, with or without the missing 'c'
		# ... looking via Chrome dev tools Elements, it shows: id="c34" and not id="34":
		# <div class="q-message q-message-sent" id="c34">
		#   <div class="q-message-container row items-end no-wrap reverse">
		#       <div class="">
		#           <div class="q-message-text q-message-text--sent">
		#               <div class="q-message-text-content q-message-text-content--sent"><div>
		#                   <div id="c35">
		#                       <pre style="white-space: pre-wrap; user-select: text;">ME: list the planets</pre>
		#                   </div>
		#               </div>
		#               <div class="q-message-stamp">09:49:47 AM on Sunday, Sep 01, 2024</div>
		#           </div>
		#       </div>
		#   </div>
		# </div>
		text = "\n"
		text += await ui.run_javascript(f"return document.getElementById('c{me_message.id}').innerText;")
		text += await ui.run_javascript(f"return document.getElementById('c{response_message.id}').innerText;")
		filtered_lines = (
			("\n" + re.sub(r"\*\*|##|###", "", line).strip() if re.sub(r"\*\*|##|###", "", line).strip() == "AI:" 
			 else re.sub(r"\*\*|##|###", "", line).strip())
			for line in text.splitlines() 
			if re.sub(r"\*\*|##|###", "", line).strip() != "content_paste"
		)
		text_without_markdown_and_content_paste = "\n".join(filtered_lines)
		text_without_markdown_and_content_paste += "\n"
		pyperclip.copy(text_without_markdown_and_content_paste)
		ui.notify("Copied ME/AI pair to clipboard", timeout=3)

	async def copy_chat():
		text = await ui.run_javascript(f"getElement({MESSAGE_CONTAINER.id}).innerText")
		# this also works and may make more sense than using: MESSAGE_CONTAINER.id:
		# text = await ui.run_javascript(f"return document.getElementById('scrollable').innerText;")

		# note: let's use a single generator expression to iterate through the lines of text, 
		# to filter by removing Markdown: "**", "##", "###", stripping whitespace, 
		# and ignoring lines with just "content_paste" (i.e. copy button)
		# ... which should be more efficient for large chat texts 
		# because it avoids unnecessary list creation and 
		# performs both filtering operations in a single pass:
		filtered_lines = (
			re.sub(r"\*\*|##|###", "", line).strip() 
			for line in text.splitlines() 
			if re.sub(r"\*\*|##|###", "", line).strip() != "content_paste"
		)
		text_without_markdown_and_content_paste = "\n".join(filtered_lines)
		pyperclip.copy(text_without_markdown_and_content_paste)
		ui.notify("Copied to clipboard", timeout=3)

	async def clear_chat():
		global MESSAGE_CONTAINER, CHAT_HISTORY
		MESSAGE_CONTAINER.clear()
		CHAT_HISTORY = ""

	async def save_chat(text) -> None:
		text = await ui.run_javascript(f"getElement({MESSAGE_CONTAINER.id}).innerText")
		filename = await app.native.main_window.create_file_dialog(
			dialog_type=webview.SAVE_DIALOG,
			allow_multiple=False, 
			file_types=("Text file (*.txt)",), 
			save_filename="aidetour_chat_history.txt",
		)
		if filename is not None:
			try:
				with open(filename, "w") as f:
					filtered_lines = (
						re.sub(r"\*\*|##|###", "", line).strip() 
						for line in text.splitlines() 
						if re.sub(r"\*\*|##|###", "", line).strip() != "content_paste"
					)
					text_without_markdown_and_content_paste = "\n".join(filtered_lines)
					f.write(text_without_markdown_and_content_paste)
					ui.notify("Chat history saved.")
			except Exception as e:
				ui.notify(f"Error saving file: {e}")
		else:
			ui.notify("Filename is unknown/none, so unable file save!")

	async def send() -> None:
		global CHAT_HISTORY, SEND_BUTTON, THINKING_LABEL
		prompt_sent = bool(user_prompt.value and user_prompt.value.strip())
		if PROVIDER == 'Aidetour':
			pass
		elif not prompt_sent:
			ui.notify("Prompt is empty, please type something.")
			return
		if PROVIDER == 'Aidetour':
			pass
		else:
			CHAT_HISTORY += user_prompt.value
		question = user_prompt.value
		user_prompt.value = ''

		SEND_BUTTON.set_enabled(False)  # disable the button
		THINKING_LABEL.set_visibility(True)
		ABORT_STREAM.set_visibility(True)

		# track the elapsed time from sent message until end of response message:
		start_time = time.time()

		with MESSAGE_CONTAINER:
			timestamp = datetime.datetime.now().strftime("%I:%M:%S %p") + " on " + datetime.datetime.now().strftime("%A, %b %d, %Y")
			me_message = ui.chat_message(sent=True, stamp=timestamp)
			me_message.clear()
			with me_message:
				if PROVIDER == 'Aidetour' and MODEL == 'Insert a Note':
					ui.html(f"<pre style='white-space: pre-wrap;'>\nAidetour:   [{MODEL}]  {timestamp}:\n{question}</pre>")
				elif PROVIDER == 'Aidetour':
					pass
				else:
					ui.html(f"<pre style='white-space: pre-wrap;'>ME:   {PROVIDER} - {MODEL} - temp: {TEMP}  {timestamp}\n{question}</pre>")

			response_message = ui.chat_message(sent=False, stamp=timestamp)

			spinner = ui.spinner('grid', size='sm')

		response = ''

		try:
			await ui.context.client.connected() # necessary?
			await ui.run_javascript('scrollable.scrollTo(0, scrollable.scrollHeight)')
		except Exception as e:
			pass # no biggie, if can't scroll as user can do it manually

		if PROVIDER == 'Aidetour' and MODEL == 'Insert a Note':
			# just 'Insert a Note' in as ME: and no need to stream it
			await ui.run_javascript('scrollable.scrollTo(0, scrollable.scrollHeight)')
		else:
			async for chunk in run_streamer(PROVIDER, CHAT_HISTORY):
				if ABORT:
					set_abort(False)
					break
				await ui.context.client.connected() # necessary?
				response_message.clear() # cleared for each chunk = why?
				with response_message:
					response += "" if chunk is None else chunk
					if PROVIDER == 'Aidetour':
						ui.html(f"<pre style='white-space: pre-wrap;'><br>Aidetour:   [{MODEL}]  {timestamp}:\n{response}</pre>")
					else:
						ui.html(f"<pre style='white-space: pre-wrap;'><br>AI:\n{response}</pre>")
				
				# show elapsed time, clock time, calendar date, and update stamp in ui.chat_message:
				end_time = time.time()
				elapsed_time = end_time - start_time
				minutes, seconds = divmod(elapsed_time, 60)
				end_time_date = f"{int(minutes)}:{seconds:.2f} elapsed at " + datetime.datetime.now().strftime("%I:%M:%S %p") + " on " + datetime.datetime.now().strftime("%A, %b %d, %Y")
				response_message.props(f'stamp="{end_time_date}"')
				response_message.update()

				try:
					await ui.context.client.connected() # necessary?
					await ui.run_javascript('scrollable.scrollTo(0, scrollable.scrollHeight)')
				except Exception as e:
					THINKING_LABEL.set_visibility(False)
					SEND_BUTTON.set_enabled(True)

		# ************************
		# *** stream has ended ***
		# ************************

		THINKING_LABEL.set_visibility(False)
		SEND_BUTTON.set_enabled(True)
		ABORT_STREAM.set_visibility(False)

		# fixme nice for testing without repeated typing:
		# user_prompt.value = 'write a story about Japan, take your time, and use lots of words'

		try:
			# fixme best solution is to deny(can't click) user all of the buttons! except for quit/exit
			with MESSAGE_CONTAINER:
				ui.button(
					icon='content_paste', 
					on_click=lambda: copy_me_ai_chat_pair(me_message, response_message)
					) \
					.tooltip("copy this section (ME/AI) to the clipboard") \
					.props('icon=content_paste round flat') \
					.style("padding: 1px 1px; font-size: 9px;")
				ui.html(f"<pre style='white-space: pre-wrap;'><br></pre>")
			await ui.run_javascript('scrollable.scrollTo(0, scrollable.scrollHeight)')
			MESSAGE_CONTAINER.remove(spinner)
		except Exception as e:
			ui.notify(f"The chat history was cleared before response finished.\nError: {e}")

	# ************************
	# page layout and elements:
	# ************************

	# custom css to remove the one pointy corner (that's used with avatar's) 
	# and ensure all corners are rounded:
	ui.add_head_html('''
	<style>
		/* remove the pointy pseudo-element */
		.q-message-text::before {
			content: none !important;
			display: none !important;
		}

		/* ensure all corners of the message bubble are rounded */
		.q-message-text {
			border-radius: 12px !important;
			background-color: transparent !important;
			border: 1px solid #B0B0B0 !important; /* add a neutral grey border */
		}

		.q-message-text-content {
			border-radius: 12px !important;
			background-color: transparent !important;
		}

		.dark .q-message-text-content {
			color: #cccccc !important; /* text color for dark mode */
		}
	</style>
	''')

	# using ui.run_javascript is only possible after a client is connected
	# ... doesn't help: "TimeoutError: JavaScript did not respond within 1.0 s"
	await ui.context.client.connected()

	wih = await windowInnerHeight() - 300 # leave some empty space at bottom of page
	# wiw = await windowInnerWidth() - 200 # not needed

	with ui.header().classes('bg-transparent text-gray-800 dark:text-gray-200 z-10 mt-0').style('margin-top: 0; padding-top: 0;'):

		with ui.row().classes("w-full no-wrap mb-0 mt-5 ml-0").style('min-width: 100%; margin-left: 0; justify-content: left;'):

			# SEND button and thinking label
			with ui.row():
				SEND_BUTTON = (
					ui.button(
						icon="send",
						on_click=send,
					)
					.props('outline')
					.classes("ml-0 mr-2 text-sm px-4 py-2 mt-3")
					.style(
						"box-shadow: 0 0 1rem 0 #546e7a; transition: transform 0.3s ease;"
					)
					# .props('icon=img:/images/Aidetour.png')
				)

				with SEND_BUTTON:
					with ui.tooltip('').props("flat fab"):
						ui.html("send Prompt")
						# ui.html(
						#   "<p>Enter a <b>Prompt</b> below,<br>"
						#   "then click this button to send<br>"
						#   "to the selected AI Provider/Model.</p>"
						# )
				THINKING_LABEL = ui.spinner('grid', size='sm') # , color='green')
				THINKING_LABEL.set_visibility(False)

			# maintains case sensitivity in ui.select:
			ui.add_head_html(
				"<style> .prevent-uppercase { text-transform: none !important; } </style>"
			)

			with ui.column().classes("flex-1 w-1/3 p-0 ml-15"):
				provider_select = (
					ui.select(
						PROVIDERS,
						label=f"? Providers:",
						value=PROVIDER,
						on_change=lambda e: update_model_choices(),
					)
					.classes("w-48 prevent-uppercase")
					.bind_value(globals(), "PROVIDER")  # bind the selected value to the global PROVIDER variable
				)

			with ui.column().classes("flex-1 w-1/3 p-0 mr-2"):
				# model_select = (
				#   ui.select(
				#       PROVIDER_MODELS[PROVIDER],
				#       value=MODEL,
				#       label="Models:",
				#   ).classes("w-64 prevent-uppercase")
				#   .bind_value(globals(), "MODEL")  # bind the selected value to the global MODEL variable
				# )

				# user can type to search/select:
				model_select = (
					ui.select(
						value=MODEL,
						label="Models:",
						options=PROVIDER_MODELS[PROVIDER], 
						with_input=True,
					)
					.props("clearable")
					.props("spellcheck=false")
					.props("autocomplete=off")
					.props("autocorrect=off")
					.bind_value(globals(), "MODEL")  # bind the selected value to the global MODEL variable
				)

			provider_select.on_value_change(
				lambda e: model_select.props(
					f'label="{len(PROVIDER_MODELS[PROVIDER])} Models:"' if PROVIDER_MODELS.get(PROVIDER) else 'label="No Models Available"'
				) if e.value != "Aidetour" else model_select.props('label="Models:"')
			)

			with ui.column().classes("flex-1 w-1/3 p-0 mt-2"):
				# use gap-0 to make button/knob closer together:
				with ui.row().classes("mb-0 mt-0 ml-0 gap-0 items-center"):
					ui.button(
						icon='dew_point', #'device_thermostat',
						on_click=lambda e: update_temp(None)
					) \
					.tooltip("clear/reset Temp") \
					.props('no-caps flat round')

					ui.knob(
						None,
						min=None,
						max=2,
						step=0.1,
						show_value=True, 
						color=CURRENT_PRIMARY_COLOR,
						# center_color='red',
						track_color='blue-grey-7',
						size='xl'
					) \
					.bind_value(globals(), "TEMP") \
					.tooltip("Temperature")

		with ui.row().classes("w-full mb-0 mt-0 ml-0"):
			user_prompt = (
				ui.textarea(label="Prompt:", placeholder="Enter your prompt here...")
				.classes("w-full")
				.props("clearable")
				.props("rows=3")
				.props("spellcheck=false")
				.props("autocomplete=off")
				.props("autocorrect=off")
				.props("tabindex=0")
				.classes('w-full self-center')
			)

		# fixme nice for testing without repeated typing:
		# user_prompt.value = 'write a story about Japan, take your time, and use lots of words'

		with ui.row().classes("w-full items-center mb-0.1 space-x-2"):

			# https://fonts.google.com/icons?icon.query=clip&icon.size=24&icon.color=%23e8eaed

			async def scroll_to_bottom():
				await ui.run_javascript('scrollable.scrollTo(0, scrollable.scrollHeight)')

			ui.button(icon='arrow_downward', on_click=scroll_to_bottom) \
			.tooltip("scroll to bottom") \
			.props('no-caps flat fab-mini')

			async def scroll_to_top():
				await ui.run_javascript('scrollable.scrollTo(0, 0)')

			ui.button(icon='arrow_upward', on_click=scroll_to_top) \
			.tooltip("scroll to top") \
			.props('no-caps flat fab-mini')

			ui.button(icon='content_paste', on_click=copy_chat) \
			.tooltip("copy entire chat history to clipboard") \
			.props('no-caps flat fab-mini')

			ui.button(icon="delete_sweep", on_click=clear_chat) \
			.tooltip("clear chat history") \
			.props('no-caps flat fab-mini')

			ui.button(icon='save_as', on_click=save_chat) \
			.props('no-caps flat fab-mini') \
			.tooltip("save entire chat history as a text file")

			def update_tooltip(button, tooltip_text):
				button.props(f'tooltip="{tooltip_text}"')

			with ui.element():
				dark_button = ui.button(icon='dark_mode', on_click=lambda: [DARKNESS.set_value(True), update_tooltip(dark_button, 'be Dark')]) \
					.props('flat fab-mini').tooltip('be Dark').bind_visibility_from(DARKNESS, 'value', value=False)
				light_button = ui.button(icon='light_mode', on_click=lambda: [DARKNESS.set_value(False), update_tooltip(light_button, 'be Light')]) \
					.props('flat fab-mini').tooltip('be Light').bind_visibility_from(DARKNESS, 'value', value=True)

			chat_settings = ui.button(icon='settings', on_click=lambda: chat_settings_dialog()) \
			.tooltip("Chat    Settings") \
			.props('no-caps flat fab-mini')

			ui.button(icon='settings_power', on_click=app.shutdown) \
			.tooltip("Quit") \
			.props('no-caps flat fab-mini')

			ABORT_STREAM = ui.button(
				icon='content_cut',
				on_click=lambda e: set_abort(True)
			) \
			.tooltip("stop AI's response") \
			.props('flat outline round color=red').classes('shadow-lg')

			ABORT_STREAM.set_visibility(False)


	with ui.element('div').classes('flex flex-col min-h-full w-full max-w-3xl mx-auto'):
		MESSAGE_CONTAINER = (
			ui.element("div")
			.classes(
				"aidetour-chat-history w-full overflow-auto p-2 rounded flex-grow"
			)
			.props('id="scrollable"')
			.style(f'height: {wih}px; font-size: 15px !important;')
		)
		ui.separator().props("size=4px color=primary") # insinuate bottom of chat history

	def check_splashed_and_providers():
		if SPLASHED:
			if len(PROVIDERS) - 1 <= 0:
				ui.html('<style>.multi-line-notification { white-space: pre-line; }</style>')
				ui.notification(
				    '________________ No AI providers were discovered! ______________ \n'
				    'Please click on Chat Settings to add/change AI provider API keys, \n'
				    'or if you are using Ollama or LM Studio  \n'
				    'ensure both/either are running before starting Aidetour Chat. \n'
				    'note: Chat Settings is the gear icon in the button bar below.',
				    multi_line=True,
				    classes='multi-line-notification',
					type='negative', 
					close_button='⚙️ click after reading',
					position='top',
					# spinner=True,
					timeout=0 # wait for user to click close_button
				)
				chat_settings.props('color=negative')
				chat_settings.tooltip('Chat 😱 Settings')
				chat_settings.update()  # refresh the UI to reflect changes

			splash_timer.cancel()

	# await asyncio.sleep(3)
	splash_timer = ui.timer(2, check_splashed_and_providers)

	async def loading_models(i):
		global TOTAL_MODELS, PROVIDERS
		# Let's intentionally slow down the following operations.
		# For some providers, these actions happen too quickly to be noticed in the splash popup.
		if i > 0:
			append_splash_text(model_log, providers_models, f'Creating a list of AI models for each provider...')
			await asyncio.sleep(0.03)
			model_count = await anthropic_models()
			append_splash_text(model_log, providers_models, f"Anthropic offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await google_models()
			append_splash_text(model_log, providers_models, f"Google offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await groq_models()
			append_splash_text(model_log, providers_models, f"Groq offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await lm_studio_models()
			append_splash_text(model_log, providers_models, f"LM Studio offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await mistral_models()
			append_splash_text(model_log, providers_models, f"Mistral offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await ollama_models()
			append_splash_text(model_log, providers_models, f"Ollama offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await openai_models()
			append_splash_text(model_log, providers_models, f"OpenAI offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await perplexity_models()
			append_splash_text(model_log, providers_models, f"Perplexity offers {model_count} models.")
			await asyncio.sleep(0.01)
			model_count = await openrouter_models()
			append_splash_text(model_log, providers_models, f"OpenRouter offers {model_count} models.")
			await asyncio.sleep(1)
			if model_count <= 0:
				append_splash_text(model_log, providers_models, 
					f"{'*' * 50}<br>OpenRouter is known for timing out when getting a list of models!<br>{'*' * 50}"
				)
			await asyncio.sleep(0.01)
			await loading_models(i-1) # recursive?
		else:
			TOTAL_MODELS = sum(len(models) for models in PROVIDER_MODELS.values())
			# ignore the extra aidetour fake model stuff:
			ignored = len(PROVIDER_MODELS["Aidetour"])
			total_ai_providers = len(PROVIDERS) - 1 # ignore aidetour provider
			total_ai_models = TOTAL_MODELS - ignored
			append_splash_text(model_log, providers_models, f"With {total_ai_models} models available from {total_ai_providers} providers.")
			append_splash_text(model_log, providers_models, f"Enjoy!")
			splash.close()
			splash.clear() # removes the hidden splash ui.dialog

	def on_loading_models_complete(_):
		global SPLASHED
		# note: the underscore above is a way of saying, 
		#       "I acknowledge this argument is passed, but I don't need to use it." 
		#       This is common in situations like callbacks where the parameter is 
		#       necessary syntactically but not functionally required in the callback logic.
		provider_select.options = PROVIDERS  # update the options in the select element
		provider_select.props(f'label="{len(PROVIDERS) - 1} Providers:"')
		provider_select.update()  # refresh the UI to reflect changes
		# because of nicegui's webserver-ness(fastapi/uvicorn); let's remember we splashed already:
		SPLASHED = True

	if not SPLASHED:
		task = asyncio.create_task(loading_models(1))
		task.add_done_callback(on_loading_models_complete)


	async def chat_settings_dialog():
		global CURRENT_PRIMARY_COLOR
		with ui.dialog() as settings_popup:
			settings_popup.props("persistent")
			settings_popup.props("maximized")
			with settings_popup, ui.card():
				with ui.column():
					with ui.row().classes("w-full items-center mb-0.1 space-x-2"):
						ui.space()
						ui.label('Aidetour Chat Settings').style("font-size: 20px; font-weight: bold").classes("m-0")

						def save_settings(host_input, port_input, window_width_input, window_height_input, dark_mode_switch, primary_color, provider_inputs):
							# ui.notify('Saving ... any errors found will revert to the default values.', color='orange')
							set_app_setting('host', host_input.value)
							set_app_setting('port', convert_to_int(port_input.value, PORT))
							set_app_setting('window_width', convert_to_int(window_width_input.value, WIDTH))
							set_app_setting('window_height', convert_to_int(window_height_input.value, HEIGHT))
							set_app_setting('dark_mode', True if dark_mode_switch.value else False)
							set_app_setting('primary_color', primary_color)
							for provider, inputs in provider_inputs.items():
							  for key, key_object in inputs.items():
								  if key == 'timeout':
									  set_provider_setting(provider, key, convert_to_int(key_object.value, None))
								  else:
									  set_provider_setting(provider, key, key_object.value)
							ui.notify('Settings saved, but the changes only apply after restarting Aidetour Chat.')
							chat_settings.props('color=primary')
							chat_settings.tooltip(f"Chat Settings")
							chat_settings.update()  # refresh the UI to reflect changes

						ui.space()
						ui.button(icon='save_as', on_click=lambda: save_settings(
							host_input, 
							port_input, 
							window_width_input, 
							window_height_input, 
							dark_mode_switch,
							get_primary_color(),
							provider_inputs
						)).tooltip("Save to Aidetour_Chat_Settings.json").props('no-caps flat dense')

						async def close_clear_dialog():
							settings_popup.close()
							settings_popup.clear() # removes the hidden settings_popup ui.dialog

						ui.button(
							icon='close', 
							on_click=close_clear_dialog
							) \
							.tooltip("Close") \
							.props('no-caps flat fab-mini')

						with ui.avatar(color=None, square=True, size='xl'):
						  ui.image('/images/Aidetour.png')
						  with ui.tooltip().classes('bg-transparent'):
							  ui.image('/images/Aidetour.png').classes('w-64')
							  ui.label(f"Aidetour Chat Settings").classes("text-2xl font-bold text-center mt-4").style('background-color: green;')

					with ui.column().classes('mb-2'):
						ui.label('App Settings:').style('font-size: 18px; font-weight: bold;')

						def validate_port(value, port_input):
							try:
								port_value = int(value)
								if 81 <= port_value <= 65535:
									pass
								else:
									ui.notify(f"Port must be between 81 and 65535.", color='red')
									port_input.value = ''
							except ValueError:
								ui.notify("Port must be a number.", color='red')
								port_input.value = ''
							except Exception:
								ui.notify("Port must be a number.", color='red')
								port_input.value = ''
							port_input.update()

						with ui.row().classes('w-full items-center'):
							host_input = ui.input(
								label='Host', 
								value=get_app_setting('host')) \
								.classes('w-1/5') \
								.props("spellcheck=false") \
								.props("autocomplete=off") \
								.props("autocorrect=off")

							port_input = ui.input(
								label='Port', 
								value=get_app_setting('port'), 
								) \
								.classes('w-1/5') \
								.props("spellcheck=false") \
								.props("autocomplete=off") \
								.props("autocorrect=off") \
								.on('blur', lambda e: validate_port(e.sender.value, port_input))

							window_width_input = ui.input(
								label='Width', 
								value=get_app_setting('window_width')) \
								.classes('w-1/5') \
								.props("spellcheck=false") \
								.props("autocomplete=off") \
								.props("autocorrect=off")

							window_height_input = ui.input(
								label='Height', 
								value=get_app_setting('window_height')) \
								.classes('w-1/5')

						with ui.row().classes('w-full items-center'):
							dark_light = get_app_setting('dark_mode')
							dark_light = ""
							if dark_light is None or dark_light == "":
								dark_light = DARKNESS.value
							ui.label('Light or Dark').classes('ml-2 mr-0')
							dark_mode_switch = ui.switch(value=dark_light).classes('ml-0').tooltip("select light or dark mode")

							def set_primary_color(color):
								global CURRENT_PRIMARY_COLOR
								CURRENT_PRIMARY_COLOR = color
								js_code = f"""
								document.getElementById('picker').style.setProperty('color', '{color}', 'important');
								"""
								ui.run_javascript(js_code)

							def get_primary_color():
								return CURRENT_PRIMARY_COLOR

							with ui.button(icon='palette').props('id=picker').props('no-caps flat fab-mini').classes('ml-4').tooltip("select primary color") as button:
								button = ui.color_picker(on_pick=lambda e: set_primary_color(e.color))
								button.q_color.props('''default-view=palette no-header no-footer :palette="['#6200ea', '#ff0000', '#ff8000', '#d6d600', '#4CAF50', '#00a3a3', '#007bf5', '#7b00f5', '#d600d6', '#333333']"''')
								# button.q_color.props('default-view=palette no-header no-footer') # all colors
							ui.label('color changes after relaunching app').classes('ml-0').style('font-size: 10px; font-style: italic; color: #546e7a;')

					with ui.row().classes('w-full items-center'):
						ui.label('Provider Settings:').style('font-size: 18px; font-weight: bold; margin-bottom: 8px;')
						ui.space()
						ui.label("* be careful as these settings contain API keys, i.e. money!").style('font-size: 12px; font-style: italic; margin-bottom: 8px; color: #546e7a;')

						provider_inputs = {}
						with ui.column().classes('w-full'):
							for provider in PROVIDERS_SETTINGS:
								provider_name = provider['name']
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

										if provider_name in ['OpenRouter', 'Perplexity', 'LMStudio']:
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

										if provider_name in ['OpenRouter', 'LMStudio', 'Perplexity', 'Mistral']:
											inputs['timeout'] = ui.input(
												label='Timeout', 
												value=get_provider_setting(provider_name, 'timeout')) \
											.classes('w-full mb-2') \
											.props("spellcheck=false") \
											.props("autocomplete=off") \
											.props("autocorrect=off")

										provider_inputs[provider_name] = inputs

							ui.separator().props("size=4px color=primary") # insinuate bottom of settings

		settings_popup.open()

# def startup():
#     loop = asyncio.get_running_loop()
#     loop.set_debug(True)
#     loop.slow_callback_duration = 0.05

def main():
	try:
		# app.on_startup(startup)

		read_settings_from_db()

		HOST = get_app_setting('host')
		PORT = get_app_setting('port')
		WIDTH = get_app_setting('window_width')
		HEIGHT = get_app_setting('window_height')

		ui.run(
			host=HOST,
			port=PORT,
			title=" ",
			reload=False,
			show_welcome_message=False,
			native=True,
			window_size=(WIDTH, HEIGHT),  # Using width and height retrieved from TinyDB
			# dark=None,
			# show=False,
			# frameless=True,  # Commented due to known issues
		)
	except Exception as e:
		app.shutdown() # is not required but feels logical and says it all
		sys.exit(1)


# if __name__ in {"__main__", "__mp_main__"}:
if __name__ == '__main__':
	# the following works for 'native=True' mode, as 
	# this code is trying to be more like a desktop app 
	# with only a single user (a personal server) with 
	# no login and only 1 running instance;
	# but the following does not work for 'native=False' 
	# which makes sense in a web browser and without an 
	# auth/login there's no way to stop that:
	running = False
	url = f"http://{HOST}:{PORT}/busy"
	transport = httpx.HTTPTransport(retries=0) # disable retries entirely
	try:
		with httpx.Client(transport=transport) as client:
			response = client.get(url)
			if response.status_code == 200:
				running = True
			else:
				pass
	except httpx.RequestError:
		pass
	if running:
		sys.exit(1)

	# notes: 
	# in the following main guard:
	#       if __name__ in {"__main__", "__mp_main__"}:
	# it causes main() to be executed twice, so the above httpx /busy code
	# does not work properly, but in this:
	#       if __name__ == '__main__':
	# it is not executed twice, and the httpx code works as expected.
	# note: if needed, this also works in a pystray menu.

	try:
		main() # does 'ui.run' and 'app.' stuff
	except Exception as e:
		app.shutdown() # maybe not required but feels logical = says it all

