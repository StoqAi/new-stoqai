import csv
from flask import Response
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import re
from datetime import datetime, date
from decimal import Decimal

app = Flask(__name__)

def conectar_mysql():
        """
        Conecta ao banco de dados MySQL usando as credenciais locais.
        Retorna uma conexão ativa para uso nas operações SQL.
        Lista todas as vendas realizadas, incluindo dados do cliente.
        Retorna o template 'vendas.html' com a lista de vendas.
        """
        return mysql.connector.connect(
        host="localhost",
        user="root",
        password="henry",
        database="estoque_loja"
    )

@app.route('/')
def index():
    '''
    Página inicial do sistema. Exibe lista de produtos com informações de categoria, fornecedor e estoque.
    - Consulta todos os produtos, juntando com categoria e fornecedor.
    - Identifica produtos com estoque baixo (<=5).
    - Retorna o template 'index.html' com as listas 'produtos' e 'estoque_baixo'.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            Produto.IdProduto, Produto.Nome,
            Categoria.Nome AS NomeCategoria,
            Fornecedor.Nome AS NomeFornecedor,
            Produto.Preco, Produto.Descricao,
            Produto.IdCategoria, Produto.IdFornecedor,
            Estoque.Quantidade
        FROM Produto
        JOIN Estoque ON Produto.IdProduto = Estoque.IdProduto
        LEFT JOIN Categoria ON Produto.IdCategoria = Categoria.IdCategoria
        LEFT JOIN Fornecedor ON Produto.IdFornecedor = Fornecedor.IdFornecedor
    """)
    produtos = cursor.fetchall()
    conn.close()
    estoque_baixo = [p for p in produtos if p.get('Quantidade', 0) <= 5]
    return render_template('index.html', produtos=produtos, estoque_baixo=estoque_baixo)


@app.route('/atualizar_estoque/<int:id>', methods=['GET', 'POST'])
def atualizar_estoque(id):
    '''
    Atualiza os dados de um produto e seu estoque.
    Parâmetros:
        id (int): ID do produto a ser atualizado.
    Fluxo:
        - Busca dados do produto, categorias e fornecedores.
        - Se POST, atualiza dados do produto e estoque, registra movimentação de ajuste.
        - Em caso de erro, exibe mensagem.
        - Retorna template de atualização com dados necessários.
    Variáveis:
        produto: dict com dados do produto
        categorias: lista de categorias
        fornecedores: lista de fornecedores
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Produto.IdProduto, Produto.Nome, Produto.Preco, Produto.Descricao,
               Produto.IdCategoria, Produto.IdFornecedor, Estoque.Quantidade
        FROM Produto
        JOIN Estoque ON Produto.IdProduto = Estoque.IdProduto
        WHERE Produto.IdProduto = %s
    """, (id,))
    produto = cursor.fetchone()
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT IdFornecedor, Nome FROM Fornecedor")
    fornecedores = cursor.fetchall()

    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        descricao = request.form.get('descricao')
        id_categoria = request.form.get('id_categoria')
        id_fornecedor = request.form.get('id_fornecedor') or None
        quantidade = request.form.get('quantidade')

        try:
            cursor2 = conn.cursor()
            cursor2.execute(
                "UPDATE Produto SET Nome=%s, Preco=%s, Descricao=%s, IdCategoria=%s, IdFornecedor=%s WHERE IdProduto=%s",
                (nome, preco, descricao, id_categoria, id_fornecedor, id)
            )
            cursor2.execute(
                "UPDATE Estoque SET Quantidade=%s WHERE IdProduto=%s",
                (quantidade, id)
            )
            cursor2.execute(
                "INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)",
                ("ajuste", id, quantidade)
            )
            conn.commit()
            cursor2.close()
        except Exception as e:
            conn.close()
            return render_template('atualizar_estoque.html', erro=f'Erro ao atualizar: {e}', produto=produto, categorias=categorias, fornecedores=fornecedores)
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('atualizar_estoque.html', produto=produto, categorias=categorias, fornecedores=fornecedores)



@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    '''
    Cadastra um novo produto e seu estoque inicial.
    Fluxo:
        Busca categorias e fornecedores para o formulário.
        Se POST, insere produto, estoque e registra movimentação de entrada.
        Em caso de erro, exibe mensagem.
        Retorna template de cadastro.
    Variáveis:
        categorias: lista de categorias
        fornecedores: lista de fornecedores
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT IdFornecedor, Nome FROM Fornecedor")
    fornecedores = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        nome = request.form.get('nome')
        id_categoria = request.form.get('id_categoria')
        quantidade = request.form.get('quantidade')
        preco = request.form.get('preco')
        descricao = request.form.get('descricao')
        id_fornecedor = request.form.get('id_fornecedor') or None
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Produto (Nome, Preco, Descricao, IdCategoria, IdFornecedor) VALUES (%s, %s, %s, %s, %s)",
                (nome, preco, descricao, id_categoria, id_fornecedor)
            )
            id_produto = cursor.lastrowid
            cursor.execute(
                "INSERT INTO Estoque (IdProduto, Quantidade) VALUES (%s, %s)",
                (id_produto, quantidade)
            )
            cursor.execute(
                "INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)",
                ("entrada", id_produto, quantidade)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            return render_template('cadastrar.html', erro=f'Erro ao cadastrar: {e}', categorias=categorias, fornecedores=fornecedores)

        return redirect(url_for('index'))

    return render_template('cadastrar.html', categorias=categorias, fornecedores=fornecedores)



@app.route('/aumentar/<int:id_produto>', methods=['POST'])
def aumentar(id_produto):
    '''
    Aumenta a quantidade de um produto no estoque.
    Parâmetros:
        id_produto (int): ID do produto a ser ajustado.
    Fluxo:
        Atualiza o estoque e registra movimentação de entrada.
    '''
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade + %s WHERE IdProduto = %s", (qtd, id_produto))
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("entrada", id_produto, qtd))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/reduzir/<int:id_produto>', methods=['POST'])
def reduzir(id_produto):
    '''
    Reduz a quantidade de um produto no estoque.
    Parâmetros:
        id_produto (int): ID do produto a ser ajustado.
    Fluxo:
        Atualiza o estoque e registra movimentação de saída.
    '''
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade - %s WHERE IdProduto = %s AND Quantidade >= %s", (qtd, id_produto, qtd))
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("saida", id_produto, qtd))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/ajustar/<int:id_produto>', methods=['POST'])
def ajustar(id_produto):
    '''
    Ajusta manualmente a quantidade de um produto no estoque.
    Parâmetros:
        id_produto (int): ID do produto a ser ajustado.
    Fluxo:
        Atualiza o estoque e registra movimentação de ajuste.
    '''
    nova_qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = %s WHERE IdProduto = %s", (nova_qtd, id_produto))
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("ajuste", id_produto, nova_qtd))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/excluir/<int:id_produto>', methods=['POST'])
def excluir(id_produto):
    '''
    Exclui um produto e seu estoque do sistema.
    Parâmetros:
        id_produto (int): ID do produto a ser excluído.
    Fluxo:
        Remove registros de estoque e produto.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Estoque WHERE IdProduto = %s", (id_produto,))
    cursor.execute("DELETE FROM Produto WHERE IdProduto = %s", (id_produto,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/fornecedores/')
def fornecedores():
    '''
    Lista todos os fornecedores cadastrados, incluindo dados de contato e endereço.
    Retorna o template 'fornecedores.html' com a lista de fornecedores.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
               Contato.Telefone, Contato.Email,
               Endereco.NomeRua, Endereco.Num, Endereco.CEP, Endereco.Bairro, Endereco.Cidade, Endereco.Estado
        FROM Fornecedor
        LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
        LEFT JOIN Endereco ON Fornecedor.IdEndereco = Endereco.IdEndereco
    """)
    fornecedores = cursor.fetchall()
    conn.close()
    return render_template('fornecedores.html', fornecedores=fornecedores)

