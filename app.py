"""
Este é o arquivo principal da aplicação Flask (Backend).
Ele gerencia o banco de dados SQLite, define as rotas web (URLs) e controla a lógica de negócio do sistema.
"""

import sqlite3
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, Response

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('banco.db')
    # Permite acessar as colunas do banco pelo nome (ex: item['nome']) em vez de índice numérico
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            status TEXT NOT NULL,
            valor REAL
        )
    ''')
    conn.commit()
    conn.close()

# Executa a criação da tabela na inicialização
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    
    total_equipamentos = conn.execute('SELECT COUNT(*) FROM equipamentos').fetchone()[0]
    valor_total = conn.execute('SELECT SUM(valor) FROM equipamentos').fetchone()[0]
    
    if valor_total is None:
        valor_total = 0.0
        
    itens_manutencao = conn.execute("SELECT COUNT(*) FROM equipamentos WHERE status = 'Manutenção'").fetchone()[0]
    
    conn.close()
    
    return render_template('index.html', 
                           total=total_equipamentos, 
                           valor=valor_total, 
                           manutencao=itens_manutencao)

@app.route('/cadastro', methods=('GET', 'POST'))
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        categoria = request.form['categoria']
        status = request.form['status']
        valor = request.form['valor']

        conn = get_db_connection()
        conn.execute('INSERT INTO equipamentos (nome, categoria, status, valor) VALUES (?, ?, ?, ?)',
                     (nome, categoria, status, valor))
        conn.commit()
        conn.close()
        
        return redirect(url_for('listar'))

    return render_template('cadastro.html')

@app.route('/listar')
def listar():
    busca = request.args.get('busca')
    conn = get_db_connection()
    
    if busca:
        term = f"%{busca}%"
        equipamentos = conn.execute('SELECT * FROM equipamentos WHERE nome LIKE ? OR categoria LIKE ?', (term, term)).fetchall()
    else:
        equipamentos = conn.execute('SELECT * FROM equipamentos').fetchall()
    
    conn.close()
    
    return render_template('listar.html', equipamentos=equipamentos)

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    equipamentos = conn.execute('SELECT * FROM equipamentos').fetchall()
    conn.close()
    
    # Cria um buffer de memória para gerar o CSV sem precisar salvar em disco (Overengineering/Optimization)
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Nome', 'Categoria', 'Status', 'Valor'])
    
    for item in equipamentos:
        writer.writerow([item['id'], item['nome'], item['categoria'], item['status'], item['valor']])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=inventario_devsetup.csv"}
    )
    
if __name__ == '__main__':
    app.run(debug=True)
