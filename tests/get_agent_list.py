#!/usr/bin/env python3
"""
get_agent_list.py

A simple script to fetch and print the list of agents 
from your Chatwoot account using environment variables.
Requires:
    pip install python-dotenv requests
Usage:
    python get_agent_list.py
"""
from dotenv import load_dotenv
import os
import requests

def main():
    # Load environment variables from .env file
    load_dotenv()

    account_id = os.getenv('ACCOUNT_ID')
    api_token = os.getenv('CHATWOOT_API_TOKEN')

    if not account_id or not api_token:
        print("Error: ACCOUNT_ID and CHATWOOT_API_TOKEN must be set in your environment.")
        return

    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/agents"
    headers = {
        "api_access_token": api_token
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print("Response content:", response.text)
        return
    except Exception as err:
        print(f"An error occurred: {err}")
        return

    agents = response.json()
    print("Agents:")
    for agent in agents:
        print(f"- ID: {agent.get('id')} | Name: {agent.get('name')} | Email: {agent.get('email')}")

main()
