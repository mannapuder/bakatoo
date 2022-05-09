async function upload() {
    console.log("here");
    let fd = new FormData();
    let frontPageInfo = document.getElementById('frontPageInfo');
    let fileUpload = document.getElementById('fileUpload');
    fd.append('file', fileUpload.files[0]);
    const id = await (await fetch('/upload', {
        method: 'POST',
        body: fd
    })).text();
    let mainDiv = document.getElementById("main");
    mainDiv.removeChild(frontPageInfo);
    let progressReport = document.createElement('p');
    progressReport.setAttribute("id", "progressBar")
    mainDiv.appendChild(progressReport);
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
    mainDiv.removeChild(progressReport);

    let results = document.createElement('div');
    results.id = "result";
    let resultText = document.createElement('p');
    resultText.innerText = response.result + " peateema algab " + response.chorus_start;
    if (!resultText.innerText.startsWith("Error")) {
        let audioPlayer = document.createElement('div');

        audioPlayer.innerHTML = '<audio controls="controls" src="'+ URL.createObjectURL(fileUpload.files[0])+'" type="audio/mpeg"></audio>';
        results.appendChild(audioPlayer);
    } else {
        results.appendChild(resultText);
        mainDiv.appendChild(frontPageInfo);
    }
    //results.appendChild(resultText);

    let chorus;
    if (!resultText.innerText.startsWith("Error")) {
        /*let chorusPlayer = document.createElement('div');
        chorusPlayer.innerHTML = '<audio controls="controls" src="uploads/' + response.chorus + '" type="audio/mpeg"></audio>';
        results.appendChild(chorusPlayer);*/

        //Segmentation visualisation
        let audioSegmentation = document.createElement('div');
        audioSegmentation.id = "segmentationGraph";
        console.log(response.segmentation);
        segmArray = JSON.parse(JSON.stringify(response.segmentation));
        keyArray = JSON.parse(JSON.stringify(response.keys));
        timestampsArray = JSON.parse(JSON.stringify(response.timestamps));
        console.log(segmArray);
        for (var i = 0; i < segmArray.length; i++){
            var segm = segmArray[i];
            var key = keyArray[i];
            var timestamp = JSON.parse(JSON.stringify(timestampsArray[i]));
            segm = JSON.parse(JSON.stringify(segm));
            console.log(segm);
            let part = document.createElement('div');
            let length = segm[1];
            let name = segm[0];
            let segm_title = document.createElement('h4');
            let par = document.createElement("p");
            segm_title.innerText= name;
            par.innerText = timestamp[0] + " - "+timestamp[1];
            part.className = "part " + name;
            console.log(length);
            console.log(name);
            part.style.width = length+"%";
            part.appendChild(segm_title);
            part.appendChild(par);
            audioSegmentation.appendChild(part);

        }

        //Form description

        let general_desc = document.createElement('div');

        let descTitle = document.createElement('h3');
        descTitle.innerText = "Analüüsi tulemus";
        let descPara = document.createElement('p');
        descPara.id = "desc_p"
        descPara.innerText = response.general_desc;

        general_desc.append(descTitle);
        general_desc.append(descPara);


        results.appendChild(audioSegmentation);
        results.appendChild(general_desc);
        mainDiv.appendChild(results);
    }

}
