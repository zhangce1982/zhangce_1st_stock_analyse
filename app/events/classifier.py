from hashlib import sha256


INDUSTRY_KEYWORDS = {
    "电子": ("半导体", "芯片", "集成电路", "电子"),
    "计算机": ("人工智能", "算力", "数据要素", "软件", "数字化"),
    "电力设备": ("新能源", "光伏", "风电", "储能", "电池", "充电桩"),
    "汽车": ("汽车", "新能源车", "智能网联"),
    "医药生物": ("医药", "医疗", "药品", "中医药", "生物技术"),
    "机械设备": ("设备更新", "工业母机", "机器人", "农机"),
    "农林牧渔": ("农业", "粮食", "种业", "养殖", "乡村振兴"),
    "房地产": ("房地产", "住房", "城市更新"),
    "家用电器": ("家电", "以旧换新"),
    "商贸零售": ("消费", "零售", "以旧换新"),
    "环保": ("环保", "节能", "污染治理", "生态环境"),
    "国防军工": ("军工", "航空航天", "国防"),
}

POSITIVE_WORDS = ("支持", "补贴", "促进", "加快", "扩大", "贴息", "提升", "鼓励", "中标", "增持", "回购", "预增")
NEGATIVE_WORDS = ("限制", "禁止", "处罚", "立案", "暂停", "收紧", "减持", "亏损", "退市", "风险警示")


def classify_text(title: str) -> tuple[list[str], str, float, list[str]]:
    industries = [
        industry
        for industry, keywords in INDUSTRY_KEYWORDS.items()
        if any(keyword in title for keyword in keywords)
    ]
    positive_hits = [word for word in POSITIVE_WORDS if word in title]
    negative_hits = [word for word in NEGATIVE_WORDS if word in title]
    if positive_hits and not negative_hits:
        direction = "positive"
    elif negative_hits and not positive_hits:
        direction = "negative"
    elif positive_hits or negative_hits:
        direction = "uncertain"
    else:
        direction = "neutral"
    impact = min(90, 45 + len(industries) * 8 + (15 if positive_hits or negative_hits else 0))
    evidence = [f"行业关键词：{', '.join(industries)}"] if industries else []
    evidence.extend([f"方向关键词：{', '.join(positive_hits + negative_hits)}"] if positive_hits or negative_hits else [])
    return industries, direction, impact, evidence


def event_id(source: str, url: str, title: str) -> str:
    return sha256(f"{source}|{url}|{title}".encode("utf-8")).hexdigest()[:20]
