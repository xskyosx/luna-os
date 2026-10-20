#!/usr/bin/env python3
"""LUNA Voice First Light: optional Termux speech input/output and local-model bridge.

No microphone is activated on import. Run this program explicitly to begin a
voice session. Conversation history stays in RAM and is discarded on exit.
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are Luna, a warm, respectful, practical AI assistant in the LUNA OS "
    "project. Speak naturally, support English and Spanish, be honest about "
    "uncertainty, protect user privacy, and never claim access to the device "
    "or files unless a tool explicitly provides it. Treat simulations as "
    "simulations, not evidence of new physical laws."
)
EXIT_PHRASES = {"exit", "quit", "stop listening", "goodbye luna", "adios luna", "salir"}


def configured_endpoint(environ=None):
    """Return an approved model endpoint; remote hosts require explicit opt-in."""
    env = os.environ if environ is None else environ
    endpoint = env.get("LUNA_CHAT_ENDPOINT", DEFAULT_ENDPOINT).strip()
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("LUNA_CHAT_ENDPOINT must be an absolute HTTP(S) URL.")
    host = parsed.hostname.lower()
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if host not in local_hosts and env.get("LUNA_ALLOW_REMOTE") != "1":
        raise ValueError(
            "Remote model endpoints are disabled. Set LUNA_ALLOW_REMOTE=1 only "
            "after reviewing the endpoint and privacy implications."
        )
    return endpoint


def local_reply(text):
    """Small offline command set used when no model server is configured."""
    normalized = " ".join(text.casefold().strip().split())
    if normalized in EXIT_PHRASES:
        return "Goodbye for now, Fabian. Voice mode is closing. Hasta pronto."
    if any(word in normalized for word in ("hello", "hi luna", "hola luna", "buenos dias", "buenas")):
        return "Hello, Fabian. I'm Luna's voice interface. I'm ready when you are."
    if normalized in {"help", "ayuda", "what can you do", "que puedes hacer"}:
        return (
            "I can greet you, explain voice setup, and connect to an explicitly "
            "configured local language model. Say status to check the voice bridge."
        )
    if normalized in {"status", "estado", "are you connected", "estas conectada"}:
        return (
            "Voice input and speech output are running if the Termux API commands "
            "are installed. Generative replies require a configured local language model endpoint."
        )
    return (
        "I heard you, but the language model is not connected yet. Configure a "
        "local OpenAI-compatible chat endpoint, then restart Luna Voice."
    )


def ask_model(text, history=None, environ=None, timeout=30):
    """Send one turn to an OpenAI-compatible endpoint; keep history in caller RAM."""
    env = os.environ if environ is None else environ
    endpoint = configured_endpoint(env)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-12:])
    messages.append({"role": "user", "content": text})
    payload = {
        "model": env.get("LUNA_CHAT_MODEL", "local-model"),
        "messages": messages,
        "temperature": 0.7,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    api_key = env.get("LUNA_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    try:
        answer = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("The configured model returned an unexpected response shape.") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("The configured model returned an empty reply.")
    if history is not None:
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        del history[:-12]
    return answer.strip()


def speak(text):
    """Speak using the Android voice configured for Termux:API."""
    command = shutil.which("termux-tts-speak")
    if not command:
        print("Luna:", text)
        print("Tip: install Termux:API and its Termux package to enable speech output.")
        return False
    try:
        result = subprocess.run(
            [command, text], check=False, capture_output=True, text=True, timeout=45
        )
    except (OSError, subprocess.TimeoutExpired):
        print("Luna:", text)
        return False
    if result.returncode:
        print("Luna:", text)
        if result.stderr.strip():
            print("Speech output warning:", result.stderr.strip(), file=sys.stderr)
        return False
    return True


def listen():
    """Capture one utterance via Termux:API; returns recognized text or raises."""
    command = shutil.which("termux-speech-to-text")
    if not command:
        raise RuntimeError(
            "termux-speech-to-text was not found. Install Termux:API and its "
            "matching Termux package, or use the text-only fallback."
        )
    result = subprocess.run(
        [command], check=False, capture_output=True, text=True, timeout=90
    )
    if result.returncode:
        detail = result.stderr.strip() or "speech recognition failed"
        raise RuntimeError(detail)
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("No speech was recognized. Try again.")
    return text


def main():
    if "--help" in sys.argv:
        print("LUNA Voice First Light")
        print("Run: python luna_voice.py")
        print("Optional env: LUNA_CHAT_ENDPOINT, LUNA_CHAT_MODEL, LUNA_API_KEY.")
        print("Remote endpoints require LUNA_ALLOW_REMOTE=1.")
        print("History is temporary and discarded when the program exits.")
        return 0

    try:
        endpoint = configured_endpoint()
        model_ready = bool(os.environ.get("LUNA_CHAT_ENDPOINT")) or endpoint == DEFAULT_ENDPOINT
        # A default endpoint is only considered available after an actual request;
        # this flag describes configuration, not a health check.
        del model_ready
    except ValueError as exc:
        speak(str(exc))
        return 2

    speak("Hello, Fabian. Luna voice mode is ready. Say goodbye Luna to close.")
    history = []
    while True:
        try:
            heard = listen()
            print("You:", heard)
            if " ".join(heard.casefold().split()) in EXIT_PHRASES:
                speak(local_reply(heard))
                return 0
            if os.environ.get("LUNA_CHAT_ENDPOINT") or os.environ.get("LUNA_API_KEY"):
                try:
                    reply = ask_model(heard, history)
                except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                    reply = "I couldn't reach the configured model safely. Check its local server and settings. " + str(exc)
            else:
                reply = local_reply(heard)
            speak(reply)
        except KeyboardInterrupt:
            speak("Voice mode paused. Goodbye for now.")
            return 0
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            print("Voice input:", exc, file=sys.stderr)
            speak("I couldn't hear that clearly. Please try again.")
        except EOFError:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
