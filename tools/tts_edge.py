import asyncio
import subprocess
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"


async def main() -> None:
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    if not slug:
        raise SystemExit("用法：python tools/tts_edge.py <视频名>")

    d = VIDEOS / slug
    script = (d / "script.txt").read_text(encoding="utf-8").strip()
    out = d / "audio" / "vo.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)

    await edge_tts.Communicate(script, "zh-CN-XiaoxiaoNeural", rate="+0%").save(str(out))
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out)],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"{float(dur):.2f}s  ->  videos/{slug}/audio/vo.mp3")


if __name__ == "__main__":
    asyncio.run(main())
