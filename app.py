python
# Import required libraries
import os
import re
from flask import Flask, request, jsonify
import slack
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import openai

# Set your API tokens for Slack and GPT-4 (replace with your actual tokens)
SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
GPT4_API_TOKEN = os.environ.get("GPT4_API_TOKEN")

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack client and event adapter
slack_client = WebClient(token=SLACK_API_TOKEN)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize GPT-4 API client
openai.api_key = GPT4_API_TOKEN

# Function to fetch the last 10 messages from the channel
def fetch_last_10_messages(channel_id):
    response = slack_client.conversations_history(channel=channel_id, limit=10)
    messages = response["messages"]
    return messages

# Function to generate a response from GPT-4
def generate_gpt4_response(prompt, system_prompt, channel_id):
    messages = fetch_last_10_messages(channel_id)
    messages_formatted = [{"role": "user" if msg["user"] != bot_user_id else "assistant", "content": msg["text"]} for msg in messages]
    messages_formatted.insert(0, {"role": "system", "content": system_prompt})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages_formatted,
        max_tokens=2000,
        n=1,
        temperature=0.5,
    )
    return response.choices[0].message["content"].strip()

# Event handler for receiving a message in Slack
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    event = event_data["event"]
    bot_user_id = slack_client.auth_test()["user_id"]
    user_input = event["text"]

    # Check if the bot is mentioned directly
    if re.search(f"<@{bot_user_id}>", user_input):
        gpt4_response = generate_gpt4_response(user_input, "You are a helpful assistant.", event["channel"])
        slack_client.chat_postMessage(channel=event["channel"], text=gpt4_response)

# Handle Slash command
@app.route("/code", methods=["POST"])
def handle_code_slash_command():
    data = request.form
    user_input = data.get("text")
    response_url = data.get("response_url")

    # Verify the request is from Slack
    if not slack.signature.verify_signature(request):
        return jsonify({"error": "Invalid request"}), 403

    gpt4_response = generate_gpt4_response(user_input, "You are a code-writing assistant.", response_url)
    slack_client.chat_postMessage(channel=response_url, text=gpt4_response)
    return jsonify({"response_type": "in_channel", "text": gpt4_response})

# Start the Flask app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)