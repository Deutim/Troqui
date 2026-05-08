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
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# datetime: trabalha com datas e horários
from datetime import datetime, date

# os: permite ler variáveis de ambiente (SECRET_KEY em produção)
import os

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
