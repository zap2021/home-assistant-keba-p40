(function(){const s=document.createElement("link").relList;if(s&&s.supports&&s.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))d(n);new MutationObserver(n=>{for(const a of n)if(a.type==="childList")for(const l of a.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&d(l)}).observe(document,{childList:!0,subtree:!0});function i(n){const a={};return n.integrity&&(a.integrity=n.integrity),n.referrerPolicy&&(a.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?a.credentials="include":n.crossOrigin==="anonymous"?a.credentials="omit":a.credentials="same-origin",a}function d(n){if(n.ep)return;n.ep=!0;const a=i(n);fetch(n.href,a)}})();const y="keba-test-client-settings",h={host:"192.168.147.169",port:"8443",username:"admin",password:"",verifySsl:!1,selectedSerial:"",startTokenId:""},t={settings:T(),tokens:{accessToken:"",refreshToken:""},busy:!1,latestWallbox:null,latestWallboxes:[],latestVersion:"",latestSerial:"",logs:[]},S=document.querySelector("#app");if(!S)throw new Error("App root not found");b();function T(){const e=localStorage.getItem(y);if(!e)return{...h};try{return{...h,...JSON.parse(e)}}catch{return{...h}}}function v(){localStorage.setItem(y,JSON.stringify(t.settings))}function b(){S.innerHTML=`
    <main class="page">
      <section class="hero">
        <div class="eyebrow">KEBA REST API · Test Client</div>
        <h1>Lokale API prüfen, bevor Home Assistant übernimmt.</h1>
        <p>Die Webanwendung spricht im Dev-Betrieb über den lokalen Vite-Forwarder mit deiner KEBA-Wallbox. Damit kannst du Login, Status-Endpunkte und schreibende Funktionen gezielt verifizieren.</p>
      </section>

      <section class="layout">
        <div class="stack">
          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h2>Verbindung</h2>
                <span>${o(w())}</span>
              </div>

              <div class="grid two">
                <div class="field">
                  <label for="host">Host</label>
                  <input id="host" name="host" value="${o(t.settings.host)}" />
                </div>
                <div class="field">
                  <label for="port">Port</label>
                  <input id="port" name="port" value="${o(t.settings.port)}" />
                </div>
              </div>

              <div class="grid two">
                <div class="field">
                  <label for="username">Benutzername</label>
                  <input id="username" name="username" value="${o(t.settings.username)}" />
                </div>
                <div class="field">
                  <label for="password">Passwort</label>
                  <input id="password" name="password" type="password" value="${o(t.settings.password)}" />
                </div>
              </div>

              <label class="checkbox">
                <input id="verifySsl" name="verifySsl" type="checkbox" ${t.settings.verifySsl?"checked":""} />
                SSL-Zertifikat der Wallbox prüfen
              </label>

              <div class="button-row">
                <button class="button primary" data-action="login" ${r()}>Login testen</button>
                <button class="button" data-action="refresh" ${r(!t.tokens.refreshToken)}>Token refresh</button>
                <button class="button ghost" data-action="version" ${r()}>Version</button>
                <button class="button ghost" data-action="serial" ${r()}>Seriennummer</button>
              </div>

              <div class="status-card">
                <div class="status-line"><strong>Access Token</strong><span>${t.tokens.accessToken?m(t.tokens.accessToken):"nicht gesetzt"}</span></div>
                <div class="status-line"><strong>Refresh Token</strong><span>${t.tokens.refreshToken?m(t.tokens.refreshToken):"nicht gesetzt"}</span></div>
                <div class="status-line"><strong>API Version</strong><span>${o(t.latestVersion||"unbekannt")}</span></div>
                <div class="status-line"><strong>Geräte-Seriennummer</strong><span>${o(t.latestSerial||"unbekannt")}</span></div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h2>Wallbox Funktionen</h2>
                <span>Authentifizierte Endpunkte</span>
              </div>

              <div class="field">
                <label for="selectedSerial">Wallbox-Seriennummer</label>
                <input id="selectedSerial" name="selectedSerial" value="${o(t.settings.selectedSerial)}" placeholder="Wird nach Listenabruf automatisch gesetzt" />
              </div>

              <div class="field">
                <label for="startTokenId">Optional Token-ID für StartCharging</label>
                <input id="startTokenId" name="startTokenId" value="${o(t.settings.startTokenId)}" placeholder="z. B. A2D80F8E" />
              </div>

              <div class="action-grid">
                <button class="button" data-action="wallboxes" ${r()}>Wallboxes laden</button>
                <button class="button" data-action="wallbox" ${r(!c())}>Wallbox lesen</button>
                <button class="button" data-action="startCharging" ${r(!c())}>Start charging</button>
                <button class="button danger" data-action="stopCharging" ${r(!c())}>Stop charging</button>
                <button class="button" data-action="availabilityOn" ${r(!c())}>Verfügbar</button>
                <button class="button danger" data-action="availabilityOff" ${r(!c())}>Nicht verfügbar</button>
                <button class="button" data-action="lockOn" ${r(!c())}>Dauersperre setzen</button>
                <button class="button danger" data-action="lockOff" ${r(!c())}>Dauersperre lösen</button>
              </div>

              <div class="hint">Schreibende Funktionen greifen direkt auf die lokale Wallbox zu. Für produktive Tests zuerst Status und Identität verifizieren.</div>
            </div>
          </article>
        </div>

        <div class="stack">
          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h3>Aktueller Status</h3>
                <span class="pill ${t.busy?"":t.tokens.accessToken?"success":""} ${t.busy,""}">
                  ${t.busy?"Request läuft":t.tokens.accessToken?"Authentifiziert":"Bereit"}
                </span>
              </div>

              <div class="status-card">
                <div class="status-line"><strong>Ausgewählte Wallbox</strong><span>${o(t.settings.selectedSerial||"nicht gesetzt")}</span></div>
                <div class="status-line"><strong>Letzter Listenabruf</strong><span>${String(t.latestWallboxes.length)}</span></div>
                <div class="status-line"><strong>Letztes Objekt</strong><span>${t.latestWallbox?"vorhanden":"leer"}</span></div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h3>Antwortprotokoll</h3>
                <button class="button ghost" data-action="clearLogs">Leeren</button>
              </div>
              <div class="terminal"><pre>${o(N())}</pre></div>
            </div>
          </article>
        </div>
      </section>
    </main>
  `,$(),x()}function $(){const e=["host","port","username","password","selectedSerial","startTokenId"];for(const i of e)document.querySelector(`#${i}`)?.addEventListener("input",n=>{const a=n.currentTarget;t.settings[i]=a.value,v(),b()});document.querySelector("#verifySsl")?.addEventListener("change",i=>{t.settings.verifySsl=i.currentTarget.checked,v(),b()})}function x(){document.querySelectorAll("[data-action]").forEach(e=>{e.addEventListener("click",async()=>{const s=e.dataset.action;s&&await A(s)})})}async function A(e){if(e==="clearLogs"){t.logs=[],b();return}t.busy=!0,b();try{switch(e){case"login":await O();break;case"refresh":await L();break;case"version":await E();break;case"serial":await W();break;case"wallboxes":await z();break;case"wallbox":await P();break;case"startCharging":await I();break;case"stopCharging":await g("POST",f("/stopCharging"),void 0,"Stop charging");break;case"availabilityOn":await g("POST",f("/changeAvailability"),{available:!0},"Availability on");break;case"availabilityOff":await g("POST",f("/changeAvailability"),{available:!1},"Availability off");break;case"lockOn":await g("POST",f("/permanentlyLock"),{},"Permanent lock on");break;case"lockOff":await g("DELETE",f("/permanentlyLock"),void 0,"Permanent lock off");break;default:throw new Error(`Unknown action: ${e}`)}}catch(s){u(e,s instanceof Error?s.message:String(s))}finally{t.busy=!1,b()}}async function O(){const e=await p("POST","/v2/jwt/login",{username:t.settings.username,password:t.settings.password});t.tokens.accessToken=e.accessToken??"",t.tokens.refreshToken=e.refreshToken??"",u("Login",e)}async function L(){const e=await p("POST","/v2/jwt/refresh",void 0,{Authorization:`Bearer ${t.tokens.refreshToken}`});t.tokens.accessToken=e.accessToken??t.tokens.accessToken,t.tokens.refreshToken=e.refreshToken??t.tokens.refreshToken,u("Refresh token",e)}async function E(){const e=await p("GET","/version");t.latestVersion=typeof e=="string"?e:JSON.stringify(e),u("Version",e)}async function W(){const e=await p("GET","/serialnumber");t.latestSerial=typeof e=="string"?e:JSON.stringify(e),!t.settings.selectedSerial&&typeof e=="string"&&(t.settings.selectedSerial=e,v()),u("Serial number",e)}async function z(){const e=await k("GET","/v2/wallboxes");if(t.latestWallboxes=e.wallboxes??[],!t.settings.selectedSerial&&t.latestWallboxes.length>0){const s=t.latestWallboxes[0];s.serialNumber&&(t.settings.selectedSerial=s.serialNumber,v())}u("Wallboxes",e)}async function P(){const e=await k("GET",f());t.latestWallbox=e,u("Wallbox",e)}async function I(){const e=t.settings.startTokenId?`/startCharging?id=${encodeURIComponent(t.settings.startTokenId)}`:"/startCharging";await g("POST",f(e),void 0,"Start charging")}async function g(e,s,i,d){const n=await k(e,s,i);t.latestWallbox=n,u(d,n)}async function k(e,s,i){if(!t.tokens.accessToken)throw new Error("Kein Access Token vorhanden. Zuerst Login ausführen.");return p(e,s,i,{Authorization:`Bearer ${t.tokens.accessToken}`})}async function p(e,s,i,d={}){const n=await fetch(`/keba-api${s}`,{method:e,headers:{"Content-Type":"application/json","x-keba-target":w(),"x-keba-insecure":String(!t.settings.verifySsl),...d},body:e==="GET"||i===void 0?void 0:JSON.stringify(i)}),a=await n.text(),l=C(a);if(!n.ok)throw new Error(`[${n.status}] ${typeof l=="string"?l:JSON.stringify(l,null,2)}`);return l}function f(e=""){if(!c())throw new Error("Keine Wallbox-Seriennummer gesetzt.");return`/v2/wallboxes/${encodeURIComponent(t.settings.selectedSerial)}${e}`}function w(){return`https://${t.settings.host}:${t.settings.port}`}function c(){return t.settings.selectedSerial.trim().length>0}function N(){return t.logs.length===0?"Noch keine Requests ausgeführt.":t.logs.map(e=>`[${e.timestamp}] ${e.title}
${e.detail}`).join(`

`)}function u(e,s){t.logs.unshift({timestamp:new Date().toLocaleTimeString("de-DE"),title:e,detail:typeof s=="string"?s:JSON.stringify(s,null,2)}),t.logs=t.logs.slice(0,20)}function C(e){const s=e.trim();if(s.length===0)return"";try{return JSON.parse(s)}catch{return s}}function m(e){return e.length<=20?e:`${e.slice(0,12)}…${e.slice(-8)}`}function r(e=t.busy){return e?"disabled":""}function o(e){return e.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}
