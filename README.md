# A股事件机会雷达

一个以财报、股东行为和政策事件为输入的可解释 A 股研究 MVP。支持模拟数据、AKShare，以及作为免费备用源的 BaoStock。

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

默认使用模拟数据。启用免费公开数据时修改 `.env`：

```dotenv
DATA_PROVIDER=akshare
PROVIDER_FALLBACK=baostock
WATCHLIST=600519,000858,601318
```

AKShare 依赖上游公开网页，接口失败时会自动尝试 BaoStock。缺失的政策、股东或估值字段采用中性值，并在页面标注；不会用虚构数据填补。

也可以使用 Docker：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## 当前接口

- `GET /api/health`
- `GET /api/opportunities?horizon=short`
- `GET /api/stocks/{code}/opportunity?horizon=medium`

## 安全约定

- 不向 GitHub 提交 `.env`、供应商密钥、账号密码或原始授权数据。
- 浏览器仅调用本项目后端，不直接接触供应商凭据。
- 是否允许缓存、保存和展示衍生数据，以数据供应商合同为准。

## 接入真实数据前需要确认

- API 的 Python 调用示例和返回字段说明。
- 是否依赖 Windows iFinD 客户端、固定机器或固定 IP。
- 调用频率、并发数以及缓存和衍生展示授权。
