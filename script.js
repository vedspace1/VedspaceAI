const localVideo = document.getElementById("local-video");
const remoteVideo = document.getElementById("remote-video");
const localFeedback = document.getElementById("local-feedback");
const remoteFeedback = document.getElementById("remote-feedback");
const startCallButton = document.getElementById("start-call");
const endCallButton = document.getElementById("end-call");

let peerConnection;
let socket;
const iceServers = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

async function startCall() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    const videoElement = document.createElement("video");
    videoElement.srcObject = stream;
    videoElement.autoplay = true;
    localVideo.appendChild(videoElement);

    peerConnection = new RTCPeerConnection(iceServers);
    stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));

    socket = io("ws://localhost:8000/ws");

    socket.on("connect", () => console.log("Connected to signaling server"));
    socket.on("feedback", data => updateFeedback(data));

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    socket.emit("offer", offer);
}

function updateFeedback(data) {
    const { context, tone, tone_score, filler_feedback } = data;
    const feedbackHtml = `
        <p>Context: ${context}</p>
        <p>Tone: ${tone} (Score: ${tone_score})</p>
        <p>${filler_feedback}</p>
    `;
    localFeedback.innerHTML = feedbackHtml;
}

startCallButton.addEventListener("click", startCall);
endCallButton.addEventListener("click", () => peerConnection.close());
