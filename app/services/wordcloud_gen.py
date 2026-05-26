import io
import base64
import jieba
from collections import Counter
from pathlib import Path

STOPWORDS = set([
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
    "一個", "上", "也", "很", "到", "說", "要", "去", "你", "會", "著",
    "沒有", "看", "好", "自己", "這", "那", "他", "她", "它", "我們",
    "你們", "他們", "這個", "那個", "可以", "覺得", "就是", "但是", "因為",
    "所以", "如果", "然後", "這樣", "這次", "活動", "課程", "學習", "老師",
    "同學", "讓", "讓我", "使", "讓我們", "很多", "非常", "真的", "感覺",
    "時候", "時", "呢", "嗎", "吧", "啊", "喔", "哦", "嗯", "對",
])


def generate_wordcloud_b64(texts: "list[str]") -> str:
    """Generate word cloud image from list of texts, return base64 PNG."""
    try:
        from wordcloud import WordCloud
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        combined = " ".join(texts)
        words = jieba.cut(combined, cut_all=False)
        filtered = [w for w in words if w.strip() and w not in STOPWORDS and len(w) > 1]
        freq = Counter(filtered)

        if not freq:
            return ""

        font_path = _find_font()
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=400,
            background_color="white",
            max_words=100,
            colormap="Set2",
        )
        wc.generate_from_frequencies(freq)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        buf = io.BytesIO()
        fig.savefig(buf, format="PNG", bbox_inches="tight", dpi=100)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print(f"wordcloud error: {e}")
        return ""


def get_top_words(texts: "list[str]", top_n: int = 20) -> "list[dict]":
    combined = " ".join(texts)
    words = jieba.cut(combined, cut_all=False)
    filtered = [w for w in words if w.strip() and w not in STOPWORDS and len(w) > 1]
    freq = Counter(filtered)
    return [{"word": w, "count": c} for w, c in freq.most_common(top_n)]


def _find_font() -> str:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return ""
