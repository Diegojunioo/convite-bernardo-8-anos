CONVITE INTERATIVO - BERNARDO 8 ANOS

1. Instale Python 3.10 ou superior.
2. Abra o terminal nesta pasta.
3. (Opcional, recomendado) crie um ambiente virtual:
   python -m venv venv
   Windows: venv\Scripts\activate
4. Instale as dependências:
   pip install -r requirements.txt
5. Execute:
   python app.py
6. Abra no navegador:
   http://127.0.0.1:5000

CONFIRMAÇÕES:
- Os convidados enviam o nome, se irão, quantidade de acompanhantes e contato opcional.
- As respostas ficam salvas no arquivo confirmacoes.db.
- Para consultar a lista, abra http://127.0.0.1:5000/resumo

IMPORTANTE:
- /resumo não tem senha nesta versão. Não publique essa rota abertamente sem adicionar autenticação.
- Para enviar o convite a outras pessoas pela internet, será necessário publicar o app em um serviço de hospedagem.
- Em hospedagens com sistema de arquivos temporário, configure armazenamento persistente para o banco SQLite.
- Troque app.secret_key por uma chave secreta forte antes de publicar.
