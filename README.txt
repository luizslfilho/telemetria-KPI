════════════════════════════════════════════════════════════
  KPIs RASTREAMENTO — APLICAÇÃO WEB
  Guia de Deploy no Railway
════════════════════════════════════════════════════════════


─── ESTRUTURA DO PROJETO ─────────────────────────────────────

  📁 rastreamento_web/
  ├── app.py              ← servidor Flask (não editar)
  ├── requirements.txt    ← dependências Python
  ├── Procfile            ← instrução de inicialização
  ├── .gitignore          ← arquivos ignorados pelo Git
  └── 📁 templates/
      ├── index.html      ← tela de upload
      └── dashboard.html  ← dashboard gerado


─── COMO PUBLICAR NO RAILWAY (passo a passo) ─────────────────

  PRÉ-REQUISITO: Criar conta gratuita em github.com
  (o Railway conecta direto ao GitHub)

  PASSO 1 — Criar repositório no GitHub
  ──────────────────────────────────────
  1. Acesse github.com e faça login
  2. Clique em "New repository"
  3. Nome: rastreamento-kpis
  4. Marque "Private" (para não ser público)
  5. Clique "Create repository"

  PASSO 2 — Subir os arquivos
  ──────────────────────────────────────
  No VS Code, abra o terminal na pasta "rastreamento_web" e rode:

    git init
    git add .
    git commit -m "primeiro commit"
    git branch -M main
    git remote add origin https://github.com/SEU_USUARIO/rastreamento-kpis.git
    git push -u origin main

  (Substitua SEU_USUARIO pelo seu usuário do GitHub)

  PASSO 3 — Deploy no Railway
  ──────────────────────────────────────
  1. Acesse railway.app
  2. Clique "Start a New Project"
  3. Escolha "Deploy from GitHub repo"
  4. Selecione o repositório "rastreamento-kpis"
  5. Railway detecta automaticamente o Procfile e instala tudo
  6. Aguarde 2-3 minutos

  PASSO 4 — Pegar o link público
  ──────────────────────────────────────
  1. No painel do Railway, clique no projeto
  2. Vá em "Settings" → "Domains"
  3. Clique "Generate Domain"
  4. Recebe um link como: https://rastreamento-kpis.up.railway.app

  Pronto! Compartilhe esse link com a equipe.


─── COMO ATUALIZAR O SISTEMA ─────────────────────────────────

  Toda vez que editar algum arquivo e quiser atualizar online:

    git add .
    git commit -m "atualização"
    git push

  O Railway detecta automaticamente e atualiza em 1-2 minutos.


─── COMO USAR O SISTEMA ──────────────────────────────────────

  1. Acesse o link do Railway no navegador
  2. Selecione o mês e ano de cobrança
  3. Arraste os arquivos .xlsx ou clique para selecionar
  4. Clique "Gerar Dashboard"
  5. O dashboard aparece na tela com todos os KPIs
  6. Use o botão "⬇ Baixar relatório HTML" para salvar localmente
  7. Use "⬇ Exportar CSV" para exportar os comunicantes por cliente
  8. Preencha os valores de cobrança e exporte o relatório financeiro


─── CUSTO ────────────────────────────────────────────────────

  Railway oferece plano gratuito com:
  → $5 de crédito por mês (suficiente para uso interno)
  → Sem necessidade de cartão de crédito para começar
  → Se exceder, plano Hobby custa U$ 5/mês


─── TESTE LOCAL ANTES DE PUBLICAR ───────────────────────────

  Para rodar localmente no seu computador:

    pip install flask pandas openpyxl gunicorn
    python app.py

  Acesse: http://localhost:5000


════════════════════════════════════════════════════════════
