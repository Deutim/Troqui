"""
═══════════════════════════════════════════════════════════
Troqui — app.py
Aplicação Web com Flask (100% Python!)
Desenvolvido com a ajuda da Inteligência Artificial Gordi 🐘💛

Flask é um framework web para Python. Ele permite criar sites
e APIs de forma simples e elegante.

CONCEITOS CHAVE DO FLASK:
  - @app.route('/caminho')  → Define uma URL e a função Python que a atende
  - render_template(...)    → Renderiza um template HTML com dados do Python
  - request.form            → Dados enviados por formulário HTML (método POST)
  - redirect(url_for(...))  → Redireciona para outra página
  - flash(...)              → Mostra mensagem temporária para o usuário

Para rodar:  python app.py
Para acessar: http://localhost:8080

NOTA: debug=True faz o servidor RECARREGAR AUTOMATICAMENTE
      quando você edita qualquer arquivo Python ou HTML!
      Não precisa reiniciar manualmente.
═══════════════════════════════════════════════════════════
"""

# ─── Importações ───
# Flask: framework web principal
# render_template: renderiza arquivos HTML com dados Python
# request: acessa dados enviados pelo navegador (formulários, URLs)
# redirect/url_for: redireciona o usuário para outra página
# flash: mostra mensagens temporárias (feedback ao usuário)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# datetime: trabalha com datas e horários
from datetime import datetime, date

# os: permite ler variáveis de ambiente (SECRET_KEY em produção)
import os

# csv e io: para ler e processar arquivos CSV enviados pelo usuário
import csv
import io

# Importa nossas funções do banco de dados (database.py)
import database as db

# ─── Criação da aplicação Flask ───
app = Flask(__name__)
# Em produção, defina a variável de ambiente SECRET_KEY com um valor longo e aleatório.
# Localmente, usa o valor padrão abaixo.
app.secret_key = os.environ.get('SECRET_KEY', 'financecontrol-chave-local-dev-2026')

# ─── Configuração do Flask-Login ───
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redireciona para /login se não estiver logado
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'aviso'

# Classe que representa o usuário logado na sessão
class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

# Diz ao Flask-Login como carregar o usuário do banco usando o ID da sessão
@login_manager.user_loader
def load_user(user_id):
    # Flask-Login passa o user_id como string, precisamos converter para int
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None
    user_data = db.buscar_usuario_por_id(user_id)
    if user_data:
        return User(id=user_data['id'], nome=user_data['nome'], email=user_data['email'])
    return None

# ─── auto_login_local REMOVIDO ───
# O login automático foi desabilitado para uso em produção (segurança).
# Para desenvolvimento local, crie um usuário via /registro e faça login normalmente.


# ═══════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# Funções que ajudam a formatar dados para exibição.
# ═══════════════════════════════════════════════════════

def formatar_dinheiro(valor):
    """
    Converte um número para formato de moeda brasileira.
    Exemplo: 1234.56 → 'R$ 1.234,56'
    
    f-string com :,.2f formata o número com separador de milhar e 2 decimais.
    Depois trocamos ',' por '.' e '.' por ',' para ficar no padrão BR.
    """
    if valor is None:
        valor = 0.0
    # Formata com 2 casas decimais e separador de milhar
    formatado = f"{valor:,.2f}"
    # Troca separadores para padrão brasileiro
    # Passo 1: vírgula → placeholder temporário
    formatado = formatado.replace(',', 'X')
    # Passo 2: ponto → vírgula
    formatado = formatado.replace('.', ',')
    # Passo 3: placeholder → ponto
    formatado = formatado.replace('X', '.')
    return f"R$ {formatado}"


def formatar_data(data_str):
    """
    Converte '2026-04-25' para '25/04/2026' (formato brasileiro).
    Se a data for inválida ou vazia, retorna '--/--/----'.
    """
    if not data_str:
        return '--/--/----'
    try:
        # strptime = converte string para objeto datetime
        dt = datetime.strptime(data_str, '%Y-%m-%d')
        # strftime = converte objeto datetime para string formatada
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        return '--/--/----'


def nome_mes(mes_ano):
    """
    Converte '2026-04' para 'Abril 2026'.
    Reutiliza a função do database.py.
    """
    return db._nome_mes(mes_ano)


def mes_atual():
    """Retorna o mês atual no formato '2026-04'."""
    hoje = date.today()
    return f"{hoje.year}-{hoje.month:02d}"


