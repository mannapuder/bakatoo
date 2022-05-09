from collections import defaultdict

vormide_kirjeldused = {
    "rondo": "Rondo vormi puhul vaheldub peateema ehk refrään vaheosade ehk kupleedega. Selle vormi kõige sagedasem avaldumisvorm on viieosalise rondona (ABACA), mille puhul A tähistab peateemat ning B ja C vaheosasid. Rondo võib sageli avalduda ka seitsmeosalisena.",
    "sonaadivorm": "Sonaadivorm on klassikalise instrumentaalmuusika üks keskseid vorme. Kuigi vormiosade arv pole sonaadivormis keskse tähtsusega, koosneb see tavaliselt kolmest peamisest üksusest, ekspositsioonist, töötlusest ja repriisist, millest esimene esindab vormilist esitust, teine arendust ja kolmas lõpetust",
    "kaheosaline lihtvorm": "Kaheosaline lihtvorm ehk AB-vorm koosneb, nagu ka nimest aimata, kahest erinevast osast. Vormi esimene pool põhineb mõnel klassikalise peateema vormil ning teine pool on üldiselt proportsionaalselt ligikaudu sama pikk teema, mis põhineb uuel materjalil või eelneva teema arendusel, mis ei ole tõlgendatav peateema tagasitulekuna.",
    "kolmeosaline lihtvorm": "Kolmeosaline lihtvorm on tuntud ka kui ABA-vorm ning klassikalise instrumentaalmuusi-ka üks tavapärasemaid vorme. Selle vormi esimeseks osaks on sarnaselt kaheosalisele liht-vormile peateema. Vormi keskosaks on kontrastne teema, kuhu üldreeglina tuuakse sisse uus muusikaline materjal ning vormi kolmas osa koosneb peateema tagasitulekust.",
    "variatsioonivorm" : "Selle vormi nimi tuleb ladinakeelsest sõnast variatio mis tähendab muutust või teisendust. Variatsioonivormi esimene osa on peateema ekspositsiooni, millele järgneb piiritlemata arv peateema variatsioone. Variatsioonide puhul jääb reeglina samaks teema vorm ning har-moonia, kuid muutub teema karakter, mida võib mõjutada nii peateemast erinev faktuur, dünaamika, orkestratsioon jne.",
    "rondo-sonaat" : "Rondo-sonaat on rondo vormi erikuju ABACAB₁A. Kui rondo vormi puhul vaheldub peateema ehk refrään vaheosade ehk kupleedega, siis rondo sonaadi puhul on eelviimane kuplee B₁ uue muusikalise materjali asemel esimese kuplee juurde tagasipöördumist uues helistikus."
}


vormid = [
    ["rondo", "ABACA", "ABACADA"],
    ["rondo-sonaat", "ABACABA"],
    ["kaheosaline lihtvorm", "AB", "AABB"],
    ["kolmeosaline lihtvorm", "ABA"],
    ["sonaadivorm", "ABCA"],

]
def predict(segm):
    path = "".join([i[0] for i in segm])

    if path == "ABACA":
        return "rondo", vormide_kirjeldused["rondo"]
    if path == "AB":
        return "kaheosaline lihtvorm", vormide_kirjeldused["kaheosaline lihtvorm"]
    if path == "ABA":
        return "kolmeosaline lihtvorm", vormide_kirjeldused["kolmeosaline lihtvorm"]
    if "B" not in path:
        return "variatsioonivorm", vormide_kirjeldused["variatsioonivorm"]

    min_distance = 2000
    best_guess = vormid[0][0]
    for vorm in vormid:
        for i in range(1, len(vorm)):
            distance = edit_distance(vorm[i], path)
            if distance < min_distance:
                min_distance = distance
                best_guess = vorm[0]

    return best_guess, vormide_kirjeldused[best_guess]
# Edit distance

def edit_distance(xs, ys):
    memory = defaultdict(lambda: defaultdict(lambda: -1))

    def _lev(s1, s2):
        if memory[s1][s2] != -1:
            return memory[s1][s2]
        if len(s1) == 0:
            memory[s1][s2] = len(s2)
            return memory[s1][s2]
        if len(s2) == 0:
            memory[s1][s2] = len(s1)
            return memory[s1][s2]
        else:
            cost = 1
            if s1[-1] == s2[-1]:
                cost = 0

            memory[s1][s2] = min(_lev(s1[:-1], s2) + 1, _lev(s1, s2[:-1]) + 1, _lev(s1[:-1], s2[:-1]) + cost)
            return memory[s1][s2]

    return _lev(xs, ys)

predict([('A', 0, 365541), ('B', 365541, 2107238), ('A', 2107238, 2675517), ('C', 2675517, 4527798), ('D', 4527798, 5234307), ('E', 5234307, 6662683), ('D', 6662683, 7043584)])