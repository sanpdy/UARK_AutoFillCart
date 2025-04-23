from flask import jsonify

def success_response(message, data=None, status=200):
    """
    Create a standardized success response
    """
    response = {'success': True, 'message': message}
    if data:
        response.update(data)
    return jsonify(response), status

def error_response(message, status=400):
    """
    Create a standardized error response
    """
    return jsonify({'success': False, 'message': message}), status