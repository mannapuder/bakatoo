vormid = {
    "rondo": "Rondo on vorm, mis põhineb peateema ehk nn refrääni (refrain) korduvatel tagasitulekutel (repriisidel). Refrääne eraldavad üksteisest aga vaheosad ehk kupleed (couplet). Rondo kõige elementaarsem avaldumisvorm on viieosaline, ABACA, kus A viitab korduvalt tagasipöörduvale refräänile ning B, C jne kupleedele. Sageli avaldub rondo aga ka seitsmeosalisena kas kujul ABACADA või ABACAB1A (kus B1 viitab esimese kuplee tagasipöördumisele uues helistikus). Viimasel puhul on põhjust rääkida juba rondo-sonaadist (rondo-sonaadivormist), sest selles mängitakse vormi arenedes ümber kahe temaatilise üksuse A ja B helistikuline suhe nii, nagu see on omane ka sonaadivormile.",
    "sonaadivorm": "Sonaadivorm on klassikalise instrumentaalmuusika üks keskseid vorme. Kuigi vormiosade arv pole sonaadivormis keskse tähtsusega, koosneb see tavaliselt kolmest peamisest üksusest, ekspositsioonist, töötlusest ja repriisist, millest esimene esindab vormilist esitust, teine arendust ja kolmas lõpetust",
    "kaheosaline lihtvorm": "Kaheosaline lihtvorm moodustub kahest poolest, millest esimene esindab vormilist esitust ning teine vormilist jätku, s.t nii arendust kui ka lõpetust. Kaheosalise lihtvormi esimene pool põhineb mõnel klassikalise peateema vormil – suurel lausel, perioodil või hübriidvormil – ning teine sellega üldreeglina proportsionaalselt samaväärsel (sama pikkusega) lõigul, mille vormiline struktuur on mõnevõrra sarnane suure lause jätkufraasile.",
    "kolmeosaline lihtvorm": "Lorem ipsum"}


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