@app.route('/fornecedores/novo', methods=['GET', 'POST'])
def novo_fornecedor():
    '''
    Cadastra um novo fornecedor, incluindo endereço e contato.
    Fluxo:
        Se POST, insere endereço, contato e fornecedor.
        Em caso de erro, exibe mensagem.
        Retorna template de cadastro de fornecedor.
    '''
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        rua = request.form.get('rua')
        numero = request.form.get('numero')
        cep = request.form.get('cep')
        complemento = request.form.get('complemento')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Endereco (NomeRua, Num, CEP, Complemento, Bairro, Cidade, Estado) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (rua, numero, cep, complemento, bairro, cidade, estado)
            )
            id_endereco = cursor.lastrowid
            cursor.execute("INSERT INTO Contato (Telefone, Email) VALUES (%s, %s)", (telefone, email))
            id_contato = cursor.lastrowid
            cursor.execute("INSERT INTO Fornecedor (Nome, CNPJ, IdContato, IdEndereco) VALUES (%s, %s, %s, %s)", (nome, cnpj, id_contato, id_endereco))
            conn.commit()
            conn.close()
            return redirect(url_for('fornecedores'))
        except Exception as e:
            erro = f'Erro ao cadastrar fornecedor: {e}'
    return render_template('fornecedor_form.html', erro=erro, fornecedor=None)

