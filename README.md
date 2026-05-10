# NexusAI Central Hub — Connecting Tools and Reasoning

A central AI system designed to coordinate multiple AI agents (Calendar, Mail, Coding, Meeting, Backend, Frontend) and enable reasoning across tools.

This repository contains modular Python agent scripts that interact with APIs and perform autonomous tasks.

## 🧠 Project Overview

This project integrates several intelligent agents to perform tasks such as:

- Scheduling events (`calender_agent.py`)
- Sending and handling emails (`mailAgent.py`)
- Running or coordinating coding activities (`codingAgent.py`)
- Managing meetings (`meet.py`, `meetAgent.py`)
- Handling backend and frontend logic (`backend.py`, `frontend.py`)

The architecture enables agents to communicate and perform tasks collaboratively, forming a central reasoning hub.

## 📁 Repository Structure
```
├── backend.py
├── calender_agent.py
├── codingAgent.py
├── frontend.py
├── mailAgent.py
├── meet.py
├── meetAgent.py
├── requirements.txt
├── testing.ipynb
├── .gitignore
```

## 🧩 Features

- Modular agent design
- Individual script for each functional agent
- Easily extendable to add more agents
- Designed for multi-agent reasoning workflows
- Can be connected with external APIs (Google Calendar, Gmail, etc.)

## ⚙️ Setup & Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/PrasannaMadiwar/NexusAI-Central-hub-connecting-tools-and-reasoning.git
   cd NexusAI-Central-hub-connecting-tools-and-reasoning
   ```
2. Create a virtual environment and activate it:
```
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```
## 🛠️ Environment Variables

Create a .env file in the root directory with credentials and API keys required by the agents:
```
API_KEY=your_api_key_here
CALENDAR_CREDENTIALS=path/to/credentials.json
MAIL_CREDENTIALS=path/to/service_account.json
```
Important: Keep .env and credentials files out of Git and never commit them.

## 🧪 Testing

You can use testing.ipynb to explore and test agent functionality interactively.

## 📌 Usage

Each agent script is designed to be run individually or as part of an orchestrator:

```
python backend.py
python mailAgent.py
python meetAgent.py
```
You can build a coordinator script to run agents in sequence or based on triggers.

## 💡 Examples

### Example usage in other applications:

Trigger an email reminder using the calendar agent

Automate meeting creation with invite links

Run coding assistant tasks from the command line
