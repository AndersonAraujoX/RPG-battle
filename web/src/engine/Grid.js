export const TERRAIN_TYPES = {
    NORMAL: { color: 'rgba(255,255,255,0.05)', cost: 1 },
    FOREST: { color: 'rgba(34, 197, 94, 0.1)', cost: 1.5 },
    DIFICIL: { color: 'rgba(245, 158, 11, 0.1)', cost: 2 },
    WALL: { color: 'rgba(0,0,0,0.5)', cost: Infinity },
    ICE: { color: 'rgba(56, 189, 248, 0.1)', cost: 1 },
    FIRE: { color: 'rgba(239, 68, 68, 0.1)', cost: 1 }
};

export class Grid {
    constructor(width = 20, height = 20) {
        this.width = width;
        this.height = height;
        this.cells = Array(height).fill().map(() => Array(width).fill('NORMAL'));
        this.characters = new Map(); // Map of "x,y" to character
    }

    setTerrain(x, y, type) {
        if (this.isValid(x, y)) this.cells[y][x] = type;
    }

    isValid(x, y) {
        return x >= 0 && x < this.width && y >= 0 && y < this.height;
    }

    getCharacterAt(x, y) {
        return this.characters.get(`${x},${y}`);
    }

    moveCharacter(char, x, y) {
        const oldKey = `${char.pos.x},${char.pos.y}`;
        this.characters.delete(oldKey);
        char.pos = { x, y };
        this.characters.set(`${x},${y}`, char);
    }

    getValidMoves(char) {
        const reachable = [];
        const visited = new Set();
        const queue = [{ x: char.pos.x, y: char.pos.y, cost: 0 }];
        visited.add(`${char.pos.x},${char.pos.y}`);

        while (queue.length > 0) {
            const { x, y, cost } = queue.shift();

            if (cost > 0) reachable.push({ x, y });

            const neighbors = [
                { dx: 0, dy: 1 }, { dx: 0, dy: -1 },
                { dx: 1, dy: 0 }, { dx: -1, dy: 0 },
                { dx: 1, dy: 1 }, { dx: 1, dy: -1 },
                { dx: -1, dy: 1 }, { dx: -1, dy: -1 }
            ];

            for (const { dx, dy } of neighbors) {
                const nx = x + dx;
                const ny = y + dy;
                const key = `${nx},${ny}`;

                if (this.isValid(nx, ny) && !visited.has(key)) {
                    const terrain = TERRAIN_TYPES[this.cells[ny][nx]];
                    const moveCost = terrain.cost;
                    
                    if (cost + moveCost <= char.velocidade && terrain.cost !== Infinity) {
                        // Check if occupied by another character
                        if (!this.getCharacterAt(nx, ny)) {
                            visited.add(key);
                            queue.push({ x: nx, y: ny, cost: cost + moveCost });
                        }
                    }
                }
            }
        }
        return reachable;
    }
    
    getDistance(a, b) {
        return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
    }
}