@app.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    '''
    Edita os dados de um fornecedor existente.
    Parâmetros:
        id (int): ID do fornecedor a ser editado.
    Fluxo:
        Busca dados do fornecedor, endereço e contato.
        Se POST, atualiza os dados.
        Em caso de erro, exibe mensagem.
        Retorna template de edição de fornecedor.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
               Contato.Telefone, Contato.Email, Fornecedor.IdContato,
               Endereco.IdEndereco, Endereco.NomeRua as Rua, Endereco.Num as Numero, Endereco.CEP, 
               Endereco.Complemento, Endereco.Bairro, Endereco.Cidade, Endereco.Estado
        FROM Fornecedor
        LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
        LEFT JOIN Endereco ON Fornecedor.IdEndereco = Endereco.IdEndereco
        WHERE Fornecedor.IdFornecedor = %s
    """, (id,))
    fornecedor = cursor.fetchone()
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        rua = request.form.get('rua')
        numero = request.form.get('numero')
        cep = request.form.get('cep')
        complemento = request.form.get('complemento')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        try:
            cursor2 = conn.cursor()
            
            cursor2.execute("UPDATE Fornecedor SET Nome=%s, CNPJ=%s WHERE IdFornecedor=%s", (nome, cnpj, id))
            
            cursor2.execute("UPDATE Contato SET Telefone=%s, Email=%s WHERE IdContato=%s", (telefone, email, fornecedor['IdContato']))
            
            cursor2.execute(
                "UPDATE Endereco SET NomeRua=%s, Num=%s, CEP=%s, Complemento=%s, Bairro=%s, Cidade=%s, Estado=%s WHERE IdEndereco=%s",
                (rua, numero, cep, complemento, bairro, cidade, estado, fornecedor['IdEndereco'])
            )
            conn.commit()
            cursor2.close()
            conn.close()
            return redirect(url_for('fornecedores'))
        except Exception as e:
            erro = f'Erro ao editar fornecedor: {e}'
    conn.close()
    return render_template('fornecedor_form.html', erro=erro, fornecedor=fornecedor)

@app.route('/fornecedores/excluir/<int:id>', methods=['POST'])
def excluir_fornecedor(id):
    '''
    Exclui um fornecedor do sistema, se não houver produtos vinculados.
    Parâmetros:
        id (int): ID do fornecedor a ser excluído.
    Fluxo:
        Verifica dependências, exclui fornecedor e contato.
        Em caso de erro, exibe mensagem.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM Produto WHERE IdFornecedor = %s", (id,))
        result = cursor.fetchone()
        if result and result['total'] > 0:
            conn.close()
            erro = "Não é possível excluir: existem produtos cadastrados com este fornecedor."
            conn2 = conectar_mysql()
            cursor2 = conn2.cursor(dictionary=True)
            cursor2.execute("""
                SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
                       Contato.Telefone, Contato.Email, Fornecedor.IdContato
                FROM Fornecedor
                LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
                WHERE Fornecedor.IdFornecedor = %s
            """, (id,))
            fornecedor = cursor2.fetchone()
            conn2.close()
            return render_template('fornecedor_form.html', fornecedor=fornecedor, erro=erro)
        cursor.execute("SELECT IdContato FROM Fornecedor WHERE IdFornecedor=%s", (id,))
        fornecedor = cursor.fetchone()
        id_contato = fornecedor['IdContato'] if fornecedor else None
        cursor.execute("DELETE FROM Fornecedor WHERE IdFornecedor=%s", (id,))
        if id_contato:
            cursor.execute("DELETE FROM Contato WHERE IdContato=%s", (id_contato,))
        conn.commit()
        conn.close()
    except Exception as e:
        
        erro = f"Erro ao excluir fornecedor: {e}"
        conn2 = conectar_mysql()
        cursor2 = conn2.cursor(dictionary=True)
        cursor2.execute("""
            SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
                   Contato.Telefone, Contato.Email, Fornecedor.IdContato
            FROM Fornecedor
            LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
            WHERE Fornecedor.IdFornecedor = %s
        """, (id,))
        fornecedor = cursor2.fetchone()
        conn2.close()
        return render_template('fornecedor_form.html', fornecedor=fornecedor, erro=erro)
    return redirect(url_for('fornecedores'))


