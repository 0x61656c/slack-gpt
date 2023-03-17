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

# Function to generate a response from GPT-4
def generate_gpt4_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful slackbot assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=2000,
        n=1,
        temperature=0.5,
    )
    return response.choices[0].message["content"].strip()

# Function to generate a response from GPT-4 with conversation history as context
def generate_gpt4_response_with_context(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2000,
        n=1,
        temperature=0.5,
    )
    return response.choices[0].message["content"].strip()

# Event handler for receiving a message in Slack
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    retry_num = request.headers.get('X-Slack-Retry-Num')
    if retry_num and int(retry_num) > 0:
        return "OK", 200
    event = event_data["event"]
    bot_user_id = slack_client.auth_test()["user_id"]
    user_input = event["text"]

    # Check if the bot is mentioned directly
    if re.search(f"<@{bot_user_id}>", user_input):
        # Fetch the last 10 messages in the thread
        conversation_history = []
        try:
            result = slack_client.conversations_history(
                channel=event["channel"],
                latest=event["ts"],
                limit=10,
                inclusive=False
            )
            conversation_history = result["messages"]
        except Exception as e:
            print(f"Error fetching conversation history: {e}")

        # Prepare the context for GPT-4
        messages = [{"role": "system", "content": "You are a helpful slackbot assistant."}]
        for message in reversed(conversation_history):
            role = "user" if message.get("user") != bot_user_id else "assistant"
            content = message["text"]
            messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_input})

        # Generate a response using the context
        gpt4_response = generate_gpt4_response_with_context(messages)
        slack_client.chat_postMessage(channel=event["channel"], text=gpt4_response, thread_ts=event["ts"])

# Slash command handler for /code
@app.route("/slack/code", methods=["POST"])
def handle_slash_code():
    prompt = request.form["text"]
    response_text = generate_gpt4_code_response(prompt)
    response = {"response_type": "in_channel", "text": response_text}
    return jsonify(response)

# Start the Flask app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)