from app.services.voice import voice_service
from app.services.voice.intent_engine import strip_leading_wake_name
from tests.conftest import days_ago


def voice_command(client, headers, transcript: str, language_hint: str = "auto"):
    return client.post(
        "/api/v1/voice/command",
        headers=headers,
        data={"browser_transcript": transcript, "language_hint": language_hint},
        files={"audio": ("voice.webm", b"voice-bytes", "audio/webm")},
    )


def test_voice_endpoints_require_auth(client):
    response = client.post(
        "/api/v1/voice/transcribe",
        data={"browser_transcript": "I drank 500 ml of water"},
        files={"audio": ("voice.webm", b"voice-bytes", "audio/webm")},
    )
    assert response.status_code == 401


def test_transcribe_uses_browser_transcript_in_mock_mode(client, male_headers):
    response = client.post(
        "/api/v1/voice/transcribe",
        headers=male_headers,
        data={"browser_transcript": "Maine 500 ml pani piya"},
        files={"audio": ("voice.webm", b"voice-bytes", "audio/webm")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "transcript": "Maine 500 ml pani piya",
        "language": "ur",
        "provider": "mock",
    }


def test_transcribe_rejects_invalid_audio_and_missing_mock_transcript(client, male_headers):
    empty = client.post(
        "/api/v1/voice/transcribe",
        headers=male_headers,
        data={"browser_transcript": "I drank water"},
        files={"audio": ("voice.webm", b"", "audio/webm")},
    )
    assert empty.status_code == 422

    unsupported = client.post(
        "/api/v1/voice/transcribe",
        headers=male_headers,
        data={"browser_transcript": "I drank water"},
        files={"audio": ("voice.txt", b"voice-bytes", "text/plain")},
    )
    assert unsupported.status_code == 415

    missing_transcript = client.post(
        "/api/v1/voice/transcribe",
        headers=male_headers,
        files={"audio": ("voice.webm", b"voice-bytes", "audio/webm")},
    )
    assert missing_transcript.status_code == 422


def test_hydration_command_updates_dashboard_and_deduplicates_timeline(client, male_headers):
    first = voice_command(client, male_headers, "I drank 500 ml of water")
    assert first.status_code == 200
    assert first.json()["action"] == "executed"
    assert first.json()["intent"] == "log_hydration"
    assert first.json()["refresh_scopes"] == ["dashboard"]

    second = voice_command(client, male_headers, "I drank 500 ml of water")
    assert second.status_code == 200

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["hydration"]["today_ml"] == 1000
    assert len(dashboard["hydration"]["logs"]) == 2
    events = [event for event in dashboard["timeline"] if event["event_type"] == "voice_hydration"]
    assert len(events) == 1
    assert events[0]["title"] == "Hydration logged via Voice — 500 ml"


def test_mira_prefix_english_hydration_preserves_raw_transcript(client, male_headers):
    response = voice_command(client, male_headers, "Mira, I drank 500 ml of water.")
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "executed"
    assert payload["intent"] == "log_hydration"
    assert payload["transcript"] == "Mira, I drank 500 ml of water."

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["hydration"]["today_ml"] == 500


def test_mira_prefix_liter_hydration_converts_to_milliliters(client, male_headers):
    for transcript in ["Mira, log 1 liter of water.", "Mira, log 1 litre of water.", "Mira, log 1 L of water."]:
        response = voice_command(client, male_headers, transcript)
        assert response.status_code == 200, transcript
        assert response.json()["action"] == "executed", transcript
        assert response.json()["intent"] == "log_hydration", transcript

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["hydration"]["today_ml"] == 3000


def test_mira_prefix_liter_out_of_range_returns_clarification(client, male_headers):
    response = voice_command(client, male_headers, "Mira, log 10 liters of water.")
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "clarification_required"
    assert payload["intent"] == "unknown"

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["hydration"]["today_ml"] == 0


def test_mira_prefix_roman_urdu_hydration(client, male_headers):
    response = voice_command(client, male_headers, "Mira, maine 500 ml pani piya.")
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "executed"
    assert payload["intent"] == "log_hydration"
    assert payload["language"] == "ur"
    assert payload["transcript"] == "Mira, maine 500 ml pani piya."
    assert "pani" in payload["response_text"].casefold()


def test_mira_prefix_query_routes_to_existing_health_ai(client, male_headers):
    response = voice_command(client, male_headers, "mira how many steps have I taken")
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "answered"
    assert payload["intent"] == "query_steps"
    assert payload["transcript"] == "mira how many steps have I taken"
    assert payload["result"]["answer_provider"] == "mock"


def test_mira_wake_name_stripping_boundaries():
    assert strip_leading_wake_name("Mira, I drank water.") == "I drank water."
    assert strip_leading_wake_name("MIRA: log sleep") == "log sleep"
    assert strip_leading_wake_name("  mira   what are my priorities") == "what are my priorities"
    assert strip_leading_wake_name("Miracle, I drank water.") == "Miracle, I drank water."
    assert strip_leading_wake_name("Please tell Mira to log water") == "Please tell Mira to log water"
    assert strip_leading_wake_name("Mira") == ""
    assert strip_leading_wake_name("Miranda, log water") == "Miranda, log water"


def test_voice_lifestyle_commands_use_typed_writes(client, male_headers):
    activity = voice_command(client, male_headers, "I walked for 30 minutes")
    sleep = voice_command(client, male_headers, "I slept for 7 hours")
    nutrition = voice_command(client, male_headers, "I ate daal for lunch")

    assert activity.json()["intent"] == "log_activity"
    assert sleep.json()["intent"] == "log_sleep"
    assert nutrition.json()["intent"] == "log_nutrition"

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["activity"]["recent"][0]["duration_min"] == 30
    assert dashboard["sleep"]["logs"][0]["hours_slept"] == 7
    assert dashboard["nutrition"]["meals"][0]["meal_type"] == "lunch"


def test_roman_urdu_and_urdu_commands_are_detected(client, male_headers):
    roman = voice_command(client, male_headers, "Maine 500 ml pani piya")
    urdu = voice_command(client, male_headers, "میں نے 300 ملی لیٹر پانی پیا")

    assert roman.json()["language"] == "ur"
    assert roman.json()["action"] == "executed"
    assert "pani" in roman.json()["response_text"].casefold()
    assert urdu.json()["language"] == "ur"
    assert urdu.json()["action"] == "executed"


def test_voice_query_uses_existing_health_ai_path(client, male_headers):
    response = voice_command(client, male_headers, "What are my health priorities?")
    assert response.status_code == 200
    assert response.json()["action"] == "answered"
    assert response.json()["intent"] == "query_priorities"
    assert response.json()["result"]["answer_provider"] == "mock"


def test_sensitive_cycle_command_requires_bound_single_use_confirmation(client, female_headers, second_female_headers):
    pending = voice_command(client, female_headers, "Mira, my period started")
    assert pending.status_code == 200
    payload = pending.json()
    assert payload["action"] == "confirmation_required"
    assert payload["requires_confirmation"] is True
    assert payload["transcript"] == "Mira, my period started"

    assert client.get("/api/v1/cycles", headers=female_headers).json() == []

    mismatch = client.post(
        "/api/v1/voice/command",
        headers=second_female_headers,
        data={"confirmation_token": payload["confirmation_token"], "confirm": "true"},
    )
    assert mismatch.status_code == 422

    confirmed = client.post(
        "/api/v1/voice/command",
        headers=female_headers,
        data={"confirmation_token": payload["confirmation_token"], "confirm": "true"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["action"] == "executed"
    assert confirmed.json()["refresh_scopes"] == ["dashboard", "womens_health"]
    assert len(client.get("/api/v1/cycles", headers=female_headers).json()) == 1

    replay = client.post(
        "/api/v1/voice/command",
        headers=female_headers,
        data={"confirmation_token": payload["confirmation_token"], "confirm": "true"},
    )
    assert replay.status_code == 422


def test_male_profile_cannot_use_womens_health_voice_commands(client, male_headers):
    response = voice_command(client, male_headers, "My period started")
    assert response.status_code == 200
    assert response.json()["action"] == "unavailable"
    assert response.json()["intent"] == "start_cycle"


def test_voice_speak_returns_explicit_mock_browser_fallback(client, male_headers):
    response = client.post(
        "/api/v1/voice/speak",
        headers=male_headers,
        json={"text": "Your water was logged.", "language": "en"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "mode": "browser_fallback",
        "text": "Your water was logged.",
        "language": "en",
        "provider": "mock",
    }
