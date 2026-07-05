// Cave à vin partagée — frontend (vanilla JS, sans dépendance de build).

const app = document.getElementById("app");
const modalOverlay = document.getElementById("modal-overlay");
const modalContenu = document.getElementById("modal-contenu");

let utilisateurCourantId = localStorage.getItem("utilisateurId") || "";

// ---------------------------------------------------------------------
// Appels API
// ---------------------------------------------------------------------
async function api(path, options = {}) {
  const headers = options.headers || {};
  if (utilisateurCourantId) headers["X-Utilisateur-Id"] = utilisateurCourantId;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const resp = await fetch(`/api${path}`, { ...options, headers });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}));
    throw new Error(detail.detail || `Erreur ${resp.status}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

function fermerModal() {
  modalOverlay.classList.add("masque");
  modalContenu.innerHTML = "";
}
function ouvrirModal(html) {
  modalContenu.innerHTML = html;
  modalOverlay.classList.remove("masque");
}
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) fermerModal(); });

function formatDate(epoch) {
  if (!epoch) return "";
  return new Date(epoch * 1000).toLocaleDateString("fr-FR");
}
function epochAujourdhui() { return Math.floor(Date.now() / 1000); }

// ---------------------------------------------------------------------
// Navigation par onglets
// ---------------------------------------------------------------------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("actif"));
    btn.classList.add("actif");
    afficherVue(btn.dataset.vue);
  });
});

async function afficherVue(vue) {
  if (vue === "caves") return vueCaves();
  if (vue === "vins") return vueVins();
  if (vue === "ajouter") return vueAjouter();
}

// ---------------------------------------------------------------------
// Utilisateurs
// ---------------------------------------------------------------------
async function chargerUtilisateurs() {
  const select = document.getElementById("selecteur-utilisateur");
  try {
    const utilisateurs = await api("/utilisateurs");
    select.innerHTML = utilisateurs.map((u) => `<option value="${u.id}">${u.nom}</option>`).join("");
    if (utilisateurCourantId && utilisateurs.some((u) => u.id === utilisateurCourantId)) {
      select.value = utilisateurCourantId;
    } else if (utilisateurs.length) {
      utilisateurCourantId = utilisateurs[0].id;
      localStorage.setItem("utilisateurId", utilisateurCourantId);
    }
    select.addEventListener("change", () => {
      utilisateurCourantId = select.value;
      localStorage.setItem("utilisateurId", utilisateurCourantId);
    });
  } catch (e) {
    select.innerHTML = "<option>?</option>";
  }
}

// ---------------------------------------------------------------------
// Vue : Caves
// ---------------------------------------------------------------------
async function vueCaves() {
  app.innerHTML = `<p class="texte-discret">Chargement…</p>`;
  const caves = await api("/caves");
  app.innerHTML = `
    <button class="bouton bouton-bloc" id="btn-nouvelle-cave">+ Nouvelle cave</button>
    ${caves.map((c) => `
      <div class="carte" data-id="${c.id}" onclick="ouvrirCave('${c.id}')">
        <p class="carte-titre">${c.nom}</p>
        <p class="carte-sous-titre">${c.lignes} × ${c.colonnes} emplacements — ${c.emplacements_occupes}/${c.emplacements_total} occupés</p>
      </div>
    `).join("") || `<p class="texte-discret">Aucune cave pour l'instant.</p>`}
  `;
  document.getElementById("btn-nouvelle-cave").addEventListener("click", () => formulaireCave());
}

function formulaireCave(cave = null) {
  ouvrirModal(`
    <h2>${cave ? "Modifier la cave" : "Nouvelle cave"}</h2>
    <div class="champ"><label>Nom</label><input id="f-nom" value="${cave?.nom || ""}"></div>
    <div class="ligne-form">
      <div class="champ"><label>Lignes</label><input id="f-lignes" type="number" min="1" value="${cave?.lignes || 6}"></div>
      <div class="champ"><label>Colonnes</label><input id="f-colonnes" type="number" min="1" value="${cave?.colonnes || 6}"></div>
    </div>
    <div class="champ"><label>Commentaires</label><textarea id="f-commentaires">${cave?.commentaires || ""}</textarea></div>
    <button class="bouton bouton-bloc" id="btn-enregistrer-cave">Enregistrer</button>
    <button class="bouton secondaire bouton-bloc" onclick="fermerModal()">Annuler</button>
  `);
  document.getElementById("btn-enregistrer-cave").addEventListener("click", async () => {
    const payload = {
      nom: document.getElementById("f-nom").value,
      lignes: parseInt(document.getElementById("f-lignes").value, 10),
      colonnes: parseInt(document.getElementById("f-colonnes").value, 10),
      commentaires: document.getElementById("f-commentaires").value,
    };
    if (cave) await api(`/caves/${cave.id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/caves", { method: "POST", body: JSON.stringify(payload) });
    fermerModal();
    vueCaves();
  });
}

