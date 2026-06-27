import os
import json
import logging
from .utils import resource_path

class ChapterLoader:
    def __init__(self, base_dir="dados/fases"):
        self.base_dir = resource_path(base_dir)
        self.fases = []
        self._carregar_fases()

    def _carregar_fases(self):
        if not os.path.exists(self.base_dir):
            logging.warning(f"Diretório de fases não encontrado: {self.base_dir}")
            return

        # Listar subpastas
        subpastas = sorted([d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))])
        
        for pasta in subpastas:
            caminho = os.path.join(self.base_dir, pasta)
            try:
                fase = self._carregar_fase(caminho) # Renamed capitulo to fase, _carregar_capitulo to _carregar_fase
                if fase:
                    self.fases.append(fase) # Renamed capitulos to fases
                    if pasta == "fase_01":
                        print(f"Fase carregada: {fase['info'].get('titulo')} ({pasta})") # Renamed "Capítulo" to "Fase"
            except Exception as e:
                logging.error(f"Erro ao carregar fase {pasta}: {e}") # Renamed "capítulo" to "fase"

        # Ordenar por 'ordem' definida no info.json
        self.fases.sort(key=lambda c: c.get('info', {}).get('ordem', 999)) # Renamed capitulos to fases

    def _carregar_fase(self, caminho_pasta): # Renamed _carregar_capitulo to _carregar_fase
        # Carregar arquivos essenciais
        info_path = os.path.join(caminho_pasta, "info.json")
        batalha_path = os.path.join(caminho_pasta, "batalha.json")
        dialogo_path = os.path.join(caminho_pasta, "dialogo.json")
        mapa_path = os.path.join(caminho_pasta, "mapa.json")

        if not os.path.exists(info_path):
            return None # Ignora pastas sem info.json

        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)

        batalha = {}
        if os.path.exists(batalha_path):
            with open(batalha_path, 'r', encoding='utf-8') as f:
                batalha = json.load(f)

        dialogo = {}
        if os.path.exists(dialogo_path):
            with open(dialogo_path, 'r', encoding='utf-8') as f:
                dialogo = json.load(f)

        # Mapa: pode ser um arquivo local ou referência global
        mapa_arquivo = None # Default
        if os.path.exists(mapa_path):
             # Se existe mapa.json na pasta do capítulo, usamos o caminho relativo ou carrega o conteudo?
             # Para simplificar, vamos ler o conteudo se for json
             # Ou retornar o caminho absoluto para o MapLoader carregar
             mapa_arquivo = mapa_path
        
        return {
            "info": info,
            "batalha": batalha,
            "dialogo": dialogo,
            "mapa_path": mapa_arquivo,
            "path": caminho_pasta
        }

    def get_campaign_data(self):
        """Converte o formato de capítulos para o formato esperado pelo CampaignManager/Game"""
        campaign_list = []
        
        from .personagens import get_class_by_name # Helper necessario

        for cap in self.fases:
            batalha = cap.get('batalha', {})
            inimigos_data = batalha.get('inimigos', [])
            
            # Converter inimigos JSON -> Tuplas (Classe, Qtd) ou lógica mais complexa
            # O sistema atual em campanha.py usa (Classe, Qtd).
            # Mas o nosso JSON tem posições explícitas!
            # Vamos adaptar o Game para aceitar configuração mais detalhada ou adaptar aqui.
            # O ideal é o Game aceitar a lista detalhada.
            
            enemies_list = []
            simple_enemy_list = [] # Backwards compatibility for game.py (defaults to random pos)
            
            for enemy in inimigos_data:
                 cls = get_class_by_name(enemy['tipo'])
                 if cls:
                     qtd = enemy.get('qtd', 1)
                     enemies_list.append({
                         "classe": cls,
                         "qtd": qtd,
                         "pos": enemy.get('pos', [])
                     })
                     simple_enemy_list.append((cls, qtd))
            
            mission = {
                "id": cap['info'].get('id'),
                "titulo": cap['info'].get('titulo'),
                "inimigos": simple_enemy_list, # COMPATIBILITY: Required by game.iniciar_batalha
                "inimigos_detalhados": enemies_list, 
                "itens": batalha.get('itens', []),
                "mapa": cap['mapa_path'], # Game expects 'mapa' or 'mapa_file'? Campanha.py uses 'mapa'
                "mensagem_inicio": cap['info'].get('descricao', ""),
                "dialogo_inicio": self._converter_dialogo(cap['dialogo'].get('inicio', []))
            }
            campaign_list.append(mission)
            
        return campaign_list

    def _converter_dialogo(self, lista_dialogo):
        """Converte lista de dicts (JSON) para lista de tuplas (Sistema de Dialogo)"""
        dialogo_formatado = []
        for fala in lista_dialogo:
            # Esperado pelo Dialogo: (nome, texto, retrato_key)
            nome = fala.get('nome', "Desconhecido")
            texto = fala.get('texto', "...")
            retrato = fala.get('retrato', None)
            dialogo_formatado.append((nome, texto, retrato))
        return dialogo_formatado
