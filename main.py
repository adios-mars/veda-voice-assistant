"""Main execution entry point for JARVIS Voice Assistant."""
import argparse
import sys
import threading

from src.config import config
from src.core.assistant import JarvisAssistant
from src.logger import get_logger
from src.web.server import run_server

logger = get_logger("Main")


def parse_args():
    parser = argparse.ArgumentParser(description="JARVIS: Personal Voice Assistant")
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run only the web dashboard without initializing microphone.",
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Run only the voice assistant without launching web dashboard.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the dashboard screen in default web browser.",
    )
    parser.add_argument(
        "--test-mic",
        action="store_true",
        help="Run a standalone microphone diagnostic test.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Standalone Mic Diagnostic
    if args.test_mic:
        logger.info("Running microphone diagnostic test...")
        from src.audio.recorder import AudioRecorder
        recorder = AudioRecorder()
        logger.info("Listening... Speak a sentence and pause for 2 seconds.")
        wav_path = recorder.record_until_silence()
        logger.info(f"Diagnostic success! Audio captured at: {wav_path}")
        recorder.close()
        return

    # 2. Standalone Web Dashboard
    if args.web_only:
        run_server()
        return

    # 3. Default: Voice Assistant with background Tactical HUD
    if not args.no_web:
        web_thread = threading.Thread(target=run_server, daemon=True)
        web_thread.start()

        if not args.no_browser:
            def _launch_browser():
                import time
                import webbrowser
                time.sleep(0.6)
                webbrowser.open(f"http://localhost:{config.web_port}")
            threading.Thread(target=_launch_browser, daemon=True).start()

    # Verify credentials
    if not config.validate_keys():
        logger.error("DEEPGRAM_API_KEY is missing from .env. Please configure your API key.")
        sys.exit(1)

    assistant = JarvisAssistant()
    assistant.run_forever()


if __name__ == "__main__":
    main()
