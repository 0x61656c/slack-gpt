# Import required libraries
import os
import re
from flask import Flask, request
import slack_sdk
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
import openai

# Set your API tokens for Slack and GPT-4 (replace with your actual tokens)
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
GPT4_API_TOKEN = os.environ.get("GPT4_API_TOKEN")

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack client
slack_client = WebClient(token=SLACK_API_TOKEN)

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

# Socket Mode event handler for receiving a message in Slack
def handle_message(payload):
    event = payload["event"]
    bot_user_id = slack_client.auth_test()["user_id"]
    user_input = event["text"]

    # Check if the bot is mentioned directly
    if re.search(f"<@{bot_user_id}>", user_input):
        gpt4_response = generate_gpt4_response(user_input)
        slack_client.chat_postMessage(channel=event["channel"], text=gpt4_response)

# Socket Mode event listener
def process_socket_mode_request(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        if req.payload["event"]["type"] == "app_mention":
            handle_message(req.payload)
        client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

# Initialize and start the Socket Mode client
if __name__ == "__main__":
    socket_mode_client = SocketModeClient(app_token=SLACK_APP_TOKEN)
    socket_mode_client.socket_mode_request_listeners.append(process_socket_mode_request)
    socket_mode_client.connect()