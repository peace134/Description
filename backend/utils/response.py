from flask import jsonify

def success_response(data=None, message='success'):
    return jsonify({'code': 0, 'message': message, 'data': data})

def error_response(message='error', code=1, status_code=400):
    return jsonify({'code': code, 'message': message, 'data': None}), status_code