from flask import Flask, jsonify, request
import pandas as pd
from RouteEngine import engine as eng
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  
df = pd.read_csv('./assets/transport_facilities_full.csv')

@app.route('/')
def home():
    source = "Mundra Port"
    target = "Port of Piraeus"
    preferred_mode = 'Airport'

    # Find optimal routes with mode preference
    G, paths, pos, node_colors, node_sizes, nodes_list = eng.find_optimal_routes(
        df, source, target, preferred_mode=preferred_mode, k=10
    )

    info = eng.get_routes_info(G, paths, source, target)
    ranked_routes = eng.rank_routes(info)
    # cords = eng.get_routes_coordinates(G, paths, source, target)

    return f"<p>{ranked_routes}</p>"

    # print(pos)
    # if pos=={}:
    #     print('None')
    #     return "<p>Try another mode, No optimal routes in preffered mode.</p>"
    

@app.route('/api/calculate_routes', methods=['POST', 'GET'])
def calculate_routes():
    # Get parameters from the request
    # data = request.json
    # source = data.get('source')
    # target = data.get('target')
    # preferred_mode = data.get('preferred_mode')

    source = "Mundra Port"
    target = "Port of Piraeus"
    preferred_mode = 'Airport'
    
    G, paths, pos, node_colors, node_sizes, nodes_list = eng.find_optimal_routes(
        df, source, target, preferred_mode=preferred_mode, k=10
    )
    routes_info = eng.get_routes_info(G, paths, source, target)
    ranked_routes = eng.rank_routes(routes_info)
      
    return jsonify(ranked_routes)



if __name__ == '__main__':
    app.run(debug=True)