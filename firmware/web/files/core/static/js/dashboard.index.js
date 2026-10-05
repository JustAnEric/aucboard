import { AucboardSocket } from "./websocket.js";

const auc = new AucboardSocket(
    `ws${window.location.protocol === 'https:' ? 's' : ''}://${window.location.host}/ws`
);

let currentClientState = {
    volume: 100,
    track: {
        _title: "Unknown Title",
        artist: "Unknown Artist",
        album: "Unknown Album"
    },
    playing: false,
    duration: 0.0,
    position: 0.0,
    bitrate: 0.0,
    eqConfig: {},
    eqBandLevels: Array().fill(0.0, 0, 9)
};

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

auc.onMessage((data) => {
    if (data instanceof ArrayBuffer) {
        const view = new DataView(data);
        const cmd = view.getUint8(0);

        if (cmd === 0x01) {
            console.log("pong!");
            auc.send(new Uint8Array([0x01]));
        }

        if (cmd === 0x03) {
            const cpuPerc = view.getFloat32(1, true);
            const cpuTemp = view.getFloat32(5, true);
            const ramPerc = view.getFloat32(9, true);
            const ramUsed = view.getFloat32(13, true);
            const ramMax = view.getFloat32(17, true);
            document.querySelectorAll('.card')[0].querySelector('.entity-state').innerText = `${cpuPerc.toFixed(2)}% / ${cpuTemp.toFixed(2)} °C / ${((cpuTemp * (9/5)) + 32).toFixed(2)} °F`;
            document.querySelectorAll('.card')[1].querySelector('.entity-state').innerText = `${(ramPerc * 100).toFixed(2)}% | ${formatBytes(ramUsed)} / ${formatBytes(ramMax)}`;
        }
    }
});

async function onTrackTitleChange(newTitle) {
    console.log(`track title was changed!`);
}

Object.defineProperty(currentClientState.track, 'title', {
    get: function() {
        return this._title;
    },
    set: function(value) {
        if (this._title !== value) {
            this._title = value;
            onTrackTitleChange(value);
        }
    }
})