async function ouvrirCave(caveId) {
  const [cave, emplacements] = await Promise.all([
    api(`/caves/${caveId}`),
    api(`/caves/${caveId}/emplacements`),
  ]);
  const grille = emplacements.map((e) => `
    <div class="case-cave ${e.vin_id ? "occupee" : ""}"
         title="${e.vin_nom ? e.vin_nom + " " + (e.vin_millesime || "") : "Vide (ligne " + e.ligne + ", colonne " + e.colonne + ")"}"
         onclick="clicEmplacement('${e.id}', ${e.vin_id ? `'${e.vin_id}'` : "null"})">
      ${e.vin_id ? "🍾" : ""}
    </div>
  `).join("");
  ouvrirModal(`
    <h2>${cave.nom}</h2>
    <p class="texte-discret">${cave.lignes} × ${cave.colonnes} — cliquez une case pour l'assigner ou voir le vin</p>
    <div class="grille-cave" style="grid-template-columns: repeat(${cave.colonnes}, 1fr);">${grille}</div>
    <button class="bouton secondaire bouton-bloc" onclick='formulaireCave(${JSON.stringify(cave)})'>Modifier la cave</button>
    <button class="bouton danger bouton-bloc" id="btn-suppr-cave">Supprimer la cave</button>
  `);
  document.getElementById("btn-suppr-cave").addEventListener("click", async () => {
    try {
      await api(`/caves/${caveId}`, { method: "DELETE" });
      fermerModal();
      vueCaves();
    } catch (e) { alert(e.message); }
  });
}

async function clicEmplacement(emplacementId, vinId) {
  if (vinId) return ouvrirVin(vinId);
  const vins = await api("/vins?statut=actif");
  ouvrirModal(`
    <h2>Assigner une bouteille</h2>
    <div class="champ">
      <select id="f-vin-emplacement">
        <option value="">— vide —</option>
        ${vins.map((v) => `<option value="${v.id}">${v.nom} ${v.millesime || ""} (stock ${v.stock_actuel})</option>`).join("")}
      </select>
    </div>
    <button class="bouton bouton-bloc" id="btn-assigner">Enregistrer</button>
  `);
  document.getElementById("btn-assigner").addEventListener("click", async () => {
    const vinChoisi = document.getElementById("f-vin-emplacement").value || null;
    await api(`/emplacements/${emplacementId}`, { method: "PUT", body: JSON.stringify({ vin_id: vinChoisi }) });
    fermerModal();
  });
}
window.ouvrirCave = ouvrirCave;
window.clicEmplacement = clicEmplacement;
window.formulaireCave = formulaireCave;
window.fermerModal = fermerModal;

// ---------------------------------------------------------------------
// Vue : Vins
// ---------------------------------------------------------------------
async function vueVins(recherche = "") {
  app.innerHTML = `
    <div class="champ"><input id="recherche-vin" placeholder="Rechercher un vin…" value="${recherche}"></div>
    <div id="liste-vins" class="carte"><p class="texte-discret">Chargement…</p></div>
  `;
  document.getElementById("recherche-vin").addEventListener("input", (e) => chargerListeVins(e.target.value));
  chargerListeVins(recherche);
}

