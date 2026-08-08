# A股事件机会雷达

一个以财报、股东行为、公司公告和国家政策为输入的可解释 A 股研究 MVP。支持模拟数据、AKShare，以及作为免费备用源的 BaoStock。

> 仅用于研究和软件验证，不构成投资建议。

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

打开 `http://127.0.0.1:8000`，接口文档位于 `http://127.0.0.1:8000/docs`。

启用免费公开数据时修改 `.env`：

```dotenv
DATA_PROVIDER=akshare
PROVIDER_FALLBACK=baostock
WATCHLIST=600519,000858,601318
DATABASE_PATH=data/app.db
```

也可以使用 Docker：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## 当前接口

- `GET /api/health`
- `GET /api/opportunities?horizon=short`
- `GET /api/stocks/{code}/opportunity?horizon=medium`
- `GET /api/events`
- `GET /api/events?target_date=2026-08-08`
- `GET /api/backtest?horizon=short`

事件接口按需读取关注池公司的公开公告及中国政府网最新政策，返回原文链接、方向关键词、行业映射和规则影响分。

项目默认使用免费的 SQLite 保存标准化事件和评分历史。数据库位于 `data/app.db`，已被 `.gitignore` 排除；生产数据量增长后可迁移到 PostgreSQL。

回测使用信号生成日期之后的首个交易日收盘价作为入场价，短期评估 5/20 个交易日，中期评估 60 个交易日。样本少于 20 条时明确标记为样本不足，避免把偶然结果包装成有效策略。

## 数据与安全

- AKShare 依赖上游公开网页，失败时自动尝试 BaoStock。
- 缺失字段采用中性值并在页面标注，不用虚构数据填补。
- 不向 GitHub 提交 `.env`、供应商密钥、账号密码、数据库或原始授权数据。
- 是否允许缓存、保存和展示衍生数据，以数据供应商合同为准。
