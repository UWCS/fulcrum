// utils to help /stardust/ URLs work within iframes

function sendHeight() {
    const height = document.body.scrollHeight;
    window.parent.postMessage({ type: "setHeight", height: height }, "*");
}

window.onload = sendHeight;
window.onresize = sendHeight;