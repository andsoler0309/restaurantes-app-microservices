from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configure the proxies to redirect requests
proxies = {
    "users": "http://users_service:5000",
    "menus": "http://menus_service:5000",
}

@app.route('/<service>/<path:path>', methods=["GET", "POST", "PUT", "DELETE"])
def proxy(service, path):
    if service in proxies:
        proxy_url = f"{proxies[service]}/{path}"
        headers = {}
        
        # If the service is menus, pass the Authorization header
        if service == "menus":
            auth_header = request.headers.get('Authorization')
            if auth_header:
                headers['Authorization'] = auth_header
            else:
                return jsonify({"error": "Authorization header is required for menus service"}), 401

        try:
            if request.method == "GET":
                resp = requests.get(proxy_url, params=request.args, headers=headers)
            elif request.method == "POST":
                resp = requests.post(proxy_url, json=request.json, headers=headers)
            elif request.method == "PUT":
                resp = requests.put(proxy_url, json=request.json, headers=headers)
            elif request.method == "DELETE":
                resp = requests.delete(proxy_url, headers=headers)

            return jsonify(resp.json()), resp.status_code
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Service not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)