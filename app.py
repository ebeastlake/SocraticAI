from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import uuid
import logging

from AliceBobCindy import StudentPersonaGPT, prompts

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.session_cookie_name = 'myapp_session'
app.secret_key = 'socraticalpaca'
Session(app)

session_states = {}
default_n_turns = 5

class SessionState:
    def __init__(self, client_id, n_turns=None):
        self.client_id = client_id
        self.n_turns = n_turns

        self.ai_tutor = StudentPersonaGPT(role="ai_tutor", app=app)
        self.student = StudentPersonaGPT(role="student", app=app)
        self.ai_tutor.other_role = self.student
        self.student.other_role = self.ai_tutor
        # self.proofreader = StudentPersonaGPT(role="Proofreader")

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
    try:
        app.logger.debug(f'Request to index received')
        client_id = str(uuid.uuid4())
        session['client_id'] = client_id
        session_states[client_id] = SessionState(client_id)
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering template: {e}')
        return 'An error occurred during template rendering.', 500


@app.route('/active-message')
def active_message():
    global session_states
    # app.logger.debug(f"Request to active-message received")
    client_id = session.get('client_id')
    if not client_id or client_id not in session_states:
        # app.logger.debug("Session not initialized or client_id not found in session_states.")
        return jsonify({'error': 'Session not initialized'}), 400
    
    session_state = session_states[client_id]

    if not session_state.in_progress:
        # app.logger.debug("Session not in progress yet.")
        return jsonify([])

    # Terminate the dialogue if the turn count exceeds the maximum number of rounds
    if len(session_state.dialogue_lead.history) >= session_state.n_turns:
        session_state.reset()
        return jsonify([{'role': 'system', 'response': "Our session has concluded. Thank you for participating!"}])

    # Proceed with the dialogue
    response = session_state.dialogue_lead.get_response()
    msg_list = [{'role': session_state.dialogue_lead.role.lower(), 'response': response}]
    session_state.dialogue_lead, session_state.dialogue_follower = session_state.dialogue_follower, session_state.dialogue_lead
    
    return jsonify(msg_list)

@app.route('/chat', methods=['POST'])
def chat():
    global session_states
    app.logger.debug(f"Request to chat received")
    
    client_id = session.get('client_id')
    if not client_id:
        return jsonify({'error': 'Session not initialized'}), 400
    
    session_state = session_states.get(client_id)
    if session_state and session_state.in_progress:
        return jsonify({'error': 'Conversation already in progress'}), 400
    
    data = request.get_json()
    selected_persona = data.get('selected_persona')
    n_turns = data.get('n_turns')
    display_name = prompts[selected_persona]['display_name']

    try:
        n_turns = int(n_turns) if n_turns is not None else default_n_turns
    except ValueError:
        return jsonify({'error': 'Invalid number of turns provided'}), 400

    if not session_state:
        session_states[client_id] = SessionState(client_id, n_turns=n_turns)
        session_state = session_states[client_id]
    else:
        session_state.n_turns = n_turns

    session_state.in_progress = True
    session_state.dialogue_lead, session_state.dialogue_follower = session_state.ai_tutor, session_state.student
    
    try: 
        session_state.ai_tutor.initialize_chat()
        session_state.student.initialize_chat(selected_persona)
    except Exception as e:
        app.logger.error(f"Error initializing chat: {e}")
        return jsonify({'error': 'Error initializing chat'}), 400
 
    return jsonify([{'role': 'system', 'response': f"You just chose to act as ${display_name}. A conversation between the AI Tutor and your user persona will begin shortly..."}])

@app.route('/get-personas')
def get_personas():
    # Filter the prompts to include only student personas, which start with "student_"
    student_persona_display_names = {
        key: info['display_name'] 
        for key, info in prompts.items() 
        if key.startswith("student_")
    }
    return jsonify(student_persona_display_names)
    
if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("Starting Flask application...")
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    app.run(host='127.0.0.1', port=9000, debug=True)
