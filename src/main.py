# ============================================================
# ICYARR BACKEND — main.py
# ============================================================
# This FastAPI backend manages radio streams, loads M3U playlists,
# merges metadata, tests streams, stores channels in SQLite,
# and exposes endpoints for Tickarr and Dispatcharr.
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

# SQLite persistence layer
from db import init_db, load_channels, save_channel, delete_channel


# ============================================================
# FASTAPI APP INITIALIZATION
# ============================================================

app = FastAPI()

# Initialize SQLite database and load saved channels
init_db()
local_streams = load_channels()   # Persistent list loaded from channel.db


# ============================================================
# DATA MODELS
# ============================================================

class M3URequest(BaseModel):
    url: str  # URL of the M3U file to load

class StreamRequest(BaseModel):
    url: str  # URL of the stream to test

class UpdateChannel(BaseModel):
    url: str
    name: str | None = None
    group: str | None = None


# ============================================================
# METADATA MERGE LOGIC
# ============================================================
# icyarr always keeps its own metadata if present.
# Incoming metadata only fills missing fields.

def merge_metadata(existing, incoming):
    merged = existing.copy()

    for key, value in incoming.items():
        # Only fill missing fields
        if key not in merged or merged[key] in ("", None):
            merged[key] = value

    return merged


# ============================================================
# ADD CHANNEL OBJECT (WITH MERGE + SAVE TO DB)
# ============================================================

def add_channel_object(channel):
    # Check if channel already exists
    for existing in local_streams:
        if existing["url"] == channel["url"]:
            # Merge metadata
            merged = merge_metadata(existing, channel)
            existing.update(merged)
            save_channel(existing)  # Persist update
            return

    # New channel
    local_streams.append(channel)
    save_channel(channel)  # Persist new channel


# ============================================================
# M3U LOADER ENDPOINT
# ============================================================

@app.post("/load_m3u")
def load_m3u(req: M3URequest):
    """
    Loads an M3U playlist from a URL, parses metadata,
    and stores channels in SQLite + memory.
    """
    text = requests.get(req.url).text
    lines = text.splitlines()
    current = {}

    for line in lines:
        line = line.strip()

        # Metadata line
        if line.startswith("#EXTINF"):
            meta, name = line.split(",", 1)
            current["name"] = name

            parts = meta.split(" ")
            for part in parts:
                if "tvg-id" in part:
                    current["tvg_id"] = part.split("=")[1].strip('"')
                if "tvg-name" in part:
                    current["tvg_name"] = part.split("=")[1].strip('"')
                if "group-title" in part:
                    current["group"] = part.split("=")[1].strip('"')

        # URL line
        elif line and not line.startswith("#"):
            current["url"] = line
            add_channel_object(current)
            current = {}

    return local_streams


# ============================================================
# STREAM TESTER ENDPOINT
# ============================================================

@app.post("/test_stream")
def test_stream(req: StreamRequest):
    """
    Tests a stream URL by checking if it returns audio.
    If valid, adds it to the channel list.
    """
    try:
        r = requests.get(req.url, timeout=5, stream=True)
        content_type = r.headers.get("Content-Type", "")

        if "audio" in content_type.lower():
            add_channel_object({"url": req.url})
            return {"status": "added", "url": req.url}

        return {"status": "invalid_stream", "content_type": content_type}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ============================================================
# LOCAL STREAM LIST ENDPOINT
# ============================================================

@app.get("/local_streams")
def get_local_streams():
    """Returns all channels currently stored."""
    return local_streams


# ============================================================
# UPDATE CHANNEL ENDPOINT
# ============================================================

@app.patch("/update_channel")
def update_channel(req: UpdateChannel):
    """
    Updates channel metadata (name, group).
    Saves changes to SQLite.
    """
    for ch in local_streams:
        if ch["url"] == req.url:
            if req.name is not None:
                ch["name"] = req.name
            if req.group is not None:
                ch["group"] = req.group

            save_channel(ch)  # Persist update
            return {"status": "updated", "channel": ch}

    return {"status": "not_found", "url": req.url}


# ============================================================
# DELETE CHANNEL ENDPOINT
# ============================================================

@app.delete("/delete_channel")
def delete_channel_endpoint(url: str):
    """
    Deletes a channel from memory + SQLite.
    """
    for ch in local_streams:
        if ch["url"] == url:
            local_streams.remove(ch)
            delete_channel(url)  # Persist delete
            return {"status": "deleted", "url": url}

    return {"status": "not_found", "url": url}


# ============================================================
# TICKARR TEXT BUILDER
# ============================================================

def build_tickarr_text(channel: dict) -> str:
    """
    Builds a Now Playing text string for Tickarr overlays.
    """
    parts = []

    icy_title = channel.get("icy_title") or channel.get("stream_title")
    name = channel.get("name") or channel.get("tvg_name")
    group = channel.get("group")
    bitrate = channel.get("bitrate")

    if icy_title:
        parts.append(icy_title)
    if name:
        parts.append(name)
    if group:
        parts.append(group)
    if bitrate:
        parts.append(f"{bitrate}kbps")

    if not parts:
        return "Unknown Station — No metadata available"

    return " — ".join(parts)


# ============================================================
# TICKARR TEXT ENDPOINT
# ============================================================

@app.get("/tickarr_text")
def tickarr_text(url: str):
    """
    Returns Now Playing text for Tickarr overlays.
    """
    for ch in local_streams:
        if ch.get("url") == url:
            return {"text": build_tickarr_text(ch)}

    raise HTTPException(status_code=404, detail="Channel not found")


# ============================================================
# EXPORT M3U FOR DISPATCHARR
# ============================================================

@app.get("/export_m3u")
def export_m3u():
    """
    Builds and returns a clean M3U playlist
    for Dispatcharr Organizer.
    """
    lines = ["#EXTM3U"]

    for ch in local_streams:
        name = ch.get("name", "Unknown")
        group = ch.get("group", "")
        url = ch.get("url")

        extinf = f'#EXTINF:-1 group-title="{group}",{name}'
        lines.append(extinf)
        lines.append(url)

    return "\n".join(lines)
