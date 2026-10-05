from quart import Quart, request, session, render_template, redirect, websocket
from uvicorn import run
from main import PlayerState

import threading, uuid, asyncio, psutil, shutil, struct

def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    if 'cpu_thermal' in temps:
        return temps['cpu_thermal'][0].current
    elif 'coretemp' in temps:
        return temps['coretemp'][0].current
    return None

class WebApp:
    def __init__(self, state: PlayerState):
        self.app = Quart(__name__, template_folder="../web/files/core", static_folder="../web/files/core/static")
        self.state = state

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
            return await render_template("index.html")

        @self.app.route('/api/track_state')
        async def api_track_state():
            token = session.get("token") or request.args.get("token")
            if token not in self.tokens:
                return {"error": "Unauthorized"}, 401
            if self.state:
                return {
                    "playing": self.state.playing,
                    "track_name": self.state.player.current_track.name,
                    "position": self.state.position,
                    "duration": self.state.duration,
                    "volume": self.state.player.volume(),
                    "bitrate": self.state.player.current_track.bitrate
                }
            else:
                return {"error": "No track loaded"}, 404

        self.app.websocket('/ws')(self.ws_handler)

    async def ws_handler(self):
        token = session.get("token") or websocket.args.get("token")

        if token not in self.tokens:
            await websocket.close(0)
            return
        
        ended = asyncio.Event()

        global last_pong_time
        last_pong_time = asyncio.get_event_loop().time()

        async def a_worker():
            global last_pong_time
            while True:
                ram = psutil.virtual_memory()
                ram_max = ram.total
                ram_used = ram.used
                cpu_percent = psutil.cpu_percent(interval=None)
                cpu_temp = get_cpu_temp() or 0.0
                await websocket.send(b"\x01")
                await websocket.send(b"\x03" + struct.pack("<fffff", cpu_percent, cpu_temp, ram_used / ram_max, ram_used, ram_max))
                await asyncio.sleep(10)
                if ended.is_set():
                    break
                if last_pong_time + 30 < asyncio.get_event_loop().time():
                    print("no pong received in time, closing connection")
                    await websocket.close(1000)
                    break

        asyncio.create_task(a_worker())

        try:
            while True:
                data = await websocket.receive()
                b_data = data if isinstance(data, bytes) else data.encode()

                if not b_data: continue

                cmd = b_data[0]
                if cmd == 0x01:
                    # ping -> pong
                    last_pong_time = asyncio.get_event_loop().time()
                    print("ack ping")


        except asyncio.CancelledError:
            print("client went away!")
        except Exception as e:
            print(f"oopsie, something went wrong: {e}")
        finally:
            print("cleaning up websocket resources...")
        
        ended.set()

    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        run(self.app, host="0.0.0.0", port=73)