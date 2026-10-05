export class AucboardSocket {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.reconnectInterval = 3000;
        this.onMessageCallback = null;
        this.connect();
    }

    connect() {
        console.log(`connecting to aucboard device at ${this.url}...`);
        this.socket = new WebSocket(this.url);
        this.socket.binaryType = "arraybuffer";

        this.socket.onopen = () => {
            console.log("connected! hardware is ready...");
        }

        this.socket.onmessage = (event) => {
            if (this.onMessageCallback) {
                this.onMessageCallback(event.data);
            }
        }

        this.socket.onclose = (e) => {
            console.log(`connection lost (code ${e.code}). retrying in ${this.reconnectInterval/1000}s...`);
            this.socket = null;
            setTimeout(() => this.connect(), this.reconnectInterval);
        }

        this.socket.onerror = (err) => {
            console.error("websocket error!! aucboard device might be rebooting?");
            this.socket.close();
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(data);
        } else {
            console.warn("socket is closed, can't send any command right now.");
        }
    }

    onMessage(callback) {
        this.onMessageCallback = callback;
    }
}