# ─── Registra funções no Jinja2 (templates HTML) ───
# Isso permite usar essas funções diretamente nos templates HTML:
#   {{ formatar_dinheiro(1234.56) }}  →  R$ 1.234,56
#   {{ formatar_data('2026-04-25') }} →  25/04/2026
app.jinja_env.globals.update(
    formatar_dinheiro=formatar_dinheiro,
    formatar_data=formatar_data,
    nome_mes=nome_mes,
    mes_atual=mes_atual,
)


# ═══════════════════════════════════════════════════════
# AUTENTICAÇÃO (LOGIN / REGISTRO)
# ═══════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        user_data = db.buscar_usuario_por_email(email)
        if user_data and check_password_hash(user_data['senha_hash'], senha):
            user = User(id=user_data['id'], nome=user_data['nome'], email=user_data['email'])
            login_user(user)
            flash(f'Bem-vindo de volta, {user.nome}! O Gordi guardou tudo direitinho.', 'sucesso')
            return redirect(url_for('dashboard'))
        else:
            flash('E-mail ou senha inválidos.', 'erro')
            
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if db.buscar_usuario_por_email(email):
            flash('Este e-mail já está em uso.', 'erro')
        else:
            senha_hash = generate_password_hash(senha)
            novo_id = db.criar_usuario(nome, email, senha_hash)
            user = User(id=novo_id, nome=nome, email=email)
            login_user(user)
            flash('Conta criada com sucesso! O Gordi está pronto para cuidar do seu ouro.', 'sucesso')
            return redirect(url_for('dashboard'))
            
    return render_template('registro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════
# ROTAS (URLs do site)
#
# Cada @app.route() define uma página do site.
# Quando o usuário acessa a URL, o Flask chama a função
# correspondente e retorna o HTML para o navegador.
#
# Métodos HTTP:
#   GET  = O navegador pede para VER a página
#   POST = O navegador ENVIA dados (formulário preenchido)
# ═══════════════════════════════════════════════════════


@app.route('/sw.js')
def sw():
    """ Rota especial para o Service Worker ter escopo global na raiz do site """
    return app.send_static_file('sw.js')

@app.route('/')
@login_required
def dashboard():
    """
    PÁGINA PRINCIPAL — Dashboard
    
    Mostra o resumo financeiro do mês atual:
    receitas, despesas pagas, despesas pendentes e saldo.
    Também calcula os totais por categoria para o gráfico.
    """
    import json
    ma = mes_atual()
    
    # Processa as despesas fixas para garantir que foram lançadas no mês atual
    db.processar_despesas_fixas_do_mes(ma, current_user.id)

    resumo = db.calcular_resumo_mes(ma, current_user.id)
    # Calcula o saldo acumulado histórico em vez de apenas o do mês atual
    saldo_acumulado = db.calcular_saldo_acumulado(ma, current_user.id)

    # ── Busca despesas atrasadas de meses anteriores ──
    todas_transacoes = db.buscar_todas(current_user.id)
    atrasadas = [t for t in todas_transacoes 
                 if t['tipo'] == 'despesa' 
                 and t['status'] == 'pendente' 
                 and t['mesAno'] < ma]
    
    total_atrasadas = sum(t['valor'] for t in atrasadas)
    
    # Adiciona as atrasadas ao total de pendentes
    total_pendentes = resumo['pendentes'] + total_atrasadas

    # Buscar transações do mês para calcular as categorias
    transacoes_mes = db.buscar_por_mes(ma, current_user.id)
    categorias = {}
    
    for t in transacoes_mes:
        if t['tipo'] == 'despesa' and t['categoria'] and t['status'] == 'pago':
            cat = t['categoria']
            categorias[cat] = categorias.get(cat, 0) + t['valor']

    # Prepara os dados para o Chart.js
    labels_grafico = list(categorias.keys())
    valores_grafico = list(categorias.values())

    return render_template('dashboard.html',
        mes_nome=nome_mes(ma),
        ma_atual=ma,
        saldo=saldo_acumulado,
        receitas=resumo['receitas'],
        despesas=resumo['despesas'],
        pendentes=total_pendentes,
        cat_labels=json.dumps(labels_grafico),
        cat_valores=json.dumps(valores_grafico)
    )



# ─── BUSCA ───

@app.route('/busca')
@login_required
def busca():
    """
    PÁGINA: Resultados da Busca
    Recebe um termo na URL (?q=termo) e mostra as transações correspondentes.
    """
    termo = request.args.get('q', '').strip()
    if not termo:
        # Se não digitou nada, volta pra onde estava
        return redirect(request.referrer or url_for('dashboard'))
    
    resultados = db.buscar_por_descricao(termo, current_user.id)
    return render_template('busca.html', termo=termo, transacoes=resultados)


# ─── LANÇAMENTOS (CRIAR) ───

@app.route('/lancamento')
@login_required
def lancamento_tipo():
    """
    PÁGINA: Escolher tipo de lançamento
    Exibe dois botões: Receita ou Despesa.
    """
    return render_template('lancamento_tipo.html')


@app.route('/lancamento/receita', methods=['GET', 'POST'])
@login_required
def lancamento_receita():
    """
    PÁGINA: Formulário de Nova Receita
    
    GET  → Mostra o formulário vazio para preenchimento
    POST → Recebe os dados preenchidos e salva no banco
    
    request.method indica qual ação o navegador está fazendo.
    request.form['campo'] pega o valor que o usuário digitou.
    """
    if request.method == 'POST':
        # ── O usuário enviou o formulário (clicou em Salvar) ──

        # Pega cada campo do formulário
        data = request.form.get('data', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor_str = request.form.get('valor', '').strip()
        status = request.form.get('status', 'pendente')
        data_prevista = request.form.get('dataPrevista', '')

        # Validação dos campos obrigatórios
        if not data or not descricao or not valor_str:
            flash('⚠️ Preencha todos os campos obrigatórios.', 'erro')
            return redirect(url_for('lancamento_receita'))

        try:
            valor = float(valor_str)
        except ValueError:
            flash('⚠️ Valor inválido. Use apenas números.', 'erro')
            return redirect(url_for('lancamento_receita'))

        # Monta o dicionário com os dados para salvar
        dados = {
            'tipo': 'receita',
            'data': data,
            'mesAno': data[:7],  # '2026-04-25' → '2026-04' (primeiros 7 caracteres)
            'descricao': descricao,
            'valor': valor,
            'status': status,
            'dataPrevista': data_prevista if status == 'pendente' else None,
            'categoria': None  # Receitas não têm categoria
        }

        # Salva no banco de dados SQLite
        novo_id = db.inserir(dados, current_user.id)

        # flash() mostra uma mensagem na próxima página
        flash(f'✅ Receita "{descricao}" cadastrada! (ID: {novo_id})', 'sucesso')

        # Redireciona para o dashboard
        return redirect(url_for('dashboard'))

    # ── GET: apenas mostra o formulário ──
    return render_template('lancamento_receita.html', hoje=date.today().isoformat())


@app.route('/lancamento/despesa', methods=['GET', 'POST'])
@login_required
def lancamento_despesa():
    """
    PÁGINA: Formulário de Nova Despesa
    
    Lógica especial para parcelamento:
    Se o usuário marcar "Parcelado" e informar X parcelas,
    o Python cria X transações separadas automaticamente,
    cada uma para um mês diferente.
    """
    if request.method == 'POST':
        data = request.form.get('data', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor_str = request.form.get('valor', '').strip()
        categoria = request.form.get('categoria', '')
        forma = request.form.get('forma', 'avista')
        mes_previsto = request.form.get('mesPrevisto', '')
        status = request.form.get('status', 'pendente')

        # Validação dos campos obrigatórios
        if not data or not descricao or not valor_str or not categoria:
            flash('⚠️ Preencha todos os campos obrigatórios.', 'erro')
            return redirect(url_for('lancamento_despesa'))

        try:
            valor = float(valor_str)
        except ValueError:
            flash('⚠️ Valor inválido. Use apenas números.', 'erro')
            return redirect(url_for('lancamento_despesa'))

        if forma == 'parcelado':
            # ── Parcelamento: cria várias transações com o valor digitado ──
            try:
                parcelas = int(request.form.get('parcelas', 2))
            except ValueError:
                parcelas = 2
            valor_parcela = valor  # O valor digitado agora é o valor DE CADA parcela

            # Monta a data base para calcular os meses
            ano, mes_num = map(int, mes_previsto.split('-'))

            for i in range(parcelas):
                # Calcula o mês de cada parcela
                # Se começa em abril (4) + 2 parcelas: abril, maio
                mes_parcela = mes_num + i
                ano_parcela = ano

                # Se passar de dezembro (12), vai pro próximo ano
                while mes_parcela > 12:
                    mes_parcela -= 12
                    ano_parcela += 1

                mes_ano = f"{ano_parcela}-{mes_parcela:02d}"

                dados = {
                    'tipo': 'despesa',
                    'data': data,
                    'mesAno': mes_ano,
                    'descricao': f"{descricao} (Parc. {i+1}/{parcelas})",
                    'valor': round(valor_parcela, 2),
                    'categoria': categoria,
                    # Primeira parcela pode estar paga, as demais ficam pendentes
                    'status': 'pago' if (i == 0 and status == 'pago') else 'pendente',
                    'dataPrevista': None
                }
                db.inserir(dados, current_user.id)

            flash(f'✅ Despesa "{descricao}" parcelada em {parcelas}x cadastrada!', 'sucesso')
        else:
            # ── À vista: uma única transação ──
            dados = {
                'tipo': 'despesa',
                'data': data,
                'mesAno': mes_previsto,
                'descricao': descricao,
                'valor': valor,
                'categoria': categoria,
                'status': status,
                'dataPrevista': None
            }
            db.inserir(dados, current_user.id)
            flash(f'✅ Despesa "{descricao}" cadastrada!', 'sucesso')

        return redirect(url_for('dashboard'))

    return render_template('lancamento_despesa.html', hoje=date.today().isoformat())


# ─── VISUALIZAÇÕES ───




@app.route('/dividas')
@login_required
def dividas():
    """
    PÁGINA: Dívidas Ativas
    Mostra despesas com categoria 'Dívidas' que ainda não foram pagas.
    
    Dois filtros combinados:
      1. categoria == 'Dívidas'
      2. status == 'pendente'
    """
    todas = db.buscar_todas(current_user.id)

    # Filtra: despesas + categoria Dívidas + não pagas
    lista_dividas = [
        t for t in todas
        if t['tipo'] == 'despesa'
        and t['categoria'] == 'Dívidas'
        and t['status'] == 'pendente'
    ]
    # Ordena pelo mês de vencimento (mesAno) para que fiquem na ordem correta
    lista_dividas.sort(key=lambda t: (t['mesAno'], t['id']))

    total = sum(t['valor'] for t in lista_dividas)

    return render_template('dividas.html',
        dividas=lista_dividas,
        total=total
    )


@app.route('/relatorio')
@login_required
def relatorio():
    """
    PÁGINA: Relatório Mensal
    Lista todos os meses com transações e seus resumos.
    
    db.listar_meses(current_user.id) já retorna tudo calculado!
    """
    meses = db.listar_meses(current_user.id)
    anos_dict = {}

    # Para cada mês, calcula a distribuição por categoria
    for mes in meses:
        transacoes_mes = db.buscar_por_mes(mes['mesAno'], current_user.id)
        categorias = {}
        total_desp = 0

        for t in transacoes_mes:
            if t['tipo'] == 'despesa' and t['categoria']:
                cat = t['categoria']
                categorias[cat] = categorias.get(cat, 0) + t['valor']
                total_desp += t['valor']

        # Calcula percentual de cada categoria
        mes['categorias'] = {}
        if total_desp > 0:
            for cat, val in categorias.items():
                mes['categorias'][cat] = round((val / total_desp) * 100)
                
        # Agrupa por ano
        ano_str = mes['mesAno'].split('-')[0]
        if ano_str not in anos_dict:
            anos_dict[ano_str] = []
        anos_dict[ano_str].append(mes)

    return render_template('relatorio.html', anos=anos_dict, ma_atual=mes_atual())


@app.route('/relatorio/<mes_ano>')
@login_required
def mes_detalhe(mes_ano):
    """
    PÁGINA: Detalhe de um Mês Específico
    
    O <mes_ano> na URL é uma variável dinâmica do Flask.
    Exemplo: /relatorio/2026-04 → mes_ano = '2026-04'
    """
    transacoes = db.buscar_por_mes(mes_ano, current_user.id)
    resumo = db.calcular_resumo_mes(mes_ano, current_user.id)

    return render_template('mes_detalhe.html',
        mes_ano=mes_ano,
        mes_nome=nome_mes(mes_ano),
        transacoes=transacoes,
        resumo=resumo
    )


# ─── AÇÕES (Marcar pago, Editar, Excluir) ───

@app.route('/marcar-pago/<int:id>')
@login_required
def marcar_pago(id):
    """
    Marca uma transação como 'pago'.
    
    O <int:id> na rota converte o valor da URL para inteiro.
    Exemplo: /marcar-pago/42 → id = 42
    
    request.referrer = a URL de onde o usuário veio.
    Assim ele volta para a mesma página após a ação.
    """
    db.atualizar_status(id, 'pago', current_user.id)
    flash('✅ Marcado como pago!', 'sucesso')

    # Volta para a página anterior (ou dashboard se não souber)
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/marcar-pagos-lote', methods=['POST'])
@login_required
def marcar_pagos_lote():
    """
    Recebe uma lista de IDs pelo formulário e marca todos como pagos.
    """
    ids = request.form.getlist('ids')
    cont = 0
    for id_str in ids:
        if id_str.isdigit():
            # Passa current_user.id para garantir que só marca transações do próprio usuário
            db.atualizar_status(int(id_str), 'pago', current_user.id)
            cont += 1
            
    if cont > 0:
        flash(f'✅ {cont} lançamentos marcados como pagos!', 'sucesso')
    else:
        flash('⚠️ Nenhum lançamento foi selecionado.', 'aviso')
        
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    """
    Exclui uma transação pelo ID.
    Mostra confirmação via flash().
    """
    transacao = db.buscar_por_id(id, current_user.id)
    if transacao:
        db.deletar(id, current_user.id)
        flash(f'🗑️ "{transacao["descricao"]}" excluída!', 'aviso')
    else:
        flash('⚠️ Transação não encontrada.', 'erro')

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """
    PÁGINA: Editar Transação Existente
    
    GET  → Mostra formulário preenchido com os dados atuais
    POST → Salva as alterações no banco
    """
    transacao = db.buscar_por_id(id, current_user.id)

    if not transacao:
        flash('⚠️ Transação não encontrada.', 'erro')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Pega os dados do formulário de edição
        dados = {
            'tipo': transacao['tipo'],  # Tipo não muda na edição
            'data': request.form['data'],
            'mesAno': request.form['data'][:7],
            'descricao': request.form['descricao'],
            'valor': float(request.form['valor']),
            'categoria': request.form.get('categoria'),
            'status': request.form['status'],
            'dataPrevista': request.form.get('dataPrevista', '')
        }

        db.atualizar(id, dados, current_user.id)
        flash(f'✏️ "{dados["descricao"]}" atualizada!', 'sucesso')
        return redirect(url_for('dashboard'))

    return render_template('editar.html', t=transacao)


# ─── DESPESAS FIXAS ───

@app.route('/fixas')
@login_required
def fixas():
    """Lista as despesas fixas cadastradas."""
    lista = db.buscar_fixas(current_user.id)
    return render_template('despesas_fixas.html', fixas=lista)

@app.route('/fixas/nova', methods=['GET', 'POST'])
@login_required
def nova_fixa():
    """Formulário para adicionar uma nova despesa fixa."""
    if request.method == 'POST':
        dados = {
            'descricao': request.form['descricao'],
            'valor': float(request.form['valor']),
            'categoria': request.form['categoria'],
            'dia_vencimento': int(request.form['dia_vencimento'])
        }
        db.inserir_fixa(dados, current_user.id)
        flash(f'✅ Despesa Fixa "{dados["descricao"]}" cadastrada com sucesso!', 'sucesso')
        return redirect(url_for('fixas'))
    return render_template('form_fixa.html', f=None)

@app.route('/fixas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fixa(id):
    """Editar uma despesa fixa existente."""
    fixa = db.buscar_fixa_por_id(id, current_user.id)
    if not fixa:
        flash('⚠️ Despesa Fixa não encontrada.', 'erro')
        return redirect(url_for('fixas'))

    if request.method == 'POST':
        dados = {
            'descricao': request.form['descricao'],
            'valor': float(request.form['valor']),
            'categoria': request.form['categoria'],
            'dia_vencimento': int(request.form['dia_vencimento'])
        }
        db.atualizar_fixa(id, dados, current_user.id)
        flash(f'✏️ Despesa Fixa "{dados["descricao"]}" atualizada!', 'sucesso')
        return redirect(url_for('fixas'))
    
    return render_template('form_fixa.html', f=fixa)

@app.route('/fixas/excluir/<int:id>')
@login_required
def excluir_fixa(id):
    """Excluir uma despesa fixa."""
    fixa = db.buscar_fixa_por_id(id, current_user.id)
    if fixa:
        db.deletar_fixa(id, current_user.id)
        flash(f'🗑️ Despesa Fixa "{fixa["descricao"]}" excluída!', 'aviso')
    return redirect(url_for('fixas'))


# ─── IMPORTAÇÃO CSV ───

# Categorias válidas para despesas (usadas na validação do CSV)
CATEGORIAS_VALIDAS = ['Moradia', 'Alimentação', 'Transporte', 'Saúde',
                      'Educação', 'Lazer', 'Investimentos', 'Dívidas']


def normalizar_data(data_str):
    """
    Converte diferentes formatos de data para o formato ISO (YYYY-MM-DD).
    Aceita: DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, YYYY-MM-DD
    """
    if not data_str:
        return None
    data_str = data_str.strip()
    formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y']
    for fmt in formatos:
        try:
            dt = datetime.strptime(data_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None  # Data inválida


def processar_csv(conteudo_texto):
    """
    Processa o conteúdo de um arquivo CSV e retorna as linhas válidas e os erros.
    Suporta dois formatos:
      - Formato Troqui: tipo,data,descricao,valor,categoria,status
      - Formato Simplificado (extrato): data,descricao,valor

    Retorna: (linhas_validas, erros)
      linhas_validas = lista de dicts prontos para db.inserir()
      erros = lista de dicts com {linha, campo, mensagem}
    """
    linhas_validas = []
    erros = []

    # Detecta o delimitador (vírgula ou ponto-e-vírgula)
    try:
        dialeto = csv.Sniffer().sniff(conteudo_texto[:2000], delimiters=',;\t')
        delimitador = dialeto.delimiter
    except csv.Error:
        delimitador = ','

    leitor = csv.DictReader(io.StringIO(conteudo_texto), delimiter=delimitador)

    # Normaliza os nomes das colunas (remove espaços extras, lowercase)
    if leitor.fieldnames:
        leitor.fieldnames = [c.strip().lower() for c in leitor.fieldnames]

    # ── Mapeamento flexível de colunas ──
    # Cada banco exporta com nomes diferentes. Aqui definimos todas as variações
    # conhecidas para encontrar as colunas certas automaticamente.
    colunas = set(leitor.fieldnames or [])

    # Função auxiliar: procura a primeira coluna que bater
    def encontrar_coluna(possiveis_nomes):
        for nome in possiveis_nomes:
            if nome in colunas:
                return nome
        return None

    # Nomes possíveis para cada campo
    col_data = encontrar_coluna([
        'data', 'date', 'data lançamento', 'data lancamento',
        'data do lançamento', 'data do lancamento', 'data transação',
        'data transacao', 'data movimento', 'data pagamento',
        'data de pagamento', 'data operação', 'data operacao',
        'dt. movimento', 'dt movimento', 'created_at'
    ])
    col_descricao = encontrar_coluna([
        'descricao', 'descrição', 'description', 'desc',
        'lançamento', 'lancamento', 'histórico', 'historico',
        'detalhes', 'detalhe', 'memo', 'observação', 'observacao',
        'título', 'titulo', 'nome', 'identificação', 'identificacao',
        'informações adicionais', 'informacoes adicionais',
        'transação', 'transacao', 'referência', 'referencia'
    ])
    col_valor = encontrar_coluna([
        'valor', 'value', 'amount', 'quantia', 'montante',
        'valor (r$)', 'valor(r$)', 'valor r$', 'vlr',
        'valor da transação', 'valor da transacao',
        'valor do pagamento', 'total'
    ])

    formato_troqui = 'tipo' in colunas
    formato_simplificado = not formato_troqui and col_data is not None

    if not formato_troqui and not formato_simplificado:
        colunas_encontradas = ', '.join(colunas) if colunas else 'nenhuma'
        erros.append({
            'linha': 1,
            'campo': 'cabeçalho',
            'mensagem': f'Colunas não reconhecidas: [{colunas_encontradas}]. Preciso ao menos de uma coluna de data, descrição e valor.'
        })
        return [], erros

    # Verifica se encontrou as colunas mínimas necessárias
    if not col_data:
        erros.append({'linha': 1, 'campo': 'cabeçalho', 'mensagem': 'Coluna de DATA não encontrada no CSV.'})
        return [], erros
    if not col_descricao:
        erros.append({'linha': 1, 'campo': 'cabeçalho', 'mensagem': 'Coluna de DESCRIÇÃO não encontrada no CSV.'})
        return [], erros
    if not col_valor:
        erros.append({'linha': 1, 'campo': 'cabeçalho', 'mensagem': 'Coluna de VALOR não encontrada no CSV.'})
        return [], erros

    for i, row in enumerate(leitor, start=2):
        # Limpa espaços dos valores
        row = {k: (v.strip() if v else '') for k, v in row.items()}
        erro_na_linha = False

        # ── Extrai e normaliza cada campo usando as colunas detectadas ──

        # Data
        data_raw = row.get(col_data, '')
        data_iso = normalizar_data(data_raw)
        if not data_iso:
            erros.append({'linha': i, 'campo': 'data', 'mensagem': f'Data inválida: "{data_raw}"'})
            erro_na_linha = True

        # Descrição
        descricao = row.get(col_descricao, '')
        if not descricao:
            erros.append({'linha': i, 'campo': 'descricao', 'mensagem': 'Descrição vazia'})
            erro_na_linha = True

        # Valor — detecta formato inteligentemente
        # Aceita: "1500.00" (US), "1.500,00" (BR), "1500,00" (BR sem milhar), "1,500.00" (US c/ milhar)
        valor_str = row.get(col_valor, '')
        try:
            vs = valor_str.strip()
            has_dot = '.' in vs
            has_comma = ',' in vs

            if has_dot and has_comma:
                # Ambos presentes: o ÚLTIMO separador é o decimal
                if vs.rfind(',') > vs.rfind('.'):
                    # BR: "1.500,00" → vírgula é decimal
                    vs = vs.replace('.', '').replace(',', '.')
                else:
                    # US: "1,500.00" → ponto é decimal
                    vs = vs.replace(',', '')
            elif has_comma:
                # Só vírgula: é separador decimal ("1500,00")
                vs = vs.replace(',', '.')
            # Se só tem ponto ou nenhum, mantém como está (formato US ou inteiro)

            valor = float(vs)
        except (ValueError, TypeError):
            erros.append({'linha': i, 'campo': 'valor', 'mensagem': f'Valor inválido: "{valor_str}"'})
            erro_na_linha = True
            valor = 0

        if formato_troqui:
            # Formato completo: tipo,data,descricao,valor,categoria,status
            tipo = row.get('tipo', '').lower()
            if tipo not in ('receita', 'despesa'):
                erros.append({'linha': i, 'campo': 'tipo', 'mensagem': f'Tipo inválido: "{tipo}". Use "receita" ou "despesa"'})
                erro_na_linha = True

            categoria = row.get('categoria', '')
            if tipo == 'despesa' and categoria and categoria not in CATEGORIAS_VALIDAS:
                erros.append({'linha': i, 'campo': 'categoria',
                              'mensagem': f'Categoria "{categoria}" não reconhecida. Válidas: {", ".join(CATEGORIAS_VALIDAS)}'})
                erro_na_linha = True

            status = row.get('status', 'pendente').lower()
            if status not in ('pago', 'pendente'):
                status = 'pendente'

        else:
            # Formato simplificado: detecta tipo pelo sinal do valor
            if valor < 0:
                tipo = 'despesa'
                valor = abs(valor)
                status = 'pago'
            else:
                tipo = 'receita'
                status = 'pago'
            categoria = ''

        if not erro_na_linha:
            dados = {
                'tipo': tipo,
                'data': data_iso,
                'mesAno': data_iso[:7] if data_iso else '',
                'descricao': descricao,
                'valor': round(abs(valor), 2),
                'categoria': categoria if categoria else None,
                'status': status,
                'dataPrevista': None
            }
            linhas_validas.append(dados)

    return linhas_validas, erros


@app.route('/importar-csv', methods=['GET', 'POST'])
@login_required
def importar_csv():
    """
    PÁGINA: Importar CSV

    GET  → Mostra a tela de upload com drag & drop
    POST → Processa o CSV, insere as transações válidas no banco
    """
    if request.method == 'POST':
        arquivo = request.files.get('arquivo_csv')

        if not arquivo or not arquivo.filename:
            flash('⚠️ Nenhum arquivo selecionado.', 'erro')
            return redirect(url_for('importar_csv'))

        if not arquivo.filename.lower().endswith('.csv'):
            flash('⚠️ Envie um arquivo com extensão .csv', 'erro')
            return redirect(url_for('importar_csv'))

        # Lê o conteúdo do arquivo
        try:
            conteudo_bytes = arquivo.read()
            # Tenta UTF-8 com BOM (padrão do Excel), depois Latin-1
            try:
                conteudo = conteudo_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                conteudo = conteudo_bytes.decode('latin-1')
        except Exception:
            flash('⚠️ Erro ao ler o arquivo. Verifique o formato.', 'erro')
            return redirect(url_for('importar_csv'))

        # Limita tamanho (2MB)
        if len(conteudo_bytes) > 2 * 1024 * 1024:
            flash('⚠️ Arquivo muito grande. Máximo: 2 MB.', 'erro')
            return redirect(url_for('importar_csv'))

        # Processa o CSV
        linhas_validas, erros_csv = processar_csv(conteudo)

        if not linhas_validas and erros_csv:
            for e in erros_csv[:5]:  # Mostra até 5 erros
                flash(f'❌ Linha {e["linha"]}: {e["mensagem"]}', 'erro')
            return redirect(url_for('importar_csv'))

        # Insere todas as transações válidas no banco
        contador = 0
        for dados in linhas_validas:
            db.inserir(dados, current_user.id)
            contador += 1

        flash(f'✅ {contador} transações importadas com sucesso!', 'sucesso')
        if erros_csv:
            flash(f'⚠️ {len(erros_csv)} linhas ignoradas por conter erros.', 'aviso')

        return redirect(url_for('dashboard'))

    return render_template('importar_csv.html')


@app.route('/importar-csv/preview', methods=['POST'])
@login_required
def preview_csv():
    """
    ENDPOINT AJAX: Recebe o CSV e retorna um JSON com as linhas válidas
    e os erros, sem inserir no banco. Usado para mostrar o preview
    na tela antes de confirmar a importação.
    """
    arquivo = request.files.get('arquivo_csv')

    if not arquivo or not arquivo.filename:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    try:
        conteudo_bytes = arquivo.read()
        try:
            conteudo = conteudo_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            conteudo = conteudo_bytes.decode('latin-1')
    except Exception:
        return jsonify({'erro': 'Erro ao ler o arquivo'}), 400

    linhas_validas, erros_csv = processar_csv(conteudo)

    # Formata para exibição
    preview_linhas = []
    for d in linhas_validas:
        preview_linhas.append({
            'tipo': d['tipo'],
            'data': formatar_data(d['data']),
            'data_iso': d['data'],
            'descricao': d['descricao'],
            'valor': d['valor'],
            'valor_fmt': formatar_dinheiro(d['valor']),
            'categoria': d['categoria'] or '—',
            'status': d['status']
        })

    return jsonify({
        'validas': preview_linhas,
        'erros': erros_csv,
        'total_validas': len(preview_linhas),
        'total_erros': len(erros_csv)
    })


@app.route('/download-modelo-csv')
@login_required
def download_modelo_csv():
    """
    Gera e retorna um arquivo CSV modelo para o usuário baixar.
    O modelo contém exemplos de como preencher cada coluna.
    """
    modelo = """tipo,data,descricao,valor,categoria,status
receita,2026-05-05,Salário,3500.00,,pago
receita,2026-05-15,Freelance,800.00,,pendente
despesa,2026-05-01,Aluguel,1500.00,Moradia,pago
despesa,2026-05-03,Supermercado,450.00,Alimentação,pago
despesa,2026-05-10,Uber,35.50,Transporte,pendente
despesa,2026-05-12,Farmácia,89.90,Saúde,pago
despesa,2026-05-20,Netflix,55.90,Lazer,pendente"""

    return Response(
        modelo,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=modelo_troqui.csv'}
    )


# ═══════════════════════════════════════════════════════
# INICIALIZAÇÃO
# O bloco if __name__ == '__main__' só executa quando
# rodamos diretamente: python app.py
# Não executa se importarmos este módulo de outro lugar.
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    # Cria o banco de dados (se não existir)
    db.iniciar_banco()

    print("""
==========================================
    FinanceControl — Servidor Flask      
                                         
 PC:      http://localhost:8080          
 Celular: http://SEU_IP:8080            
                                         
 Auto-reload ATIVADO!                 
 Edite qualquer arquivo e o servidor     
 recarrega sozinho. Basta dar F5!        
                                         
 Pressione Ctrl+C para encerrar.         
==========================================
""")

    # debug=True = Recarrega automaticamente ao editar arquivos!
    # host='0.0.0.0' = Aceita conexões do celular na mesma rede
    # port=8080 = Mesma porta do servidor anterior
    app.run(host='0.0.0.0', port=8080, debug=True)
