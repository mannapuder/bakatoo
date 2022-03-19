import http.client


conn = http.client.HTTPSConnection("shazam.p.rapidapi.com")

audiofile = "uploads/5bdf14f1-fa9c-44b9-95fd-faff0203195a.mp3"
import wave
w = wave.open(audiofile, 'r')
data=w.readframes(w.getnframes())
payload = data[1000:2000]

headers = {
    'x-rapidapi-host': "shazam.p.rapidapi.com",
    'x-rapidapi-key': "6e79a88e3amshaf2276986d11125p19d915jsn4de382c1d311"
}

headers = {
    'content-type': "text/plain",
    'x-rapidapi-host': "shazam.p.rapidapi.com",
    'x-rapidapi-key': "6e79a88e3amshaf2276986d11125p19d915jsn4de382c1d311"
}

conn.request("POST", "/songs/v2/detect?timezone=America%2FChicago&locale=en-US", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
