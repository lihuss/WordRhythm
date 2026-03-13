from dataclasses import dataclass
from pathlib import Path
import shutil
import urllib.error
import urllib.request


@dataclass(frozen=True)
class FontSource:
    filename: str
    label: str
    urls: tuple[str, ...]


FONT_SOURCES = [
    FontSource(
        filename="NotoSansCJKsc-Regular.otf",
        label="思源黑体",
        urls=(
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
            "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
        ),
    ),
    FontSource(
        filename="NotoSerifCJKsc-Regular.otf",
        label="思源宋体",
        urls=(
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Regular.otf",
            "https://github.com/googlefonts/noto-cjk/raw/main/Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Regular.otf",
        ),
    ),
    FontSource(
        filename="LXGWWenKai-Regular.ttf",
        label="霞鹜文楷",
        urls=(
            "https://raw.githubusercontent.com/lxgw/LxgwWenKai/master/fonts/TTF/LXGWWenKai-Regular.ttf",
            "https://github.com/lxgw/LxgwWenKai/raw/master/fonts/TTF/LXGWWenKai-Regular.ttf",
        ),
    ),
    FontSource(
        filename="MaShanZheng-Regular.ttf",
        label="马善政手写体",
        urls=(
            "https://raw.githubusercontent.com/google/fonts/main/ofl/mashanzheng/MaShanZheng-Regular.ttf",
            "https://github.com/google/fonts/raw/main/ofl/mashanzheng/MaShanZheng-Regular.ttf",
        ),
    ),
    FontSource(
        filename="ZCOOLKuaiLe-Regular.ttf",
        label="站酷快乐体",
        urls=(
            "https://raw.githubusercontent.com/google/fonts/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf",
            "https://github.com/google/fonts/raw/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf",
        ),
    ),
    FontSource(
        filename="ZhiMangXing-Regular.ttf",
        label="钟齐志莽行书",
        urls=(
            "https://raw.githubusercontent.com/google/fonts/main/ofl/zhimangxing/ZhiMangXing-Regular.ttf",
            "https://github.com/google/fonts/raw/main/ofl/zhimangxing/ZhiMangXing-Regular.ttf",
        ),
    ),
]


def _download(url: str, target: Path, timeout_seconds: int = 90) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        with target.open("wb") as output:
            shutil.copyfileobj(response, output)


def download_fonts(fonts_dir: Path) -> None:
    fonts_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    for source in FONT_SOURCES:
        target = fonts_dir / source.filename
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            print(f"[skip] {source.label} -> {target.name}")
            continue

        success = False
        for url in source.urls:
            try:
                print(f"[downloading] {source.label} from {url}")
                _download(url, target)
                success = True
                downloaded += 1
                print(f"[ok] {source.label} -> {target.name}")
                break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                print(f"[retry] {source.label} url failed: {exc}")
                if target.exists() and target.stat().st_size == 0:
                    target.unlink(missing_ok=True)

        if not success:
            failed += 1
            print(f"[failed] {source.label}")

    print("\n=== Font Download Summary ===")
    print(f"downloaded: {downloaded}")
    print(f"skipped:    {skipped}")
    print(f"failed:     {failed}")

    if failed > 0:
        raise RuntimeError("Some fonts failed to download. Check logs above.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    fonts_folder = project_root / "materials" / "fonts"
    download_fonts(fonts_folder)
