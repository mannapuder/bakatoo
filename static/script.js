async function upload() {
    let fd = new FormData();
    let fileUpload = document.getElementById('fileUpload');
    fd.append('file', fileUpload.files[0]);
    const id = await (await fetch('/upload', {
        method: 'POST',
        body: fd
    })).text();
    document.body.removeChild(fileUpload);

    // võib-olla saaks puhtamalt? i don't know
    let audioPlayer = document.createElement('div');
    audioPlayer.innerHTML = '<audio controls="controls" src="https://www.coothead.co.uk/audio/You-Cant-Always-Get-What-You-Want.mp3" type="audio/mpeg"></audio>';
    document.body.appendChild(audioPlayer);
    let progressReport = document.createElement('p');
    document.body.appendChild(progressReport);
    // peaks aga funktsionaalselt dav olema TODO: error handling xd
    let response;
    while (true) {
        await new Promise(r => setTimeout(r, 1000)); // "sleep" pmst
        response = await (await fetch('/results/' + id, {
            method: 'GET'
        })).json();
        if (response.progress === 100) break;
        progressReport.innerText = `${response.progress}% - ${response.status}`
    }

    document.body.removeChild(progressReport);
    let resultText = document.createElement('p');
    resultText.innerText = response.result;


    document.body.appendChild(resultText);

}
