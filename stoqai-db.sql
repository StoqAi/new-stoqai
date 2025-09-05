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