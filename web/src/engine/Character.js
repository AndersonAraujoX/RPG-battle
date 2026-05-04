export const CLASS_DATA = {
    "Guerreiro": {
        stats: { forca: 16, constituicao: 14, destreza: 12 },
        dadoVida: 10, ac: 18, dadoDano: [1, 8],
        velocidade: 3, alcance: 1, tipoDano: "Cortante",
        recurso: "Nenhum", recursoMax: 0
    },
    "Mago": {
        stats: { inteligencia: 16, constituicao: 12, destreza: 14 },
        dadoVida: 6, ac: 10, dadoDano: [1, 6],
        velocidade: 3, alcance: 6, tipoDano: "Magico",
        recurso: "Mana", recursoMax: 20
    },
    "Ladino": {
        stats: { destreza: 16, constituicao: 12 },
        dadoVida: 8, ac: 12, dadoDano: [1, 6],
        velocidade: 4, alcance: 1, tipoDano: "Perfurante",
        recurso: "Energia", recursoMax: 20
    },
    "Arqueiro": {
        stats: { destreza: 16, constituicao: 12 },
        dadoVida: 10, ac: 15, dadoDano: [1, 8],
        velocidade: 4, alcance: 10, tipoDano: "Perfurante",
        recurso: "Energia", recursoMax: 15
    }
};

export class Character {
    constructor(nome, classe, time) {
        const data = CLASS_DATA[classe];
        this.nome = nome;
        this.classe = classe;
        this.time = time;
        this.stats = { ...data.stats };
        
        this.hpMax = data.dadoVida + this.getMod(this.stats.constituicao || 10);
        this.hpAtual = this.hpMax;
        this.ac = data.ac;
        this.velocidade = data.velocidade;
        this.alcance = data.alcance;
        this.tipoDano = data.tipoDano;
        this.dadoDano = data.dadoDano;
        
        this.recursoNome = data.recurso;
        this.recursoMax = data.recursoMax;
        this.recursoAtual = this.recursoMax;
        
        this.pos = { x: 0, y: 0 };
        this.iniciativa = 0;
        this.vivo = true;
        this.status = [];
        this.cooldowns = {};
    }

    getMod(score) {
        return Math.floor((score - 10) / 2);
    }

    rolarIniciativa() {
        const dex = this.stats.destreza || 10;
        this.iniciativa = Math.floor(Math.random() * 20) + 1 + this.getMod(dex);
        return this.iniciativa;
    }

    receberDano(valor, atacante, tipo) {
        this.hpAtual -= valor;
        if (this.hpAtual <= 0) {
            this.hpAtual = 0;
            this.vivo = false;
        }
        return valor;
    }

    receberCura(valor) {
        this.hpAtual = Math.min(this.hpMax, this.hpAtual + valor);
        return valor;
    }

    tick() {
        // Regeneração de recursos
        if (this.recursoNome !== "Nenhum") {
            this.recursoAtual = Math.min(this.recursoMax, this.recursoAtual + 2);
        }
        
        // Tick de cooldowns
        for (let skill in this.cooldowns) {
            if (this.cooldowns[skill] > 0) this.cooldowns[skill]--;
        }
    }
}