@app.route('/categorias/')
def categorias():
    '''
    Lista todas as categorias cadastradas.
    Retorna o template 'categorias.html' com a lista de categorias.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria ORDER BY IdCategoria ASC")
    categorias = cursor.fetchall()
    conn.close()
    return render_template('categorias.html', categorias=categorias)

@app.route('/categorias/novo', methods=['GET', 'POST'])
def nova_categoria():
    '''
    Cadastra uma nova categoria de produto.
    Fluxo:
        Se POST, insere categoria.
        Em caso de erro, exibe mensagem.
        Retorna template de cadastro de categoria.
    '''
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Categoria (Nome) VALUES (%s)", (nome,))
            conn.commit()
            conn.close()
            return redirect(url_for('categorias'))
        except Exception as e:
            erro = f'Erro ao cadastrar categoria: {e}'
    return render_template('categoria_form.html', erro=erro, categoria=None)

@app.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    '''
    Edita os dados de uma categoria existente.
    Parâmetros:
        id (int): ID da categoria a ser editada.
    Fluxo:
        Busca dados da categoria.
        Se POST, atualiza os dados.
        Em caso de erro, exibe mensagem.
        Retorna template de edição de categoria.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
    categoria = cursor.fetchone()
    erro = None
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            cursor2 = conn.cursor()
            
            cursor2.execute("UPDATE Categoria SET Nome=%s WHERE IdCategoria=%s", (nome, id))
            conn.commit()
            cursor2.close()
            conn.close()
            
            return redirect(url_for('categorias'))
        except Exception as e:
            
            erro = f'Erro ao editar categoria: {e}'
    conn.close()
    
    return render_template('categoria_form.html', erro=erro, categoria=categoria)

