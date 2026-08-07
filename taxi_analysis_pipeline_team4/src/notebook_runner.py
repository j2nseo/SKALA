"""두 시각화 노트북을 원본 수정 없이 자동 실행한다.

원본 데이터와 전처리 완료 데이터 노트북을 차례로 실행해 Matplotlib 차트는
PNG로, Plotly 차트는 HTML로 저장한다. Colab 전용 폰트 명령은 실행 시에만
제외하고 현재 운영체제의 한글 폰트를 등록한다.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


SRC_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SRC_DIR.parent
PROJECT_DIR = PIPELINE_DIR.parent
NOTEBOOK_DIR = PIPELINE_DIR / "notebooks"
OUTPUT_DIR = PIPELINE_DIR / "outputs"
NOTEBOOKS = [
    (NOTEBOOK_DIR / "visualization_raw.ipynb", "visualization_raw"),
    (NOTEBOOK_DIR / "visualization_processed.ipynb", "visualization_processed"),
]


def setup_korean_font() -> str:
    """운영체제에 이미 설치된 한글 폰트를 Matplotlib에 등록한다."""
    font_files = [
        Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]
    for font_file in font_files:
        if font_file.exists():
            font_manager.fontManager.addfont(font_file)
            family = font_manager.FontProperties(fname=font_file).get_name()
            plt.rcParams["font.family"] = family
            plt.rcParams["axes.unicode_minus"] = False
            return family
    raise RuntimeError(
        "한글 폰트를 찾지 못했습니다. macOS는 AppleGothic, "
        "Linux는 fonts-nanum을 설치하세요."
    )


def remove_colab_font_setup(source: str) -> str:
    """Colab 전용 폰트 설정만 제거하고 같은 셀의 데이터 로드는 보존한다."""
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("!apt-get"):
            continue
        if "'/usr/share/fonts/truetype/nanum/" in stripped:
            continue
        if "fontManager.addfont(fontpath)" in stripped:
            continue
        if "family='NanumGothic'" in stripped:
            continue
        lines.append(line)
    return "\n".join(lines)


def run_notebook(source_path: Path, output_prefix: str) -> None:
    """단일 노트북을 실행하고 셀 위치가 포함된 오류를 전달한다."""
    print(f"노트북 실행: {source_path.name}")
    if not source_path.is_file():
        raise FileNotFoundError(f"시각화 노트북이 없습니다: {source_path}")
    try:
        notebook = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"노트북을 읽지 못했습니다: {source_path}") from exc
    namespace = {"__name__": "__notebook__"}
    plotly_count = 0
    saved_plotly_ids: set[int] = set()

    for index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = remove_colab_font_setup("".join(cell.get("source", [])))
        if re.fullmatch(r"\s*\d+\.\s+[^\n]+\s*", source):
            print(f"셀 {index}: 코드 셀에 입력된 제목 생략")
            continue

        # 자동 실행 중 GUI 창이나 브라우저를 열지 않는다.
        source = re.sub(r"\b[A-Za-z_]\w*\.show\(\)", "", source)
        before = set(plt.get_fignums())
        try:
            exec(compile(source, f"{source_path.name}:cell-{index}", "exec"), namespace)
        except Exception as exc:
            raise RuntimeError(
                f"{source_path.name}의 코드 셀 {index} 실행에 실패했습니다."
            ) from exc

        for number in sorted(set(plt.get_fignums()) - before):
            figure = plt.figure(number)
            path = OUTPUT_DIR / f"{output_prefix}_cell_{index}.png"
            figure.savefig(path, dpi=150, bbox_inches="tight")
            print(f"정적 차트 저장: {path}")
            plt.close(figure)

        for figure in namespace.values():
            if (figure is not None
                    and figure.__class__.__module__.startswith("plotly")
                    and id(figure) not in saved_plotly_ids):
                saved_plotly_ids.add(id(figure))
                plotly_count += 1
                path = OUTPUT_DIR / f"{output_prefix}_plotly_{plotly_count}.html"
                figure.write_html(path, include_plotlyjs="cdn")
                print(f"인터랙티브 차트 저장: {path}")

    print(f"노트북 완료: {source_path.name}")


def main() -> None:
    """실행 위치를 고정하고 등록된 두 노트북을 순서대로 처리한다."""
    os.chdir(PROJECT_DIR)
    font_family = setup_korean_font()
    print(f"한글 폰트 설정: {font_family}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source_path, output_prefix in NOTEBOOKS:
        run_notebook(source_path, output_prefix)
    print(f"전체 시각화 실행 완료: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
