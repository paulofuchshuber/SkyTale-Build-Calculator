# SkyTale Build Calculator

Um pequeno utilitário web (interface simples) para montar e calcular builds do servidor privado SkyTale.

Esta versão do repositório foi adaptada para um fluxo simples de "spec-2-code": manter especificações de slots e regras em YAML e permitir que o código gere/valide a interface automaticamente.

**Cabeçalho visual:** usamos a identidade do SkyTale por conveniência — logo pública usada como cabeçalho: https://www.skytale.com.br/assets/skytale-logo.png

**Estrutura proposta (simples spec-2-code)**
- `spec/` — arquivos YAML com especificação de slots, categorias e regras (ex.: `spec/example_spec.yaml`).
- `items.json` — catálogo de itens (já presente).
- `app.py` — servidor Flask que rende a UI usando `templates/index.html`.
- `templates/index.html` — template atualizado com identidade visual parecida com SkyTale.

Como usar

1. Instale dependências:

```bash
pip install -r requirements.txt
```

2. Execute o servidor:

```bash
python app.py
```

3. Abra o navegador em `http://127.0.0.1:5000`.

Como contribuir com specs

- Coloque arquivos YAML em `spec/` descrevendo os slots, categorias e regras de modificação de specs.
- O arquivo `spec/example_spec.yaml` fornece um modelo básico para começar.

Notas de identidade visual

- O template `templates/index.html` foi estilizado com cores escuras e destaque azul, e insere o logo público do SkyTale (link acima). Se preferir remover o link externo, substitua a URL no template por um arquivo local em `assets/`.

Próximos passos sugeridos

- Automatizar carregamento das specs do diretório `spec/` no `app.py`.
- Adicionar conversor `spec -> JSON` para integração com o frontend.

Licença e avisos

Este repositório é um utilitário auxiliar; use imagens e marcas do SkyTale apenas com permissão adequada. Código e dados aqui mantidos de forma independente.