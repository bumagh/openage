import base64
import json
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from openage import predict_age

app = FastAPI(title="OpenAge 生物年龄预测")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CHAT_DAILY_LIMIT = 10
OCR_DAILY_LIMIT = 3
REDEEM_CODE = "csqmr"
REDEEM_BONUS = 3

# {ip: {date_str: {"ocr": used, "chat": used, "ocr_bonus": n, "chat_bonus": n}}}
_usage: dict = defaultdict(lambda: defaultdict(lambda: {"ocr": 0, "chat": 0, "ocr_bonus": 0, "chat_bonus": 0}))


def _get_today_usage(ip: str) -> dict:
    today = str(date.today())
    u = _usage[ip]
    # clean old dates
    for d in list(u):
        if d != today:
            del u[d]
    return u[today]


def _check_limit(ip: str, feature: str):
    base = OCR_DAILY_LIMIT if feature == "ocr" else CHAT_DAILY_LIMIT
    u = _get_today_usage(ip)
    u[feature] += 1
    limit = base + u[f"{feature}_bonus"]
    if u[feature] > limit:
        raise HTTPException(status_code=429, detail="daily_limit_exceeded")

SYSTEM_PROMPT = """你是一位专业的健康顾问，擅长解读血液检查报告和生物年龄评估结果。
用中文回答，语言简洁易懂，避免过度医学术语。
不要给出具体的诊断，但可以提供健康建议和生活方式改善建议。
如果用户询问具体疾病诊断，请建议他们咨询医生。"""


class BloodPanel(BaseModel):
    chronological_age: int
    variant: str = "standard"
    # 基础血常规
    mean_cell_volume_fl: Optional[float] = None
    glycohemoglobin_percent: Optional[float] = None
    alt_iu_l: Optional[float] = None
    rbc_count_million_per_ul: Optional[float] = None
    ever_cancer_or_malignancy: int = 2
    platelet_count_thousand_per_ul: Optional[float] = None
    ldh_iu_l: Optional[float] = None
    ever_angina: int = 2
    lymphocyte_percent: Optional[float] = None
    lymphocyte_count_thousand_per_ul: Optional[float] = None
    cpk_iu_l: Optional[float] = None
    creatinine_mg_dl: Optional[float] = None
    ever_arthritis: int = 2
    alp_iu_l: Optional[float] = None
    ever_liver_condition: int = 2
    potassium_mmol_l: Optional[float] = None
    rdw_percent: Optional[float] = None
    monocyte_percent: Optional[float] = None
    bun_mg_dl: Optional[float] = None
    ever_gallstones: int = 2
    glucose_mg_dl: Optional[float] = None
    # extended 模型额外字段
    hemoglobin_g_dl: Optional[float] = None
    hematocrit_percent: Optional[float] = None
    wbc_count_thousand_per_ul: Optional[float] = None
    ast_iu_l: Optional[float] = None
    total_bilirubin_mg_dl: Optional[float] = None
    calcium_mg_dl: Optional[float] = None
    chloride_mmol_l: Optional[float] = None
    ldl_cholesterol_mg_dl: Optional[float] = None
    hdl_cholesterol_mg_dl: Optional[float] = None
    triglycerides_mg_dl: Optional[float] = None
    total_protein_g_dl: Optional[float] = None
    bicarbonate_mmol_l: Optional[float] = None
    osmolality_mmol_kg: Optional[float] = None
    sodium_mmol_l: Optional[float] = None


class RedeemRequest(BaseModel):
    code: str
    feature: str  # "ocr" or "chat"


@app.post("/api/redeem")
async def redeem(body: RedeemRequest, request: Request):
    if body.code.strip() != REDEEM_CODE:
        raise HTTPException(status_code=400, detail="invalid_code")
    if body.feature not in ("ocr", "chat"):
        raise HTTPException(status_code=400, detail="invalid_feature")
    ip = request.client.host
    u = _get_today_usage(ip)
    u[f"{body.feature}_bonus"] += REDEEM_BONUS
    return {"added": REDEEM_BONUS}


