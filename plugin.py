import requests

ICYARR_BASE = "http://your-icyarr-host"   # ← change this to your icyarr backend URL
# place this file into dispatcharr/plugins/tickarr/zips/tickarr/plugin.py

def fetch_icyarr_text(stream_url: str) -> str:
    """
    Call icyarr's /tickarr_text endpoint and return the text string.
    """
    try:
        r = requests.get(
            f"{ICYARR_BASE}/tickarr_text",
            params={"url": stream_url},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        return data.get("text", "Unknown Station — No metadata available")

    except Exception:
        return "Unknown Station — No metadata available"


def run(channel, state):
    """
    Tickarr calls this function automatically.

    channel: Tickarr channel object
    state: persistent dict for this plugin/channel
    """

    # ------------------------------------------------------------
    # 1. Only run when someone is watching the channel
    # ------------------------------------------------------------
    if not channel.is_active:
        return  # nobody watching → icyarr stays idle

    # ------------------------------------------------------------
    # 2. Get the stream URL Tickarr is playing
    # ------------------------------------------------------------
    stream_url = channel.source_url

    # ------------------------------------------------------------
    # 3. Fetch icyarr's Now Playing text
    # ------------------------------------------------------------
    new_text = fetch_icyarr_text(stream_url)

    # ------------------------------------------------------------
    # 4. Compare to last applied text
    # ------------------------------------------------------------
    last_text = state.get("last_text")

    if new_text == last_text:
        return  # no change → do nothing

    # ------------------------------------------------------------
    # 5. Update Tickarr Custom Text
    # ------------------------------------------------------------
    channel.custom_text = new_text
    channel.update_custom_text()   # Tickarr action to apply overlay

    # ------------------------------------------------------------
    # 6. Save new text for next comparison
    # ------------------------------------------------------------
    state["last_text"] = new_text
