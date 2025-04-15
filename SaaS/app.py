from flask import Flask, render_template, request, redirect, jsonify
import requests, json, os, re

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)
    
def normalize_text(text):
    text = text.strip().lower()
    text = re.sub(r'\bav[.]?\b', 'avenida', text)
    text = re.sub(r'\br[.]?\b', 'rua', text)
    return text.title()  # capitaliza cada palavra

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def validate_address(full_address):
    print(f"Validando endereço: {full_address}")  # Ver o que estamos enviando
    url = f'https://nominatim.openstreetmap.org/search'
    params = {'q': full_address, 'format': 'json'}
    response = requests.get(url, params=params, headers={"User-Agent": "CadastroApp"})
    print(f"Resposta da API: {response.json()}")  # Ver a resposta da API
    results = response.json()
    
    if not results:
        # Tentar buscar pelo CEP
        cep_only = f"{full_address.split()[-1]}"  # Apenas o CEP
        print(f"Tentando apenas o CEP: {cep_only}")
        response = requests.get(url, params={'q': cep_only, 'format': 'json'}, headers={"User-Agent": "CadastroApp"})
        results = response.json()

    if results:
        return results[0]
    return None

@app.route('/delete/<int:index>', methods=['POST'])
def delete_address(index):
    data = load_data()
    
    if 0 <= index < len(data):
        del data[index]  # Remove o endereço da lista
        save_data(data)
        return redirect('/map')  # Redireciona de volta para o mapa
    return "Endereço não encontrado.", 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        endereco = normalize_text(request.form['endereco'])
        bairro = normalize_text(request.form['bairro'])
        numero = request.form['numero'].strip()
        cep = re.sub(r'\D', '', request.form['cep'])  # Remove tudo que não for número


        full_address = f"{endereco}, {numero}, {bairro}, {cep}"
        validated = validate_address(full_address)

        if validated:
            data = load_data()
            data.append({
                "endereco": f"{endereco}, {numero} - {bairro}, CEP: {cep}",
                "lat": validated['lat'],
                "lon": validated['lon']
            })
            save_data(data)
            return redirect('/')
        else:
            return "Endereço inválido. <a href='/form'>Tente novamente</a>"

    return render_template('form.html')
@app.route('/map')
def map_view():
    data = load_data()
    return render_template('map.html', data=data)

@app.route('/data')
def data_api():
    return jsonify(load_data())

@app.route('/enderecos')
def listar_enderecos():
    data = load_data()
    return render_template('enderecos.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)


