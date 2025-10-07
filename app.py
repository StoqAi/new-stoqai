import csv
from flask import Response
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import re
from datetime import datetime, date
from decimal import Decimal


# Inicializa a aplicação Flask
app = Flask(__name__)


# Função para conectar ao banco de dados MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="henry",
        database="estoque_loja"
    )


# Rota da página inicial: exibe lista de produtos com informações de categoria, fornecedor e estoque
@app.route('/')
def index():
    # Conecta ao banco
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    # Consulta todos os produtos, juntando com categoria e fornecedor
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
    # Lista produtos com estoque baixo (<=5)
    estoque_baixo = [p for p in produtos if p.get('Quantidade', 0) <= 5]
    # Renderiza template passando lista de produtos e os de estoque baixo
    return render_template('index.html', produtos=produtos, estoque_baixo=estoque_baixo)


# Rota para atualizar dados de um produto e seu estoque
@app.route('/atualizar_estoque/<int:id>', methods=['GET', 'POST'])
def atualizar_estoque(id):
    # Busca dados do produto pelo id
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
    # Busca categorias e fornecedores para os selects do formulário
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT IdFornecedor, Nome FROM Fornecedor")
    fornecedores = cursor.fetchall()

    # Se o formulário foi enviado (POST), atualiza os dados
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        descricao = request.form.get('descricao')
        id_categoria = request.form.get('id_categoria')
        id_fornecedor = request.form.get('id_fornecedor') or None
        quantidade = request.form.get('quantidade')

        try:
            cursor2 = conn.cursor()
            # Atualiza dados do produto
            cursor2.execute(
                "UPDATE Produto SET Nome=%s, Preco=%s, Descricao=%s, IdCategoria=%s, IdFornecedor=%s WHERE IdProduto=%s",
                (nome, preco, descricao, id_categoria, id_fornecedor, id)
            )
            # Atualiza quantidade em estoque
            cursor2.execute(
                "UPDATE Estoque SET Quantidade=%s WHERE IdProduto=%s",
                (quantidade, id)
            )
            # Registra movimentação de ajuste
            cursor2.execute(
                "INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)",
                ("ajuste", id, quantidade)
            )
            conn.commit()
            cursor2.close()
        except Exception as e:
            conn.close()
            # Se der erro, mostra mensagem na tela
            return render_template('atualizar_estoque.html', erro=f'Erro ao atualizar: {e}', produto=produto, categorias=categorias, fornecedores=fornecedores)
        conn.close()
        # Redireciona para página inicial após atualizar
        return redirect(url_for('index'))

    conn.close()
    # Renderiza template de atualização de estoque
    return render_template('atualizar_estoque.html', produto=produto, categorias=categorias, fornecedores=fornecedores)


# Rota para cadastrar novo produto
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    # Busca categorias e fornecedores para o formulário
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT IdFornecedor, Nome FROM Fornecedor")
    fornecedores = cursor.fetchall()
    conn.close()

    # Se o formulário foi enviado (POST), insere novo produto e estoque
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
            # Insere produto
            cursor.execute(
                "INSERT INTO Produto (Nome, Preco, Descricao, IdCategoria, IdFornecedor) VALUES (%s, %s, %s, %s, %s)",
                (nome, preco, descricao, id_categoria, id_fornecedor)
            )
            id_produto = cursor.lastrowid
            # Insere estoque inicial
            cursor.execute(
                "INSERT INTO Estoque (IdProduto, Quantidade) VALUES (%s, %s)",
                (id_produto, quantidade)
            )
            # Registra movimentação de entrada inicial
            cursor.execute(
                "INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)",
                ("entrada", id_produto, quantidade)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            # Se der erro, mostra mensagem na tela
            return render_template('cadastrar.html', erro=f'Erro ao cadastrar: {e}', categorias=categorias, fornecedores=fornecedores)

        # Redireciona para página inicial após cadastrar
        return redirect(url_for('index'))

    # Renderiza template de cadastro
    return render_template('cadastrar.html', categorias=categorias, fornecedores=fornecedores)


# Rota para aumentar a quantidade de um produto no estoque
@app.route('/aumentar/<int:id_produto>', methods=['POST'])
def aumentar(id_produto):
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    # Soma quantidade ao estoque
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade + %s WHERE IdProduto = %s", (qtd, id_produto))
    # Registra movimentação de entrada
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("entrada", id_produto, qtd))
    conn.commit()
    conn.close()
    # Redireciona para página inicial
    return redirect(url_for('index'))