async function chargerListeVins(recherche) {
  const params = new URLSearchParams();
  if (recherche) params.set("recherche", recherche);
  const vins = await api(`/vins?${params.toString()}`);
  document.getElementById("liste-vins").innerHTML = vins.map((v) => `
    <div class="liste-item" onclick="ouvrirVin('${v.id}')">
      <div>
        <div>${v.nom} ${v.millesime ? `<span class="texte-discret">${v.millesime}</span>` : ""}</div>
        ${v.statut === "brouillon" ? `<span class="texte-discret">🕓 brouillon à valider</span>` : ""}
      </div>
      <span class="badge">${v.stock_actuel} bout.</span>
    </div>
  `).join("") || `<p class="texte-discret">Aucun vin trouvé.</p>`;
}

async function ouvrirVin(vinId, ongletInitial = "infos") {
  const vin = await api(`/vins/${vinId}`);
  ouvrirModal(`
    <h2>${vin.nom}</h2>
    <div class="onglets-secondaires">
      <button class="onglet-sec ${ongletInitial === "infos" ? "actif" : ""}" data-o="infos">Infos</button>
      <button class="onglet-sec ${ongletInitial === "stock" ? "actif" : ""}" data-o="stock">Stock</button>
      <button class="onglet-sec ${ongletInitial === "degustations" ? "actif" : ""}" data-o="degustations">Dégustations</button>
      <button class="onglet-sec ${ongletInitial === "ia" ? "actif" : ""}" data-o="ia">Photo / IA</button>
    </div>
    <div id="contenu-onglet-vin"></div>
  `);
  const conteneur = document.getElementById("contenu-onglet-vin");
  const afficherOnglet = (o) => {
    document.querySelectorAll(".onglet-sec").forEach((b) => b.classList.toggle("actif", b.dataset.o === o));
    if (o === "infos") ongletInfos(conteneur, vin);
    if (o === "stock") ongletStock(conteneur, vin);
    if (o === "degustations") ongletDegustations(conteneur, vin);
    if (o === "ia") ongletIA(conteneur, vin);
  };
  modalContenu.querySelectorAll(".onglet-sec").forEach((b) => b.addEventListener("click", () => afficherOnglet(b.dataset.o)));
  afficherOnglet(ongletInitial);
}
window.ouvrirVin = ouvrirVin;

function ongletInfos(conteneur, vin) {
  conteneur.innerHTML = `
    <div class="champ"><label>Nom</label><input id="vi-nom" value="${vin.nom || ""}"></div>
    <div class="ligne-form">
      <div class="champ"><label>Cuvée</label><input id="vi-cuvee" value="${vin.cuvee || ""}"></div>
      <div class="champ"><label>Millésime</label><input id="vi-millesime" type="number" value="${vin.millesime || ""}"></div>
    </div>
    <div class="champ"><label>Composition (cépages)</label><input id="vi-composition" value="${vin.composition || ""}"></div>
    <div class="ligne-form">
      <div class="champ"><label>Degré d'alcool</label><input id="vi-degre" type="number" step="0.1" value="${vin.degre_alcool || ""}"></div>
      <div class="champ"><label>Prix estimé (€)</label><input id="vi-prix" type="number" step="0.01" value="${vin.prix_estime || ""}"></div>
    </div>
    <div class="champ"><label>Commentaires</label><textarea id="vi-commentaires">${vin.commentaires || ""}</textarea></div>
    <div class="champ"><label>Statut</label>
      <select id="vi-statut">
        <option value="brouillon" ${vin.statut === "brouillon" ? "selected" : ""}>Brouillon</option>
        <option value="actif" ${vin.statut === "actif" ? "selected" : ""}>Actif</option>
        <option value="archive" ${vin.statut === "archive" ? "selected" : ""}>Archivé</option>
      </select>
    </div>
    <p class="texte-discret">Stock actuel calculé : <strong>${vin.stock_actuel}</strong> bouteille(s)</p>
    <button class="bouton bouton-bloc" id="btn-enregistrer-vin">Enregistrer</button>
    <button class="bouton danger bouton-bloc" id="btn-suppr-vin">Supprimer la fiche</button>
  `;
  document.getElementById("btn-enregistrer-vin").addEventListener("click", async () => {
    const payload = {
      nom: document.getElementById("vi-nom").value,
      cuvee: document.getElementById("vi-cuvee").value,
      millesime: parseInt(document.getElementById("vi-millesime").value, 10) || null,
      composition: document.getElementById("vi-composition").value,
      degre_alcool: parseFloat(document.getElementById("vi-degre").value) || null,
      prix_estime: parseFloat(document.getElementById("vi-prix").value) || null,
      commentaires: document.getElementById("vi-commentaires").value,
      statut: document.getElementById("vi-statut").value,
    };
    await api(`/vins/${vin.id}`, { method: "PUT", body: JSON.stringify(payload) });
    fermerModal();
    vueVins();
  });
  document.getElementById("btn-suppr-vin").addEventListener("click", async () => {
    if (!confirm("Supprimer définitivement cette fiche ?")) return;
    await api(`/vins/${vin.id}`, { method: "DELETE" });
    fermerModal();
    vueVins();
  });
}

