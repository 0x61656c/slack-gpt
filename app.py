# Import required libraries
import os
import re
from flask import Flask, request, jsonify
import slack
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import openai
import sentry_sdk

sentry_sdk.init(
    dsn="https://7f314340aa0742c7aa30c562a670a27c@o339809.ingest.sentry.io/4504848446062592",
    traces_sample_rate=1.0
)

# Set your API tokens for Slack and GPT-4 (replace with your actual tokens)
SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack client and event adapter
slack_client = WebClient(token=SLACK_API_TOKEN)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)
from datetime import datetime

@slack_events_adapter.on("message")
def handle_message(event_data):
    retry_num = request.headers.get('X-Slack-Retry-Num')
    if retry_num and int(retry_num) > 0:
        return "OK", 200
    event = event_data["event"]
    bot_user_id = slack_client.auth_test()["user_id"]
    user_input = event["text"]
    thread_ts = event.get("thread_ts") or event["ts"]
    channel = event["channel"]
    
    # Check if the bot is mentioned directly
    if re.search(f"<@{bot_user_id}>", user_input):
        # Fetch the messages in the current thread
        conversation_history = []
        try:
            result = slack_client.conversations_replies(
                channel=event["channel"],
                ts=thread_ts
            )
            conversation_history = result["messages"]
        except Exception as e:
            print(f"Error fetching conversation history: {e}")

        slack_response = "Thanks for requesting support from Tangram. Please only fill out this form if you have an urgent error that is hindering your platform's ability to operate. Here's the link to file:  https://form.typeform.com/to/TWWlou8R"
        slack_client.chat_postMessage(channel=event["channel"], text=slack_response, thread_ts=thread_ts)

    # Check if the message mentions Aaron and it's not Monday or Friday
    if re.search("U012Z5J50M8", user_input):
        current_day = datetime.now().strftime('%A')
        if current_day not in ['Monday', 'Friday']:
            if current_day in ['Saturday', 'Sunday']:
                slack_response = "Aaron is currently unavailable for support. His next available complimentary support window is 9am-5pm on Monday. If you need help with an urgent bug, please file a support ticket here: https://form.typeform.com/to/TWWlou8R"
            else:
                slack_response = "Aaron is currently unavailable for support. His next available complimentary support window is 9am-5pm on Friday. If you need help with an urgent bug, please file a support ticket here: https://form.typeform.com/to/TWWlou8R"
            slack_client.chat_postMessage(channel=channel, text=slack_response, thread_ts=thread_ts)

    if re.search("U012SDDLX8E", user_input):
        current_day = datetime.now().strftime('%A')
        if current_day not in ['Monday', 'Friday']:
            if current_day in ['Saturday', 'Sunday']:
                slack_response = "Paris is currently unavailable for support. Her next available complimentary support window is 9am-5pm on Monday. If you need help with an urgent bug, please file a support ticket here: https://form.typeform.com/to/TWWlou8R"
            else:
                slack_response = "Paris is currently unavailable for support. Her next available complimentary support window is 9am-5pm on Friday. If you need help with an urgent bug, please file a support ticket here: https://form.typeform.com/to/TWWlou8R"
            slack_client.chat_postMessage(channel=channel, text=slack_response, thread_ts=thread_ts)

# Start the Flask app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)