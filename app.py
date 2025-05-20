
from flask import Flask, jsonify, request # Flask, jsonify para formatar resposta, request para acessar dados da requisição
from flask_cors import CORS # Para lidar com Cross-Origin Resource Sharing
from google import genai # Biblioteca para interagir com o modelo Gemini
import os # Módulo para interagir com o sistema operacional (usaremos para variáveis de ambiente)
from dotenv import load_dotenv # Importa a função para carregar .env (se python-dotenv foi instalado)
import json # Para manipulação de JSON

load_dotenv()

app = Flask(__name__)

CORS(app)

API_KEY=os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

def buscar_jogo(caracteriticas, preco):
    prompt = f"""
        Busque jogos (PC, console, Celular) com base nos seguintes critérios: {caracteriticas} e {preco}.
        Em caso as caracteristicas não sejam critérios de verdade para jogos, por exemplo, orgãos sexuais, coisas inapropriadas e palavras sem sentido, ignore-os, não busque jogos e alerte o usuário sobre o conteudo impróprio.
        Caso o preço esteja em zero ou menos, busque jogos gratuitos.
        Qualquer jogo é valido (indie, triple A e etc...), mas foque em jogos mais "desconhecidos", que tenham menos players, menos hype e menos marketing.
        Dê preferência jogos em plataformas como Steam, Epic Games, PlayStation Store, Xbox Store, Google Play Store e Apple App Store.
        Retorne para cada jogo encontrado as seguintes informações: título, plataforma, tempo de jogo em média, o preço e o link para compra.
        **As características devem ser retornadas como um array de strings, por exemplo: ["ação", "aventura", "RPG"].**
        Devolva o resultado em um formato JSON que contenha um array de objetos de jogos, cada um com as chaves "titulo", "plataforma", "tempo_de_jogo", "preco", "link" e "caracteristicas".

        Se encontrar jogos, o JSON deve ter a estrutura:
        {{
            "status": "success",
            "jogos": [
                {{
                    "titulo": "titulo do jogo 1",
                    "plataforma": "plataforma 1",
                    "tempo_de_jogo": "tempo médio de jogo 1",
                    "link": "link para compra 1",
                    "preco": "preço do jogo 1",
                    "caracteristicas": ["caracteristica A", "caracteristica B"]
                }},
                {{
                    "titulo": "titulo do jogo 2",
                    "plataforma": "plataforma 2",
                    "tempo_de_jogo": "tempo médio de jogo 2",
                    "link": "link para compra 2",
                    "preco": "preço do jogo 2",
                    "caracteristicas": ["caracteristica C", "caracteristica D"]
                }}
            ]
        }}
        Se não encontrar jogos, ou se as características forem impróprias, o JSON deve ter a estrutura:
        {{
            "status": "error",
            "message": "Mensagem de erro ou aviso sobre conteúdo impróprio."
        }}
        """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt, 
        config={
        "response_mime_type": "application/json",
        }
    )
    
    # Tenta decodificar a resposta da API Gemini como JSON.
    # É crucial que o Gemini siga o formato, caso contrário, json.loads pode falhar ou retornar algo inesperado.
    try:
        response_data = json.loads(response.text)
        # O Gemini pode retornar um objeto ou uma lista diretamente.
        # Ajustamos para sempre retornar um objeto com 'status' e 'jogos'
        if isinstance(response_data, list): # Se o Gemini retornar apenas uma lista de jogos
            return {"status": "success", "jogos": response_data}
        elif isinstance(response_data, dict) and "nome" in response_data: # Se o Gemini retornar um único objeto de jogo
             return {"status": "success", "jogos": [response_data]}
        else: # Se o Gemini já retornou no formato desejado ou com erro
            return response_data
    except json.JSONDecodeError:
        # Se a resposta do Gemini não for um JSON válido
        return {"status": "error", "message": "Erro na formatação da resposta do modelo AI."}


@app.route('/caracteristica', methods=['POST'])
def search_game_route(): # Renomeado para evitar conflito com a função de cima se for o mesmo nome
    try:
        dados = request.get_json()

        if not dados or not isinstance(dados, dict):
            return jsonify({'status': 'error', 'message': 'Requisição JSON inválida. Esperava um dicionário.'}), 400

        caracteristica = dados.get('caracteristicas')
        preco = dados.get('preco')

        if not caracteristica: # Adicionando validação básica
            return jsonify({'status': 'error', 'message': 'Características são obrigatórias.'}), 400

        if not isinstance(caracteristica, list): # Garante que é uma lista
            caracteristica = [str(caracteristica)] # Converte para lista se for string

        # Se o preço não for fornecido ou for vazio, defina como 0 para buscar gratuitos
        if not preco or str(preco).strip() == '':
            preco = "0"

        response_from_gemini = buscar_jogo(caracteristica, preco) # Chama a função que interage com o Gemini

        # O `buscar_jogo` já está retornando no formato {"status": ..., "jogos": ...} ou {"status": "error", "message": ...}
        return jsonify(response_from_gemini), 200

    except Exception as e:
        print(f"Um erro interno ocorreu na API: {e}")
        return jsonify({'status': 'error', 'message': f'Erro interno do servidor: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
                

