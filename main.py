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
    MessageEvent, TextMessage, TextSendMessage,TemplateSendMessage, ButtonsTemplate, PostbackAction, PostbackEvent, TextSendMessage
)

import threading

import time

timer_duration = 0

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
    if send_message == "うみがめ問題":
        mess = "ゲームを立ち上げました! KPを決めてください。\n時間を設定する場合は「ゲーム時間設定」と入力してください。"
        line_bot_api.reply_message(
            event.reply_token,
            [TextMessage(text=mess)]
        )
    elif send_message =="ゲーム時間設定":
        time_selection(event)
    elif send_message in ["10","20","30"]:
        global timer_duration
        timer_duration = int(send_message)
        message_time = f"{timer_duration}分に決定しました！\nタイマーを開始するときは「タイマー開始」を入力してください。"
        line_bot_api.reply_message(
            event.reply_token,
            [TextMessage(text=message_time)]
        )
    elif send_message =="タイマー開始":
        message_timer = "タイマーを開始します。"
        line_bot_api.reply_message(
            event.reply_token,
            [TextMessage(text=message_timer)]
        )
        start_timer_event(event, timer_duration)

    # 時間管理
def time_selection(event):
    message = "時間を決定してください。\n単位は分で決定しています。数字のみ記入してください。\n10分 \n20分 \n30分"
    line_bot_api.reply_message(
        event.reply_token,
        [TextMessage(text=message)]
    )
    
def start_timer_event(event, timer_duration):
    secounds = timer_duration * 60

    def timer_thread(user_id,seconds): 
        time.sleep(seconds)
        if seconds == timer_duration * 60:
            line_bot_api.push_message(
                user_id,
                [TextMessage(text=f"{timer_duration}分のタイマーが終了しました。")]
            )
    threading.Thread(target=timer_thread, args=(event.source.user_id,secounds)).start()

       
    # KP確認＆問題提示


    # 回答表示


    # 個チャのやつ


if __name__ == "__main__":
    app.run()