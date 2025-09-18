# Importa as bibliotecas necessárias do Flask e MySQL Connector
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import re


# Inicializa a aplicação Flask
app = Flask(__name__)


# Função para conectar ao banco de dados MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="fiap",
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


# Executa a aplicação Flask em modo debug
if __name__ == '__main__':
    app.run(debug=True)