async function ongletStock(conteneur, vin) {
  conteneur.innerHTML = `<p class="texte-discret">Chargement…</p>`;
  const mouvements = await api(`/vins/${vin.id}/mouvements`);
  conteneur.innerHTML = `
    <div class="ligne-form">
      <div class="champ">
        <label>Type</label>
        <select id="mv-type">
          <option value="achat">Achat</option>
          <option value="consommation">Consommation</option>
          <option value="casse">Casse</option>
          <option value="don">Don</option>
          <option value="ajustement">Ajustement d'inventaire</option>
        </select>
      </div>
      <div class="champ"><label>Quantité</label><input id="mv-quantite" type="number" value="1" min="1"></div>
    </div>
    <div class="champ"><label>Commentaire (occasion, etc.)</label><input id="mv-commentaire"></div>
    <button class="bouton bouton-bloc" id="btn-ajouter-mouvement">Ajouter le mouvement</button>
    <h3>Historique</h3>
    ${mouvements.map((m) => `
      <div class="liste-item">
        <div>${m.type_mouvement} — ${formatDate(m.date_mouvement)} ${m.commentaires ? `<div class="texte-discret">${m.commentaires}</div>` : ""}</div>
        <span class="badge">${m.quantite}</span>
      </div>
    `).join("") || `<p class="texte-discret">Aucun mouvement.</p>`}
  `;
  document.getElementById("btn-ajouter-mouvement").addEventListener("click", async () => {
    const payload = {
      type_mouvement: document.getElementById("mv-type").value,
      quantite: parseInt(document.getElementById("mv-quantite").value, 10),
      commentaires: document.getElementById("mv-commentaire").value,
      date_mouvement: epochAujourdhui(),
    };
    await api(`/vins/${vin.id}/mouvements`, { method: "POST", body: JSON.stringify(payload) });
    const vinMaj = await api(`/vins/${vin.id}`);
    ongletStock(conteneur, vinMaj);
  });
}

async function ongletDegustations(conteneur, vin) {
  conteneur.innerHTML = `<p class="texte-discret">Chargement…</p>`;
  const notes = await api(`/vins/${vin.id}/degustations`);
  conteneur.innerHTML = `
    <div class="champ"><label>Note (/20)</label><input id="dg-note" type="number" step="0.5" min="0" max="20"></div>
    <div class="champ"><label>Commentaires de dégustation</label><textarea id="dg-commentaires"></textarea></div>
    <button class="bouton bouton-bloc" id="btn-ajouter-degustation">Ajouter la dégustation</button>
    <h3>Historique</h3>
    ${notes.map((n) => `
      <div class="liste-item">
        <div>${formatDate(n.date_degustation)} ${n.commentaires ? `<div class="texte-discret">${n.commentaires}</div>` : ""}</div>
        <span class="badge">${n.note ?? "—"}/20</span>
      </div>
    `).join("") || `<p class="texte-discret">Aucune dégustation notée.</p>`}
  `;
  document.getElementById("btn-ajouter-degustation").addEventListener("click", async () => {
    const payload = {
      note: parseFloat(document.getElementById("dg-note").value) || null,
      commentaires: document.getElementById("dg-commentaires").value,
      date_degustation: epochAujourdhui(),
    };
    await api(`/vins/${vin.id}/degustations`, { method: "POST", body: JSON.stringify(payload) });
    ongletDegustations(conteneur, vin);
  });
}

