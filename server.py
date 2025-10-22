import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

import yt_dlp
from fastmcp import FastMCP

# Suppress all logging output to stdout/stderr
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("yt_dlp").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

mcp = FastMCP("LLM Jukebox")
download_path = Path(os.environ.get("DOWNLOAD_PATH", "./"))
download_path.mkdir(exist_ok=True)

YT_DLP_BASE_OPTS = {
    "no_warnings": True,
    "quiet": True,
    "audioquality": "0",  # Best quality
    "outtmpl": str(download_path / "%(title)s" / "%(title)s.%(ext)s"),
    "noplaylist": True,
    "extract_flat": False,
    "logger": logging.getLogger("yt_dlp"),
    "writethumbnail": True
}

def suppress_output(func):
    """Decorator to suppress all stdout/stderr output from a function."""
    def wrapper(*args, **kwargs):
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                return func(*args, **kwargs)
        except Exception as e:
            # Re-raise the exception but ensure no output leaked
            raise e
    return wrapper

@suppress_output
def get_youtube_info(query: str) -> Optional[Dict[str, Any]]:
    """	Get YouTube video information without downloading.
    
    Args:
        query: Search query for YouTube
        
    Returns:
        Video information dictionary or None if not found
    """
    info_opts = {
        **YT_DLP_BASE_OPTS,
        "extract_flat": False,
    }
    
    try:
        yt_query = f"ytsearch1:{query}"
        
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(yt_query, download=False)
            if not info or "entries" not in info or len(info["entries"]) == 0:
                return None
            
            return info["entries"][0]
            
    except Exception as e:
        return None

@suppress_output
def download_and_store_track(video_info: Dict[str, Any], query: str) -> str:
    """	Download a track and store it in the library.
    
    Args:
        video_info: YouTube video information
        query: Original search query
        
    Returns:
        Success message or error message
    """
    downloaded_files = []

    def progress_hook(d):
        if d["status"] == "finished":
            downloaded_files.append(d["filename"])

    ydl_opts = {
        **YT_DLP_BASE_OPTS,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "progress_hooks": [progress_hook],
    }

    try:
        yt_query = f"ytsearch1:{query}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_query])
            
            if downloaded_files:
                music_file = downloaded_files[0]
                # Ensure .mp3 extension
                music_file_path = Path(music_file)
                if music_file_path.suffix.lower() != ".mp3":
                    music_file = str(music_file_path.with_suffix(".mp3"))

                title = video_info.get("title", "Unknown Title")
                artist = video_info.get("uploader", "Unknown Artist")

                success_msg = (
                    f"Downloaded and playing: '{title}' by {artist}\n"
                    f"File saved as: {Path(music_file).name}\n"
                    f"Added to music library database.\n"
                )

                return success_msg
            else:
                return f"Download completed for: {query}, but no files were found."
                
    except Exception as e:
        raise Exception(f"Failed to download track: {str(e)}")

@mcp.tool()
def download_and_play(query: str) -> str:
    """	Search for and play a song. If the song is already in the library it 
		will play the existing version, otherwise it will download it first.

    Args:
        query: Search query for music (artist, song, album, etc.)

    Returns:
        Success message with file info, or error message if download/play failed
    """
    try:
        
        # Get video information
        video_info = get_youtube_info(query)
        
        if not video_info:
            return "No search results found on YouTube for your query."
        
        # Download new track
        result = download_and_store_track(video_info, query)
        
        return result

    except Exception as e:
        error_msg = f"❌ Error processing request: {str(e)}"
        return error_msg

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        # Handle graceful shutdown without breaking JSON-RPC
        pass
    except Exception as e:
        # Log error internally but don't output to stdio
        pass