from flask import Flask, request, abort

# dotenv
from dotenv import load_dotenv
import os
load_dotenv()

# line-sdk
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    send_message = event.message.text # 送られてきたメッセージ

    # ゲーム開始
    if send_message == "うみがめ開始":
        mess = "ゲームを立ち上げました!\nKPが決まったら「KP決まった」と送信してください"
        line_bot_api.reply_message(
            event.reply_token,
            [TextMessage(text=mess)]
        )


if __name__ == "__main__":
    app.run()