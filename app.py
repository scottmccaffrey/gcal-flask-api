
from flask import Flask, request, redirect, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import pickle

app = Flask(__name__)
app.secret_key = 'your_secret_key'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_PICKLE = "token.pickle"

@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect('authorize')
    return 'Authorized! You can now send POST to /create_event'

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True))
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True))
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    with open(CREDENTIALS_PICKLE, 'wb') as token:
        pickle.dump(credentials, token)
    return redirect('/')

@app.route('/create_event', methods=['POST'])
def create_event():
    if not os.path.exists(CREDENTIALS_PICKLE):
        return jsonify({'error': 'User not authorized'}), 401

    with open(CREDENTIALS_PICKLE, 'rb') as token:
        credentials = pickle.load(token)

    service = build('calendar', 'v3', credentials=credentials)

    data = request.json
    event = {
        'summary': data.get('summary'),
        'description': data.get('description'),
        'start': {'dateTime': data.get('start'), 'timeZone': 'Europe/London'},
        'end': {'dateTime': data.get('end'), 'timeZone': 'Europe/London'},
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return jsonify({'event_id': created_event.get('id')}), 201

def credentials_to_dict(creds):
    return {'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes}

if __name__ == '__main__':
    app.run(port=5000)

