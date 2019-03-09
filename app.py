import logging
import json
from logging.handlers import RotatingFileHandler
from flask import Flask, request, abort
#from flask_cors import CORS
#from session import Session
from auth import Auth
from user import User


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
        resp = _process_response(result, code)

    return resp


@app.route("/progress-tracker/v1/getUserRole", methods=['POST'])
def getUserRole():
    if not request.is_json:
        abort(400)

    data = request.get_json
    user_email = data.get('user_email')
    authorization = request.headers.get('Authorization')
    success, msg, code = _verify_access_token(user_email, authorization)
    if code >= 400:
        result = {
            "success": success,
            "code": code,
            "error": msg
        }
        resp = _process_response(result, code)

    else:
        user = User(user_email)
        role = user.get_user_role()
        result = {
            "user_role": role,
            "code": 200,
            "success": 1
        }
        resp = _process_response(result, 200)

    return resp


@app.route("/progress-tracker/v1/getStudentDetails", methods=['POST'])
def getStudentDetails():
    if not request.is_json:
        abort(400)
    else:
        data = request.get_json()
        user_email = data['user_email']
        authorization = request.headers.get('Authorization')
        success, msg, code = _verify_access_token(user_email, authorization)
        if code >= 400:
            result = {
                "success": success,
                "code": code,
                "error": msg
            }
            resp = _process_response(result, code)
        else:
            user = User(user_email)
            user_details = user.get_student_details()


def _process_response(result: any, code: int) -> any:
    resp = app.response_class(
        response=json.dumps(result),
        status=code,
        mimetype='application/json'
    )
    resp.headers['Content-Type'] = 'application/json;charset=UTF-8'

    return resp


def _verify_access_token(user_email: str, authorization: str):
    ttype, token = authorization.split(' ')
    auth = Auth()
    return auth.validate_token(token, user_email)


if __name__ == '__main__':
   # _logger.info('Server is Listening.....')
    app.run(debug=True)