@app.route('/categorias/excluir/<int:id>', methods=['POST'])
def excluir_categoria(id):
    '''
    Exclui uma categoria do sistema, se não houver produtos vinculados.
    Parâmetros:
        id (int): ID da categoria a ser excluída.
    Fluxo:
        Verifica dependências, exclui categoria.
        Em caso de erro, exibe mensagem.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) AS total FROM Produto WHERE IdCategoria = %s", (id,))
        result = cursor.fetchone()
        if result and result['total'] > 0:
            conn.close()
            
            erro = "Não é possível excluir: existem produtos cadastrados com esta categoria."
            conn2 = conectar_mysql()
            cursor2 = conn2.cursor(dictionary=True)
            cursor2.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
            categoria = cursor2.fetchone()
            conn2.close()
            return render_template('categoria_form.html', categoria=categoria, erro=erro)
        
        cursor.execute("DELETE FROM Categoria WHERE IdCategoria=%s", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        
        erro = f"Erro ao excluir categoria: {e}"
        conn2 = conectar_mysql()
        cursor2 = conn2.cursor(dictionary=True)
        cursor2.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
        categoria = cursor2.fetchone()
        conn2.close()
        return render_template('categoria_form.html', categoria=categoria, erro=erro)
    
    return redirect(url_for('categorias'))


    
@app.route('/vendas/')
def vendas():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.IdVenda, v.DataVenda, v.ValorTotal, v.Desconto, v.ValorFinal, 
               v.Status, c.Nome AS NomeCliente
        FROM Venda v
        LEFT JOIN Cliente c ON v.IdCliente = c.IdCliente
        ORDER BY v.DataVenda DESC
    """)
    vendas = cursor.fetchall()
    conn.close()
    return render_template('vendas.html', vendas=vendas)

    
def processar_venda():
    '''
    Processa uma nova venda, atualizando estoque e registrando movimentações.
    Fluxo:
        Valida itens, calcula totais, insere venda e itens, atualiza estoque, registra movimentações.
        Em caso de erro, retorna formulário com mensagem.
    Variáveis:
        itens_venda: lista de itens vendidos
        valor_total_bruto: valor total sem descontos
        total_descontos_produtos: descontos por produto
        total_descontos: descontos totais
        valor_final: valor final da venda
    '''
    try:
        
        id_cliente = request.form.get('id_cliente') or None
        id_promocao = request.form.get('id_promocao') or None
        desconto_geral = float(request.form.get('desconto_geral', 0))
        
        produtos_ids = request.form.getlist('produto_id[]')
        quantidades = request.form.getlist('quantidade[]')
        descontos_produto = request.form.getlist('desconto_produto[]')
        
        if not produtos_ids:
            raise Exception("Nenhum produto selecionado para a venda")
        
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        
        itens_venda = []
        valor_total_bruto = 0
        total_descontos_produtos = 0
        
        for i, produto_id in enumerate(produtos_ids):
            if not produto_id:
                continue
            quantidade = int(quantidades[i])
            desconto_produto = float(descontos_produto[i]) if descontos_produto[i] else 0
            cursor.execute("""
                SELECT p.Preco, e.Quantidade 
                FROM Produto p 
                JOIN Estoque e ON p.IdProduto = e.IdProduto 
                WHERE p.IdProduto = %s
            """, (produto_id,))
            produto_info = cursor.fetchone()
            
            if not produto_info:
                raise Exception(f"Produto {produto_id} não encontrado")
            
            if produto_info['Quantidade'] < quantidade:
                raise Exception(f"Estoque insuficiente para o produto {produto_id}")
            
            preco_unitario = float(produto_info['Preco'])
            subtotal_bruto = preco_unitario * quantidade
            subtotal_final = subtotal_bruto - desconto_produto
            
            valor_total_bruto += subtotal_bruto
            total_descontos_produtos += desconto_produto
            
            itens_venda.append({
                'produto_id': produto_id,
                'quantidade': quantidade,
                'preco_unitario': preco_unitario,
                'subtotal': subtotal_final,
                'desconto_produto': desconto_produto
            })
        
        
        total_descontos = total_descontos_produtos + desconto_geral
        valor_final = valor_total_bruto - total_descontos
        
        
        cursor.execute("""
            INSERT INTO Venda (ValorTotal, Desconto, ValorFinal, IdCliente) 
            VALUES (%s, %s, %s, %s)
        """, (valor_total_bruto, total_descontos, valor_final, id_cliente))
        
        id_venda = cursor.lastrowid
        
        
        for item in itens_venda:
            cursor.execute("""
                INSERT INTO ItemVenda (IdVenda, IdProduto, Quantidade, PrecoUnitario, Subtotal, DescontoProduto) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_venda, item['produto_id'], item['quantidade'], 
                  item['preco_unitario'], item['subtotal'], item['desconto_produto']))
            
            cursor.execute("""
                UPDATE Estoque SET Quantidade = Quantidade - %s WHERE IdProduto = %s
            """, (item['quantidade'], item['produto_id']))
            
            cursor.execute("""
                INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)
            """, ("venda", item['produto_id'], item['quantidade']))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('recibo_venda', id_venda=id_venda))
        
    except Exception as e:
        
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT IdCliente, Nome FROM Cliente ORDER BY Nome")
        clientes = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.IdProduto, p.Nome, p.Preco, e.Quantidade 
            FROM Produto p 
            JOIN Estoque e ON p.IdProduto = e.IdProduto 
            WHERE e.Quantidade > 0 
            ORDER BY p.Nome
        """)
        produtos = cursor.fetchall()
        
        cursor.execute("""
            SELECT IdPromocao, Nome, TipoDesconto, ValorDesconto 
            FROM Promocao 
            WHERE Ativa = 1 AND DataInicio <= CURDATE() AND DataFim >= CURDATE()
            ORDER BY Nome
        """)
        promocoes = cursor.fetchall()
        
        conn.close()
        
        return render_template('nova_venda.html', erro=f'Erro ao processar venda: {e}', 
                             clientes=clientes, produtos=produtos, promocoes=promocoes)

    
@app.route('/vendas/recibo/<int:id_venda>')
def recibo_venda(id_venda):
    '''
    Exibe o recibo de uma venda específica, incluindo dados do cliente e itens vendidos.
    Parâmetros:
        id_venda (int): ID da venda a ser exibida.
    Variáveis:
        venda: dict com dados da venda e cliente
        itens: lista de itens vendidos
    Retorno:
        Renderiza o template 'recibo_venda.html' com os dados da venda e itens.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.IdVenda, v.DataVenda, v.ValorTotal, v.Desconto, v.ValorFinal,
               c.Nome AS NomeCliente, c.CPF,
               cont.Email, cont.Telefone
        FROM Venda v
        LEFT JOIN Cliente c ON v.IdCliente = c.IdCliente
        LEFT JOIN Contato cont ON c.IdContato = cont.IdContato
        WHERE v.IdVenda = %s
    """, (id_venda,))
    venda = cursor.fetchone()
    cursor.execute("""
        SELECT iv.Quantidade, iv.PrecoUnitario, iv.Subtotal, iv.DescontoProduto,
               p.Nome AS NomeProduto
        FROM ItemVenda iv
        JOIN Produto p ON iv.IdProduto = p.IdProduto
        WHERE iv.IdVenda = %s
    """, (id_venda,))
    itens = cursor.fetchall()
    conn.close()
    if not venda:
        return redirect(url_for('vendas'))
    return render_template('recibo_venda.html', venda=venda, itens=itens)

    
@app.route('/vendas/cancelar/<int:id_venda>', methods=['POST'])
def cancelar_venda(id_venda):
    '''
    Cancela uma venda, restituindo o estoque dos itens vendidos.
    Parâmetros:
        id_venda (int): ID da venda a ser cancelada.
    Variáveis:
        itens: lista de itens da venda
    Retorno:
        Atualiza estoque, altera status da venda e redireciona para a lista de vendas.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT IdProduto, Quantidade FROM ItemVenda WHERE IdVenda = %s
        """, (id_venda,))
        itens = cursor.fetchall()
        for item in itens:
            cursor.execute("""
                UPDATE Estoque SET Quantidade = Quantidade + %s WHERE IdProduto = %s
            """, (item['Quantidade'], item['IdProduto']))
        cursor.execute("""
            UPDATE Venda SET Status = 'Cancelada' WHERE IdVenda = %s
        """, (id_venda,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    return redirect(url_for('vendas'))


    
@app.route('/promocoes/nova', methods=['GET', 'POST'])
def nova_promocao():
    '''
    Cadastra uma nova promoção.
    Fluxo:
        Valida datas, insere promoção.
        Em caso de erro, exibe mensagem.
    Variáveis:
        erro: mensagem de erro (se houver)
        nome, tipo_desconto, valor_desconto, data_inicio, data_fim: dados do formulário
    Retorno:
        Renderiza o template 'promocao_form.html' ou redireciona para lista de promoções.
    '''
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        tipo_desconto = request.form.get('tipo_desconto')
        valor_desconto = request.form.get('valor_desconto')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            data_fim_obj = datetime.strptime(data_fim, '%d/%m/%Y').date()
            data_inicio_mysql = data_inicio_obj.strftime('%Y-%m-%d')
            data_fim_mysql = data_fim_obj.strftime('%Y-%m-%d')
            data_hoje = date.today()
            if data_inicio_obj < data_hoje:
                raise Exception("A data de início não pode ser anterior ao dia atual")
            if data_fim_obj < data_inicio_obj:
                raise Exception("A data de fim não pode ser anterior à data de início")
        except ValueError:
            raise Exception("Formato de data inválido")
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Promocao (Nome, TipoDesconto, ValorDesconto, DataInicio, DataFim) 
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, tipo_desconto, valor_desconto, data_inicio_mysql, data_fim_mysql))
            conn.commit()
            conn.close()
            return redirect(url_for('promocoes'))
        except Exception as e:
            erro = f'Erro ao cadastrar promoção: {e}'
    return render_template('promocao_form.html', erro=erro, promocao=None)

    
