#!/usr/bin/env python3
"""
Generate base64-encoded MP3 audio for all unique Italian phrases
from the driving test modules, using edge-tts (Italian female voice).
Output: audio/XXXX.json files containing {"text": "...", "base64": "..."}
"""

import asyncio
import base64
import hashlib
import json
import os
import sys
import time

# All unique Italian phrases extracted from MODULES data
PHRASES = [
    # Module 0 - Prep & Questions
    "Regola il sedile",
    "Regola il poggiatesta",
    "Regola gli specchietti",
    "Controlla la chiusura delle porte",
    "Allaccia la cintura di sicurezza",
    "Consegna i documenti",
    "Come si controlla lo spessore del battistrada?",
    "Qual è la pressione corretta degli pneumatici?",
    "Come si controlla la pressione di gonfiaggio?",
    "Come si controlla il livello dell'olio motore?",
    "Come si controlla il freno a mano?",
    "Come si verifica il liquido dei freni?",
    "Come si accendono i fari anabbaglianti?",
    "Come si accendono gli abbaglianti?",
    "Cosa indica la spia rossa sul cruscotto?",
    "Come si attivano le quattro frecce?",
    "Come si attivano i tergicristalli?",
    "Come si controlla il liquido lavavetri?",
    "Quali documenti bisogna portare per guidare?",
    "Dove si trova il triangolo di emergenza?",
    # Module 1 - Starting
    "Accendi il motore",
    "Controlla gli specchietti prima di partire",
    "Metti la cintura di sicurezza",
    "Controlla i pedali",
    "Metti la prima marcia",
    "Controlla la strada davanti e dietro",
    "Guarda a destra e sinistra",
    "Riparti con cautela",
    "Segnala con la freccia se necessario",
    # Module 2 - Driving
    "Mantieni la velocità corretta",
    "Accelera dolcemente",
    "Rallenta quando serve",
    "Mantieni la distanza di sicurezza",
    "Controlla lo specchietto retrovisore centrale",
    "Controlla gli specchietti laterali",
    "Guarda avanti",
    "Segui la segnaletica",
    "Stai nella tua corsia",
    "Usa correttamente gli indicatori",
    "Controlla lo stato del traffico",
    # Module 3 - Turning
    "Svolta a destra",
    "Svolta a sinistra",
    "Riduci la velocità prima della curva",
    "Controlla gli specchietti prima di girare",
    "Usa la freccia almeno 30 metri prima",
    "Non tagliare la curva",
    "Mantieni la corsia durante la curva",
    "Controlla eventuali pedoni",
    "Guarda la segnaletica verticale",
    "Guarda eventuali veicoli provenienti dall'altra corsia",
    # Module 4 - Lane Change & Overtaking
    "Cambia corsia a destra / sinistra",
    "Controlla gli specchietti prima di cambiare corsia",
    "Controlla l'angolo cieco",
    "Usa la freccia prima di cambiare corsia",
    "Non cambiare corsia in curva",
    "Non cambiare corsia su linea continua",
    "Sorpassa solo se sicuro",
    "Controlla il traffico dietro",
    "Tornare nella corsia iniziale se necessario",
    # Module 5 - Roundabout
    "Entra nella rotonda",
    "Prendi la prima uscita",
    "Prendi la seconda uscita",
    "Prendi la terza uscita",
    "Dai la precedenza a chi è dentro la rotonda",
    "Non fermarti dentro la rotonda",
    "Segnala l'uscita dalla rotonda",
    "Mantieni la corsia nella rotonda",
    # Module 6 - Parking & Reversing
    "Parcheggia parallelamente al marciapiede",
    "Fai un parcheggio a L",
    "Fai un parcheggio a S",
    "Fai retromarcia lentamente",
    "Controlla gli specchietti durante il parcheggio",
    "Usa la freccia quando parcheggi",
    "Mantieni la distanza dal marciapiede",
    "Ferma il veicolo completamente",
    "Tieni il freno a mano inserito",
    "Controlla lo spazio dietro",
    "Non urtare altri veicoli",
    "Inserisci la retromarcia",
    # Module 7 - Hill Start
    "Ferma il veicolo in salita",
    "Riparti in salita",
    "Non far spegnere il motore",
    "Non arretrare",
    "Usa il freno a mano se necessario",
    "Controlla il traffico prima di ripartire",
    # Module 8 - Highway
    "Imbocca l'autostrada",
    "Accelera nella corsia di accelerazione",
    "Guarda bene prima di immetterti",
    "Mantieni la destra",
    "Rispetta i limiti di velocità in autostrada",
    "Non sorpassare a destra",
    "Prepara l'uscita con anticipo",
    "Entra nella corsia di decelerazione",
    "Esci dall'autostrada",
    # Module 9 - Lights
    "Accendi i fari anabbaglianti",
    "Accendi gli abbaglianti",
    "Spegni gli abbaglianti",
    "Accendi le luci di posizione",
    "Accendi i fendinebbia anteriori",
    "Accendi i retronebbia",
    "Usa le luci in galleria",
    "Verifica il funzionamento delle frecce",
    # Module 10 - Emergency
    "Frena immediatamente",
    "Evita l'ostacolo",
    "Accosta sulla destra",
    "Accendi le quattro frecce",
    "Controlla i pedoni / ciclisti",
    "Non entrare nell'incrocio se bloccato",
    "Mantieni la calma",
    "Usa il clacson se necessario",
    "Spegni il motore se in incidente",
    "Chiama i soccorsi in caso di emergenza",
    # Module 11 - Ending
    "Torna al punto di partenza",
    "Parcheggia e spegni il motore",
    "Lascia il veicolo in sicurezza",
    "Firma il verbale",
    "Grazie e arrivederci",
    # Extra reference phrases
    "Si controlla attraverso i testimoni di usura. Lo spessore minimo legale è 1,6 mm.",
    "La pressione consigliata si trova sul libretto di circolazione o sull'adesivo vicino alla portiera.",
    "Si controlla a pneumatici freddi con un manometro.",
    "Si controlla con l'astina di livello, a motore freddo e su terreno pianeggiante.",
    "Si tira la leva e si verifica che il veicolo rimanga fermo.",
    "Si controlla il livello del liquido freni nel serbatoio sotto il cofano.",
    "Girando la manopola sul volante fino al simbolo degli anabbaglianti.",
    "Spingendo in avanti la leva di sinistra. Sul cruscotto appare la spia blu.",
    "Una spia rossa indica un pericolo o un guasto grave, bisogna fermarsi immediatamente.",
    "Premendo il pulsante rosso con il triangolo sul cruscotto.",
    "Con la leva di destra sul volante, si può regolare la velocità.",
    "Si controlla il serbatoio del liquido lavavetri sotto il cofano.",
    "Patente di guida, carta di circolazione e certificato di assicurazione.",
    "Nel bagagliaio. Va posizionato ad almeno 50 metri dietro il veicolo.",
    "Ecco i miei documenti",
    "Grazie mille, arrivederci!",
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
VOICE = "it-IT-ElsaNeural"
MAX_CONCURRENT = 3

def text_to_hash(text):
    """Generate a short unique hash for each text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

async def generate_one(text, sem, idx, total):
    """Generate base64 MP3 for a single Italian phrase."""
    async with sem:
        text_hash = text_to_hash(text)
        json_path = os.path.join(OUTPUT_DIR, f"{text_hash}.json")
        
        # Skip if already generated
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get("text") == text and data.get("base64"):
                    print(f"  [{idx}/{total}] ✅ SKIP (exists): {text[:50]}...")
                    return True
            except:
                pass
        
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(text, VOICE)
            mp3_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_data += chunk["data"]
            
            if not mp3_data:
                print(f"  [{idx}/{total}] ❌ FAIL (no audio): {text[:50]}...")
                return False
            
            b64 = base64.b64encode(mp3_data).decode('ascii')
            
            result = {
                "text": text,
                "voice": VOICE,
                "base64": b64,
                "size_bytes": len(mp3_data),
                "hash": text_hash
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
            
            print(f"  [{idx}/{total}] ✅ OK ({len(mp3_data)} bytes): {text[:50]}...")
            return True
            
        except Exception as e:
            print(f"  [{idx}/{total}] ❌ ERROR: {text[:50]}... → {e}")
            return False

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total = len(PHRASES)
    print(f"\n🎙️  Generating {total} audio files with voice: {VOICE}")
    print(f"   Output: {OUTPUT_DIR}/")
    print(f"   Concurrency: {MAX_CONCURRENT}\n")
    
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [generate_one(text, sem, i+1, total) for i, text in enumerate(PHRASES)]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    ok = sum(1 for r in results if r)
    fail = total - ok
    
    print(f"\n{'='*60}")
    print(f"  完成！成功: {ok}/{total} | 失败: {fail}")
    print(f"  耗时: {elapsed:.1f}s")
    print(f"  输出目录: {OUTPUT_DIR}/")
    print(f"{'='*60}\n")
    
    # Create index file for the HTML to know which hashes map to which texts
    index = {}
    for text in PHRASES:
        text_hash = text_to_hash(text)
        index[text] = text_hash
    
    index_path = os.path.join(OUTPUT_DIR, "_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"  📋 索引文件: {index_path}\n")

if __name__ == "__main__":
    asyncio.run(main())
