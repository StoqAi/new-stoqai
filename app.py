from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import re

app = Flask(__name__)

# Conexão com MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Thor2019@sql",
        database="estoque_loja"
    )

# Página inicial - Lista de produtos
@app.route('/')
def index():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            Produto.IdProduto, Produto.Nome, Produto.Preco, Produto.Descricao,
            Produto.IdCategoria, Produto.IdFornecedor,
            Estoque.Quantidade
        FROM Produto
        JOIN Estoque ON Produto.IdProduto = Estoque.IdProduto
    """)
    produtos = cursor.fetchall()
    conn.close()
    estoque_baixo = [p for p in produtos if p.get('Quantidade', 0) <= 5]
    return render_template('index.html', produtos=produtos, estoque_baixo=estoque_baixo)

# Página para atualizar estoque
@app.route('/atualizar_estoque/<int:id>', methods=['GET', 'POST'])
def atualizar_estoque(id):
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
            conn.commit()
            conn.close()
        except Exception as e:
            return render_template('cadastrar.html', erro=f'Erro ao cadastrar: {e}', categorias=categorias, fornecedores=fornecedores)

        return redirect(url_for('index'))

    return render_template('cadastrar.html', categorias=categorias, fornecedores=fornecedores)

# Aumentar quantidade
@app.route('/aumentar/<int:id_produto>', methods=['POST'])
def aumentar(id_produto):
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade + %s WHERE IdProduto = %s", (qtd, id_produto))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Reduzir quantidade
@app.route('/reduzir/<int:id_produto>', methods=['POST'])
def reduzir(id_produto):
    qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = Quantidade - %s WHERE IdProduto = %s AND Quantidade >= %s", (qtd, id_produto, qtd))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Ajustar quantidade
@app.route('/ajustar/<int:id_produto>', methods=['POST'])
def ajustar(id_produto):
    nova_qtd = int(request.form.get('quantidade', 0))
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("UPDATE Estoque SET Quantidade = %s WHERE IdProduto = %s", (nova_qtd, id_produto))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Excluir produto (remove de Estoque e Produto)
@app.route('/excluir/<int:id_produto>', methods=['POST'])
def excluir(id_produto):
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Estoque WHERE IdProduto = %s", (id_produto,))
    cursor.execute("DELETE FROM Produto WHERE IdProduto = %s", (id_produto,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Rotas para gerenciamento de fornecedores
@app.route('/fornecedores/')
def fornecedores():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
               Contato.Telefone, Contato.Email
        FROM Fornecedor
        LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
    """)
    fornecedores = cursor.fetchall()
    conn.close()
    return render_template('fornecedores.html', fornecedores=fornecedores)

@app.route('/fornecedores/novo', methods=['GET', 'POST'])
def novo_fornecedor():
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Contato (Telefone, Email) VALUES (%s, %s)", (telefone, email))
            id_contato = cursor.lastrowid
            cursor.execute("INSERT INTO Fornecedor (Nome, CNPJ, IdContato) VALUES (%s, %s, %s)", (nome, cnpj, id_contato))
            conn.commit()
            conn.close()
            return redirect(url_for('fornecedores'))
        except Exception as e:
            erro = f'Erro ao cadastrar fornecedor: {e}'
    return render_template('fornecedor_form.html', erro=erro, fornecedor=None)

@app.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Fornecedor.IdFornecedor, Fornecedor.Nome, Fornecedor.CNPJ, 
               Contato.Telefone, Contato.Email, Fornecedor.IdContato
        FROM Fornecedor
        LEFT JOIN Contato ON Fornecedor.IdContato = Contato.IdContato
        WHERE Fornecedor.IdFornecedor = %s
    """, (id,))
    fornecedor = cursor.fetchone()
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        try:
            cursor2 = conn.cursor()
            cursor2.execute("UPDATE Fornecedor SET Nome=%s, CNPJ=%s WHERE IdFornecedor=%s", (nome, cnpj, id))
            cursor2.execute("UPDATE Contato SET Telefone=%s, Email=%s WHERE IdContato=%s", (telefone, email, fornecedor['IdContato']))
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
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        # Verifica se existe algum produto usando este fornecedor
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
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT IdCategoria, Nome FROM Categoria ORDER BY IdCategoria ASC")
    categorias = cursor.fetchall()
    conn.close()
    return render_template('categorias.html', categorias=categorias)

@app.route('/categorias/novo', methods=['GET', 'POST'])
def nova_categoria():
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
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        # Verifica se existe algum produto usando esta categoria
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

if __name__ == '__main__':
    app.run(debug=True)
