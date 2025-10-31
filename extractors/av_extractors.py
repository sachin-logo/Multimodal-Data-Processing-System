import os
import tempfile
import speech_recognition as sr
from youtube_transcript_api import YouTubeTranscriptApi as YTA, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# Audio file transcription (supports MP3 by converting to WAV)
def extract_audio_text(audio_path):
    r = sr.Recognizer()
    path_to_transcribe = audio_path
    ext = os.path.splitext(audio_path)[1].lower()
    # Convert non-native formats (e.g., mp3, mp4, m4a) to WAV
    if ext not in [".wav", ".aiff", ".aif", ".flac"]:
        try:
            from pydub import AudioSegment
            # Allow explicit ffmpeg/ffprobe locations via env vars
            ffmpeg_bin = os.getenv('FFMPEG_BINARY')
            ffprobe_bin = os.getenv('FFPROBE_BINARY')
            if ffmpeg_bin:
                AudioSegment.converter = ffmpeg_bin
            if ffprobe_bin:
                AudioSegment.ffprobe = ffprobe_bin
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            AudioSegment.from_file(audio_path).set_channels(1).set_frame_rate(16000).export(tmp.name, format="wav")
            path_to_transcribe = tmp.name
        except Exception as e:
            raise ValueError(f"Audio conversion failed: {e}")
    with sr.AudioFile(path_to_transcribe) as source:
        audio = r.record(source)
    return r.recognize_google(audio)

# TODO: Add logic to extract audio from video (mp4 -> wav)
def extract_video_text(video_path):
    from moviepy.editor import VideoFileClip
    import tempfile
    clip = VideoFileClip(video_path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        clip.audio.write_audiofile(tmp.name)
        return extract_audio_text(tmp.name)

# YouTube transcript
def _extract_youtube_video_id(youtube_url: str):
    # Supports: standard, youtu.be, and shorts URLs
    import re
    patterns = [
        r"[?&]v=([\w-]{6,})",                 # https://www.youtube.com/watch?v=ID
        r"youtu\.be/([\w-]{6,})",            # https://youtu.be/ID
        r"youtube\.com/shorts/([\w-]{6,})",  # https://www.youtube.com/shorts/ID
    ]
    for p in patterns:
        m = re.search(p, youtube_url)
        if m:
            return m.group(1)
    return None

def extract_youtube_text(youtube_url):
    video_id = _extract_youtube_video_id(youtube_url)
    if not video_id:
        return ""
    try:
        srt = None
        # Newer API: list_transcripts
        if hasattr(YTA, 'list_transcripts'):
            transcripts = YTA.list_transcripts(video_id)
            try:
                srt = transcripts.find_transcript(['en']).fetch()
            except (NoTranscriptFound, Exception):
                try:
                    for tr in transcripts:
                        try:
                            srt = tr.fetch()
                            if srt:
                                break
                        except Exception:
                            continue
                except Exception:
                    srt = None
        # Older API: get_transcript
        if (not srt) and hasattr(YTA, 'get_transcript'):
            try:
                srt = YTA.get_transcript(video_id)
            except Exception:
                srt = None
        if srt:
            return '\n'.join([x.get('text', '') for x in srt])
        # Fallback: download audio and transcribe
        try:
            text = _transcribe_youtube_audio(video_id)
            if text:
                return text
        except Exception:
            pass
        # Final fallback: include title + description as context
        meta = _get_youtube_metadata(video_id)
        return meta or ""
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        # Fallback to audio transcription when transcripts are disabled
        try:
            text = _transcribe_youtube_audio(video_id)
            if text:
                return text
        except Exception:
            pass
        meta = _get_youtube_metadata(video_id)
        return meta or ""

def _transcribe_youtube_audio(video_id: str) -> str:
    """Download YouTube audio via pytube and transcribe with SpeechRecognition."""
    from pytube import YouTube
    from moviepy.editor import AudioFileClip
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(only_audio=True).first()
    if stream is None:
        return ""
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_mp4 = os.path.join(tmpdir, 'audio.mp4')
        stream.download(output_path=tmpdir, filename='audio.mp4')
        # Convert to wav for SpeechRecognition
        wav_path = os.path.join(tmpdir, 'audio.wav')
        clip = AudioFileClip(audio_mp4)
        clip.write_audiofile(wav_path)
        clip.close()
        return extract_audio_text(wav_path)

def _get_youtube_metadata(video_id: str) -> str:
    """Fetch YouTube title and description via pytube for minimal context."""
    try:
        from pytube import YouTube
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        title = yt.title or ""
        desc = yt.description or ""
        return f"Title: {title}\nDescription: {desc}"
    except Exception:
        return ""
