import { CombatEngine } from './src/engine/CombatEngine.js';
import { Character } from './src/engine/Character.js';

const engine = new CombatEngine();
const boardEl = document.getElementById('board');
const logEl = document.getElementById('combat-log');
const charInfoEl = document.getElementById('character-info');
const roundNumEl = document.getElementById('round-number');

let selectedAction = null;
let validTiles = [];

// Initialize Board
function initBoard() {
    boardEl.innerHTML = '';
    for (let y = 0; y < 20; y++) {
        for (let x = 0; x < 20; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.addEventListener('click', () => handleCellClick(x, y));
            cell.addEventListener('mouseenter', () => updateStatus(x, y));
            boardEl.appendChild(cell);
        }
    }
}

function render() {
    // Clear tokens
    document.querySelectorAll('.token').forEach(t => t.remove());
    document.querySelectorAll('.cell').forEach(c => {
        c.classList.remove('valid-move', 'valid-attack');
    });

    // Render characters
    engine.combatentes.forEach(char => {
        if (!char.vivo) return;
        const cell = document.querySelector(`.cell[data-x="${char.pos.x}"][data-y="${char.pos.y}"]`);
        const token = document.createElement('div');
        token.className = `token team-${char.time.toLowerCase()} ${char === engine.combatenteAtual ? 'active' : ''}`;
        token.innerText = char.nome[0];
        cell.appendChild(token);
    });

    // Render valid actions
    validTiles.forEach(({x, y}) => {
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (selectedAction === 'move') cell.classList.add('valid-move');
        if (selectedAction === 'attack') cell.classList.add('valid-attack');
    });

    // Update UI
    roundNumEl.innerText = engine.rodada;
    updateCharacterInfo(engine.combatenteAtual);
    updateControls();
}

function handleCellClick(x, y) {
    const char = engine.combatenteAtual;
    
    if (selectedAction === 'move') {
        if (validTiles.some(t => t.x === x && t.y === y)) {
            engine.grid.moveCharacter(char, x, y);
            engine.log(`${char.nome} se moveu para (${x}, ${y})`);
            selectedAction = null;
            validTiles = [];
            render();
        }
    } else if (selectedAction === 'attack') {
        const target = engine.grid.getCharacterAt(x, y);
        if (target && target.time !== char.time) {
            const dist = engine.grid.getDistance(char.pos, {x, y});
            if (dist <= char.alcance) {
                executeAttack(char, target);
                selectedAction = null;
                validTiles = [];
                render();
            }
        }
    }
}

function executeAttack(attacker, target) {
    const d20 = Math.floor(Math.random() * 20) + 1;
    const attackRoll = d20 + attacker.getMod(attacker.stats.forca || 10) + 2; // +2 proficiency approx
    
    if (attackRoll >= target.ac) {
        const dmg = Math.floor(Math.random() * attacker.dadoDano[1]) + 1 + attacker.getMod(attacker.stats.forca || 10);
        target.receberDano(dmg);
        engine.log(`${attacker.nome} ACERTOU ${target.nome} com ${attackRoll} vs ${target.ac} (Dano: ${dmg})`, 'success');
        if (!target.vivo) engine.log(`${target.nome} foi DERROTADO!`, 'critical');
    } else {
        engine.log(`${attacker.nome} ERROU ${target.nome} com ${attackRoll} vs ${target.ac}`, 'damage');
    }
    
    const win = engine.verificarVitoria();
    if (win) {
        alert(`${win} venceu!`);
        location.reload();
    }
}

function updateCharacterInfo(char) {
    if (!char) return;
    charInfoEl.innerHTML = `
        <h4>${char.nome} (${char.classe})</h4>
        <div class="stat-row">HP: ${char.hpAtual} / ${char.hpMax}</div>
        <div class="stat-bar"><div class="bar-fill bar-hp" style="width: ${(char.hpAtual/char.hpMax)*100}%"></div></div>
        <div class="stat-row">${char.recursoNome}: ${char.recursoAtual} / ${char.recursoMax}</div>
        <div class="stat-bar"><div class="bar-fill bar-resource" style="width: ${(char.recursoAtual/char.recursoMax)*100}%"></div></div>
        <div class="stat-grid">
            <span>AC: ${char.ac}</span>
            <span>Mov: ${char.velocidade}</span>
        </div>
    `;
}

function updateControls() {
    const btnMove = document.getElementById('btn-move');
    const btnAttack = document.getElementById('btn-attack');
    const btnPass = document.getElementById('btn-pass');

    btnMove.disabled = false;
    btnAttack.disabled = false;
    btnPass.disabled = false;
}

// Event Listeners for Controls
document.getElementById('btn-move').addEventListener('click', () => {
    selectedAction = 'move';
    validTiles = engine.grid.getValidMoves(engine.combatenteAtual);
    render();
});

document.getElementById('btn-attack').addEventListener('click', () => {
    selectedAction = 'attack';
    // Simple logic: all characters are valid targets if in range
    validTiles = [];
    engine.combatentes.forEach(c => {
        if (c.vivo && c.time !== engine.combatenteAtual.time) {
            validTiles.push({x: c.pos.x, y: c.pos.y});
        }
    });
    render();
});

document.getElementById('btn-pass').addEventListener('click', () => {
    selectedAction = null;
    validTiles = [];
    engine.proximoTurno();
    render();
});

function updateStatus(x, y) {
    document.getElementById('coord-info').innerText = `X: ${x}, Y: ${y}`;
}

// Start Game
engine.setLogger((msg, type) => {
    const p = document.createElement('p');
    p.className = `log-entry ${type}`;
    p.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logEl.prepend(p);
});

engine.onUpdate = render;

// Setup initial characters for demo
const p1 = new Character("Guerreiro A", "Guerreiro", "A");
const p2 = new Character("Mago A", "Mago", "A");
const e1 = new Character("Inimigo 1", "Guerreiro", "B");
const e2 = new Character("Inimigo 2", "Ladino", "B");

engine.adicionarCombatente(p1, 2, 2);
engine.adicionarCombatente(p2, 2, 3);
engine.adicionarCombatente(e1, 15, 15);
engine.adicionarCombatente(e2, 15, 14);

initBoard();
engine.iniciarCombate();
render();
