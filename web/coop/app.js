/**
 * web/coop/app.js — Cliente Web Co-op em Tempo Real (RPG-battle)
 * 
 * Gerencia a conexão WebSocket com o servidor autoritativo,
 * renderização interativa do tabuleiro via Canvas API 20x20,
 * seleção de heróis no lobby, sincronia de cartas e chat tático.
 */

(function () {
  "use strict";

  // ── Constantes e Terrenos ──────────────────────────────────────────────────
  const TERRENO_NORMAL = 0;
  const TERRENO_FLORESTA = 1;
  const TERRENO_DIFICIL = 2;
  const TERRENO_PAREDE = 3;
  const TERRENO_ROCHA = 4;
  const TERRENO_BARRIL = 5;

  const GRID_SIZE = 20;

  // ── Estado do Cliente ──────────────────────────────────────────────────────
  let socket = null;
  let roomId = null;
  let playerId = "p_" + Math.random().toString(36).substring(2, 9);
  let playerName = "Aventureiro";
  let heroesCatalog = [];
  let gameState = null;
  let hoveredTile = { x: -1, y: -1 };
  let selectedTile = null;

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
    // Verifica parâmetros na URL (convite ?room=XYZ)
    const urlParams = new URLSearchParams(window.location.search);
    const roomParam = urlParams.get("room");
    if (roomParam) {
      inputRoomCode.value = roomParam.toUpperCase().trim();
    }

    // Carrega catálogo de heróis da API REST
    await fetchHeroesCatalog();

    // Eventos do Modal
    btnJoinRoom.addEventListener("click", handleJoinSubmit);
    inputRoomCode.addEventListener("keydown", (e) => e.key === "Enter" && handleJoinSubmit());
    inputPlayerName.addEventListener("keydown", (e) => e.key === "Enter" && handleJoinSubmit());

    // Eventos de Ação
    btnStartGame.addEventListener("click", () => sendSocketMessage("START_GAME"));
    btnEndTurn.addEventListener("click", () => sendSocketMessage("END_ROUND"));
    btnCopyInvite.addEventListener("click", copyInviteLink);

    // Eventos do Chat
    btnSendChat.addEventListener("click", sendChatMessage);
    chatInput.addEventListener("keydown", (e) => e.key === "Enter" && sendChatMessage());

    // Eventos do Canvas
    boardCanvas.addEventListener("mousemove", onCanvasMouseMove);
    boardCanvas.addEventListener("mouseleave", () => { hoveredTile = { x: -1, y: -1 }; renderBoard(); });
    boardCanvas.addEventListener("click", onCanvasClick);
    boardCanvas.addEventListener("dblclick", onCanvasDblClick);
  });

  // ── Carregar Heróis da API ─────────────────────────────────────────────────
  async function fetchHeroesCatalog() {
    try {
      const res = await fetch("/api/heroes");
      if (res.ok) {
        heroesCatalog = await res.json();
      }
    } catch (err) {
      console.warn("Não foi possível carregar heróis via REST, usando catálogo local:", err);
      heroesCatalog = [
        { nome: "Aquele", classe: "Guerreiro", icone: "🌑", hp_base: 50, ac: 16, descricao: "Guerreiro sombrio e resistente.", especial: "Ataque Furioso" },
        { nome: "Stark", classe: "Paladino", icone: "🛡️", hp_base: 60, ac: 18, descricao: "Bastião inabalável com escudos divinos.", especial: "Aura Protetora" },
        { nome: "Elden", classe: "Mago", icone: "✨", hp_base: 35, ac: 12, descricao: "Alcance estendido de até 8 células.", especial: "Chuva Arcana" },
        { nome: "Doom", classe: "Ladino", icone: "💀", hp_base: 42, ac: 15, descricao: "Golpes críticos letais e sombras.", especial: "Passo Sombrio" },
        { nome: "Gruu", classe: "Bárbaro", icone: "🪓", hp_base: 65, ac: 14, descricao: "Fúria implacável e grande vitalidade.", especial: "Fúria Bárbara" },
        { nome: "Kuro", classe: "Ladino", icone: "🗡️", hp_base: 40, ac: 15, descricao: "Ágil nas armadilhas e movimentação.", especial: "Truques Ágeis" },
        { nome: "Darwin", classe: "Druida", icone: "🌿", hp_base: 48, ac: 14, descricao: "Especialista em escavação e terreno.", especial: "Raízes Primais" }
      ];
    }
  }

  // ── Conexão WebSocket ──────────────────────────────────────────────────────
  function handleJoinSubmit() {
    const pName = inputPlayerName.value.trim() || "Aventureiro";
    let rCode = inputRoomCode.value.trim().toUpperCase();

    if (!rCode) {
      // Gera código aleatório de 6 caracteres se vazio
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
        console.error("Erro ao decodificar mensagem do servidor:", err);
      }
    };

    socket.onclose = () => {
      updateConnectionStatus("offline", "Desconectado");
      setTimeout(() => {
        if (modalEntry.style.display === "none") {
          console.log("Tentando reconectar...");
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
    } else {
      console.warn("Socket não está aberto para enviar:", type);
    }
  }

  // ── Despachante de Mensagens do Servidor ────────────────────────────────────
  function handleServerMessage(msg) {
    const { type, payload } = msg;

    if (type === "STATE_UPDATE") {
      gameState = payload;
      updateUI();
    } else if (type === "ACTION_REJECTED") {
      alert(`⚠️ Ação rejeitada: ${payload.motivo || "Comando inválido."}`);
    } else if (type === "ERROR") {
      alert(`🚨 Erro do servidor: ${payload.mensagem || "Falha desconhecida."}`);
    }
  }

  // ── Atualização Geral da Interface ─────────────────────────────────────────
  function updateUI() {
    if (!gameState) return;

    // Header Status
    displayRoomCode.textContent = gameState.room_id || roomId;
    displayPhase.textContent = formatPhaseName(gameState.fase);
    displayRound.textContent = `R${gameState.round || 1}`;

    if (gameState.recursos) {
      resMadeira.textContent = gameState.recursos.madeira || 0;
      resMetal.textContent = gameState.recursos.metal || 0;
      resCristal.textContent = gameState.recursos.cristal || 0;
    }

    // Sinergia Banner
    if (gameState.sinergia_ativa) {
      synergyBanner.style.display = "block";
      synergyText.textContent = gameState.sinergia_ativa.mensagem || "SINCRONIA ATIVA!";
    } else {
      synergyBanner.style.display = "none";
    }

    // Alterna Visão: Lobby vs Combate
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
    // Renderiza Cards de Heróis
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

      card.className = "hero-card" + (isMine ? " selected-by-me" : isTaken ? " taken" : "");
      card.innerHTML = `
        <div class="hero-card-header">
          <div class="hero-icon">${hero.icone || "🛡️"}</div>
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
          sendSocketMessage("SELECT_HERO", { hero_name: hero.nome });
        });
      }

      heroesGrid.appendChild(card);
    });

    // Renderiza Lista de Jogadores
    rosterList.innerHTML = "";
    let allReady = (gameState.heroes || []).length > 0;

    (gameState.heroes || []).forEach((p) => {
      const row = document.createElement("div");
      row.className = "roster-card";
      const hasHero = !!p.hero_name;
      if (!hasHero) allReady = false;

      row.innerHTML = `
        <div class="roster-user">
          <span class="user-avatar">${hasHero ? "🛡️" : "⏳"}</span>
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
    // Acha meus dados
    const myHero = (gameState.heroes || []).find((h) => h.player_id === playerId);
    if (myHero) {
      apMov.textContent = myHero.pontos_movimento || 0;
      apTrab.textContent = myHero.pontos_trabalho || 0;
      apEsc.textContent = myHero.pontos_escavacao || 0;
    }

    // Botão de encerrar ações só é útil na fase ACAO_LIVRE
    btnEndTurn.style.display = gameState.fase === "ACAO_LIVRE" ? "inline-block" : "none";

    renderCardsHand(myHero);
    renderTeamRoster();
    renderCombatLog();
    renderBoard();
  }

  // ── Mão de Cartas & Seleção ────────────────────────────────────────────────
  function renderCardsHand(myHero) {
    cardsHand.innerHTML = "";
    if (!myHero) return;

    if (gameState.fase === "SELECAO_CARTAS") {
      handTip.textContent = myHero.card_locked
        ? "🔒 Carta travada! Aguardando os demais heróis escolherem..."
        : "🃏 Turno de Sincronia: Escolha 1 carta para travar a sinergia.";
    } else {
      handTip.textContent = "⚔️ Fase de Ação Livre: Mova, ataque ou escave rochas no tabuleiro.";
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
        <div class="card-desc">${carta.descricao || "Ação tática de cerco."}</div>
        ${gameState.fase === "SELECAO_CARTAS" && !isLocked ? `
          <button class="btn-lock-card">TRAVAR CARTA</button>
        ` : ""}
      `;

      if (gameState.fase === "SELECAO_CARTAS" && !isLocked) {
        const btn = cardEl.querySelector(".btn-lock-card");
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          sendSocketMessage("SELECT_CARD", { card_idx: idx });
        });
      }

      cardsHand.appendChild(cardEl);
    });
  }

  // ── Roster de Aliados na Batalha ───────────────────────────────────────────
  function renderTeamRoster() {
    combatTeamRoster.innerHTML = "";
    (gameState.heroes || []).forEach((h) => {
      const card = document.createElement("div");
      const isMe = h.player_id === playerId;
      card.className = "ally-card" + (isMe ? " is-me" : "");

      const hpPercent = Math.max(0, Math.min(100, Math.round((h.hp_atual / h.hp_max) * 100)));
      const isLow = hpPercent < 30;

      card.innerHTML = `
        <div class="ally-header">
          <span><b>${h.player_name}</b> (${h.hero_name || "Herói"})</span>
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

  // ── Log de Combate e Chat ──────────────────────────────────────────────────
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
      alert("📋 Link de convite copiado para a área de transferência!");
    }).catch(() => {
      prompt("Copie o link de convite:", url);
    });
  }

  // ── Renderizador do Tabuleiro Canvas 20x20 ─────────────────────────────────
  function renderBoard() {
    if (!ctx || !gameState) return;

    const width = boardCanvas.width;
    const height = boardCanvas.height;
    const tileSize = width / GRID_SIZE;

    // Fundo limpo
    ctx.clearRect(0, 0, width, height);

    const terrainGrid = gameState.grid_terreno || [];

    // Desenha terrenos
    for (let y = 0; y < GRID_SIZE; y++) {
      for (let x = 0; x < GRID_SIZE; x++) {
        const px = x * tileSize;
        const py = y * tileSize;
        const t = terrainGrid[y] ? terrainGrid[y][x] : TERRENO_NORMAL;

        // Cor de base do terreno
        if (t === TERRENO_PAREDE) {
          ctx.fillStyle = "#334155";
        } else if (t === TERRENO_ROCHA) {
          ctx.fillStyle = "#475569";
        } else if (t === TERRENO_FLORESTA) {
          ctx.fillStyle = "#064e3b";
        } else if (t === TERRENO_BARRIL) {
          ctx.fillStyle = "#78350f";
        } else {
          // Normal: padrão xadrez suave
          ctx.fillStyle = (x + y) % 2 === 0 ? "#0f172a" : "#131c31";
        }
        ctx.fillRect(px, py, tileSize, tileSize);

        // Grade suave
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        ctx.strokeRect(px, py, tileSize, tileSize);

        // Símbolos de terreno especial
        if (t === TERRENO_PAREDE) {
          drawEmoji(px + tileSize / 2, py + tileSize / 2, "🧱", 16);
        } else if (t === TERRENO_ROCHA) {
          drawEmoji(px + tileSize / 2, py + tileSize / 2, "🪨", 16);
        } else if (t === TERRENO_FLORESTA) {
          drawEmoji(px + tileSize / 2, py + tileSize / 2, "🌲", 16);
        } else if (t === TERRENO_BARRIL) {
          drawEmoji(px + tileSize / 2, py + tileSize / 2, "🛢️", 16);
        }
      }
    }

    // Realce de Hover
    if (hoveredTile.x >= 0 && hoveredTile.y >= 0) {
      ctx.fillStyle = "rgba(56, 189, 248, 0.25)";
      ctx.fillRect(hoveredTile.x * tileSize, hoveredTile.y * tileSize, tileSize, tileSize);
      ctx.strokeStyle = "rgba(56, 189, 248, 0.8)";
      ctx.lineWidth = 2;
      ctx.strokeRect(hoveredTile.x * tileSize, hoveredTile.y * tileSize, tileSize, tileSize);
    }

    // Desenha Inimigos
    (gameState.enemies || []).forEach((ini) => {
      const ix = ini.pos_x * tileSize;
      const iy = ini.pos_y * tileSize;

      // Aura vermelha
      ctx.fillStyle = "rgba(239, 68, 68, 0.2)";
      ctx.beginPath();
      ctx.arc(ix + tileSize / 2, iy + tileSize / 2, tileSize * 0.45, 0, Math.PI * 2);
      ctx.fill();

      // Emoji do inseto
      let emoji = "🐛";
      if (ini.tipo && ini.tipo.includes("Guerreiro")) emoji = "🐝";
      if (ini.tipo && ini.tipo.includes("Explorador")) emoji = "🦗";
      if (ini.tipo && ini.tipo.includes("Trabalhador")) emoji = "🐜";

      drawEmoji(ix + tileSize / 2, iy + tileSize / 2, emoji, 20);

      // Mini barra de vida do inimigo
      drawMiniHpBar(ix, iy + tileSize - 5, tileSize, ini.hp_atual, ini.hp_max, "#ef4444");
    });

    // Desenha Heróis da Equipe
    (gameState.heroes || []).forEach((h) => {
      if (h.hp_atual <= 0) return;
      const hx = h.pos_x * tileSize;
      const hy = h.pos_y * tileSize;
      const isMe = h.player_id === playerId;

      // Círculo base do herói
      ctx.fillStyle = isMe ? "rgba(245, 158, 11, 0.3)" : "rgba(56, 189, 248, 0.25)";
      ctx.beginPath();
      ctx.arc(hx + tileSize / 2, hy + tileSize / 2, tileSize * 0.45, 0, Math.PI * 2);
      ctx.fill();

      // Borda do herói
      ctx.strokeStyle = isMe ? "#f59e0b" : "#38bdf8";
      ctx.lineWidth = isMe ? 3 : 1.5;
      ctx.stroke();

      // Ícone do Herói
      let icon = "🛡️";
      if (h.hero_name === "Aquele") icon = "🌑";
      if (h.hero_name === "Elden") icon = "✨";
      if (h.hero_name === "Doom") icon = "💀";
      if (h.hero_name === "Gruu") icon = "🪓";
      if (h.hero_name === "Kuro") icon = "🗡️";
      if (h.hero_name === "Darwin") icon = "🌿";

      drawEmoji(hx + tileSize / 2, hy + tileSize / 2 - 2, icon, 18);

      // Mini barra de vida do herói
      drawMiniHpBar(hx, hy + tileSize - 5, tileSize, h.hp_atual, h.hp_max, "#10b981");

      // Nome do herói flutuante
      ctx.font = "bold 9px Inter, sans-serif";
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.fillText(h.hero_name || h.player_name, hx + tileSize / 2, hy - 3);
    });
  }

  function drawEmoji(cx, cy, emoji, size = 18) {
    ctx.font = `${size}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(emoji, cx, cy);
  }

  function drawMiniHpBar(x, y, width, current, max, color) {
    const barW = width - 4;
    const barH = 3;
    const pct = Math.max(0, Math.min(1, current / max));

    ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
    ctx.fillRect(x + 2, y, barW, barH);

    ctx.fillStyle = color;
    ctx.fillRect(x + 2, y, barW * pct, barH);
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
    renderBoard();
  }

  function onCanvasClick(e) {
    if (!gameState || gameState.fase !== "ACAO_LIVRE") {
      return;
    }

    const myHero = (gameState.heroes || []).find((h) => h.player_id === playerId);
    if (!myHero || myHero.hp_atual <= 0) return;

    const tx = hoveredTile.x;
    const ty = hoveredTile.y;
    if (tx < 0 || ty < 0) return;

    // Checa se clicou em um Invasor inimigo -> ATAQUE!
    const enemyAtTile = (gameState.enemies || []).find((ini) => ini.pos_x === tx && ini.pos_y === ty);
    if (enemyAtTile) {
      sendSocketMessage("ATTACK_TARGET", { target_x: tx, target_y: ty });
      return;
    }

    // Caso contrário, tenta mover para a célula desimpedida -> MOVIMENTO!
    sendSocketMessage("MOVE_HERO", { dest_x: tx, dest_y: ty });
  }

  function onCanvasDblClick(e) {
    if (!gameState || gameState.fase !== "ACAO_LIVRE") return;

    const tx = hoveredTile.x;
    const ty = hoveredTile.y;
    if (tx < 0 || ty < 0) return;

    // Ação de escavação/mineração
    sendSocketMessage("WORK_ACTION", { target_x: tx, target_y: ty });
  }

})();
