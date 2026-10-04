from quart import Quart, request, session, render_template, redirect
from uvicorn import run
from main import PlayerState

import threading, uuid

class WebApp:
    def __init__(self, state: PlayerState):
        self.app = Quart(__name__, template_folder="../web/files/core", static_folder="../web/files/core/static")

        self.app.secret_key = b"AUCBOARD_holdonthiswillbedynamicallychangedlater"
        self.tokens = []

        @self.app.route('/')
        async def index():
            token = session.get("token") or request.args.get("token")
            if token in self.tokens:
                return redirect("/dashboard")
            return await render_template('login.html')

        @self.app.route('/login', methods=['POST'])
        async def login_api():
            if not request.is_json:
                return "Invalid request", 400
            data = await request.json
            username = data.get("username")
            password = data.get("password")
            if username == "admin" and password == "admin":
                session["token"] = str(uuid.uuid4())
                self.tokens.append(session["token"])
                return {"code": 0x00}
            else:
                return {"error": "Invalid username or password"}, 400

        @self.app.route('/dashboard')
        async def dashboard():
            token = session.get("token") or request.args.get("token")
            if token not in self.tokens:
                return redirect("/")
            return "There is nothing here yet!"

    def run_in_thread(self):
        threading.Thread(target=self.run).start()

    def run(self):
        run(self.app, host="0.0.0.0", port=73)