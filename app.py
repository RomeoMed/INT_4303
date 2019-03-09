import logging
import json
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, flash, request, jsonify, url_for, abort, Response
from flask_cors import CORS
from session import Session
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
        auth = Auth()
        data = request.get_json()
        user = data['user']
        password = data['password']
        success, message = auth.fetch_or_create(user, password)
        if success:
            status = 200
        else:
            status = 401

        result = {
            'success': success,
            'access_token': message
        }

        resp = app.response_class(
            response=json.dumps(result),
            status=status,
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

        if success:
            content = Session(user).get_content()
            if content:
                return jsonify(content)

    return jsonify({'error': 'something went wrong', 'status': 500})


@app.route('/login', methods=['GET'])
def login():
    user = request.args.get('user')
    psw = request.args.get('password')
    if user and psw:
        result = _session.login_user(user, psw)

    if result and result['status'] == 200:
        page = '/main'
    else:
        page = '/error'
    if not result:
        result['status'] = 404
        result['message'] = 'Unable to process request at this time'
    response = {'url': page, 'data': result}

    return jsonify(response)


@app.route("/content", methods=['GET'])
def steps_content(step):
    content = _session.get_content()
    return jsonify(content)


@app.route("/next_page", methods=['GET'])
def advance_next():
    content = _session.update_content('forward')
    return jsonify(content)

@app.route('/story_part/<part_id>', methods=['GET'])
def story_part(part_id):

    try:
        print(part_id)
        return jsonify()

    except Exception as e:
     #   _logger.info('Error processing data: %s' % str(e))
        flash('Something Went Terribly Wrong!')
        return render_template('error.html')

@app.route('/get_locations_data', methods=['GET'])
def get_locations_data():
    #_logger.info('/get_locations_data --processing request')
    # Get the request parameter
    state = request.args.get('state')
    try:
        result = ''
        if 'None Found' not in result:
            for res in result:
                total_score = 0
                max_score = 0
                possible_score = res['possible_score']
                for k, v in res.items():
                    if k == 'address':
                        res[k] = v + ' ' + res['csz']
                    if k != 'address' and k != 'csz' and k != 'total_reviews' and k != 'possible_score':
                        # Calculate the total score for each category, calculate the total possible
                        # score based on reviews num or reviews * 5
                        # calculate score percentage for each category.
                        total_score += v
                        max_score += possible_score
                        tmp = round((v / possible_score), 2) * 100
                        res[k] = '%.1f' % tmp + '%'
                if total_score and possible_score:
                    overall = round((total_score/max_score), 2) * 100
                    overall = '%.1f' % overall
                    res['overall'] = "{0}%".format(overall)
                else:
                    res['overall'] = '--%'
            return jsonify(result)
        else:
            return jsonify({'error': 'No trips for selected location & travel_type'})
    except Exception as e:
        print('ERROR-------> %s' % e)


@app.route('/get_dashboard_select', methods=['GET'])
def getDashboardSelect():
    #_logger.info('/getDashboardSelect --processing request')
    state_obj = {}
    try:
        result = ''
        if result:
            for res in result:
                state_obj[res[0]] = res[1]
            return jsonify(state_obj)
    except Exception as e:
        print('ERROR--------> %s' % e)


@app.route('/get_panel_data', methods=['GET'])
def get_panel_data():
    # get query parameters
    location_id = request.args.get('id')
   # _logger.info('/get_panel_data for: %s' % location_id)
    try:
        result = ''
        if result:
            return jsonify(result)
    except Exception as e:
        print('ERROR--------> %s' % e)


@app.route('/get_travel_style_analysis', methods=['GET'])
def get_travel_style_analysis():
    location_id = request.args.get('id')
    #_logger.info('/get_travel_style_analysis --processing request')
    try:
        result = ''
        if result:
            return jsonify(result)
    except Exception as e:
        print('ERROR--------> %s' % e)


@app.route('/get_doughnut_chart', methods=['GET'])
def get_doughnut_char():
    location_id = request.args.get('id')
   # _logger.info('/get_doughnut_chart --processing request')
    try:
        result = ''
        if result:
            return jsonify(result)
    except Exception as e:
        print('ERROR--------> %s' % e)


@app.route('/get_reviews', methods=['GET'])
def get_reviews():
    location_id = request.args.get('id')
   # _logger.info('/get_reviews for: %s' % location_id)
    try:
        result = ''
        if result:
            return jsonify(result)
    except Exception as e:
        print('ERROR--------> %s' % e)


if __name__ == '__main__':
   # _logger.info('Server is Listening.....')
    app.run(debug=True)