class ChatMessage(BaseModel):
    message: str
    history: list
    report_context: Optional[dict] = None


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.post("/api/ocr")
async def ocr_image(request: Request, file: UploadFile = File(...)):
    """用 Claude Vision 解析血检图片，提取数值"""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="未配置 ANTHROPIC_API_KEY")

    ip = request.client.host
    _check_limit(ip, "ocr")

    content = await file.read()
    b64 = base64.standard_b64encode(content).decode()
    media_type = file.content_type or "image/jpeg"

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64}
                },
                {
                    "type": "text",
                    "text": """请从这张血检报告图片中提取数值，返回 JSON 格式。
只返回 JSON，不要其他文字。字段名使用以下英文名称：
- mean_cell_volume_fl: 平均红细胞体积 MCV (fL)
- glycohemoglobin_percent: 糖化血红蛋白 HbA1c (%)
- alt_iu_l: 谷丙转氨酶 ALT (IU/L)
- ast_iu_l: 谷草转氨酶 AST (IU/L)
- rbc_count_million_per_ul: 红细胞计数 (10^6/μL)
- hemoglobin_g_dl: 血红蛋白，若单位g/L请除以10
- hematocrit_percent: 红细胞压积/红细胞比积 (%)
- wbc_count_thousand_per_ul: 白细胞计数 (10^3/μL)
- platelet_count_thousand_per_ul: 血小板计数 (10^3/μL)
- ldh_iu_l: 乳酸脱氢酶 LDH (IU/L)
- lymphocyte_percent: 淋巴细胞百分比 (%)
- lymphocyte_count_thousand_per_ul: 淋巴细胞绝对值 (10^3/μL)
- monocyte_percent: 单核细胞百分比 (%)
- rdw_percent: 红细胞分布宽度 RDW (%)
- cpk_iu_l: 肌酸激酶 CPK/CK (IU/L)
- alp_iu_l: 碱性磷酸酶 ALP (IU/L)
- total_protein_g_dl: 总蛋白，若单位g/L请除以10
- total_bilirubin_mg_dl: 总胆红素，若单位μmol/L请除以17.1
- creatinine_mg_dl: 肌酐，若单位μmol/L请除以88.4
- bun_mg_dl: 尿素氮，若单位mmol/L请乘以2.8
- glucose_mg_dl: 血糖，若单位mmol/L请乘以18
- triglycerides_mg_dl: 甘油三酯，若单位mmol/L请乘以88.6
- ldl_cholesterol_mg_dl: 低密度脂蛋白LDL，若单位mmol/L请乘以38.67
- hdl_cholesterol_mg_dl: 高密度脂蛋白HDL，若单位mmol/L请乘以38.67
- sodium_mmol_l: 血钠 (mmol/L)
- potassium_mmol_l: 血钾 (mmol/L)
- calcium_mg_dl: 血钙，若单位mmol/L请乘以4.0
- chloride_mmol_l: 血氯 (mmol/L)

没有的字段不要包含在JSON中。"""
                }
            ]
        }]
    )

    text = response.content[0].text.strip()
    # 提取 JSON 块
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except Exception:
        raise HTTPException(status_code=422, detail=f"无法解析图片中的数据: {text}")


@app.post("/api/predict")
async def predict(panel: BloodPanel):
    """预测生物年龄"""
    data = {k: v for k, v in panel.dict().items()
            if k not in ("chronological_age", "variant") and v is not None}

    for q in ["ever_cancer_or_malignancy", "ever_angina", "ever_arthritis",
              "ever_liver_condition", "ever_gallstones"]:
        data[q] = getattr(panel, q)

    try:
        result = predict_age(data, chronological_age=panel.chronological_age,
                             variant=panel.variant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "biological_age": round(result.biological_age, 1),
        "chronological_age": panel.chronological_age,
        "delta": round(result.chronological_age_delta, 1) if result.chronological_age_delta else None,
        "classification": result.age_acceleration,
        "model_variant": result.model_variant,
    }


@app.post("/api/chat")
async def chat(body: ChatMessage, request: Request):
    """流式对话，携带报告上下文"""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="未配置 ANTHROPIC_API_KEY")

    ip = request.client.host
    _check_limit(ip, "chat")

    messages = []

    # 注入报告上下文作为第一条消息
    if body.report_context:
        ctx = body.report_context
        context_text = f"""用户的生物年龄预测报告：
- 实际年龄：{ctx.get('chronological_age')} 岁
- 生物年龄：{ctx.get('biological_age')} 岁
- 差值：{ctx.get('delta', 0):+.1f} 年
- 衰老状态：{ctx.get('classification')}
- 血检数据：{json.dumps(ctx.get('blood_panel', {}), ensure_ascii=False)}"""
        messages.append({"role": "user", "content": context_text})
        messages.append({"role": "assistant", "content": "好的，我已了解您的报告情况，请问有什么想了解的？"})

    for msg in body.history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": body.message})

    def generate():
        with claude.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
