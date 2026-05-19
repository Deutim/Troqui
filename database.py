"""
═══════════════════════════════════════════════════════════
Troqui — database.py
Módulo responsável pelo Banco de Dados SQLite

O QUE É UM BANCO DE DADOS?
  Um banco de dados é como uma planilha do Excel, mas mais poderosa.
  Ele guarda informações de forma organizada em "tabelas" (como abas do Excel),
  cada tabela com "colunas" (como cabeçalhos) e "linhas" (como registros).

O QUE É SQLITE?
  SQLite é um tipo de banco de dados que salva tudo em um único arquivo .db.
  Não precisa instalar nada separado — já vem embutido no Python!
  Ideal para projetos pessoais e aplicações com poucos usuários.

O QUE É SQL?
  SQL (Structured Query Language) é a linguagem usada para conversar com
  bancos de dados. Os comandos mais comuns são:
    SELECT  → Buscar/ler dados
    INSERT  → Adicionar novos dados
    UPDATE  → Modificar dados existentes
    DELETE  → Apagar dados

ESTRUTURA DESTE ARQUIVO:
  Este arquivo contém TODAS as funções que tocam no banco de dados.
  Separamos do app.py para manter o código organizado (princípio de
  "separação de responsabilidades" — cada arquivo faz uma coisa só).
═══════════════════════════════════════════════════════════
"""

# ── Importações ──
# sqlite3: módulo nativo do Python para trabalhar com SQLite
import sqlite3
# os: módulo para interagir com o sistema operacional (caminhos de arquivo, etc.)
import os


# ── Caminho do banco de dados ──
# os.path.abspath(__file__)  → Caminho completo deste arquivo (database.py)
# os.path.dirname(...)       → Pega só a pasta onde o arquivo está
# os.path.join(..., 'financas.db') → Junta a pasta com o nome do arquivo .db
# Resultado: o banco sempre fica na mesma pasta que os arquivos Python
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'financas.db')


# ══════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO BANCO
# ══════════════════════════════════════════════════════════

def iniciar_banco():
    """
    Cria todas as tabelas do banco de dados SE elas ainda não existirem.

    Esta função é chamada uma vez quando o servidor inicia.
    "CREATE TABLE IF NOT EXISTS" é seguro de rodar várias vezes:
    ele só cria a tabela se ela ainda não existir, sem apagar os dados.

    TABELAS CRIADAS:
      1. usuarios        → Quem pode acessar o sistema
      2. transacoes      → Cada receita ou despesa lançada
      3. despesas_fixas  → Contas recorrentes (aluguel, internet, etc.)
      4. historico_geracao_fixas → Controla quais meses já tiveram
                                   as fixas lançadas automaticamente
    """
    # Abre a conexão com o banco de dados
    # timeout=15.0 → Se o banco estiver ocupado, espera até 15 segundos antes de dar erro
    conn = sqlite3.connect(DB_PATH, timeout=15.0)

    # O cursor é o "braço" que executa os comandos SQL dentro da conexão
    cursor = conn.cursor()

    # ── Tabela de Usuários ──
    # Armazena os dados de login de cada pessoa que usa o sistema.
    # PRIMARY KEY AUTOINCREMENT → o "id" é gerado automaticamente (1, 2, 3...)
    # TEXT NOT NULL             → campo obrigatório de texto
    # UNIQUE                    → não pode ter dois emails iguais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        )
    ''')

    # ── Tabela de Transações ──
    # Cada linha aqui é um lançamento financeiro (receita ou despesa).
    # FOREIGN KEY(usuario_id) REFERENCES usuarios(id) →
    #   Garante que usuario_id sempre aponte para um usuário real.
    #   Isso é um "relacionamento" entre tabelas: cada transação pertence a um usuário.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo         TEXT NOT NULL,               -- 'receita' ou 'despesa'
            data         TEXT NOT NULL,               -- '2026-04-25' (formato ISO)
            mesAno       TEXT NOT NULL,               -- '2026-04' (para agrupamento)
            descricao    TEXT NOT NULL,               -- Texto livre: 'Aluguel', 'Salário'...
            valor        REAL NOT NULL,               -- REAL = número decimal (ex: 1500.50)
            categoria    TEXT,                        -- Pode ser NULL para receitas
            status       TEXT NOT NULL DEFAULT 'pendente', -- 'pendente' ou 'pago'
            dataPrevista TEXT,                        -- Data prevista (opcional)
            usuario_id   INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # ── Tabela de Despesas Fixas ──
    # Modelo de contas recorrentes. A cada mês, o sistema cria automaticamente
    # uma transação baseada neste modelo.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS despesas_fixas (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao      TEXT NOT NULL,
            valor          REAL NOT NULL,
            categoria      TEXT NOT NULL,
            dia_vencimento INTEGER NOT NULL,  -- Dia do mês (1 a 31)
            usuario_id     INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # ── Tabela de Histórico de Geração das Fixas ──
    # Controla para quais meses as despesas fixas já foram geradas,
    # evitando duplicatas se o servidor for reiniciado.
    # UNIQUE(mesAno, usuario_id) → combinação única: um mês + um usuário só pode
    # aparecer uma vez nesta tabela.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_geracao_fixas (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            mesAno     TEXT NOT NULL,
            usuario_id INTEGER NOT NULL DEFAULT 1,
            UNIQUE(mesAno, usuario_id)
        )
    ''')

    # conn.commit() → "Salva" todas as alterações no arquivo .db
    # Sem o commit, as mudanças existem só na memória e se perdem ao fechar
    conn.commit()
    conn.close()
    print(f"[OK] Banco de dados pronto em: {DB_PATH}")