@app.route('/promocoes/editar/<int:id>', methods=['GET', 'POST'])
def editar_promocao(id):
    '''
    Edita os dados de uma promoção existente.
    Parâmetros:
        id (int): ID da promoção a ser editada.
    Variáveis:
        promocao: dict com dados da promoção
        erro: mensagem de erro (se houver)
        nome, tipo_desconto, valor_desconto, data_inicio, data_fim, ativa: dados do formulário
    Retorno:
        Renderiza o template 'promocao_form.html' ou redireciona para lista de promoções.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Promocao WHERE IdPromocao = %s", (id,))
    promocao = cursor.fetchone()
    if not promocao:
        conn.close()
        return redirect(url_for('promocoes'))
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        tipo_desconto = request.form.get('tipo_desconto')
        valor_desconto = request.form.get('valor_desconto')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        ativa = request.form.get('ativa', '1')
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            data_fim_obj = datetime.strptime(data_fim, '%d/%m/%Y').date()
            data_inicio_mysql = data_inicio_obj.strftime('%Y-%m-%d')
            data_fim_mysql = data_fim_obj.strftime('%Y-%m-%d')
            data_hoje = date.today()
            promocao_data_inicio = promocao['DataInicio']
            if isinstance(promocao_data_inicio, str):
                promocao_data_inicio = datetime.strptime(promocao_data_inicio, '%Y-%m-%d').date()
            if promocao_data_inicio > data_hoje and data_inicio_obj < data_hoje:
                raise Exception("A data de início não pode ser anterior ao dia atual")
            if data_fim_obj < data_inicio_obj:
                raise Exception("A data de fim não pode ser anterior à data de início")
        except ValueError:
            raise Exception("Formato de data inválido")
        except Exception as e:
            erro = str(e)
        if not erro:
            try:
                cursor.execute("""
                    UPDATE Promocao SET Nome=%s, TipoDesconto=%s, ValorDesconto=%s, 
                           DataInicio=%s, DataFim=%s, Ativa=%s 
                    WHERE IdPromocao=%s
                """, (nome, tipo_desconto, valor_desconto, data_inicio_mysql, data_fim_mysql, ativa, id))
                conn.commit()
                conn.close()
                return redirect(url_for('promocoes'))
            except Exception as e:
                erro = f'Erro ao editar promoção: {e}'
    conn.close()
    return render_template('promocao_form.html', erro=erro, promocao=promocao)

    
def atualizar_status_promocoes():
    '''
    Atualiza automaticamente o status das promoções (ativa/desativa conforme datas).
    Fluxo:
        Desativa promoções vencidas, ativa promoções válidas.
    Variáveis:
        conn, cursor: conexão e cursor do banco
    Retorno:
        Atualiza status das promoções no banco de dados.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Promocao 
            SET Ativa = 0 
            WHERE DataFim < CURDATE() AND Ativa = 1
        """)
        cursor.execute("""
            UPDATE Promocao 
            SET Ativa = 1 
            WHERE DataInicio <= CURDATE() AND DataFim >= CURDATE() AND Ativa = 0
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar status das promoções: {e}")

