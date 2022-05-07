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
        tempoArray = JSON.parse(JSON.stringify(response.tempos));
        console.log(segmArray);
        for (var i = 0; i < segmArray.length; i++){
            var segm = segmArray[i];
            var key = keyArray[i];
            var tempo = JSON.parse(JSON.stringify(tempoArray[i]));
            segm = JSON.parse(JSON.stringify(segm));
            console.log(segm);
            let part = document.createElement('div');
            let length = segm[1];
            let name = segm[0];
            let segm_title = document.createElement('h4');
            let par = document.createElement("p");
            segm_title.innerText= name;
            par.innerText = /*key + "\n" + */ tempo[1] + " ("+tempo[0]+")";
            part.className = "part " + name;
            console.log(length);
            console.log(name);
            part.style.width = length+"%";
            part.appendChild(segm_title);
            part.appendChild(par);
            audioSegmentation.appendChild(part);

        }

        //Form description

        let form = document.createElement('div');
        form.id = "form_div";

        let formName = document.createElement('h3');
        formName.innerText = response.structure_name;
        let formDesc = document.createElement('p');
        formDesc.innerText = response.structure_desc;

        form.appendChild(formName);
        form.appendChild(formDesc);

        let general_desc = document.createElement('div');
        form.id = "desc_div";

        let descTitle = document.createElement('h3');
        descTitle.innerText = "Tulemus";
        let descPara = document.createElement('p');
        descPara.innerText = response.general_desc;

        general_desc.append(descTitle);
        general_desc.append(descPara);


        results.appendChild(audioSegmentation);
        results.appendChild(general_desc);
        results.appendChild(form);
        mainDiv.appendChild(results);
    }

}
