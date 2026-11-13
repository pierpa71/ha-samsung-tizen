# Samsung TV (Tizen) per Home Assistant

Integrazione personalizzata per i TV Samsung con Tizen (modelli dal 2016 in poi).

## Funzioni

### Novità 0.3.0: card telecomando
L'integrazione installa una card a forma di telecomando, senza bisogno di HACS o di aggiungere risorse. In una dashboard aggiungi:

```yaml
type: custom:samsung-remote-card
entity: media_player.samsung_tv          # obbligatorio
apps: [Netflix, YouTube, RaiPlay, DAZN]  # facoltativo: le app in evidenza
sources: [TV, HDMI 1, HDMI 2]            # facoltativo
```

La card comprende:
- accensione, sorgenti, tastierino numerico, pad direzionale e OK
- Indietro, Home, Esci, bilancieri volume e canale, muto, info, guida, riproduzione, tasti colorati
- le app del TV, con le principali in evidenza e "Tutte le app"

Tenendo premuti frecce, volume e canale il comando si ripete. Da computer funzionano anche frecce, Invio, Backspace, +/− e i numeri della tastiera.

### Novità 0.2.0
- **App**: l'elenco viene letto dal TV, con gli ID giusti per il tuo modello. Ci sono un menu *App* e le app nelle sorgenti del media player.
- **Sorgente**: un menu con TV, HDMI e HDMI 1-4.
- **Canale**: scrivi il numero e il TV ci va.
- **26 pulsanti**: frecce, OK, Indietro, Esci, Home, Menu, Info, Guida, Lista canali, Canale ±, Volume ±, Muto, Play, Pausa, Avanti e indietro veloce, tasti colorati.
- **Dashboard di esempio** con il pad direzionale in `examples/dashboard_telecomando_tv.yaml`. Sostituisci `soggiorno_tv_65_pollici` con il nome delle tue entità.

### Base

- **Media player**: accensione e spegnimento, volume su/giù, muto, play/pausa/stop, canale su/giù (tasti avanti/indietro), sorgenti (TV, HDMI 1-4) e app (Netflix, YouTube, Prime Video, Disney+, Apple TV, Spotify, Plex)
- **Telecomando** (`remote`): invia qualsiasi tasto, per esempio `KEY_HOME`, `KEY_UP`, `KEY_ENTER`, `KEY_RETURN`
- **Abbinamento guidato**: accetti il popup sul TV e il token viene salvato
- **Wake-on-LAN** per accendere il TV quando è spento del tutto

## Installazione

**HACS:** HACS → menu ⋮ → *Repository personalizzati* → aggiungi l'URL di questo repo con categoria *Integration* → installa → riavvia Home Assistant.

**Manuale:** copia `custom_components/samsung_tizen` nella cartella `config/custom_components/` di Home Assistant e riavvia.

Poi: *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Samsung TV (Tizen)*, inserisci l'IP del TV (acceso) e accetta il popup sul TV.

## Esempi

```yaml
# Apri Netflix
action: media_player.select_source
target: { entity_id: media_player.samsung_tv }
data: { source: Netflix }

# App qualsiasi tramite app id
action: media_player.play_media
target: { entity_id: media_player.samsung_tv }
data: { media_content_type: app, media_content_id: "111299001912" }

# Vai al canale 5
action: media_player.play_media
target: { entity_id: media_player.samsung_tv }
data: { media_content_type: channel, media_content_id: "5" }

# Sequenza di tasti
action: remote.send_command
target: { entity_id: remote.samsung_tv_telecomando }
data: { command: [HOME, LEFT, ENTER], delay_secs: 0.5 }
```

## Limiti

- **Volume**: il TV non comunica il livello del volume né lo stato del muto. Si usano volume su/giù e il muto è un interruttore.
- **Accensione da spento**: serve il Wake-on-LAN, quindi devi impostare il MAC nelle opzioni e attivare sul TV *Accendi con dispositivo mobile*. Il pacchetto WoL deve poter raggiungere la rete del TV; da Docker o Podman su macOS non ci arriva.
- **Tasti HDMI 1-4**: non tutti i modelli supportano `KEY_HDMI1`…`4`. In alternativa c'è `HDMI`, che passa alla sorgente successiva.
