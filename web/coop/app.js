/**
 * web/coop/app.js — Cliente Web Co-op em Tempo Real (RPG-battle)
 * 
 * Renderizador de alta fidelidade visual (Paridade 1:1 com main.py):
 * - Texturas oficiais de terreno (/assets/images/environment/)
 * - Sprites oficiais de heróis (/assets/images/characters/heroes/)
 * - Sprites oficiais de monstros Isectum (/assets/images/characters/monsters/isectum/)
 * - Efeitos sonoros originais (/assets/sounds/)
 * - Rótulos de dano flutuante, animações suaves e HUD tático.
 */

(function () {
  "use strict";

  // ── Constantes de Terrenos e Tabuleiro ──────────────────────────────────────
  const TERRENO_NORMAL = 0;
  const TERRENO_FLORESTA = 1;
  const TERRENO_DIFICIL = 2;
  const TERRENO_PAREDE = 3;
  const TERRENO_ROCHA = 4;
  const TERRENO_BARRIL = 5;
  const TERRENO_FOGO = 6;

  const GRID_SIZE = 20;

  // ── Mapeamento de Assets Reais do Jogo ─────────────────────────────────────
  const ASSET_TERRENO_MAP = {
    [TERRENO_NORMAL]:   "/assets/images/environment/terreno_normal.png",
    [TERRENO_FLORESTA]: "/assets/images/environment/terreno_floresta.png",
    [TERRENO_DIFICIL]:  "/assets/images/environment/terreno_dificil.png",
    [TERRENO_PAREDE]:   "/assets/images/environment/terreno_parede.png",
    [TERRENO_ROCHA]:    "/assets/images/environment/terreno_rocha.png",
    [TERRENO_BARRIL]:   "/assets/images/environment/terreno_barril.png",
    [TERRENO_FOGO]:     "/assets/images/environment/terreno_fogo.png",
  };

  const ASSET_HERO_MAP = {
    "Aquele": "/assets/images/characters/heroes/Aquele.png",
    "Stark":  "/assets/images/characters/heroes/paladino.png",
    "Elden":  "/assets/images/characters/heroes/mago.png",
    "Doom":   "/assets/images/characters/heroes/ladino.png",
    "Gruu":   "/assets/images/characters/heroes/barbaro.png",
    "Kuro":   "/assets/images/characters/heroes/ladino.png",
    "Darwin": "/assets/images/characters/heroes/druida.png",
  };

  const ASSET_ENEMY_MAP = {
    "TrabalhadorIsectum": "/assets/images/characters/monsters/isectum/besouro_gorgulho.png",
    "GuerreiroIsectum":   "/assets/images/characters/monsters/isectum/vespa_cacadora.png",
    "ExploradorIsectum":  "/assets/images/characters/monsters/isectum/louva_deus.png",
    "default":            "/assets/images/characters/monsters/isectum/larva_carniceira.png",
  };

  const SOUND_EFFECTS = {
    attack:   new Audio("/assets/sounds/attack.ogg"),
    hit:      new Audio("/assets/sounds/hit.ogg"),
    damage:   new Audio("/assets/sounds/damage.ogg"),
    critical: new Audio("/assets/sounds/critical_hit.ogg"),
    click:    new Audio("/assets/sounds/button_click.ogg"),
    heal:     new Audio("/assets/sounds/heal.ogg"),
    miss:     new Audio("/assets/sounds/miss.ogg"),
  };

  function playAudio(name) {
    try {
      const snd = SOUND_EFFECTS[name];
      if (snd) {
        snd.currentTime = 0;
        snd.volume = 0.5;
        snd.play().catch(() => {});
      }
    } catch (_) {}
  }

  // Cache de imagens carregadas
  const imageCache = {};
  function getImage(url) {
    if (!url) return null;
    if (imageCache[url]) return imageCache[url];
    const img = new Image();
    img.src = url;
    imageCache[url] = img;
    return img;
  }

  // Pre-carrega texturas e sprites principais
  Object.values(ASSET_TERRENO_MAP).forEach(getImage);
  Object.values(ASSET_HERO_MAP).forEach(getImage);
  Object.values(ASSET_ENEMY_MAP).forEach(getImage);

  // ── Estado do Cliente ──────────────────────────────────────────────────────
  let socket = null;
  let roomId = null;
  let playerId = "p_" + Math.random().toString(36).substring(2, 9);
  let playerName = "Aventureiro";
  let heroesCatalog = [];
  let gameState = null;
  let hoveredTile = { x: -1, y: -1 };
  let floatingTexts = [];
  let lastEnemyHp = {};
  let lastHeroHp = {};
  let animTimer = 0;

  // ── Elementos DOM ──────────────────────────────────────────────────────────
  const modalEntry = document.getElementById("modalEntry");
  const inputPlayerName = document.getElementById("inputPlayerName");
  const inputRoomCode = document.getElementById("inputRoomCode");
  const btnJoinRoom = document.getElementById("btnJoinRoom");

  const connBadge = document.getElementById("connBadge");
  const connDot = document.getElementById("connDot");
  const connText = document.getElementById("connText");
  const displayRoomCode = document.getElementById("displayRoomCode");
  const btnCopyInvite = document.getElementById("btnCopyInvite");
  const displayPhase = document.getElementById("displayPhase");
  const displayRound = document.getElementById("displayRound");

  const resMadeira = document.getElementById("resMadeira");
  const resMetal = document.getElementById("resMetal");
  const resCristal = document.getElementById("resCristal");

  const synergyBanner = document.getElementById("synergyBanner");
  const synergyText = document.getElementById("synergyText");

  const lobbyView = document.getElementById("lobbyView");
  const combatView = document.getElementById("combatView");
  const heroesGrid = document.getElementById("heroesGrid");
  const rosterList = document.getElementById("rosterList");
  const btnStartGame = document.getElementById("btnStartGame");

  const boardCanvas = document.getElementById("boardCanvas");
  const ctx = boardCanvas.getContext("2d");

  const apMov = document.getElementById("apMov");
  const apTrab = document.getElementById("apTrab");
  const apEsc = document.getElementById("apEsc");
  const btnEndTurn = document.getElementById("btnEndTurn");

  const cardsHand = document.getElementById("cardsHand");
  const handTip = document.getElementById("handTip");
  const combatTeamRoster = document.getElementById("combatTeamRoster");
  const combatLog = document.getElementById("combatLog");
  const chatInput = document.getElementById("chatInput");
  const btnSendChat = document.getElementById("btnSendChat");

  // ── Inicialização ──────────────────────────────────────────────────────────
  window.addEventListener("DOMContentLoaded", async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const roomParam = urlParams.get("room");
    if (roomParam) {
      inputRoomCode.value = roomParam.toUpperCase().trim();
    }

    await fetchHeroesCatalog();

    btnJoinRoom.addEventListener("click", handleJoinSubmit);
    inputRoomCode.addEventListener("keydown", (e) => e.key === "Enter" && handleJoinSubmit());
    inputPlayerName.addEventListener("keydown", (e) => e.key === "Enter" && handleJoinSubmit());

    btnStartGame.addEventListener("click", () => { playAudio("click"); sendSocketMessage("START_GAME"); });
    btnEndTurn.addEventListener("click", () => { playAudio("click"); sendSocketMessage("END_ROUND"); });
    btnCopyInvite.addEventListener("click", copyInviteLink);

    btnSendChat.addEventListener("click", sendChatMessage);
    chatInput.addEventListener("keydown", (e) => e.key === "Enter" && sendChatMessage());

    boardCanvas.addEventListener("mousemove", onCanvasMouseMove);
    boardCanvas.addEventListener("mouseleave", () => { hoveredTile = { x: -1, y: -1 }; });
    boardCanvas.addEventListener("click", onCanvasClick);
    boardCanvas.addEventListener("dblclick", onCanvasDblClick);

    // Inicia loop contínuo de renderização para animações fluidas
    requestAnimationFrame(renderLoop);
  });

  // ── Catálogo de Heróis ─────────────────────────────────────────────────────
  async function fetchHeroesCatalog() {
    try {
      const res = await fetch("/api/heroes");
      if (res.ok) {
        heroesCatalog = await res.json();
      }
    } catch (err) {
      console.warn("Usando catálogo de heróis offline:", err);
    }
  }

  // ── Conexão WebSocket ──────────────────────────────────────────────────────
  function handleJoinSubmit() {
    playAudio("click");
    const pName = inputPlayerName.value.trim() || "Aventureiro";
    let rCode = inputRoomCode.value.trim().toUpperCase();

    if (!rCode) {
      rCode = "SALA" + Math.floor(10 + Math.random() * 90);
    }

    playerName = pName;
    roomId = rCode;

    modalEntry.style.display = "none";
    displayRoomCode.textContent = roomId;

    connectWebSocket();
  }

  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${roomId}/${playerId}?player_name=${encodeURIComponent(playerName)}`;

    updateConnectionStatus("connecting", "Conectando...");
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      updateConnectionStatus("online", "Conectado");
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (err) {
        console.error("Erro ao decodificar JSON:", err);
      }
    };

    socket.onclose = () => {
      updateConnectionStatus("offline", "Desconectado");
      setTimeout(() => {
        if (modalEntry.style.display === "none") {
          connectWebSocket();
        }
      }, 3000);
    };

    socket.onerror = (err) => {
      console.error("Erro no WebSocket:", err);
      updateConnectionStatus("offline", "Erro");
    };
  }

  function updateConnectionStatus(status, text) {
    connDot.className = "pulse-dot " + (status === "online" ? "online" : "offline");
    connText.textContent = text;
  }

  function sendSocketMessage(type, payload = {}) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type, payload }));
    }
  }

  // ── Despacho de Mensagens ──────────────────────────────────────────────────
  function handleServerMessage(msg) {
    const { type, payload } = msg;

    if (type === "STATE_UPDATE") {
      checkDamageEvents(payload);
      gameState = payload;
      updateUI();
    } else if (type === "ACTION_REJECTED") {
      playAudio("miss");
      alert(`⚠️ Comando recusado: ${payload.motivo || "Ação inválida."}`);
    } else if (type === "ERROR") {
      alert(`🚨 Erro: ${payload.mensagem || "Erro no servidor."}`);
    }
  }

  // Detecta alterações de HP para criar textos flutuantes e sons
  function checkDamageEvents(newState) {
    if (!gameState) return;

    (newState.enemies || []).forEach((ini) => {
      const oldHp = lastEnemyHp[ini.id];
      if (oldHp !== undefined && ini.hp_atual < oldHp) {
        const diff = oldHp - ini.hp_atual;
        playAudio("hit");
        floatingTexts.push({
          text: `-${diff}`,
          x: ini.pos_x,
          y: ini.pos_y,
          color: "#ef4444",
          alpha: 1.0,
          vy: -0.02,
          timer: 60,
        });
      }
      lastEnemyHp[ini.id] = ini.hp_atual;
    });

    (newState.heroes || []).forEach((h) => {
      const oldHp = lastHeroHp[h.player_id];
      if (oldHp !== undefined && h.hp_atual < oldHp) {
        const diff = oldHp - h.hp_atual;
        playAudio("damage");
        floatingTexts.push({
          text: `-${diff}`,
          x: h.pos_x,
          y: h.pos_y,
          color: "#f87171",
          alpha: 1.0,
          vy: -0.02,
          timer: 60,
        });
      }
      lastHeroHp[h.player_id] = h.hp_atual;
    });
  }

  // ── Atualização da UI ──────────────────────────────────────────────────────
  function updateUI() {
    if (!gameState) return;

    displayRoomCode.textContent = gameState.room_id || roomId;
    displayPhase.textContent = formatPhaseName(gameState.fase);
    displayRound.textContent = `R${gameState.round || 1}`;

    if (gameState.recursos) {
      resMadeira.textContent = gameState.recursos.madeira || 0;
      resMetal.textContent = gameState.recursos.metal || 0;
      resCristal.textContent = gameState.recursos.cristal || 0;
    }

    if (gameState.sinergia_ativa) {
      synergyBanner.style.display = "block";
      synergyText.textContent = gameState.sinergia_ativa.mensagem || "SINCRONIA DE EQUIPE ATIVA!";
    } else {
      synergyBanner.style.display = "none";
    }

    if (gameState.fase === "LOBBY") {
      lobbyView.style.display = "block";
      combatView.style.display = "none";
      renderLobby();
    } else {
      lobbyView.style.display = "none";
      combatView.style.display = "block";
      renderCombat();
    }
  }

  function formatPhaseName(fase) {
    switch (fase) {
      case "LOBBY": return "LOBBY";
      case "SELECAO_CARTAS": return "SINCRONIA (CARTAS)";
      case "ACAO_LIVRE": return "AÇÃO LIVRE";
      case "VITORIA": return "🏆 VITÓRIA!";
      case "DERROTA": return "💀 DERROTA!";
      default: return fase;
    }
  }

  // ── Renderização do Lobby ──────────────────────────────────────────────────
  function renderLobby() {
    heroesGrid.innerHTML = "";
    const takenHeroes = {};
    let mySelectedHero = null;

    (gameState.heroes || []).forEach((h) => {
      if (h.hero_name) {
        takenHeroes[h.hero_name] = h.player_name;
        if (h.player_id === playerId) {
          mySelectedHero = h.hero_name;
        }
      }
    });

    heroesCatalog.forEach((hero) => {
      const card = document.createElement("div");
      const isTaken = !!takenHeroes[hero.nome];
      const isMine = mySelectedHero === hero.nome;
      const spriteUrl = hero.sprite_url || ASSET_HERO_MAP[hero.nome] || "/assets/images/characters/heroes/Aquele.png";

      card.className = "hero-card" + (isMine ? " selected-by-me" : isTaken ? " taken" : "");
      card.innerHTML = `
        <div class="hero-card-header">
          <img src="${spriteUrl}" alt="${hero.nome}" class="hero-portrait" />
          <div>
            <div class="hero-name">${hero.nome}</div>
            <div class="hero-class">${hero.classe}</div>
          </div>
        </div>
        <div class="hero-stats">
          <span>❤️ HP: <b>${hero.hp_base || 50}</b></span>
          <span>🛡️ AC: <b>${hero.ac || 15}</b></span>
        </div>
        <div class="hero-desc">${hero.descricao || ""}</div>
        <div class="hero-skill">✨ ${hero.especial || "Habilidade Especial"}</div>
        <button class="btn-select-hero" ${isTaken && !isMine ? "disabled" : ""}>
          ${isMine ? "✓ SEU CAMPEÃO" : isTaken ? `Ocupado por ${takenHeroes[hero.nome]}` : "ESCOLHER HERÓI"}
        </button>
      `;

      if (!isTaken || isMine) {
        const btn = card.querySelector(".btn-select-hero");
        btn.addEventListener("click", () => {
          playAudio("click");
          sendSocketMessage("SELECT_HERO", { hero_name: hero.nome });
        });
      }

      heroesGrid.appendChild(card);
    });

    rosterList.innerHTML = "";
    let allReady = (gameState.heroes || []).length > 0;

    (gameState.heroes || []).forEach((p) => {
      const row = document.createElement("div");
      row.className = "roster-card";
      const hasHero = !!p.hero_name;
      if (!hasHero) allReady = false;

      const pSprite = hasHero ? (ASSET_HERO_MAP[p.hero_name] || "/assets/images/characters/heroes/Aquele.png") : "";

      row.innerHTML = `
        <div class="roster-user">
          ${hasHero ? `<img src="${pSprite}" class="hero-portrait" style="width: 36px; height: 36px;" />` : `<span class="user-avatar">⏳</span>`}
          <div>
            <div style="font-weight: 700; font-size: 14px;">${p.player_name} ${p.player_id === playerId ? "(Você)" : ""}</div>
            <div style="font-size: 12px; color: var(--gold);">${p.hero_name ? `Herói: ${p.hero_name}` : "Escolhendo herói..."}</div>
          </div>
        </div>
        <span class="roster-badge ${hasHero ? "ready" : "pending"}">
          ${hasHero ? "Pronto" : "Aguardando"}
        </span>
      `;
      rosterList.appendChild(row);
    });

    btnStartGame.disabled = !allReady;
  }

  // ── Renderização do Combate ────────────────────────────────────────────────
  function renderCombat() {
    const myHero = (gameState.heroes || []).find((h) => h.player_id === playerId);
    if (myHero) {
      apMov.textContent = myHero.pontos_movimento || 0;
      apTrab.textContent = myHero.pontos_trabalho || 0;
      apEsc.textContent = myHero.pontos_escavacao || 0;
    }

    btnEndTurn.style.display = gameState.fase === "ACAO_LIVRE" ? "inline-block" : "none";

    renderCardsHand(myHero);
    renderTeamRoster();
    renderCombatLog();
  }

  // ── Mão de Cartas ──────────────────────────────────────────────────────────
  function renderCardsHand(myHero) {
    cardsHand.innerHTML = "";
    if (!myHero) return;

    if (gameState.fase === "SELECAO_CARTAS") {
      handTip.textContent = myHero.card_locked
        ? "🔒 Carta travada! Aguardando a equipe para sincronizar os bônus..."
        : "🃏 Turno de Sincronia: Escolha 1 carta para travar a sinergia.";
    } else {
      handTip.textContent = "⚔️ Fase de Ação Livre: Mova, ataque inimigos ou escave rochas no tabuleiro.";
    }

    (myHero.hand || []).forEach((carta, idx) => {
      const cardEl = document.createElement("div");
      const isLocked = myHero.card_locked;
      cardEl.className = "tactical-card" + (isLocked ? " locked" : "");

      const mov = carta.movimento || 0;
      const trab = carta.trabalho || 0;
      const esc = carta.escavacao || 0;

      cardEl.innerHTML = `
        <div class="card-title">${carta.nome || "Carta Tática"}</div>
        <div class="card-badges">
          ${mov > 0 ? `<span class="badge-chip badge-mov">🏃 +${mov}</span>` : ""}
          ${trab > 0 ? `<span class="badge-chip badge-trab">🔨 +${trab}</span>` : ""}
          ${esc > 0 ? `<span class="badge-chip badge-esc">⛏️ +${esc}</span>` : ""}
        </div>
        <div class="card-desc">${carta.descricao || "Manobra de combate."}</div>
        ${gameState.fase === "SELECAO_CARTAS" && !isLocked ? `
          <button class="btn-lock-card">TRAVAR CARTA</button>
        ` : ""}
      `;

      if (gameState.fase === "SELECAO_CARTAS" && !isLocked) {
        const btn = cardEl.querySelector(".btn-lock-card");
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          playAudio("click");
          sendSocketMessage("SELECT_CARD", { card_idx: idx });
        });
      }

      cardsHand.appendChild(cardEl);
    });
  }

  // ── Roster de Aliados no Combate ───────────────────────────────────────────
  function renderTeamRoster() {
    combatTeamRoster.innerHTML = "";
    (gameState.heroes || []).forEach((h) => {
      const card = document.createElement("div");
      const isMe = h.player_id === playerId;
      card.className = "ally-card" + (isMe ? " is-me" : "");

      const hpPercent = Math.max(0, Math.min(100, Math.round((h.hp_atual / h.hp_max) * 100)));
      const isLow = hpPercent < 30;
      const spriteUrl = ASSET_HERO_MAP[h.hero_name] || "/assets/images/characters/heroes/Aquele.png";

      card.innerHTML = `
        <div class="ally-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <img src="${spriteUrl}" class="hero-portrait" style="width: 30px; height: 30px;" />
            <span><b>${h.player_name}</b> (${h.hero_name || "Herói"})</span>
          </div>
          <span style="font-size: 11px;">${h.hp_atual}/${h.hp_max} HP</span>
        </div>
        <div class="hp-bar-bg">
          <div class="hp-bar-fill ${isLow ? "low" : ""}" style="width: ${hpPercent}%;"></div>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); display: flex; justify-content: space-between;">
          <span>🏃 Passos: ${h.pontos_movimento || 0}</span>
          <span>🃏 Cartas: ${h.cards_count || 0}</span>
          <span>${h.card_locked ? "🔒 Travado" : "⏳"}</span>
        </div>
      `;
      combatTeamRoster.appendChild(card);
    });
  }

  function renderCombatLog() {
    combatLog.innerHTML = "";
    (gameState.combat_log || []).forEach((item) => {
      const line = document.createElement("div");
      line.className = "log-line";
      line.style.color = item.cor || "#cbd5e1";
      line.innerHTML = `<span class="author" style="color: ${item.cor || "#fbbf24"}">[${item.autor}]</span> ${item.texto}`;
      combatLog.appendChild(line);
    });
    combatLog.scrollTop = combatLog.scrollHeight;
  }

  function sendChatMessage() {
    const text = chatInput.value.trim();
    if (text) {
      sendSocketMessage("CHAT_MESSAGE", { text });
      chatInput.value = "";
    }
  }

  function copyInviteLink() {
    const url = `${window.location.origin}/coop/?room=${roomId}`;
    navigator.clipboard.writeText(url).then(() => {
      alert("📋 Link copiado com sucesso!");
    }).catch(() => {
      prompt("Copie o link de convite:", url);
    });
  }

  // ── RenderLoop Contínuo (Canvas 20x20 & Animações 60fps) ───────────────────
  function renderLoop() {
    animTimer += 0.05;
    renderBoard();
    updateFloatingTexts();
    requestAnimationFrame(renderLoop);
  }

  function updateFloatingTexts() {
    for (let i = floatingTexts.length - 1; i >= 0; i--) {
      const ft = floatingTexts[i];
      ft.y += ft.vy;
      ft.timer -= 1;
      ft.alpha = Math.max(0, ft.timer / 60);
      if (ft.timer <= 0) {
        floatingTexts.splice(i, 1);
      }
    }
  }

  // ── Renderizador do Tabuleiro (Texturas e Sprites Oficiais) ─────────────────
  function renderBoard() {
    if (!ctx || !gameState || gameState.fase === "LOBBY") return;

    const width = boardCanvas.width;
    const height = boardCanvas.height;
    const tileSize = width / GRID_SIZE;

    ctx.clearRect(0, 0, width, height);

    const terrainGrid = gameState.grid_terreno || [];
    const myHero = (gameState.heroes || []).find((h) => h.player_id === playerId);

    // 1. Desenha as texturas do terreno
    for (let y = 0; y < GRID_SIZE; y++) {
      for (let x = 0; x < GRID_SIZE; x++) {
        const px = x * tileSize;
        const py = y * tileSize;
        const t = terrainGrid[y] ? terrainGrid[y][x] : TERRENO_NORMAL;

        const textureUrl = ASSET_TERRENO_MAP[t] || ASSET_TERRENO_MAP[TERRENO_NORMAL];
        const textureImg = getImage(textureUrl);

        if (textureImg && textureImg.complete && textureImg.naturalWidth > 0) {
          ctx.drawImage(textureImg, px, py, tileSize, tileSize);
        } else {
          // Fallback de cor
          ctx.fillStyle = (x + y) % 2 === 0 ? "#0f172a" : "#131c31";
          ctx.fillRect(px, py, tileSize, tileSize);
        }

        // Borda sutil de célula tática
        ctx.strokeStyle = "rgba(0, 0, 0, 0.25)";
        ctx.lineWidth = 1;
        ctx.strokeRect(px, py, tileSize, tileSize);
      }
    }

    // 2. Indicadores de Alcance de Movimento (se for meu turno na AÇÃO LIVRE)
    if (myHero && gameState.fase === "ACAO_LIVRE" && myHero.pontos_movimento > 0) {
      const movRange = myHero.pontos_movimento;
      const pulseAlpha = 0.15 + 0.1 * Math.sin(animTimer * 2);

      for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
          const dist = Math.abs(x - myHero.pos_x) + Math.abs(y - myHero.pos_y);
          if (dist > 0 && dist <= movRange) {
            const t = terrainGrid[y] ? terrainGrid[y][x] : TERRENO_NORMAL;
            if (t !== TERRENO_PAREDE) {
              ctx.fillStyle = `rgba(56, 189, 248, ${pulseAlpha})`;
              ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
            }
          }
        }
      }
    }

    // 3. Realce de Hover com Pulso
    if (hoveredTile.x >= 0 && hoveredTile.y >= 0) {
      const hx = hoveredTile.x * tileSize;
      const hy = hoveredTile.y * tileSize;
      const pulse = 0.5 + 0.5 * Math.sin(animTimer * 3);

      ctx.strokeStyle = `rgba(245, 158, 11, ${0.4 + 0.6 * pulse})`;
      ctx.lineWidth = 2;
      ctx.strokeRect(hx + 1, hy + 1, tileSize - 2, tileSize - 2);
    }

    // 4. Desenha Invasores Isectum (Sprites Reais)
    (gameState.enemies || []).forEach((ini) => {
      if (ini.hp_atual <= 0) return;
      const ix = ini.pos_x * tileSize;
      const iy = ini.pos_y * tileSize;

      // Sombra e base vermelha de ameaça
      drawUnitBase(ix + tileSize / 2, iy + tileSize * 0.85, tileSize * 0.38, "rgba(239, 68, 68, 0.6)");

      // Sprite oficial do inseto
      const enemySpriteUrl = ini.sprite_url || ASSET_ENEMY_MAP[ini.tipo] || ASSET_ENEMY_MAP.default;
      const enemyImg = getImage(enemySpriteUrl);

      if (enemyImg && enemyImg.complete && enemyImg.naturalWidth > 0) {
        ctx.drawImage(enemyImg, ix + 4, iy + 2, tileSize - 8, tileSize - 8);
      } else {
        ctx.font = "20px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("🐛", ix + tileSize / 2, iy + tileSize / 2);
      }

      // Barra de Vida e Nome da Casta
      drawUnitHpBar(ix, iy + tileSize - 4, tileSize, ini.hp_atual, ini.hp_max, "#ef4444");
      drawUnitName(ini.tipo || ini.nome, ix + tileSize / 2, iy - 2, "#fca5a5");
    });

    // 5. Desenha Heróis da Equipe (Sprites Oficiais)
    (gameState.heroes || []).forEach((h) => {
      if (h.hp_atual <= 0) return;
      const hx = h.pos_x * tileSize;
      const hy = h.pos_y * tileSize;
      const isMe = h.player_id === playerId;

      // Base com anel dourado (is_me) ou ciano (aliados)
      const ringColor = isMe ? "rgba(245, 158, 11, 0.9)" : "rgba(56, 189, 248, 0.7)";
      drawUnitBase(hx + tileSize / 2, hy + tileSize * 0.85, tileSize * 0.4, ringColor);

      // Sprite oficial do herói
      const heroSpriteUrl = h.sprite_url || ASSET_HERO_MAP[h.hero_name] || "/assets/images/characters/heroes/Aquele.png";
      const heroImg = getImage(heroSpriteUrl);

      if (heroImg && heroImg.complete && heroImg.naturalWidth > 0) {
        ctx.drawImage(heroImg, hx + 3, hy + 2, tileSize - 6, tileSize - 6);
      } else {
        ctx.font = "20px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("🛡️", hx + tileSize / 2, hy + tileSize / 2);
      }

      // Barra de Vida e Nome do Jogador/Herói
      drawUnitHpBar(hx, hy + tileSize - 4, tileSize, h.hp_atual, h.hp_max, isMe ? "#10b981" : "#38bdf8");
      drawUnitName(h.hero_name || h.player_name, hx + tileSize / 2, hy - 2, isMe ? "#fef08a" : "#e2e8f0");
    });

    // 6. Textos de Combate Flutuantes (Dano, Cura, Crítico)
    floatingTexts.forEach((ft) => {
      ctx.save();
      ctx.globalAlpha = ft.alpha;
      ctx.font = "bold 15px 'Cinzel', serif";
      ctx.fillStyle = ft.color;
      ctx.shadowColor = "#000000";
      ctx.shadowBlur = 4;
      ctx.textAlign = "center";
      ctx.fillText(ft.text, ft.x * tileSize + tileSize / 2, ft.y * tileSize + tileSize * 0.3);
      ctx.restore();
    });
  }

  function drawUnitBase(cx, cy, radius, strokeColor) {
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(cx, cy, radius, radius * 0.45, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
    ctx.fill();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
  }

  function drawUnitHpBar(x, y, width, current, max, color) {
    const barW = width - 4;
    const barH = 4;
    const pct = Math.max(0, Math.min(1, current / max));

    // Borda preta dupla estilo retro
    ctx.fillStyle = "#020617";
    ctx.fillRect(x + 2, y, barW, barH);

    // Preenchimento de vida
    ctx.fillStyle = color;
    ctx.fillRect(x + 2, y, barW * pct, barH);

    // Contorno
    ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
    ctx.lineWidth = 0.7;
    ctx.strokeRect(x + 2, y, barW, barH);
  }

  function drawUnitName(name, cx, cy, color) {
    ctx.save();
    ctx.font = "bold 9px 'Inter', sans-serif";
    ctx.fillStyle = color;
    ctx.shadowColor = "#000000";
    ctx.shadowBlur = 3;
    ctx.textAlign = "center";
    ctx.fillText(name, cx, cy);
    ctx.restore();
  }

  // ── Interação com o Tabuleiro ──────────────────────────────────────────────
  function onCanvasMouseMove(e) {
    const rect = boardCanvas.getBoundingClientRect();
    const scaleX = boardCanvas.width / rect.width;
    const scaleY = boardCanvas.height / rect.height;

    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;

    const tileSize = boardCanvas.width / GRID_SIZE;
    const gx = Math.floor(mx / tileSize);
    const gy = Math.floor(my / tileSize);

    if (gx >= 0 && gx < GRID_SIZE && gy >= 0 && gy < GRID_SIZE) {
      hoveredTile = { x: gx, y: gy };
    } else {
      hoveredTile = { x: -1, y: -1 };
    }
  }

  function onCanvasClick(e) {
    if (!gameState || gameState.fase !== "ACAO_LIVRE") return;

    const myHero = (gameState.heroes || []).find((h) => h.player_id === playerId);
    if (!myHero || myHero.hp_atual <= 0) return;

    const tx = hoveredTile.x;
    const ty = hoveredTile.y;
    if (tx < 0 || ty < 0) return;

    // Alvo inimigo -> ATAQUE!
    const enemyAtTile = (gameState.enemies || []).find((ini) => ini.pos_x === tx && ini.pos_y === ty);
    if (enemyAtTile) {
      playAudio("attack");
      sendSocketMessage("ATTACK_TARGET", { target_x: tx, target_y: ty });
      return;
    }

    // Célula vazia -> MOVIMENTO!
    playAudio("click");
    sendSocketMessage("MOVE_HERO", { dest_x: tx, dest_y: ty });
  }

  function onCanvasDblClick(e) {
    if (!gameState || gameState.fase !== "ACAO_LIVRE") return;

    const tx = hoveredTile.x;
    const ty = hoveredTile.y;
    if (tx < 0 || ty < 0) return;

    // Ação de mineração/escavação
    playAudio("click");
    sendSocketMessage("WORK_ACTION", { target_x: tx, target_y: ty });
  }

})();
