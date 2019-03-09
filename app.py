import logging
import json
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, flash, request, jsonify, url_for, abort, Response
#from flask_cors import CORS
#from session import Session
from auth import Auth

logPath = 'logs/api.log'
_logger = logging.getLogger("progress_tracker_api")
_logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(logPath, maxBytes=20971520, backupCount=10)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
_logger.addHandler(handler)

app = Flask(__name__)


@app.route("/progress-tracker/v1/authenticate", methods=['POST'])
def authenticate():
    _logger.info('Authentication request')
    if not request.is_json:
        _logger.info('ERROR---->Invalid request body')
        abort(400)
    else:
        data = request.get_json()
        user_email = data['user_email']
        password = data['password']
        auth = Auth(user_email)
        success, message, code = auth.process_user(password)

        result = {
            'success': success,
            'code': code
        }

        if code >= 400:
            result['error'] = message
        else:
            result['access_token'] = message
        resp = app.response_class(
            response=json.dumps(result),
            status=code,
            mimetype='application/json'
        )
        resp.headers['Content-Type'] = 'application/json;charset=UTF-8'

    return resp


@app.route("/progress-tracker/v1/", methods=['POST'])
def intro():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        user = data['user']
        auth = request.headers.get('Authorization')
        ttype, token = auth.split(' ')
        success, msg = Auth().validate_token(token, user)




if __name__ == '__main__':
   # _logger.info('Server is Listening.....')
    app.run(debug=True)
