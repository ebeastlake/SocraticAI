from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import uuid
import time
import subprocess
import logging
from subprocess import TimeoutExpired

from AliceBobCindy import *

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.session_cookie_name = 'myapp_session'
app.secret_key = 'socraticalpaca'
Session(app)

N = 3
last_client_id = 0
session_states = {}

class SessionState:
    def __init__(self, client_id):
        self.client_id = client_id

        self.ai_tutor = StudentPersonaGPT(role="ai_tutor", n_round=N)
        self.student = StudentPersonaGPT(role="student", n_round=N)
        # self.proofreader = StudentPersonaGPT(role="Proofreader", n_round=N)

        self.dialogue_lead = None
        self.dialogue_follower = None
        self.in_progress = False

    def reset(self):
        self.ai_tutor.history.clear()
        self.student.history.clear()
        # Optionally, reset the proofreader history if implemented
        # if hasattr(session_state, 'proofreader'):
        #     session_state.proofreader.history.clear()

        self.dialogue_lead = None
        self.dialogue_follower = None

        self.in_progress = False

@app.route('/')
def index():
    global last_client_id
    last_client_id += 1
    session['client_id'] = last_client_id
    session_states[last_client_id] = SessionState(last_client_id)

    app.logger.info(f'Request to index received')
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering template: {e}')
        return 'An error occurred during template rendering.', 500


@app.route('/active-message')
def active_message():
    client_id = int(session['client_id'])
    if client_id not in session_states:
        session_states[client_id] = SessionState(client_id)
    session_state = session_states[client_id]

    if session_state.in_progress:
        # TODO: Add logic to only check the dialogue lead's history
        ai_tutor_reached_limit = len(session_state.ai_tutor.history) >= session_state.ai_tutor.n_round
        student_reached_limit = len(session_state.student.history) >= session_state.student.n_round
        if ai_tutor_reached_limit or student_reached_limit:
            # Terminate the dialogue if the turn count exceeds the maximum number of rounds
            session_state.reset()
            completion_message = "Our session has concluded. Thank you for participating!"
            return jsonify([{'role': 'system', 'response': completion_message}])

        # Proceed with the dialogue
        rep = session_state.dialogue_follower.get_response()
        session_state.dialogue_lead.update_history(rep)

        msg_list = [{'role': session_state.dialogue_follower.role.lower(), 'response': rep}]

        # Swap roles for the next turn, if the dialogue continues
        session_state.dialogue_lead, session_state.dialogue_follower = session_state.dialogue_follower, session_state.dialogue_lead
        return jsonify(msg_list)

@app.route('/chat', methods=['POST'])
def chat():
    # global session_states
    # client_id = int(session['client_id'])
    # session_state = session_states[client_id]

    client_id = session.get('client_id')
    if not client_id:
        # Handle error: No client ID found in session
        return jsonify({'error': 'Session not initialized'}), 400
    
    session_state = session_states.get(client_id)
    if session_state and session_state.in_progress:
        return jsonify({'error': 'Conversation already in progress'}), 400
    
    selected_persona = request.json.get('selected_persona')
    if not session_state:
        session_states[client_id] = SessionState(client_id)
        session_state = session_states[client_id]

    session_state.in_progress = True

    session_state.dialogue_lead, session_state.dialogue_follower = session_state.ai_tutor, session_state.student
    session_state.ai_tutor.initialize_chat()
    session_state.student.initialize_chat(selected_persona)

    return jsonify([{'role': 'system', 'response': f"You just chose to act as the distracted student. A conversation between the AI Tutor and your user persona will begin shortly..."}])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.logger.info("Starting Flask application...")
    app.run(host='127.0.0.1', port=5000, debug=True)