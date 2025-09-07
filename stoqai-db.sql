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
    Nome VARCHAR(100) NOT NULL,
    CPF CHAR(11) NOT NULL UNIQUE,
    IdContato INT,
    IdEndereco INT,
    FOREIGN KEY (IdContato) REFERENCES Contato(IdContato),
    FOREIGN KEY (IdEndereco) REFERENCES Endereco(IdEndereco)
);

CREATE TABLE Funcionario (
    IdFunc INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(100) NOT NULL,
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
    Nome VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Fornecedor (
    IdFornecedor INT PRIMARY KEY AUTO_INCREMENT,
    CNPJ CHAR(14) NOT NULL UNIQUE,
    Nome VARCHAR(100) NOT NULL,
    IdContato INT,
    IdEndereco INT,
    FOREIGN KEY (IdContato) REFERENCES Contato(IdContato),
    FOREIGN KEY (IdEndereco) REFERENCES Endereco(IdEndereco)
);

CREATE TABLE Produto (
    IdProduto INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(100) NOT NULL,
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

-- Tabela Endereco
SELECT * FROM Endereco;

-- Tabela Contato
SELECT * FROM Contato;

-- Tabela Usuario
SELECT * FROM Usuario;

-- Tabela Cliente
SELECT * FROM Cliente;

-- Tabela Funcionario
SELECT * FROM Funcionario;

-- Tabela Categoria
SELECT * FROM Categoria;

-- Tabela Fornecedor
SELECT * FROM Fornecedor;

-- Tabela Produto
SELECT * FROM Produto;

-- Tabela Estoque
SELECT * FROM Estoque;

INSERT INTO Contato (Telefone, Email) VALUES
-- Contatos de Clientes(o contato dos fornecedores foi colocado pelo python)
('(11)99999-8888', 'joao.silva@email.com'),
('(21)98888-7777', 'maria.santos@email.com'),
('(31)97777-6666', 'pedro.almeida@email.com'),
('(41)96666-5555', 'ana.souza@email.com'),
('(51)95555-4444', 'carlos.roberto@email.com');

-- Inserindo dados na tabela 'Endereco'
INSERT INTO Endereco (NomeRua, Num, CEP, Complemento, Bairro, Cidade, Estado) VALUES
-- Endereços de Clientes
('Rua das Amoreiras', '10', '04543000', NULL, 'Vila Olímpia', 'São Paulo', 'SP'),
('Avenida Atlântica', '1500', '22070001', 'Apto 502', 'Copacabana', 'Rio de Janeiro', 'RJ'),
('Rua da Liberdade', '305', '30140001', 'Loja 2', 'Lourdes', 'Belo Horizonte', 'MG'),
('Rua Visconde de Mauá', '88', '40110005', 'Casa', 'Graça', 'Salvador', 'BA'),
('Avenida Ipiranga', '200', '90040000', 'Sala 10', 'Centro Histórico', 'Porto Alegre', 'RS'),
-- Endereços de Fornecedores
('Rua dos Guaranis', '500', '01211000', NULL, 'Centro', 'São Paulo', 'SP'),
('Avenida Rio Branco', '20', '20090003', 'Andar 12', 'Centro', 'Rio de Janeiro', 'RJ'),
('Rua Piauí', '125', '30150000', NULL, 'Funcionários', 'Belo Horizonte', 'MG'),
('Rua da Mouraria', '220', '40050000', 'Galpão', 'Mouraria', 'Salvador', 'BA'),
('Avenida Assis Brasil', '150', '91010000', 'Conjunto B', 'São João', 'Porto Alegre', 'RS');

-- Inserindo dados na tabela 'Usuario'
INSERT INTO Usuario (Login, Senha) VALUES
('joao.silva', 'senha123'),
('maria.santos', 'senha456'),
('pedro.almeida', 'senha789'),
('ana.souza', 'senha1011'),
('carlos.roberto', 'senha1213');

-- Inserindo dados na tabela 'Cliente'
-- Precisa ter colocado primeiro nas tabelas 'Contato' e 'Endereço'
INSERT INTO Cliente (Nome, CPF, IdContato, IdEndereco) VALUES
('João Silva', '11122233344', 7, 1),
('Maria Santos', '22233344455', 8, 2),
('Pedro Almeida', '33344455566', 9, 3),
('Ana Souza', '44455566677', 10, 4),
('Carlos Roberto', '55566677788', 11, 5);

-- Inserindo dados na tabela 'Funcionario'
-- Precisa ter colocado primeiro nas tabelas 'Contato' e 'Endereço'
INSERT INTO Funcionario (Nome, CPF, IdEndereco, IdContato, Cargo, Salario, DataAdmissao, IdUser) VALUES
('Fernanda Lima', '66677788899', 11, 12, 'Gerente', 8000.00, '2020-01-15', 1),
('Rafael Costa', '77788899900', 12, 13, 'Analista de Vendas', 4500.00, '2021-03-20', 2),
('Juliana Paes', '88899900011', 13, 14, 'Desenvolvedor', 6000.00, '2019-08-10', 3),
('Paulo Guedes', '99900011122', 14, 15, 'Assistente Administrativo', 3000.00, '2022-05-01', 4),
('Sandra Regina', '00011122233', 15, 16, 'Coordenador', 7500.00, '2018-11-25', 5);

INSERT INTO Endereco (NomeRua, Num, CEP, Complemento, Bairro, Cidade, Estado) VALUES
-- Endereços de Funcionários
('Rua da Consolação', '75', '01301000', 'Conjunto 10', 'Consolação', 'São Paulo', 'SP'),
('Avenida Paulista', '1000', '01310100', 'Sala 200', 'Bela Vista', 'São Paulo', 'SP'),
('Rua dos Andradas', '120', '90020000', NULL, 'Centro', 'Porto Alegre', 'RS'),
('Avenida Sete de Setembro', '50', '40060000', NULL, 'Centro', 'Salvador', 'BA'),
('Rua da Carioca', '33', '20050000', 'Loja A', 'Centro', 'Rio de Janeiro', 'RJ');

INSERT INTO Contato (Telefone, Email) VALUES
-- Contato dos Funcionários
('(11)91111-2222', 'fernanda.lima@deltasup.com'),
('(21)92222-3333', 'rafael.costa@alphadist.com'),
('(31)93333-4444', 'juliana.paes@betaimport.com'),
('(41)94444-5555', 'paulo.guedes@gamaatac.com'),
('(51)95555-6666', 'sandra.regina@omegacom.com');

-- Atuzlizando os endereços na tabela Forecedor
UPDATE Fornecedor SET idEndereco = 6 WHERE IdFornecedor = 1;
UPDATE Fornecedor SET idEndereco = 7 WHERE IdFornecedor = 2;
UPDATE Fornecedor SET idEndereco = 8 WHERE IdFornecedor = 3;
UPDATE Fornecedor SET idEndereco = 9 WHERE IdFornecedor = 4;
UPDATE Fornecedor SET idEndereco = 10 WHERE IdFornecedor = 5;

-- As tabelas 'Categoria', 'Fornecedor' sem o idEndereco, 'Produto', 'Estoque', e parte de 'Contato',
-- foram adicionadas pela aplicação por isso não se encontram os inserts delas aqui no SQL