from flask import Flask, Blueprint, jsonify, request
from flask_cors import CORS
import pandas as pd
from RouteEngine import engine as eng

app = Flask(__name__)

# Enable CORS properly
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

df = pd.read_csv('./assets/transport_facilities_full.csv')
api = Blueprint('api', __name__, url_prefix='/api')

@app.route('/')
def home():
    return "<p>Server is running!</p>"

# Handle preflight OPTIONS request for calculate_routes
@api.route('/calculate_routes', methods=['OPTIONS', 'POST', 'GET'])
def calculate_routes():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data = request.json
    if not data:
        return _corsify_actual_response(jsonify({"error": "Invalid request, missing JSON data"}), 400)

    source = data.get('source')
    target = data.get('target')
    preferred_mode = data.get('preferred_mode')

    if not source or not target:
        return _corsify_actual_response(jsonify({"error": "Source and target are required"}), 400)

    G, paths, pos, node_colors, node_sizes, nodes_list = eng.find_optimal_routes(
        df, source, target, preferred_mode=preferred_mode, k=10
    )

    routes_data = eng.get_optimal_routes_with_coords(G, paths)
    return _corsify_actual_response(jsonify(routes_data))

# Add the missing ranked_routes endpoint
@api.route('/ranked_routes', methods=['OPTIONS', 'POST', 'GET'])
def ranked_routes():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data = request.json
    if not data:
        return _corsify_actual_response(jsonify({"error": "Invalid request, missing JSON data"}), 400)

    source = data.get('source')
    target = data.get('target')
    preferred_mode = data.get('preferred_mode')

    if not source or not target:
        return _corsify_actual_response(jsonify({"error": "Source and target are required"}), 400)

    G, paths, pos, node_colors, node_sizes, nodes_list = eng.find_optimal_routes(
        df, source, target, preferred_mode=preferred_mode, k=10
    )

    routes_info = eng.get_routes_info(G, paths, source, target)
    ranked_routes = eng.rank_routes(routes_info)

    return _corsify_actual_response(jsonify(ranked_routes))

def _build_cors_preflight_response():
    """Handles CORS preflight request (OPTIONS)."""
    response = jsonify({"message": "CORS preflight successful"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response

def _corsify_actual_response(response, status=200):
    """Adds CORS headers to actual responses."""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response, status

app.register_blueprint(api)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
