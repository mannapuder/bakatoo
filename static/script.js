async function upload() {
    let fd = new FormData();
    let fileUpload = document.getElementById('fileUpload');
    fd.append('file', fileUpload.files[0]);
    const id = await (await fetch('/upload', {
        method: 'POST',
        body: fd
    })).text();
    document.body.removeChild(fileUpload);
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
    if (!resultText.innerText.startsWith("Error")) {
        let audioPlayer = document.createElement('div');

        audioPlayer.innerHTML = '<audio controls="controls" src="'+ URL.createObjectURL(fileUpload.files[0])+'" type="audio/mpeg"></audio>';
        document.body.appendChild(audioPlayer);
    } else {
        document.body.appendChild(fileUpload);
    }

    document.body.appendChild(resultText);

}