@app.route('/promocoes')
def promocoes():
    '''
    Exibe lista de promoções cadastradas, atualizando status conforme datas.
    Fluxo:
        Atualiza status das promoções, consulta todas promoções ordenadas por data de início.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        promocoes: lista de promoções (dict)
    Retorno:
        Renderiza template 'promocoes.html' com promoções.
    '''
    atualizar_status_promocoes()
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT IdPromocao, Nome, TipoDesconto, ValorDesconto, DataInicio, DataFim, Ativa
        FROM Promocao 
        ORDER BY DataInicio DESC
    """)
    promocoes = cursor.fetchall()
    conn.close()
    
    return render_template('promocoes.html', promocoes=promocoes)

@app.route('/vendas/nova', methods=['GET', 'POST'])
def nova_venda():
    '''
    Exibe formulário para cadastrar nova venda e processa venda se método POST.
    Fluxo:
        Atualiza status das promoções, busca clientes, produtos e promoções disponíveis.
        Se POST, processa venda.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        clientes: lista de clientes
        produtos: lista de produtos disponíveis
        promocoes: lista de promoções ativas
    Retorno:
        Renderiza template 'nova_venda.html' ou redireciona após venda.
    '''
    if request.method == 'POST':
        return processar_venda()
    atualizar_status_promocoes()
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCliente, Nome FROM Cliente ORDER BY Nome")
    clientes = cursor.fetchall()
    cursor.execute("""
        SELECT p.IdProduto, p.Nome, p.Preco, e.Quantidade 
        FROM Produto p 
        JOIN Estoque e ON p.IdProduto = e.IdProduto 
        WHERE e.Quantidade > 0 
        ORDER BY p.Nome
    """)
    produtos = cursor.fetchall()
    cursor.execute("""
        SELECT IdPromocao, Nome, TipoDesconto, ValorDesconto 
        FROM Promocao 
        WHERE Ativa = 1 AND DataInicio <= CURDATE() AND DataFim >= CURDATE()
        ORDER BY Nome
    """)
    promocoes = cursor.fetchall()
    conn.close()
    return render_template('nova_venda.html', clientes=clientes, produtos=produtos, promocoes=promocoes)

@app.route('/promocoes/excluir/<int:id>', methods=['POST'])
def excluir_promocao(id):
    '''
    Exclui uma promoção do sistema pelo ID informado.
    Parâmetros:
        id (int): ID da promoção a ser excluída.
    Fluxo:
        Tenta excluir a promoção do banco de dados.
        Em caso de erro, ignora e redireciona.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
    Retorno:
        Redireciona para a lista de promoções.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Promocao WHERE IdPromocao=%s", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    return redirect(url_for('promocoes'))

@app.route('/relatorios')
def relatorios():
    '''
    Página inicial dos relatórios, com links para diferentes tipos de relatórios.
    '''
    return render_template('relatorios.html')

@app.route('/relatorios/vendas')
def relatorio_vendas():
    '''
    Gera relatório de vendas, listando todas as vendas realizadas.
    Fluxo:
        Consulta vendas e itens relacionados, ordena por data.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        vendas: lista de vendas (dict)
    Retorno:
        Renderiza template 'relatorio_vendas.html' com vendas.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(''' 
        SELECT Venda.IdVenda, Venda.DataVenda, Venda.ValorTotal, 
               ItemVenda.IdProduto, Produto.Nome AS NomeProduto, ItemVenda.Quantidade, ItemVenda.PrecoUnitario 
        FROM Venda 
        JOIN ItemVenda ON Venda.IdVenda = ItemVenda.IdVenda 
        JOIN Produto ON ItemVenda.IdProduto = Produto.IdProduto 
        ORDER BY Venda.DataVenda DESC, Venda.IdVenda DESC 
    ''')
    vendas = cursor.fetchall()
    conn.close()
    
    from collections import defaultdict
    vendas_dict = defaultdict(lambda: {'itens': []})
    for v in vendas:
        venda_id = v['IdVenda']
        if 'DataVenda' not in vendas_dict[venda_id]:
            vendas_dict[venda_id]['DataVenda'] = v['DataVenda']
            vendas_dict[venda_id]['ValorTotal'] = v['ValorTotal']
        vendas_dict[venda_id]['itens'].append({
            'IdProduto': v['IdProduto'],
            'NomeProduto': v['NomeProduto'],
            'Quantidade': v['Quantidade'],
            'PrecoUnitario': v['PrecoUnitario']
        })
    return render_template('relatorio_vendas.html', vendas=vendas_dict)

@app.route('/relatorios/estoque')
def relatorio_estoque():
    '''
    Gera relatório de estoque, listando todos os produtos com suas quantidades.
    Fluxo:
        Consulta produtos e suas quantidades no estoque.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        produtos: lista de produtos (dict)
    Retorno:
        Renderiza template 'relatorio_estoque.html' com produtos.
    '''
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(''' 
            SELECT Produto.IdProduto, Produto.Nome, Estoque.Quantidade
            FROM Produto
            JOIN Estoque ON Produto.IdProduto = Estoque.IdProduto
            ORDER BY Produto.Nome ASC
        ''')
        produtos = cursor.fetchall()
        conn.close()
        return render_template('relatorio_estoque.html', produtos=produtos)
    except Exception as e:
        return f"Erro ao gerar relatório de estoque: {e}"

@app.route('/relatorios/movimentacoes')
def relatorio_movimentacoes():
    '''
    Gera relatório de movimentações de estoque, listando todas as entradas e saídas.
    Fluxo:
        Consulta movimentações e produtos relacionados, ordena por data.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        movimentacoes: lista de movimentações (dict)
    Retorno:
        Renderiza template 'relatorio_movimentacoes.html' com movimentações.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT M.IdMovimentacao, M.DataMovimentacao, M.Tipo, M.Quantidade, M.IdProduto, Produto.Nome AS NomeProduto
        FROM MovimentacaoEstoque M
        JOIN Produto ON M.IdProduto = Produto.IdProduto
        ORDER BY M.DataMovimentacao DESC, M.IdMovimentacao DESC
    ''')
    movimentacoes = cursor.fetchall()
    conn.close()
    return render_template('relatorio_movimentacoes.html', movimentacoes=movimentacoes)

@app.route('/relatorios/vendas/csv')
def relatorio_vendas_csv():
    '''
    Gera relatório de vendas em formato CSV para download.
    Fluxo:
        Consulta vendas e itens relacionados, gera linhas CSV.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        vendas: lista de vendas (dict)
    Retorno:
        Response com conteúdo CSV e cabeçalho para download.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT Venda.IdVenda, Venda.DataVenda, Venda.ValorTotal,
               ItemVenda.IdProduto, Produto.Nome AS NomeProduto, ItemVenda.Quantidade, ItemVenda.PrecoUnitario
        FROM Venda
        JOIN ItemVenda ON Venda.IdVenda = ItemVenda.IdVenda
        JOIN Produto ON ItemVenda.IdProduto = Produto.IdProduto
        ORDER BY Venda.DataVenda DESC, Venda.IdVenda DESC
    ''')
    vendas = cursor.fetchall()
    conn.close()

    def generate():
        yield 'IdVenda,DataVenda,ValorTotal,IdProduto,NomeProduto,Quantidade,PrecoUnitario\n'
        for v in vendas:
            yield f"{v['IdVenda']},{v['DataVenda']},{v['ValorTotal']},{v['IdProduto']},\"{v['NomeProduto']}\",{v['Quantidade']},{v['PrecoUnitario']}\n"
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=relatorio_vendas.csv"})

@app.route('/relatorios/estoque/csv')
def relatorio_estoque_csv():
    '''
    Gera relatório de estoque em formato CSV para download.
    Fluxo:
        Consulta produtos e suas quantidades, gera linhas CSV.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        produtos: lista de produtos (dict)
    Retorno:
        Response com conteúdo CSV e cabeçalho para download.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT Produto.IdProduto, Produto.Nome, Estoque.Quantidade
        FROM Produto
        JOIN Estoque ON Produto.IdProduto = Estoque.IdProduto
        ORDER BY Produto.Nome ASC
    ''')
    produtos = cursor.fetchall()
    conn.close()
    def generate():
        yield 'IdProduto,Nome,Quantidade\n'
        for p in produtos:
            yield f"{p['IdProduto']},\"{p['Nome']}\",{p['Quantidade']}\n"
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=relatorio_estoque.csv"})

@app.route('/relatorios/movimentacoes/csv')
def relatorio_movimentacoes_csv():
    '''
    Gera relatório de movimentações de estoque em formato CSV para download.
    Fluxo:
        Consulta movimentações e produtos relacionados, gera linhas CSV.
    Variáveis:
        conn: conexão MySQL
        cursor: cursor do banco
        movimentacoes: lista de movimentações (dict)
    Retorno:
        Response com conteúdo CSV e cabeçalho para download.
    '''
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT M.IdMovimentacao, M.DataMovimentacao, M.Tipo, M.Quantidade, M.IdProduto, Produto.Nome AS NomeProduto
        FROM MovimentacaoEstoque M
        JOIN Produto ON M.IdProduto = Produto.IdProduto
        ORDER BY M.DataMovimentacao DESC, M.IdMovimentacao DESC
    ''')
    movimentacoes = cursor.fetchall()
    conn.close()
    def generate():
        yield 'IdMovimentacao,DataMovimentacao,Tipo,Quantidade,IdProduto,NomeProduto\n'
        for m in movimentacoes:
            yield f"{m['IdMovimentacao']},{m['DataMovimentacao']},{m['Tipo']},{m['Quantidade']},{m['IdProduto']},\"{m['NomeProduto']}\"\n"
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=relatorio_movimentacoes.csv"})

if __name__ == '__main__':
    app.run(debug=True)

