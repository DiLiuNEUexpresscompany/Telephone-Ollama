from twilio.rest import Client
import os

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(account_sid, auth_token)

# 测试 API 凭据是否正确
try:
    # 获取账户信息，验证凭据
    account = twilio_client.api.accounts(account_sid).fetch()
    print("Twilio API connection successful.")
except Exception as e:
    print(f"Twilio API connection failed: {e}")
