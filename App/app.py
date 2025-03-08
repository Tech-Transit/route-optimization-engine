from flask import Flask
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

    # print(info)
    
    # print(pos)
    # if pos=={}:
    #     print('None')
    #     return "<p>Try another mode, No optimal routes in preffered mode.</p>"
    
    return f"<p>{info}</p>"


# @app.route('/routes')



if __name__ == '__main__':
    app.run(debug=True)