# SkyTale Build Calculator

Calculadora de builds para o jogo **SkyTale** (variação de Priston Tale). Permite montar combinações de equipamentos e visualizar em tempo real os atributos totais do personagem e os requisitos mínimos de status para equipar cada item.

## Funcionalidades

- Seleção de até 9 slots de equipamento (arma secundária, armadura, escudo, bracelete, luvas, botas, anéis e amuleto)
- Suporte a **raridades**: Normal, Raro, Épico e Lendário — cada uma aplica bônus diferentes por tipo de item
- Suporte a **especializações** (Mechanician, Fighter, Pikeman, Archer, Knight, Atalanta, Priestess, Mage, Shaman, Assassin, Guerriera) — ajustam os requisitos de força, inteligência, talento e agilidade
- Sistema de **envelhecimento (aging)** para armaduras, escudos e orbitais — incrementa defesa e absorção por nível
- Painel de **agregado total**: soma de atributos e maior requisito dentre todos os itens selecionados, atualizado em tempo real
- Interface visual com tema SkyTale, mostrando imagens dos itens e indicação colorida de raridade

## Tecnologias

- **Backend**: Python 3 + Flask
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Templates**: Jinja2
- **Banco de itens**: `items.json` (~542 KB, 17 categorias)

## Como executar

### Pré-requisitos

- Python 3.10+
- pip

### Instalação

```bash
pip install -r requirements.txt
```

### Rodando o servidor

```bash
python app.py
```

O servidor sobe em `http://localhost:10000` por padrão. A porta pode ser configurada pela variável de ambiente `PORT`:

```bash
PORT=8080 python app.py
```

### Baixando as imagens dos itens

As imagens dos itens são servidas da pasta `assets/items/`. Para baixá-las do servidor do jogo:

```bash
python download_assets.py
```

## Testes

```bash
python run_tests.py
```

Os testes cobrem a lógica de agregação de stats e requisitos, aplicação de raridades, especializações e aging.

## Estrutura do projeto

```
├── app.py                  # Aplicação Flask — rotas e carregamento dos itens
├── items.json              # Banco de dados de itens (17 categorias)
├── requirements.txt
├── run_tests.py            # Runner de testes
├── download_assets.py      # Utilitário para baixar imagens do jogo
├── templates/
│   └── index.html          # Interface web (Jinja2 + JS)
├── utils/
│   └── aggregate.py        # Lógica de agregação, raridade, spec e aging
├── tests/
│   └── test_aggregate.py
└── assets/
    └── items/              # Imagens .bmp dos itens
```

## Como funciona

### Fluxo principal

1. O usuário acessa `/` e vê os 9 slots de equipamento.
2. Para cada slot, seleciona item, raridade, especialização e nível de aging.
3. A cada mudança, o frontend envia um `POST /aggregate` com os itens selecionados.
4. O backend aplica os bônus de raridade, spec e aging a cada item, depois agrega os resultados: **soma** os atributos e pega o **maior requisito** entre todos os itens.
5. O painel de agregado exibe o total de atributos e os requisitos mínimos de status necessários para usar o build completo.

### Bônus de raridade (exemplos)

| Raridade  | Defesa (armadura) | Absorção (armadura) | Ataque (arma) |
|-----------|:-----------------:|:-------------------:|:-------------:|
| Raro      | +30               | +1                  | +4            |
| Épico     | +60               | +2                  | +8            |
| Lendário  | +90               | +3                  | +12           |

### Aging

- **Armadura/Roupão**: +5% defesa por nível; +0,5 absorção/nível (1–9), +1,0/nível (10+)
- **Escudo**: +0,5 block/nível; +0,2 absorção/nível (1–9), +0,4/nível (10+)
- **Orbital**: +10% defesa por nível; +0,5 absorção/nível (1–9), +1,0/nível (10+)