# Rota para reduzir a quantidade de um produto no estoque
@app.route('/reduzir/<int:id_produto>', methods=['POST'])
def reduzir(id_produto):
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    # Subtrai quantidade do estoque, se houver quantidade suficiente
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade - %s WHERE IdProduto = %s AND Quantidade >= %s", (qtd, id_produto, qtd))
    # Registra movimentação de saída
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("saida", id_produto, qtd))
    conn.commit()
    conn.close()
    # Redireciona para página inicial
    return redirect(url_for('index'))


# Rota para ajustar (definir) a quantidade de um produto no estoque
@app.route('/ajustar/<int:id_produto>', methods=['POST'])
def ajustar(id_produto):
    nova_qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    # Define nova quantidade no estoque
    cursor.execute("UPDATE Estoque SET Quantidade = %s WHERE IdProduto = %s", (nova_qtd, id_produto))
    # Registra movimentação de ajuste
    cursor.execute("INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)", ("ajuste", id_produto, nova_qtd))
    conn.commit()
    conn.close()
    # Redireciona para página inicial
    return redirect(url_for('index'))


# Rota para excluir um produto (remove do estoque e da tabela de produtos)
@app.route('/excluir/<int:id_produto>', methods=['POST'])
def excluir(id_produto):
    conn = conectar_mysql()
    cursor = conn.cursor()
    # Remove do estoque
    cursor.execute("DELETE FROM Estoque WHERE IdProduto = %s", (id_produto,))
    # Remove da tabela de produtos
    cursor.execute("DELETE FROM Produto WHERE IdProduto = %s", (id_produto,))
    conn.commit()
    conn.close()
    # Redireciona para página inicial
    return redirect(url_for('index'))


# Rota para listar fornecedores, incluindo dados de contato e endereço
@app.route('/fornecedores/')
def fornecedores():
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
    # Renderiza template de fornecedores
    return render_template('fornecedores.html', fornecedores=fornecedores)



# Rota para cadastrar novo fornecedor (inclui endereço e contato)
@app.route('/fornecedores/novo', methods=['GET', 'POST'])
def novo_fornecedor():
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
            # Insere endereço
            cursor.execute(
                "INSERT INTO Endereco (NomeRua, Num, CEP, Complemento, Bairro, Cidade, Estado) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (rua, numero, cep, complemento, bairro, cidade, estado)
            )
            id_endereco = cursor.lastrowid
            # Insere contato
            cursor.execute("INSERT INTO Contato (Telefone, Email) VALUES (%s, %s)", (telefone, email))
            id_contato = cursor.lastrowid
            # Insere fornecedor com FK de endereço e contato
            cursor.execute("INSERT INTO Fornecedor (Nome, CNPJ, IdContato, IdEndereco) VALUES (%s, %s, %s, %s)", (nome, cnpj, id_contato, id_endereco))
            conn.commit()
            conn.close()
            # Redireciona para lista de fornecedores
            return redirect(url_for('fornecedores'))
        except Exception as e:
            # Se der erro, mostra mensagem na tela
            erro = f'Erro ao cadastrar fornecedor: {e}'
    # Renderiza template de cadastro de fornecedor
    return render_template('fornecedor_form.html', erro=erro, fornecedor=None)


