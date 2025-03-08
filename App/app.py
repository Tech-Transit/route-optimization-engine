from flask import Flask, jsonify, request
import pandas as pd
from RouteEngine import engine as eng


app = Flask(__name__)
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
    # cords = eng.get_routes_coordinates(G, paths, source, target)

    print(info[0])
    print(type(info))
    return f"<p>{info}</p>"
    
    # print(pos)
    # if pos=={}:
    #     print('None')
    #     return "<p>Try another mode, No optimal routes in preffered mode.</p>"
    
    return f"<p>{info}</p>"

@app.route('/api/calculate_routes', methods=['POST'])
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
    # routes_data = eng.get_routes_info(G, paths, source, target)
    # routes_data = eng.get_optimal_routes(G, paths)
    routes_data = eng.get_optimal_routes_with_coords(G, paths)
      
    # For this example, we'll just return the sample data
    return jsonify(routes_data)



if __name__ == '__main__':
    app.run(debug=True)