function ongletIA(conteneur, vin) {
  const photo = vin.photos && vin.photos[0];
  conteneur.innerHTML = `
    ${photo ? `<img src="/api/documents/${photo.id}/fichier" style="width:100%;border-radius:8px;margin-bottom:10px;">` : `<p class="texte-discret">Aucune photo pour cette fiche.</p>`}
    <div class="champ"><label>Texte OCR détecté</label><textarea readonly>${vin.ocr_texte_brut || "(aucun)"}</textarea></div>
    <button class="bouton bouton-bloc" id="btn-lancer-ia">Enrichir cette fiche avec l'IA</button>
    <div id="resultat-ia"></div>
  `;
  document.getElementById("btn-lancer-ia").addEventListener("click", async () => {
    const zone = document.getElementById("resultat-ia");
    zone.innerHTML = `<p class="texte-discret">Analyse en cours…</p>`;
    try {
      const res = await api(`/vins/${vin.id}/ia-enrichissement`, { method: "POST" });
      const champs = res.champs_proposes;
      zone.innerHTML = `
        <h3>Suggestions (${res.modele})</h3>
        ${Object.entries(champs).map(([cle, valeur]) => `
          <div class="champ"><label>${cle}</label><input data-cle="${cle}" value="${valeur ?? ""}"></div>
        `).join("")}
        <button class="bouton bouton-bloc" id="btn-appliquer-ia">Appliquer ces valeurs à la fiche</button>
      `;
      document.getElementById("btn-appliquer-ia").addEventListener("click", async () => {
        const champsApplique = {};
        zone.querySelectorAll("[data-cle]").forEach((input) => { champsApplique[input.dataset.cle] = input.value; });
        await api(`/ia-enrichissement/${res.id}/appliquer`, { method: "POST", body: JSON.stringify({ champs: champsApplique }) });
        alert("Fiche mise à jour.");
        ouvrirVin(vin.id, "infos");
      });
    } catch (e) {
      zone.innerHTML = `<p class="texte-discret">Échec : ${e.message}</p>`;
    }
  });
}

// ---------------------------------------------------------------------
// Vue : Ajouter
// ---------------------------------------------------------------------
function vueAjouter() {
  app.innerHTML = `
    <div class="carte">
      <p class="carte-titre">📷 Ajouter par photo</p>
      <p class="texte-discret">Prenez l'étiquette en photo : une fiche brouillon est créée automatiquement avec le texte détecté (OCR), à compléter ensuite.</p>
      <div class="zone-photo">
        <input type="file" accept="image/*" capture="environment" id="input-photo">
      </div>
    </div>
    <div class="carte">
      <p class="carte-titre">✏️ Ajouter manuellement</p>
      <div class="champ"><label>Nom du vin</label><input id="aj-nom"></div>
      <button class="bouton bouton-bloc" id="btn-ajouter-manuel">Créer la fiche</button>
    </div>
  `;
  document.getElementById("input-photo").addEventListener("change", async (e) => {
    const fichier = e.target.files[0];
    if (!fichier) return;
    const formData = new FormData();
    formData.append("fichier", fichier);
    app.insertAdjacentHTML("afterbegin", `<p class="texte-discret" id="statut-upload">Analyse OCR en cours…</p>`);
    try {
      const res = await api("/vins/nouveau-depuis-photo", { method: "POST", body: formData });
      document.getElementById("statut-upload").remove();
      ouvrirVin(res.vin_id, "ia");
    } catch (err) {
      document.getElementById("statut-upload").textContent = "Échec : " + err.message;
    }
  });
  document.getElementById("btn-ajouter-manuel").addEventListener("click", async () => {
    const nom = document.getElementById("aj-nom").value.trim();
    if (!nom) return;
    const res = await api("/vins", { method: "POST", body: JSON.stringify({ nom, statut: "actif" }) });
    ouvrirVin(res.id, "infos");
  });
}

// ---------------------------------------------------------------------
// Démarrage
// ---------------------------------------------------------------------
(async function demarrer() {
  await chargerUtilisateurs();
  vueCaves();
})();
