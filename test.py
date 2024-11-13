import requests

def send_sms_test():
    # 设置请求的 URL，替换为您的 ngrok URL
    url = "https://5e6f-50-231-83-246.ngrok-free.app/sms/reply"
    
    # 设置请求的数据
    data = {
        "Body": "Hello",            # 短信内容
        "From": "+15146133398",     # 替换为已验证的发送号码
        "To": "+15712371754"        # 您的 Twilio 接收号码
    }
    
    try:
        # 发送 POST 请求
        response = requests.post(url, data=data)
        
        # 输出响应
        if response.status_code == 200:
            print("SMS Test Sent Successfully.")
            print("Response:", response.text)
        else:
            print(f"Failed to send SMS. Status Code: {response.status_code}")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# 执行测试
send_sms_test()
