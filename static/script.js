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
    progressReport.setAttribute("id", "progressBar")
    document.body.appendChild(progressReport);
    // TODO: error handling xd
    let response;
    while (true) {
        await new Promise(r => setTimeout(r, 1000)); // "sleep" pmst
        response = await (await fetch('/results/' + id, {
            method: 'GET'
        })).json();
        if (response.progress === 100) break;
        progressReport.style.width = response.progress + "%";
        progressReport.innerText = `${response.progress}% - ${response.status}`
    }
    document.body.removeChild(progressReport);

    let results = document.createElement('div');
    let resultText = document.createElement('p');
    resultText.innerText = response.result + " peateema algab " + response.chorus_start;
    if (!resultText.innerText.startsWith("Error")) {
        let audioPlayer = document.createElement('div');

        audioPlayer.innerHTML = '<audio controls="controls" src="'+ URL.createObjectURL(fileUpload.files[0])+'" type="audio/mpeg"></audio>';
        results.appendChild(audioPlayer);
    } else {
        document.body.appendChild(fileUpload);
    }
    results.appendChild(resultText);

    let chorus;
    if (!resultText.innerText.startsWith("Error")) {
        let chorusPlayer = document.createElement('div');
        chorusPlayer.innerHTML = '<audio controls="controls" src="uploads/' + response.chorus + '" type="audio/mpeg"></audio>';
        results.appendChild(chorusPlayer);

        document.body.appendChild(results);
    }

}