# Rota para editar dados de um fornecedor (inclui endereço e contato)
@app.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    # Busca dados do fornecedor pelo id
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
    # Se o formulário foi enviado (POST), atualiza os dados
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
            # Atualiza dados do fornecedor
            cursor2.execute("UPDATE Fornecedor SET Nome=%s, CNPJ=%s WHERE IdFornecedor=%s", (nome, cnpj, id))
            # Atualiza dados de contato
            cursor2.execute("UPDATE Contato SET Telefone=%s, Email=%s WHERE IdContato=%s", (telefone, email, fornecedor['IdContato']))
            # Atualiza dados de endereço
            cursor2.execute(
                "UPDATE Endereco SET NomeRua=%s, Num=%s, CEP=%s, Complemento=%s, Bairro=%s, Cidade=%s, Estado=%s WHERE IdEndereco=%s",
                (rua, numero, cep, complemento, bairro, cidade, estado, fornecedor['IdEndereco'])
            )
            conn.commit()
            cursor2.close()
            conn.close()
            # Redireciona para lista de fornecedores
            return redirect(url_for('fornecedores'))
        except Exception as e:
            # Se der erro, mostra mensagem na tela
            erro = f'Erro ao editar fornecedor: {e}'
    conn.close()
    # Renderiza template de edição de fornecedor
    return render_template('fornecedor_form.html', erro=erro, fornecedor=fornecedor)


# Rota para excluir fornecedor (verifica se não há produtos vinculados)
@app.route('/fornecedores/excluir/<int:id>', methods=['POST'])
def excluir_fornecedor(id):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        # Verifica se existe algum produto usando este fornecedor
        cursor.execute("SELECT COUNT(*) AS total FROM Produto WHERE IdFornecedor = %s", (id,))
        result = cursor.fetchone()
        if result and result['total'] > 0:
            conn.close()
            # Se houver produtos vinculados, não exclui e mostra erro
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
        # Busca o IdContato antes de excluir o fornecedor
        cursor.execute("SELECT IdContato FROM Fornecedor WHERE IdFornecedor=%s", (id,))
        fornecedor = cursor.fetchone()
        id_contato = fornecedor['IdContato'] if fornecedor else None
        # Exclui o fornecedor primeiro
        cursor.execute("DELETE FROM Fornecedor WHERE IdFornecedor=%s", (id,))
        # Depois exclui o contato, se existir
        if id_contato:
            cursor.execute("DELETE FROM Contato WHERE IdContato=%s", (id_contato,))
        conn.commit()
        conn.close()
    except Exception as e:
        # Se der erro, mostra mensagem na tela
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
    # Redireciona para lista de fornecedores
    return redirect(url_for('fornecedores'))


# Rota para listar categorias
@app.route('/categorias/')
def categorias():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria ORDER BY IdCategoria ASC")
    categorias = cursor.fetchall()
    conn.close()
    # Renderiza template de categorias
    return render_template('categorias.html', categorias=categorias)


# Rota para cadastrar nova categoria
@app.route('/categorias/novo', methods=['GET', 'POST'])
def nova_categoria():
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            # Insere nova categoria
            cursor.execute("INSERT INTO Categoria (Nome) VALUES (%s)", (nome,))
            conn.commit()
            conn.close()
            # Redireciona para lista de categorias
            return redirect(url_for('categorias'))
        except Exception as e:
            # Se der erro, mostra mensagem na tela
            erro = f'Erro ao cadastrar categoria: {e}'
    # Renderiza template de cadastro de categoria
    return render_template('categoria_form.html', erro=erro, categoria=None)


