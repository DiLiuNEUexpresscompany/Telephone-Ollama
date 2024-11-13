from fastapi import FastAPI, Request, HTTPException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
import httpx
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from utils.rate_limiter import RateLimiter
from utils.logger import setup_logger

# 加载环境变量
load_dotenv()

# 设置日志
logger = setup_logger()

# 初始化 FastAPI 应用
app = FastAPI(title="Twilio Voice Chatbot")

# Twilio 客户端配置
try:
    twilio_client = Client(
        os.getenv('TWILIO_ACCOUNT_SID'),
        os.getenv('TWILIO_AUTH_TOKEN')
    )
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
except Exception as e:
    logger.error(f"Twilio initialization error: {e}")
    raise

# 初始化速率限制器
voice_limiter = RateLimiter(int(os.getenv('MAX_CALLS_PER_DAY', 100)))
sms_limiter = RateLimiter(int(os.getenv('MAX_SMS_PER_DAY', 100)))

async def process_with_ollama(user_input: str) -> str:
    """使用Ollama处理用户输入"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{os.getenv('OLLAMA_API_URL')}/generate",
                json={"prompt": user_input},
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '抱歉，我现在无法理解您的输入。')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "系统暂时无法处理您的请求，请稍后再试。"
        except Exception as e:
            logger.error(f"Error processing with Ollama: {e}")
            return "抱歉，处理您的请求时出现错误。"

@app.post("/voice")
async def handle_incoming_call(request: Request):
    """处理入站电话"""
    try:
        form_data = await request.form()
        from_number = form_data.get('From')

        # 检查速率限制
        if not voice_limiter.can_proceed(from_number):
            response = VoiceResponse()
            response.say("对不起，您今天的通话次数已达上限。", language="zh-CN")
            response.hangup()
            return str(response)

        response = VoiceResponse()
        gather = Gather(
            input='speech',
            action='/process-speech',
            timeout=3,
            language='zh-CN',
            hints=['你好', '帮助', '再见']
        )
        gather.say('欢迎使用AI助手，请问有什么可以帮您？', language="zh-CN")
        response.append(gather)

        # 如果用户没有说话，重定向到开始
        response.redirect('/voice')
        
        return str(response)
    except Exception as e:
        logger.error(f"Error in voice handler: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process-speech")
async def process_speech(request: Request):
    """处理语音输入"""
    try:
        form_data = await request.form()
        user_input = form_data.get('SpeechResult', '')
        
        if not user_input:
            response = VoiceResponse()
            response.say("抱歉，我没有听清楚，请再说一遍。", language="zh-CN")
            response.redirect('/voice')
            return str(response)

        # 处理用户输入
        llm_response = await process_with_ollama(user_input)
        
        response = VoiceResponse()
        response.say(llm_response, language="zh-CN")

        # 继续对话
        gather = Gather(
            input='speech',
            action='/process-speech',
            timeout=3,
            language='zh-CN'
        )
        gather.say('您还有其他问题吗？', language="zh-CN")
        response.append(gather)
        
        return str(response)
    except Exception as e:
        logger.error(f"Error in speech processor: {e}")
        raise HTTPException(status_code=500, detail="Speech processing error")

@app.post("/sms")
async def handle_sms(request: Request):
    """处理短信"""
    try:
        form_data = await request.form()
        message_body = form_data.get('Body', '')
        from_number = form_data.get('From', '')

        # 检查速率限制
        if not sms_limiter.can_proceed(from_number):
            return "对不起，您今天的短信次数已达上限。"

        # 处理消息
        response_text = await process_with_ollama(message_body)
        
        # 发送回复
        twilio_client.messages.create(
            body=response_text,
            to=from_number,
            from_=twilio_number
        )
        
        return "Message processed"
    except Exception as e:
        logger.error(f"Error in SMS handler: {e}")
        raise HTTPException(status_code=500, detail="SMS processing error")

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Twilio Voice Chatbot")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Twilio Voice Chatbot")