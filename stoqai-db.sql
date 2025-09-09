CREATE DATABASE estoque_loja;
USE estoque_loja;

CREATE TABLE Endereco (
    IdEndereco INT PRIMARY KEY AUTO_INCREMENT,
    NomeRua VARCHAR(100) NOT NULL,
    Num VARCHAR(10),
    CEP CHAR(8) NOT NULL,
    Complemento VARCHAR(50),
    Bairro VARCHAR(50) NOT NULL,
    Cidade VARCHAR(50) NOT NULL,
    Estado CHAR(2) NOT NULL
);

CREATE TABLE Contato (
    IdContato INT PRIMARY KEY AUTO_INCREMENT,
    Telefone VARCHAR(15),
    Email VARCHAR(100)
);

CREATE TABLE Usuario (
    IdUser INT PRIMARY KEY AUTO_INCREMENT,
    Login VARCHAR(50) NOT NULL UNIQUE,
    Senha VARCHAR(255) NOT NULL
);

CREATE TABLE Cliente (
    IdCliente INT PRIMARY KEY AUTO_INCREMENT,
    Nome_cliente VARCHAR(100) NOT NULL,
    CPF CHAR(11) NOT NULL UNIQUE,
    IdContato INT,
    IdEndereco INT,
    FOREIGN KEY (IdContato) REFERENCES Contato(IdContato),
    FOREIGN KEY (IdEndereco) REFERENCES Endereco(IdEndereco)
);

CREATE TABLE Funcionario (
    IdFunc INT PRIMARY KEY AUTO_INCREMENT,
    Nome_func VARCHAR(100) NOT NULL,
    CPF CHAR(11) NOT NULL UNIQUE,
    IdEndereco INT,
    IdContato INT,
    Cargo VARCHAR(50) NOT NULL,
    Salario DECIMAL(10,2) NOT NULL,
    DataAdmissao DATE NOT NULL,
    IdUser INT,
    FOREIGN KEY (IdEndereco) REFERENCES Endereco(IdEndereco),
    FOREIGN KEY (IdContato) REFERENCES Contato(IdContato),
    FOREIGN KEY (IdUser) REFERENCES Usuario(IdUser)
);