# Rota para editar categoria
@app.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    # Busca dados da categoria pelo id
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
    categoria = cursor.fetchone()
    erro = None
    # Se o formulário foi enviado (POST), atualiza os dados
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            cursor2 = conn.cursor()
            # Atualiza nome da categoria
            cursor2.execute("UPDATE Categoria SET Nome=%s WHERE IdCategoria=%s", (nome, id))
            conn.commit()
            cursor2.close()
            conn.close()
            # Redireciona para lista de categorias
            return redirect(url_for('categorias'))
        except Exception as e:
            # Se der erro, mostra mensagem na tela
            erro = f'Erro ao editar categoria: {e}'
    conn.close()
    # Renderiza template de edição de categoria
    return render_template('categoria_form.html', erro=erro, categoria=categoria)


# Rota para excluir categoria (verifica se não há produtos vinculados)
@app.route('/categorias/excluir/<int:id>', methods=['POST'])
def excluir_categoria(id):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        # Verifica se existe algum produto usando esta categoria
        cursor.execute("SELECT COUNT(*) AS total FROM Produto WHERE IdCategoria = %s", (id,))
        result = cursor.fetchone()
        if result and result['total'] > 0:
            conn.close()
            # Se houver produtos vinculados, não exclui e mostra erro
            erro = "Não é possível excluir: existem produtos cadastrados com esta categoria."
            conn2 = conectar_mysql()
            cursor2 = conn2.cursor(dictionary=True)
            cursor2.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
            categoria = cursor2.fetchone()
            conn2.close()
            return render_template('categoria_form.html', categoria=categoria, erro=erro)
        # Exclui categoria
        cursor.execute("DELETE FROM Categoria WHERE IdCategoria=%s", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        # Se der erro, mostra mensagem na tela
        erro = f"Erro ao excluir categoria: {e}"
        conn2 = conectar_mysql()
        cursor2 = conn2.cursor(dictionary=True)
        cursor2.execute("SELECT IdCategoria, Nome FROM Categoria WHERE IdCategoria = %s", (id,))
        categoria = cursor2.fetchone()
        conn2.close()
        return render_template('categoria_form.html', categoria=categoria, erro=erro)
    # Redireciona para lista de categorias
    return redirect(url_for('categorias'))


# Rota para listar vendas realizadas
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

# Função para processar a venda
def processar_venda():
    try:
        # Dados da venda
        id_cliente = request.form.get('id_cliente') or None
        id_promocao = request.form.get('id_promocao') or None
        desconto_geral = float(request.form.get('desconto_geral', 0))
        
        # Itens da venda
        produtos_ids = request.form.getlist('produto_id[]')
        quantidades = request.form.getlist('quantidade[]')
        descontos_produto = request.form.getlist('desconto_produto[]')
        
        if not produtos_ids:
            raise Exception("Nenhum produto selecionado para a venda")
        
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar estoque disponível e calcular totais
        itens_venda = []
        valor_total_bruto = 0
        total_descontos_produtos = 0
        
        for i, produto_id in enumerate(produtos_ids):
            if not produto_id:
                continue
                
            quantidade = int(quantidades[i])
            desconto_produto = float(descontos_produto[i]) if descontos_produto[i] else 0
            
            # Buscar preço do produto e estoque atual
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
        
        # Calcular totais finais
        total_descontos = total_descontos_produtos + desconto_geral
        valor_final = valor_total_bruto - total_descontos
        
        # Inserir venda SEM IdPromocao se a coluna não existir
        cursor.execute("""
            INSERT INTO Venda (ValorTotal, Desconto, ValorFinal, IdCliente) 
            VALUES (%s, %s, %s, %s)
        """, (valor_total_bruto, total_descontos, valor_final, id_cliente))
        
        id_venda = cursor.lastrowid
        
        # Inserir itens da venda e atualizar estoque
        for item in itens_venda:
            cursor.execute("""
                INSERT INTO ItemVenda (IdVenda, IdProduto, Quantidade, PrecoUnitario, Subtotal, DescontoProduto) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_venda, item['produto_id'], item['quantidade'], 
                  item['preco_unitario'], item['subtotal'], item['desconto_produto']))
            # Atualiza estoque
            cursor.execute("""
                UPDATE Estoque SET Quantidade = Quantidade - %s WHERE IdProduto = %s
            """, (item['quantidade'], item['produto_id']))
            # Registra movimentação de saída por venda
            cursor.execute("""
                INSERT INTO movimentacaoestoque (DataMovimentacao, Tipo, IdProduto, Quantidade) VALUES (CURDATE(), %s, %s, %s)
            """, ("venda", item['produto_id'], item['quantidade']))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('recibo_venda', id_venda=id_venda))
        
    except Exception as e:
        # Buscar dados novamente para reexibir o formulário
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

# Rota para visualizar recibo da venda
@app.route('/vendas/recibo/<int:id_venda>')
def recibo_venda(id_venda):
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar dados da venda com contato usando a estrutura correta
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
    
    # Buscar itens da venda
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

# Rota para cancelar venda
@app.route('/vendas/cancelar/<int:id_venda>', methods=['POST'])
def cancelar_venda(id_venda):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar itens da venda para restituir estoque
        cursor.execute("""
            SELECT IdProduto, Quantidade FROM ItemVenda WHERE IdVenda = %s
        """, (id_venda,))
        itens = cursor.fetchall()
        
        # Restituir estoque
        for item in itens:
            cursor.execute("""
                UPDATE Estoque SET Quantidade = Quantidade + %s WHERE IdProduto = %s
            """, (item['Quantidade'], item['IdProduto']))
        
        # Atualizar status da venda
        cursor.execute("""
            UPDATE Venda SET Status = 'Cancelada' WHERE IdVenda = %s
        """, (id_venda,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Em caso de erro, apenas redireciona
        pass
    
    return redirect(url_for('vendas'))


# Rota para nova promoção
@app.route('/promocoes/nova', methods=['GET', 'POST'])
def nova_promocao():
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        tipo_desconto = request.form.get('tipo_desconto')
        valor_desconto = request.form.get('valor_desconto')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        
        # Validações de data
        try:
            # Aceita apenas 'dd/MM/yyyy'
            data_inicio_obj = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            data_fim_obj = datetime.strptime(data_fim, '%d/%m/%Y').date()
            # Converter para yyyy-mm-dd para o MySQL
            data_inicio_mysql = data_inicio_obj.strftime('%Y-%m-%d')
            data_fim_mysql = data_fim_obj.strftime('%Y-%m-%d')
            data_hoje = date.today()
            
            # Permitir data de início igual ao dia atual
            if data_inicio_obj < data_hoje:
                raise Exception("A data de início não pode ser anterior ao dia atual")
            
            # Verificar se a data de fim não é anterior à data de início
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

# Rota para editar promoção
@app.route('/promocoes/editar/<int:id>', methods=['GET', 'POST'])
def editar_promocao(id):
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
        
        # Validações de data (mais flexíveis para edição)
        try:
            # Aceita apenas 'dd/MM/yyyy'
            data_inicio_obj = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            data_fim_obj = datetime.strptime(data_fim, '%d/%m/%Y').date()
            # Converter para yyyy-mm-dd para o MySQL
            data_inicio_mysql = data_inicio_obj.strftime('%Y-%m-%d')
            data_fim_mysql = data_fim_obj.strftime('%Y-%m-%d')
            data_hoje = date.today()
            
            # Para promoções já iniciadas, não validar data de início
            promocao_data_inicio = promocao['DataInicio']
            if isinstance(promocao_data_inicio, str):
                promocao_data_inicio = datetime.strptime(promocao_data_inicio, '%Y-%m-%d').date()
            
            # Se a promoção ainda não começou, validar data de início (permitir igual ao dia atual)
            if promocao_data_inicio > data_hoje and data_inicio_obj < data_hoje:
                raise Exception("A data de início não pode ser anterior ao dia atual")
            
            # Verificar se a data de fim não é anterior à data de início
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

# Função para atualizar status das promoções automaticamente
def atualizar_status_promocoes():
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        
        # Desativar promoções vencidas
        cursor.execute("""
            UPDATE Promocao 
            SET Ativa = 0 
            WHERE DataFim < CURDATE() AND Ativa = 1
        """)
        
        # Ativar promoções que devem estar ativas
        cursor.execute("""
            UPDATE Promocao 
            SET Ativa = 1 
            WHERE DataInicio <= CURDATE() AND DataFim >= CURDATE() AND Ativa = 0
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar status das promoções: {e}")

# Rota para listar promoções (com atualização automática)
@app.route('/promocoes')
def promocoes():
    # Atualizar status das promoções antes de listar
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

# Rota para nova venda (com atualização automática de promoções)
@app.route('/vendas/nova', methods=['GET', 'POST'])
def nova_venda():
    if request.method == 'POST':
        return processar_venda()
    
    # Atualizar status das promoções antes de buscar
    atualizar_status_promocoes()
    
    # Buscar dados necessários para o formulário
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar clientes
    cursor.execute("SELECT IdCliente, Nome FROM Cliente ORDER BY Nome")
    clientes = cursor.fetchall()
    
    # Buscar produtos com estoque
    cursor.execute("""
        SELECT p.IdProduto, p.Nome, p.Preco, e.Quantidade 
        FROM Produto p 
        JOIN Estoque e ON p.IdProduto = e.IdProduto 
        WHERE e.Quantidade > 0 
        ORDER BY p.Nome
    """)
    produtos = cursor.fetchall()
    
    # Buscar promoções ativas
    cursor.execute("""
        SELECT IdPromocao, Nome, TipoDesconto, ValorDesconto 
        FROM Promocao 
        WHERE Ativa = 1 AND DataInicio <= CURDATE() AND DataFim >= CURDATE()
        ORDER BY Nome
    """)
    promocoes = cursor.fetchall()
    
    conn.close()
    
    return render_template('nova_venda.html', clientes=clientes, produtos=produtos, promocoes=promocoes)

# Rota para excluir promoção
@app.route('/promocoes/excluir/<int:id>', methods=['POST'])
def excluir_promocao(id):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Promocao WHERE IdPromocao=%s", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        # Em caso de erro, apenas redireciona
        pass
    return redirect(url_for('promocoes'))


# ------------------- PÁGINA UNIFICADA DE RELATÓRIOS -------------------
@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

# ------------------- RELATÓRIOS -------------------
# Relatório de Vendas: Detalha vendas realizadas (data, produtos vendidos, quantidade, valor total)
@app.route('/relatorios/vendas')
def relatorio_vendas():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    # Consulta vendas e itens vendidos
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
    # Agrupa vendas por IdVenda
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

# Relatório de Estoque: Mostra quantidade atual de todos os produtos
@app.route('/relatorios/estoque')
def relatorio_estoque():
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

# Histórico de Movimentações: Registra todas as adições e remoções de estoque
@app.route('/relatorios/movimentacoes')
def relatorio_movimentacoes():
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


# Exportar relatório de vendas para CSV
@app.route('/relatorios/vendas/csv')
def relatorio_vendas_csv():
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
    # Monta CSV
    def generate():
        yield 'IdVenda,DataVenda,ValorTotal,IdProduto,NomeProduto,Quantidade,PrecoUnitario\n'
        for v in vendas:
            yield f"{v['IdVenda']},{v['DataVenda']},{v['ValorTotal']},{v['IdProduto']},\"{v['NomeProduto']}\",{v['Quantidade']},{v['PrecoUnitario']}\n"
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=relatorio_vendas.csv"})

# Exportar relatório de estoque para CSV
@app.route('/relatorios/estoque/csv')
def relatorio_estoque_csv():
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

# Exportar histórico de movimentações para CSV
@app.route('/relatorios/movimentacoes/csv')
def relatorio_movimentacoes_csv():
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

# Executa a aplicação Flask em modo debug
if __name__ == '__main__':
    app.run(debug=True)

