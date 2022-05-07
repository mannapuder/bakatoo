vormid = {
    "rondo": "Rondo vormi puhul vaheldub peateema ehk refrään vaheosade ehk kupleedega. Selle vormi kõige sagedasem avaldumisvorm on viieosalise rondona (ABACA), mille puhul A tähistab peateemat ning B ja C vaheosasid. Rondo võib sageli avalduda ka seitsmeosalisena.",
    "sonaadivorm": "Sonaadivorm on klassikalise instrumentaalmuusika üks keskseid vorme. Kuigi vormiosade arv pole sonaadivormis keskse tähtsusega, koosneb see tavaliselt kolmest peamisest üksusest, ekspositsioonist, töötlusest ja repriisist, millest esimene esindab vormilist esitust, teine arendust ja kolmas lõpetust",
    "kaheosaline lihtvorm": "Kaheosaline lihtvorm ehk AB-vorm koosneb, nagu ka nimest aimata, kahest erinevast osast. Vormi esimene pool põhineb mõnel klassikalise peateema vormil ning teine pool on üldiselt proportsionaalselt ligikaudu sama pikk teema, mis põhineb uuel materjalil või eelneva teema arendusel, mis ei ole tõlgendatav peateema tagasitulekuna.",
    "kolmeosaline lihtvorm": "Kolmeosaline lihtvorm on tuntud ka kui ABA-vorm ning klassikalise instrumentaalmuusi-ka üks tavapärasemaid vorme. Selle vormi esimeseks osaks on sarnaselt kaheosalisele liht-vormile peateema. Vormi keskosaks on kontrastne teema, kuhu üldreeglina tuuakse sisse uus muusikaline materjal ning vormi kolmas osa koosneb peateema tagasitulekust.",
    "variatsioonivorm" : "Selle vormi nimi tuleb ladinakeelsest sõnast variatio mis tähendab muutust või teisendust. Variatsioonivormi esimene osa on peateema ekspositsiooni, millele järgneb piiritlemata arv peateema variatsioone. Variatsioonide puhul jääb reeglina samaks teema vorm ning har-moonia, kuid muutub teema karakter, mida võib mõjutada nii peateemast erinev faktuur, dünaamika, orkestratsioon jne."}


def predict(segm):
    path = ""

    if path == "ABACA":
        return "rondo", vormid["rondo"]
    if path == "AB":
        return "kaheosaline lihtvorm", vormid["kaheosaline lihtvorm"]
    if path == "ABA":
        return "kolmeosaline lihtvorm", vormid["kolmeosaline lihtvorm"]
    if "B" not in path:
        return "variatsioonivorm", "TBA"
    return "undefined", "Lorem ipsum dolor sit amet..."

# Edit distance