CREATE TABLE Categoria (
    IdCategoria INT PRIMARY KEY AUTO_INCREMENT,
    Nome_cat VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Fornecedor (
    IdFornecedor INT PRIMARY KEY AUTO_INCREMENT,
    CNPJ CHAR(14) NOT NULL UNIQUE,
    Nome_forn VARCHAR(100) NOT NULL,
    IdContato INT,
    IdEndereco INT,
    FOREIGN KEY (IdContato) REFERENCES Contato(IdContato),
    FOREIGN KEY (IdEndereco) REFERENCES Endereco(IdEndereco)
);

CREATE TABLE Produto (
    IdProduto INT PRIMARY KEY AUTO_INCREMENT,
    Nome_prod VARCHAR(100) NOT NULL,
    Preco DECIMAL(10,2) NOT NULL,
    Descricao TEXT,
    IdCategoria INT,
    IdFornecedor INT,
    FOREIGN KEY (IdCategoria) REFERENCES Categoria(IdCategoria),
    FOREIGN KEY (IdFornecedor) REFERENCES Fornecedor(IdFornecedor)
);

CREATE TABLE Estoque (
    IdEstoque INT PRIMARY KEY AUTO_INCREMENT,
    IdProduto INT NOT NULL,
    Quantidade INT NOT NULL DEFAULT 0,
    FOREIGN KEY (IdProduto) REFERENCES Produto(IdProduto)
);

show tables;

DELIMITER $$

CREATE PROCEDURE ver_todas_tabelas()
BEGIN
    SELECT * FROM Endereco;
    SELECT * FROM Contato;
    SELECT * FROM Usuario;
    SELECT * FROM Cliente;
    SELECT * FROM Funcionario;
    SELECT * FROM Categoria;
    SELECT * FROM Fornecedor;
    SELECT * FROM Produto;
    SELECT * FROM Estoque;
END $$

DELIMITER ;

-- PARA FUNCIONAR RODE
-- CALL ver_todas_tabelas();

DELIMITER $$

CREATE PROCEDURE dropar_todas_tabelas()
BEGIN
    DROP TABLE IF EXISTS Endereco;
    DROP TABLE IF EXISTS Contato;
    DROP TABLE IF EXISTS Usuario;
    DROP TABLE IF EXISTS Cliente;
    DROP TABLE IF EXISTS Funcionario;
    DROP TABLE IF EXISTS Categoria;
    DROP TABLE IF EXISTS Fornecedor;
    DROP TABLE IF EXISTS Produto;
    DROP TABLE IF EXISTS Estoque;
END $$

DELIMITER ;

-- PARA FUNCIONAR RODE
-- CALL dropar_todas_tabelas();


-- População da tabela: Contato
INSERT INTO Contato (IdContato, Telefone, Email) VALUES
-- Contato dos Clientes
(1, '(11)99999-8888', 'joao.silva@email.com'),
(2, '(21)98888-7777', 'maria.santos@email.com'),
(3, '(31)97777-6666', 'pedro.almeida@email.com'),
(4, '(41)96666-5555', 'ana.souza@email.com'),
(5, '(51)95555-4444', 'carlos.roberto@email.com'),
-- Contato dos funcionarios
(6, '(11)91111-2222', 'fernanda.lima@stoqai.com'),
(7, '(21)92222-3333', 'rafael.costa@stoqai.com'),
(8, '(31)93333-4444', 'juliana.paes@stoqai.com'),
(9, '(41)94444-5555', 'paulo.guedes@stoqai.com'),
(10, '(51)95555-6666', 'sandra.regina@stoqai.com'),
-- Contato dos fornecedores
(11, '(41) 3344-5566', 'contato@deltasup.com'),
(12, '(11) 3456-7890', 'contato@alphadist.com'),
(13, '(21) 2345-6789', 'vendas@betaimport.com'),
(14, '(31) 2233-4455', 'sac@gamaatac.com'),
(15, '(51) 4455-6677', 'omega@omegacom.com');

-- População da tabela: Endereco
INSERT INTO Endereco (IdEndereco, NomeRua, Num, CEP, Complemento, Bairro, Cidade, Estado) VALUES
-- Endereços dos clientes
(1, 'Rua das Amoreiras', '10', '04543000', NULL, 'Vila Olímpia', 'São Paulo', 'SP'),
(2, 'Avenida Atlântica', '1500', '22070001', 'Apto 502', 'Copacabana', 'Rio de Janeiro', 'RJ'),
(3, 'Rua da Liberdade', '305', '30140001', 'Loja 2', 'Lourdes', 'Belo Horizonte', 'MG'),
(4, 'Rua Visconde de Mauá', '88', '40110005', 'Casa', 'Graça', 'Salvador', 'BA'),
(5, 'Avenida Ipiranga', '200', '90040000', 'Sala 10', 'Centro Histórico', 'Porto Alegre', 'RS'),
-- Endereços dos funcionarios
(6, 'Rua da Consolação', '75', '01301000', 'Conjunto 10', 'Consolação', 'São Paulo', 'SP'),
(7, 'Avenida Paulista', '1000', '01310100', 'Sala 200', 'Bela Vista', 'São Paulo', 'SP'),
(8, 'Rua dos Andradas', '120', '90020000', NULL, 'Centro', 'Porto Alegre', 'RS'),
(9, 'Avenida Sete de Setembro', '50', '40060000', NULL, 'Centro', 'Salvador', 'BA'),
(10, 'Rua da Carioca', '33', '20050000', 'Loja A', 'Centro', 'Rio de Janeiro', 'RJ'),
-- Endereços dos fornecedores
(11, 'Rua dos Guaranis', '500', '01211000', NULL, 'Centro', 'São Paulo', 'SP'),
(12, 'Avenida Rio Branco', '20', '20090003', 'Andar 12', 'Centro', 'Rio de Janeiro', 'RJ'),
(13, 'Rua Piauí', '125', '30150000', NULL, 'Funcionários', 'Belo Horizonte', 'MG'),
(14, 'Rua da Mouraria', '220', '40050000', 'Galpão', 'Mouraria', 'Salvador', 'BA'),
(15, 'Avenida Assis Brasil', '150', '91010000', 'Conjunto B', 'São João', 'Porto Alegre', 'RS');

-- População da tabela: Usuario
INSERT INTO Usuario (IdUser, Login, Senha) VALUES
(1, 'fernanda.lima', 'senha123'),
(2, 'rafael.costa', 'senha456'),
(3, 'juliana.paes', 'senha789'),
(4, 'paulo.guedes', 'senha101'),
(5, 'sandra.regina', 'senha121');

-- População da tabela: Cliente
INSERT INTO Cliente (IdCliente, Nome_cliente, CPF, IdContato, IdEndereco) VALUES
(1, 'João Silva', '11122233344', 1, 1),
(2, 'Maria Santos', '22233344455', 2, 2),
(3, 'Pedro Almeida', '33344455566', 3, 3),
(4, 'Ana Souza', '44455566677', 4, 4),
(5, 'Carlos Roberto', '55566677788', 5, 5);

-- População da tabela: Funcionario
INSERT INTO Funcionario (IdFunc, Nome_func, CPF, IdEndereco, IdContato, Cargo, Salario, DataAdmissao, IdUser) VALUES
(1, 'Fernanda Lima', '66677788899', 6, 6, 'Gerente', 8000.00, '2020-01-15', 1),
(2, 'Rafael Costa', '77788899900', 7, 7, 'Analista de Vendas', 4500.00, '2021-03-20', 2),
(3, 'Juliana Paes', '88899900011', 8, 8, 'Desenvolvedor', 6000.00, '2019-08-10', 3),
(4, 'Paulo Guedes', '99900011122', 9, 9, 'Assistente Administrativo', 3000.00, '2022-05-01', 4),
(5, 'Sandra Regina', '00011122233', 10, 10, 'Coordenador', 7500.00, '2018-11-25', 5);

-- População da tabela: Fornecedor
INSERT INTO Fornecedor (IdFornecedor, CNPJ, Nome_forn, IdContato, IdEndereco) VALUES
(1, '00920731000902', 'Delta Suprimentos', 11, 11),
(2, '12345678000190', 'Alpha Distribuidora', 12, 12),
(3, '98765432000110', 'Beta Importadora', 13, 13),
(4, '45678912000155', 'Gama Atacadista', 14, 14),
(5, '77889900000133', 'Omega Comércio', 15, 15);

-- População da tabela: Categoria
INSERT INTO Categoria (IdCategoria, Nome_cat) VALUES
(1, 'Eletrônicos'),
(2, 'Alimentos'),
(3, 'Limpeza'),
(4, 'Móveis'),
(5, 'Vestuário'),
(6, 'Beleza');

-- População da tabela: Produto
INSERT INTO Produto (IdProduto, Nome_prod, Preco, Descricao, IdCategoria, IdFornecedor) VALUES
(1, 'Smartphone X1', 1500.00, 'Smartphone de última geração com 128GB', 1, 3),
(2, 'Arroz Tipo 1 (5kg)', 25.00, 'Arroz branco tipo 1, pacote com 5kg', 2, 4),
(3, 'Detergente Líquido (500ml)', 4.00, 'Detergente líquido para louças', 3, 2),
(4, 'Mesa de Escritório', 500.00, 'Mesa de escritório em madeira MDF', 4, 5),
(5, 'Camiseta Algodão', 40.00, 'Camiseta básica de algodão, cor preta', 5, 1);

-- População da tabela: Estoque
INSERT INTO Estoque (IdEstoque, IdProduto, Quantidade) VALUES
(1, 1, 50),
(2, 2, 200),
(3, 3, 500),
(4, 4, 20),
(5, 5, 100);