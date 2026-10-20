# LUNA Voice First Light — Android / Termux

This is an early, inspectable voice shell for the LUNA OS project. It connects Android's speech input and text-to-speech services to a small command fallback and, optionally, a local OpenAI-compatible language model.

## 1. Requirements

- Android phone with Termux installed.
- The Termux:API companion Android app installed from the same trusted distribution source as Termux.
- In Termux, install the command package:

  ```sh
  pkg update
  pkg install python termux-api
  ```

- Grant microphone permission to the Termux:API app when Android asks. The script does not request or activate the microphone merely by being imported; it listens only after you run it.

## 2. First voice test

From the repository root:

```sh
python luna_voice.py
```

Try “Hola Luna”, “help”, “status”, and “goodbye Luna”. Without a language model configured, Luna can handle only these small built-in replies and will tell you when a generative model is not connected. This is intentional: the repository does not pretend a language model is bundled.

If speech input/output commands are missing, check that the Termux:API app and the Termux package are both installed. Set your preferred Android text-to-speech engine and voice under Android Settings → Accessibility or Text-to-speech output (wording varies by device). Luna uses that configured voice rather than silently selecting a voice without your permission.

## 3. Connect a local language model

Start a local server that exposes an OpenAI-compatible `/v1/chat/completions` endpoint, then configure its address. Example for a server listening on the same device at port 1234:

```sh
export LUNA_CHAT_ENDPOINT="http://127.0.0.1:1234/v1/chat/completions"
export LUNA_CHAT_MODEL="local-model"
python luna_voice.py
```

Set `LUNA_CHAT_MODEL` to the model name expected by your server. If authentication is needed, put the key in `LUNA_API_KEY`; never paste secrets into source files, GitHub issues, or committed configuration.

Remote endpoints are blocked by default. To permit one, you must deliberately set `LUNA_ALLOW_REMOTE=1` after reviewing what data leaves the device. HTTPS is strongly recommended for remote use. The app sends the active conversation context to the configured endpoint.

## 4. Privacy and limitations

- The voice session does not write transcripts or conversation history to disk; session history is held in RAM and discarded on exit.
- Android speech recognition and text-to-speech behavior depends on the installed Android services and their own privacy settings.
- The optional model endpoint receives the user's spoken text and short recent conversation context.
- The built-in fallback is not generative AI. A configured model server is required for open-ended answers.
- No background listening, wake-word service, automatic account login, or remote device control is implemented.
- The script does not grant itself Android permissions. The user must approve them through Android.
- This is a first prototype. Do not treat it as a safety-critical system.

## 5. Troubleshooting

- **No speech command:** run `command -v termux-speech-to-text` and `command -v termux-tts-speak`. Install `termux-api` inside Termux and the matching Android companion app.
- **No microphone:** check Android app permissions and try the speech command directly.
- **No spoken output:** check Android's selected text-to-speech engine, language, media volume, and Termux:API permissions.
- **Model unavailable:** verify the endpoint, port, model name, and server logs. Keep the endpoint on loopback unless you intentionally configure a remote service.
- **Need text only:** the built-in replies print to the terminal if the TTS command is unavailable.

## Next milestones

1. Add a small UI with explicit listening state and a visible stop control.
2. Add user-approved persistent memory using the existing local memory engine.
3. Add a wake-word option only after evaluating battery use, false activations, and clear microphone indicators.
4. Add provider adapters and integration tests without hardcoding secrets or weakening endpoint restrictions.
