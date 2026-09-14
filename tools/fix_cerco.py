"""Script para remover o bloco órfão no cerco_state.py entre linhas 992 e 1203."""
filepath = "src/states/cerco_state.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"Total linhas: {total}")
# Linhas 992-1203 = índices 991-1202 (0-indexed)
# Vamos checar o conteúdo primeiro
print("Linha 991 (992 no editor):", repr(lines[991]))
print("Linha 1202 (1203 no editor):", repr(lines[1202]))
print("Linha 1203 (1204 no editor):", repr(lines[1203]))

# Remove linhas 992 a 1203 (1-indexed) = índices 991 a 1202 inclusive
# Mas mantém linha 991 (índice 990) que é a linha em branco antes do método
new_lines = lines[:991] + lines[1203:]
print(f"Novas linhas: {len(new_lines)}")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Arquivo corrigido com sucesso!")
