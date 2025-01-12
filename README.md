# VRPTW Optimization API

## Descrição
Esta API em Python implementa a resolução do problema de Roteirização de Veículos com Janelas de Tempo (VRPTW) usando OR-Tools e dados do Google Maps. A API recebe uma origem e múltiplos destinos com janelas de tempo, consulta a Google Distance Matrix API para obter tempos de viagem e utiliza um algoritmo de otimização para calcular a rota ideal.

## Arquitetura
- **FastAPI**: Framework web para criação de endpoints HTTP.
- **Google Maps API**: Para obter matrizes de distâncias e tempos.
- **OR-Tools**: Biblioteca de otimização para resolver o VRPTW.
- **Estrutura**:
  - `main.py`: Arquivo principal contendo endpoints, lógica de consulta ao Google Maps, configuração do OR-Tools e solução do problema VRPTW.

## Funcionamento do Algoritmo
1. **Entrada**: Recebe uma origem e uma lista de destinos com janelas de tempo (início e fim).
2. **Consulta de Distâncias**: Utiliza a Google Distance Matrix API para obter tempos entre todos os pontos.
3. **Modelagem do Problema**: Cria um modelo de dados para o OR-Tools, incluindo matrizes de tempo e janelas para cada destino.
4. **Resolução**: O OR-Tools resolve o problema levando em consideração as janelas de tempo, priorizando entregas com prazos próximos.
5. **Saída**: Retorna a sequência de endereços otimizados e um link do Google Maps para visualizar a rota.

## Como Utilizar
1. Configure a chave da API do Google no arquivo `main.py`.
2. Instale as dependências:
````bash
  pip install fastapi uvicorn googlemaps ortools
````
3. Inicie a API:
````bash
  uvicorn main:app --reload
````
4. Acesse a documentação interativa em `http://127.0.0.1:8000/docs` para testar o endpoint `/optimize`.

## Frontend

Há um [Projeto Frontend](https://github.com/alexistoigo/vrptw-api), que pode ser utilizado em conjunto com esta api.

## Exemplo de Body Request
````JSON
  {
   "origin":"Av. Paulista, 1000, São Paulo, SP, Brasil",
   "destinations":[
      {
         "address":"Rua Augusta, 500, São Paulo, SP, Brasil",
         "time_window_start":36000,
         "time_window_end":39600
      },
      {
         "address":"Rua das Flores, 250, São Paulo, SP, Brasil",
         "time_window_start":37800,
         "time_window_end":41400
      },
      {
         "address":"Av. Brigadeiro Faria Lima, 1500, São Paulo, SP, Brasil",
         "time_window_start":32400,
         "time_window_end":36000
      }
   ]
}
````

## Exemplo de Resposta
````JSON
{
	"optimized_route": [
		"Av. Paulista, 1000, São Paulo, SP, Brasil",
		"Av. Brigadeiro Faria Lima, 1500, São Paulo, SP, Brasil",
		"Rua Augusta, 500, São Paulo, SP, Brasil",
		"Rua das Flores, 250, São Paulo, SP, Brasil",
		"Av. Paulista, 1000, São Paulo, SP, Brasil"
	],
	"google_maps_url": "https://www.google.com/maps/dir/?api=1&origin=Av. Paulista, 1000, São Paulo, SP, Brasil&destination=Av. Paulista, 1000, São Paulo, SP, Brasil&waypoints=Av. Brigadeiro Faria Lima, 1500, São Paulo, SP, Brasil|Rua Augusta, 500, São Paulo, SP, Brasil|Rua das Flores, 250, São Paulo, SP, Brasil&travelmode=driving"
}
````

---

*Obs: O algoritmo pode não encontrar uma rota caso o tempo mínimo ou máximo de uma entrega seja impossível de fazer uma rota. 
Ex: uma entrega que precisa ser entregue num período máximo de 15 minutos, porém o tempo de deslocamento da origem leva 30 minutos para percorrer. Neste caso não poderá ser encontrado uma rota.*