# ══════════════════════════════════════════════════════════
# FUNÇÕES DE LEITURA (SELECT)
# Buscam dados do banco sem modificar nada.
# ══════════════════════════════════════════════════════════

def buscar_todas(usuario_id):
    """
    Retorna TODAS as transações de um usuário, ordenadas da mais recente para a mais antiga.

    Parâmetro:
      usuario_id → ID do usuário logado (garante que cada um vê só os seus dados)

    Retorna:
      Uma lista de dicionários. Cada dicionário representa uma linha da tabela.
      Exemplo: [{'id': 1, 'tipo': 'despesa', 'valor': 150.0, ...}, ...]
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)

    # row_factory = sqlite3.Row faz com que as linhas retornem como dicionários,
    # permitindo acessar colunas pelo nome: row['descricao'] em vez de row[4]
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # O ? é um "placeholder" (marcador de posição) — nunca coloque valores
    # direto na string SQL! Isso previne ataques de "SQL Injection".
    # Os valores reais são passados como uma tupla: (usuario_id,)
    # ORDER BY data DESC → ordena do mais recente (DESC = decrescente)
    cursor.execute(
        'SELECT * FROM transacoes WHERE usuario_id = ? ORDER BY data DESC',
        (usuario_id,)
    )

    rows = cursor.fetchall()  # fetchall() pega TODOS os resultados de uma vez
    conn.close()

    # Converte cada Row para um dict Python puro, mais fácil de manipular
    return [dict(row) for row in rows]


def buscar_por_id(id_transacao, usuario_id):
    """
    Busca uma transação específica pelo seu ID único.

    O filtro 'AND usuario_id = ?' é uma camada de segurança:
    mesmo que alguém tente acessar o ID de outro usuário pela URL,
    não vai encontrar nada porque os IDs cruzam.

    Retorna:
      Um dicionário com os dados da transação, ou None se não encontrar.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM transacoes WHERE id = ? AND usuario_id = ?',
        (id_transacao, usuario_id)
    )

    row = cursor.fetchone()  # fetchone() pega apenas o primeiro resultado (ou None)
    conn.close()

    # Expressão condicional (ternário): "X if condição else Y"
    # Se encontrou algo, converte para dict; senão, retorna None
    return dict(row) if row else None


