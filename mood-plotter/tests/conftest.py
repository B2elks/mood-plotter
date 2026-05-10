"""Pytest-konfiguration: env-vars måste sättas innan config.py importeras."""
import os

os.environ.setdefault("ELKS_API_USERNAME", "test")
os.environ.setdefault("ELKS_API_PASSWORD", "test")
os.environ.setdefault("ELKS_FROM_NUMBER", "+46000")
os.environ.setdefault("USER_PHONE_NUMBER", "+46111")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("ELEVENLABS_API_KEY", "test")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "test")
os.environ.setdefault("SERVER_PUBLIC_URL", "https://test")
os.environ.setdefault("PI_TOKEN", "test-token")
