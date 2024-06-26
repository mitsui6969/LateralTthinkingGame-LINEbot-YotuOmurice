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
    MessageEvent, TextMessage, TextSendMessage, TextSendMessage, SourceUser, SourceGroup, JoinEvent
)

import threading

import json
import random

timer_duration = 0

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# jsonファイル読み込み
with open('./questions.json', 'r', encoding='utf-8') as json_file:
    questions = json.load(json_file)


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

timer_duration = 0
game_stated = False
timer_set = False
timer_running = False  # タイマーが実行中かどうかを追跡するためのフラグ

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    send_message = event.message.text.strip().lower() # 送られてきたメッセージ
    global timer_duration, id, game_stated, timer_set, timer_running
    

    ### グループの処理 ###
    if isinstance(event.source, SourceGroup):
        # ゲーム開始
        if send_message == "うみがめくん":
            game_stated = True
            mess = "ゲームを立ち上げました! KPを決めてください。\nKPが決まったら「ゲーム開始」と入力すると問題が表示されます。\n「時間設定」と入力すると制限時間を設定することができます。"
            line_bot_api.reply_message(
                event.reply_token,
                [TextMessage(text=mess)]
            )

        if game_stated == True:
            # 時間設定
            if send_message =="時間設定":
                time_selection(event)
            if send_message in ["10", "20", "30"]:
                timer_duration = int(send_message)
                message_time = f"{timer_duration}分に決定しました！\nタイマーはゲーム開始と同時にスタートします\n「ゲーム開始」と入力すると問題が表示されます"
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextMessage(text=message_time)]
                )
                timer_set = True

            # 問題出題
            if send_message == "ゲーム開始":
                mess = "問題を出題します\n\nKPは問題IDをうみがめくん個人チャットに入力して答えを取得してください。\n\n「ゲーム終了」と入力すると答えを表示してゲームを終了します"
                id = random.choice(list(questions.keys()))
                mess2 = f"質問を開始してください！"
                title = questions[id]["title"]
                id_title = f"問題ID:{id}\nタイトル:{title}"
                question = questions[id]["question"]
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text=mess),TextSendMessage(text=id_title),TextSendMessage(text=question),TextSendMessage(text=mess2)]
                )
                if timer_set == True:
                    timer_running = True
                    start_timer_event(event, timer_duration)

            # 答え表示
            if send_message == "ゲーム終了":
                mess = "答えです"
                answer = questions[id]["answer"]
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text=mess),TextSendMessage(text=answer)]
                )
                game_stated = False
                timer_set = False
                timer_running = False

        else:
            if send_message in [ "時間設定", "ゲーム開始", "ゲーム終了"]:
                mess = "ゲームが開始されていません。\nゲームを開始するには「うみがめくん」と入力してください"
                line_bot_api.reply_message(
                        event.reply_token,
                        [TextSendMessage(text=mess)]
                    )

    # 個人チャット
    if isinstance(event.source, SourceUser):
        if send_message in questions.keys():
            id = send_message
            title = questions[id]["title"]
            mess = f"タイトル「{title}」の答えです"
            answer = questions[id]["answer"]
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text=mess),TextSendMessage(text=answer)]
            )

## グループ加入時
@handler.add(JoinEvent)
def handle_join(event):
    greeting_message = "こんにちは！うみがめ問題ボットです。\nゲームを開始するには「うみがめくん」と入力してください。"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=greeting_message)
    )



# 時間選択
def time_selection(event):
    message = "制限時間を以下から選び入力してください。\n数字のみ記入してください。単位は分です。\n10分 \n20分 \n30分"
    line_bot_api.reply_message(
        event.reply_token,
        [TextMessage(text=message)]
    )
    
# タイマー機能
def start_timer_event(event, duration):
    secounds = duration * 60
    def timer_thread(group_id,seconds): 
        import time
        time.sleep(seconds)
        if seconds == duration * 60:
            global game_stated, timer_running
            game_stated = False
            timer_running = False
            answer = questions[id]["answer"]
            line_bot_api.push_message(
                group_id,
                [TextMessage(text=f"{duration}分のタイマーが終了しました。答えを表示します"), TextSendMessage(text=answer)]
            )
    threading.Thread(target=timer_thread, args=(event.source.group_id,secounds)).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  # デプロイ環境
    # app.run() # 開発環境