def buscar_por_mes(mes_ano, usuario_id):
    """
    Retorna todas as transações de um mês específico.

    Parâmetro mes_ano:
      Formato 'YYYY-MM', ex: '2026-04'
      A coluna mesAno foi projetada exatamente para facilitar essa busca.

    Retorna:
      Lista de dicionários, ordenada da data mais recente para a mais antiga.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM transacoes WHERE mesAno = ? AND usuario_id = ? ORDER BY data DESC',
        (mes_ano, usuario_id)
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def buscar_por_descricao(termo, usuario_id):
    """
    Busca transações cuja descrição contenha o termo digitado.
    O operador LIKE do SQL ignora maiúsculas/minúsculas e o '%' 
    funciona como um curinga (procura o termo em qualquer parte do texto).
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    like_termo = f'%{termo}%'
    cursor.execute('''
        SELECT * FROM transacoes 
        WHERE usuario_id = ? AND descricao LIKE ? 
        ORDER BY data DESC
    ''', (usuario_id, like_termo))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ══════════════════════════════════════════════════════════
# FUNÇÕES DE ESCRITA (INSERT, UPDATE, DELETE)
# Modificam dados no banco.
# ══════════════════════════════════════════════════════════

def inserir(dados, usuario_id):
    """
    Insere uma nova transação no banco de dados.

    Parâmetro dados:
      Um dicionário Python com os campos da transação.
      dados.get('campo') → Pega o valor do campo, ou None se não existir.

    Retorna:
      O ID numérico do novo registro criado (útil para confirmar).
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()

    # INSERT INTO → Adiciona uma nova linha na tabela
    # VALUES (?, ?, ...) → Os ? são preenchidos com os valores da tupla abaixo
    cursor.execute('''
        INSERT INTO transacoes
            (tipo, data, mesAno, descricao, valor, categoria, status, dataPrevista, usuario_id)
        VALUES
            (?,    ?,    ?,      ?,         ?,     ?,         ?,      ?,            ?)
    ''', (
        dados.get('tipo'),
        dados.get('data'),
        dados.get('mesAno'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('categoria'),
        dados.get('status', 'pendente'),  # Valor padrão: 'pendente' se não informado
        dados.get('dataPrevista'),
        usuario_id
    ))

    # lastrowid → ID gerado automaticamente para o registro recém-inserido
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar(id_transacao, dados, usuario_id):
    """
    Atualiza os dados de uma transação existente.

    UPDATE ... SET ... WHERE →
      SET   = quais colunas mudar e para quais valores
      WHERE = qual(is) linha(s) devem ser alteradas

    Retorna:
      True se alguma linha foi alterada, False se não encontrou.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE transacoes
        SET tipo = ?, data = ?, mesAno = ?, descricao = ?, valor = ?,
            categoria = ?, status = ?, dataPrevista = ?
        WHERE id = ? AND usuario_id = ?
    ''', (
        dados.get('tipo'),
        dados.get('data'),
        dados.get('mesAno'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('categoria'),
        dados.get('status', 'pendente'),
        dados.get('dataPrevista'),
        id_transacao,
        usuario_id
    ))

    # cursor.rowcount → Número de linhas afetadas pelo último comando
    alterado = cursor.rowcount
    conn.commit()
    conn.close()
    return alterado > 0  # Retorna True se pelo menos 1 linha foi alterada


def atualizar_status(id_transacao, novo_status, usuario_id):
    """
    Muda apenas o status de uma transação ('pendente' ↔ 'pago').

    Usamos UPDATE parcial para não precisar reenviar todos os campos.
    O WHERE com usuario_id garante que só o dono pode alterar.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE transacoes SET status = ? WHERE id = ? AND usuario_id = ?',
        (novo_status, id_transacao, usuario_id)
    )

    conn.commit()
    conn.close()


def deletar(id_transacao, usuario_id):
    """
    Remove permanentemente uma transação do banco.

    DELETE FROM ... WHERE → Apaga as linhas que satisfazem a condição.
    O filtro por usuario_id impede que alguém apague dados de outro usuário.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()

    cursor.execute(
        'DELETE FROM transacoes WHERE id = ? AND usuario_id = ?',
        (id_transacao, usuario_id)
    )

    conn.commit()
    conn.close()


def limpar_tudo(usuario_id):
    """
    Apaga TODAS as transações de um usuário.
    Use com cuidado — não há desfazer!
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transacoes WHERE usuario_id = ?', (usuario_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════
# FUNÇÕES DE CÁLCULO
# Fazem agregações matemáticas sobre os dados.
# ══════════════════════════════════════════════════════════

def calcular_resumo_mes(mes_ano, usuario_id):
    """
    Calcula os totais financeiros de um mês: receitas, despesas e saldo.

    Lógica:
      - Busca todas as transações do mês
      - Percorre cada uma somando nos totais corretos
      - Saldo = receitas - despesas pagas (despesas pendentes não entram ainda)

    Retorna um dicionário com 4 chaves:
      receitas  → Total recebido no mês
      despesas  → Total de despesas JÁ pagas
      pendentes → Total de despesas AINDA a pagar
      saldo     → receitas - despesas pagas
    """
    transacoes = buscar_por_mes(mes_ano, usuario_id)

    # Inicializa os acumuladores em zero
    receitas = 0.0
    despesas_pagas = 0.0
    despesas_pendentes = 0.0

    # Percorre cada transação e soma no total correto
    for t in transacoes:
        if t['tipo'] == 'receita':
            receitas += t['valor']
        elif t['tipo'] == 'despesa':
            # Despesas se dividem entre pagas e pendentes
            if t['status'] == 'pago':
                despesas_pagas += t['valor']
            else:
                despesas_pendentes += t['valor']

    return {
        'receitas':  receitas,
        'despesas':  despesas_pagas,
        'pendentes': despesas_pendentes,
        'saldo':     receitas - despesas_pagas
    }


def calcular_saldo_acumulado(mes_ano_limite, usuario_id):
    """
    Calcula o saldo acumulado de TODOS os meses ATÉ o mês atual limite.
    Isso permite que o que sobrou no mês passado transborde para o atual,
    em vez de o saldo "zerar" a cada virada de mês.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    
    # Soma de TODAS as receitas até o mês limite
    cursor.execute('''
        SELECT SUM(valor) FROM transacoes 
        WHERE usuario_id = ? AND tipo = 'receita' AND mesAno <= ?
    ''', (usuario_id, mes_ano_limite))
    receitas = cursor.fetchone()[0] or 0.0
    
    # Soma de TODAS as despesas PAGAS até o mês limite
    cursor.execute('''
        SELECT SUM(valor) FROM transacoes 
        WHERE usuario_id = ? AND tipo = 'despesa' AND status = 'pago' AND mesAno <= ?
    ''', (usuario_id, mes_ano_limite))
    despesas_pagas = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return receitas - despesas_pagas


def listar_meses(usuario_id):
    """
    Lista todos os meses em que o usuário tem transações, com seus resumos.

    DISTINCT → Remove duplicatas: mesmo que haja 50 transações em abril/2026,
               '2026-04' aparece apenas uma vez na lista.
    ORDER BY mesAno ASC → Ordena do mês mais antigo para o mais recente.

    Retorna:
      Lista de dicionários, cada um representando um mês com seu nome e totais.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()

    cursor.execute(
        'SELECT DISTINCT mesAno FROM transacoes WHERE usuario_id = ? ORDER BY mesAno ASC',
        (usuario_id,)
    )

    meses_raw = cursor.fetchall()
    conn.close()

    resultado = []

    # Para cada mês encontrado, calcula o resumo e monta o dicionário
    for (mes_ano,) in meses_raw:
        resumo = calcular_resumo_mes(mes_ano, usuario_id)

        # ** (desempacotamento de dicionário) → Copia todas as chaves do resumo
        # É o mesmo que escrever 'receitas': resumo['receitas'], 'despesas': ...
        resultado.append({
            'mesAno': mes_ano,
            'nome':   _nome_mes(mes_ano),
            **resumo
        })

    return resultado


def _nome_mes(mes_ano):
    """
    Converte '2026-04' para 'Abril 2026'.

    O underscore (_) no início do nome indica que esta é uma função
    "privada" — criada para uso interno deste módulo, não para ser
    chamada de outros arquivos diretamente.

    Lógica:
      '2026-04'.split('-') → ['2026', '04']
      int('04') → 4
      nomes[4]  → 'Abril'
    """
    if not mes_ano or '-' not in mes_ano:
        return 'Desconhecido'

    nomes = [
        '',          # índice 0 (não existe mês 0)
        'Janeiro', 'Fevereiro', 'Março', 'Abril',
        'Maio', 'Junho', 'Julho', 'Agosto',
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    try:
        partes = mes_ano.split('-')  # Separa pelo traço: ['2026', '04']
        ano = partes[0]              # '2026'
        mes = int(partes[1])         # Converte '04' para o número 4

        if 1 <= mes <= 12:
            return f"{nomes[mes]} {ano}"  # f-string: monta 'Abril 2026'
        return mes_ano  # Retorna o original se o mês for inválido

    except (IndexError, ValueError):
        # IndexError  → Caso a lista não tenha o índice esperado
        # ValueError  → Caso int() receba algo que não é número
        return 'Desconhecido'


# ══════════════════════════════════════════════════════════
# DESPESAS FIXAS
# Funções para gerenciar contas recorrentes (aluguel, etc.)
# ══════════════════════════════════════════════════════════

def buscar_fixas(usuario_id):
    """Retorna todas as despesas fixas do usuário, ordenadas pelo dia de vencimento."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM despesas_fixas WHERE usuario_id = ? ORDER BY dia_vencimento ASC',
        (usuario_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def buscar_fixa_por_id(id_fixa, usuario_id):
    """Busca uma despesa fixa específica pelo ID."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM despesas_fixas WHERE id = ? AND usuario_id = ?',
        (id_fixa, usuario_id)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def inserir_fixa(dados, usuario_id):
    """Cadastra uma nova despesa fixa recorrente e gera o lançamento do mês atual se necessário."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO despesas_fixas (descricao, valor, categoria, dia_vencimento, usuario_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        dados['descricao'],
        dados['valor'],
        dados['categoria'],
        dados['dia_vencimento'],
        usuario_id
    ))
    
    from datetime import date
    hoje = date.today()
    mes_ano = f"{hoje.year}-{hoje.month:02d}"
    
    # Verifica se este mês já foi processado
    cursor.execute(
        'SELECT 1 FROM historico_geracao_fixas WHERE mesAno = ? AND usuario_id = ?',
        (mes_ano, usuario_id)
    )
    ja_processado = cursor.fetchone()
    
    if ja_processado:
        # Se já foi processado, a rotina automática não vai pegar essa despesa nova.
        # Então, inserimos manualmente para o mês atual.
        dia = f"{dados['dia_vencimento']:02d}"
        data = f"{mes_ano}-{dia}"
        cursor.execute('''
            INSERT INTO transacoes
                (tipo, data, mesAno, descricao, valor, categoria, status, dataPrevista, usuario_id)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'despesa',
            data,
            mes_ano,
            dados['descricao'] + ' (Fixa)',
            dados['valor'],
            dados['categoria'],
            'pendente',
            None,
            usuario_id
        ))

    conn.commit()
    conn.close()


