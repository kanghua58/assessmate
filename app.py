from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

# Global variable to store the current thread
current_thread = None

@app.route("/")
def index():
    # Ensure any existing session data is cleared when returning to the index page
    session.pop('messages', None)
    session.pop('thread_id', None)
    return render_template("index.html")

@app.route("/chat")
def chat():
    # Render chat page with existing messages, if any
    return render_template("chat.html", messages=session.get('messages', []))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from dotenv import load_dotenv
from openai import OpenAI, APIError

# Load environment variables
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

# Global variable to store the current thread
current_thread = None

@app.route("/")
def index():
    # Ensure any existing session data is cleared when returning to the index page
    session.pop('messages', None)
    session.pop('thread_id', None)
    return render_template("index.html")

@app.route("/chat")
def chat():
    # Render chat page with existing messages, if any
    return render_template("chat.html", messages=session.get('messages', []))

@app.route("/ask", methods=["POST"])
def ask():
    global current_thread

    try:
        user_message = request.json["message"]

        # Create a new thread if none exists
        if current_thread is None:
            current_thread = openai_client.beta.threads.create()
            session["thread_id"] = current_thread.id

        # Add user's message to the session
        session['messages'] = session.get('messages', []) + [('user', user_message)]

        # Send the user's message to the thread
        message = openai_client.beta.threads.messages.create(
            thread_id=current_thread.id,
            role="user",
            content=user_message
        )

        # Run the assistant on the thread
        run = openai_client.beta.threads.runs.create(
            thread_id=current_thread.id,
            assistant_id=os.getenv("OPENAI_ASSISTANT_ID")
        )

        # Retrieve the assistant's response
        while True:
            run = openai_client.beta.threads.runs.retrieve(thread_id=current_thread.id, run_id=run.id)
            if run.status == "completed":
                messages = openai_client.beta.threads.messages.list(thread_id=current_thread.id)
                latest_message = messages.data[0]
                assistant_response = latest_message.content[0].text.value
                break

        # Add assistant's response to the session
        session['messages'] = session.get('messages', []) + [('assistant', assistant_response)]

        return jsonify({
            "answer": assistant_response,
            "userMessage": user_message,
            "userAvatarUrl": url_for('static', filename='images/logo/you.svg'),
            "systemAvatarUrl": url_for('static', filename='images/logo/icon.svg')
        })

    except APIError as e:
        # Handle OpenAI API specific errors
        error_message = f"OpenAI API Error: {str(e)}"
        return jsonify({"error": error_message}), 500

    except KeyError as e:
        # Handle missing 'message' key in request JSON
        error_message = f"Missing 'message' in request: {str(e)}"
        return jsonify({"error": error_message}), 400

    except Exception as e:
        # Handle any other unexpected errors
        error_message = f"Unexpected error: {str(e)}"
        return jsonify({"error": error_message}), 500

@app.route("/clear-session", methods=["POST"])
def clear_session():
    global current_thread
    # No need to check session_id in this simplified version, but you could add that check for more complex scenarios
    current_thread = None
    session.pop('messages', None)
    session.pop('thread_id', None)

    return jsonify({"status": "session cleared"})

if __name__ == "__main__":
    app.run(debug=True)
