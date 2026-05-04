import { Grid } from './Grid.js';

export class CombatEngine {
    constructor() {
        this.grid = new Grid();
        this.combatentes = [];
        this.ordemCombate = [];
        this.turnoIdx = 0;
        this.rodada = 1;
        this.logger = null;
        this.onUpdate = null;
    }

    setLogger(callback) {
        this.logger = callback;
    }

    adicionarCombatente(char, x, y) {
        char.pos = { x, y };
        this.combatentes.push(char);
        this.grid.characters.set(`${x},${y}`, char);
    }

    iniciarCombate() {
        this.combatentes.forEach(c => c.rolarIniciativa());
        this.ordemCombate = [...this.combatentes].sort((a, b) => b.iniciativa - a.iniciativa);
        this.turnoIdx = 0;
        this.rodada = 1;
        this.log(`Combate iniciado! Rodada ${this.rodada}`, 'system');
        this.logIniciativa();
    }

    logIniciativa() {
        this.ordemCombate.forEach(c => {
            this.log(`${c.nome}: Iniciativa ${c.iniciativa}`, 'system');
        });
    }

    get combatenteAtual() {
        return this.ordemCombate[this.turnoIdx];
    }

    proximoTurno() {
        this.combatenteAtual.tick();
        this.turnoIdx++;
        if (this.turnoIdx >= this.ordemCombate.length) {
            this.turnoIdx = 0;
            this.rodada++;
            this.log(`--- RODADA ${this.rodada} ---`, 'system');
        }
        
        if (!this.combatenteAtual.vivo) {
            return this.proximoTurno();
        }
        
        this.log(`Vez de ${this.combatenteAtual.nome}`, 'system');
        if (this.onUpdate) this.onUpdate();
    }

    log(msg, type = '') {
        if (this.logger) this.logger(msg, type);
    }

    verificarVitoria() {
        const vivosA = this.combatentes.filter(c => c.time === 'A' && c.vivo).length;
        const vivosB = this.combatentes.filter(c => c.time === 'B' && c.vivo).length;
        
        if (vivosA === 0) return 'Time B';
        if (vivosB === 0) return 'Time A';
        return null;
    }
}