def atualizar_fixa(id_fixa, dados, usuario_id):
    """Atualiza os dados de uma despesa fixa existente."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE despesas_fixas
        SET descricao = ?, valor = ?, categoria = ?, dia_vencimento = ?
        WHERE id = ? AND usuario_id = ?
    ''', (
        dados['descricao'],
        dados['valor'],
        dados['categoria'],
        dados['dia_vencimento'],
        id_fixa,
        usuario_id
    ))
    conn.commit()
    conn.close()


def deletar_fixa(id_fixa, usuario_id):
    """Remove uma despesa fixa. Não apaga os lançamentos já gerados."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM despesas_fixas WHERE id = ? AND usuario_id = ?',
        (id_fixa, usuario_id)
    )
    conn.commit()
    conn.close()


def total_despesas_fixas(usuario_id):
    """
    Retorna a soma do valor de todas as despesas fixas cadastradas pelo usuário.
    Usado para calcular projeções financeiras no dashboard.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT SUM(valor) FROM despesas_fixas WHERE usuario_id = ?',
        (usuario_id,)
    )
    total = cursor.fetchone()[0] or 0.0
    conn.close()
    return total


def processar_despesas_fixas_do_mes(mes_ano, usuario_id):
    """
    Gera automaticamente os lançamentos de despesas fixas para um mês.
    Esta função agora verifica individualmente cada despesa fixa para garantir
    que foi lançada no mês, tornando o sistema auto-corretivo caso uma nova
    despesa seja adicionada após o início do mês.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)

    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Busca todas as despesas fixas do usuário
        cursor.execute(
            'SELECT * FROM despesas_fixas WHERE usuario_id = ?',
            (usuario_id,)
        )
        fixas = cursor.fetchall()

        # Para cada fixa cadastrada, verifica se já existe lançamento neste mês
        for fixa in fixas:
            descricao_esperada = fixa['descricao'] + ' (Fixa)'
            
            cursor.execute('''
                SELECT 1 FROM transacoes 
                WHERE mesAno = ? AND usuario_id = ? AND descricao = ?
            ''', (mes_ano, usuario_id, descricao_esperada))
            
            ja_existe = cursor.fetchone()

            if not ja_existe:
                # Monta a data de vencimento
                dia = f"{fixa['dia_vencimento']:02d}"
                data = f"{mes_ano}-{dia}"

                cursor.execute('''
                    INSERT INTO transacoes
                        (tipo, data, mesAno, descricao, valor, categoria, status, dataPrevista, usuario_id)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'despesa',
                    data,
                    mes_ano,
                    descricao_esperada,
                    fixa['valor'],
                    fixa['categoria'],
                    'pendente',
                    None,
                    usuario_id
                ))

        # Registra que este mês já foi processado na tabela histórica (apenas por garantia/histórico)
        cursor.execute(
            'SELECT 1 FROM historico_geracao_fixas WHERE mesAno = ? AND usuario_id = ?',
            (mes_ano, usuario_id)
        )
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO historico_geracao_fixas (mesAno, usuario_id) VALUES (?, ?)',
                (mes_ano, usuario_id)
            )

        conn.commit()

    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
# AUTENTICAÇÃO (USUÁRIOS)
# Funções para criar e buscar usuários no sistema.
# ══════════════════════════════════════════════════════════

def buscar_usuario_por_email(email):
    """
    Busca um usuário pelo email (usado no login).

    Retorna o dicionário com todos os dados do usuário, incluindo
    o 'senha_hash' — que é a senha criptografada (nunca guardamos
    a senha em texto puro por segurança!).
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_usuario_por_id(usuario_id):
    """
    Busca um usuário pelo ID numérico.

    O Flask-Login chama esta função automaticamente a cada requisição
    para verificar se o usuário ainda existe e está ativo na sessão.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def criar_usuario(nome, email, senha_hash):
    """
    Cadastra um novo usuário no banco.

    Parâmetro senha_hash:
      A senha JÁ criptografada pelo Werkzeug (gerada em app.py).
      Nunca recebemos nem guardamos a senha em texto puro.

    Retorna:
      O ID do novo usuário criado.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)',
        (nome, email, senha_hash)
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id
