import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi
from django.conf import settings


DEFAULT_TIMEOUT_SECONDS = 12


class GeminiError(Exception):
    pass


def is_gemini_configured():
    return bool(get_api_key())


def get_api_key():
    return (
        getattr(settings, 'GOOGLE_API_KEY', '')
        or getattr(settings, 'GEMINI_API_KEY', '')
    )


def generate_json_response(prompt, *, temperature=0.2, max_output_tokens=900):
    text = generate_text_response(
        prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type='application/json',
    )
    return json.loads(strip_json_code_block(text))


def generate_text_response(
    prompt,
    *,
    temperature=0.25,
    max_output_tokens=900,
    response_mime_type='text/plain',
):
    api_key = get_api_key()
    if not api_key:
        raise GeminiError('Gemini API key is not configured.')

    payload = {
        'contents': [
            {
                'parts': [
                    {'text': prompt},
                ],
            },
        ],
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': max_output_tokens,
            'responseMimeType': response_mime_type,
        },
    }
    response_body = post_generate_content(api_key, payload)
    return extract_text(response_body)


def post_generate_content(api_key, payload):
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-3.5-flash')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    request = Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key,
        },
        method='POST',
    )

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(
            request,
            context=ssl_context,
            timeout=getattr(settings, 'GEMINI_TIMEOUT_SECONDS', DEFAULT_TIMEOUT_SECONDS),
        ) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        try:
            detail = exc.read().decode('utf-8')[:500]
        except Exception:
            detail = ''
        message = f'Gemini returned HTTP {exc.code}'
        if detail:
            message = f'{message}: {detail}'
        raise GeminiError(message) from exc
    except (URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise GeminiError(str(exc)) from exc


def extract_text(response_body):
    candidates = response_body.get('candidates') or []
    if not candidates:
        raise GeminiError('Gemini returned no candidates.')

    content = candidates[0].get('content') or {}
    parts = content.get('parts') or []
    text = ''.join(str(part.get('text', '')) for part in parts).strip()
    if not text:
        raise GeminiError('Gemini returned an empty response.')

    return text


def strip_json_code_block(text):
    cleaned_text = text.strip()

    if cleaned_text.startswith('```json'):
        return cleaned_text.removeprefix('```json').removesuffix('```').strip()

    if cleaned_text.startswith('```'):
        return cleaned_text.removeprefix('```').removesuffix('```').strip()

    return cleaned_text
