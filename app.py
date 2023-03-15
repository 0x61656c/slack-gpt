# Import required libraries
import os
import re
from flask import Flask, request
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
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

# Event handler for receiving a message in Slack
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    event = event_data["event"]
    bot_user_id = slack_client.auth_test()["user_id"]
    user_input = event["text"]

    # Check if the bot is mentioned directly
    if re.search(f"<@{bot_user_id}>", user_input):
        gpt4_response = generate_gpt4_response(user_input)
        slack_client.chat_postMessage(channel=event["channel"], text=gpt4_response)

# Start the Flask app
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)