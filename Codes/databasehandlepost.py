from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this to handle CORS

app = Flask(__name__)
CORS(app)  # Enable CORS

@app.route('/api/databasehandlepost', methods=['POST'])
def handle_user_data():
    try:
        data = request.get_json()
        uid = data.get('uid')
        email = data.get('email')
        
        print(uid, email)
        
        return jsonify({"message": "User data received successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500      

if __name__ == '__main__':
    app.run(debug=True, port=5000)