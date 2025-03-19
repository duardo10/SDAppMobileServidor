
# Servidor de Segurança

Este é um servidor Flask que gerencia alertas de segurança, toca um som de alarme e salva imagens de intrusos. O servidor também fornece rotas para interagir com o sistema de segurança.

## Dependências

- **Flask**: A principal biblioteca usada para criar o servidor.
- **Flask-CORS**: Para habilitar CORS (Cross-Origin Resource Sharing) no seu servidor, permitindo que seu aplicativo web ou móvel se conecte sem problemas.
- **pygame**: Usado para tocar o som do alarme.
- **threading** e **time**: Bibliotecas padrão do Python para manipulação de threads e tempo.
- **os** e **datetime**: Bibliotecas padrão do Python para manipulação de arquivos e datas.

## Como rodar o servidor

### 1. Instalar as dependências:

Para rodar o servidor, você precisa instalar as bibliotecas que não são padrão do Python. Use o seguinte comando para instalar as dependências:

```bash
pip install Flask Flask-CORS pygame


## 2. Arquivos necessários:

- **alarm.mp3**: Você deve ter o arquivo `alarm.mp3` no mesmo diretório do seu script para que o alarme seja reproduzido corretamente.
- **security_images/**: O diretório onde as fotos serão salvas. Ele será criado automaticamente, mas você pode garantir que existe, caso contrário.

## 3. Rodar o servidor:

Após instalar as dependências, você pode rodar o servidor com o seguinte comando:

```bash
python nome_do_arquivo.py
```

Substitua `nome_do_arquivo.py` pelo nome do arquivo onde o código do servidor está salvo.

## 4. Verificação:

Quando o servidor estiver rodando, ele estará acessível através de:
- [http://0.0.0.0:5000/](http://0.0.0.0:5000/)
- [http://localhost:5000/](http://localhost:5000/)

---

## Explicação das rotas no servidor:

### 1. `/ping`:
- **Método**: GET
- **Descrição**: Retorna um status de "ok" para verificar se o servidor está ativo.
- **Exemplo de resposta**:

```json
{
  "status": "ok",
  "message": "Server is running"
}
```

### 2. `/alert`:
- **Método**: POST
- **Descrição**: Recebe um alerta e ativa o som do alarme se ele não estiver tocando.
- **Exemplo de requisição**:

```json
{
  "timestamp": "2025-03-18T20:00:00"
}
```

- **Exemplo de resposta**:

```json
{
  "status": "ok",
  "message": "Alert received and alarm triggered",
  "timestamp": "2025-03-18T20:00:00"
}
```

### 3. `/upload-photo`:
- **Método**: POST
- **Descrição**: Recebe uma foto (usada para capturar imagens de intrusos) e a salva com um nome baseado no timestamp.
- **Campos da requisição**:
  - **Arquivo**: Enviar uma imagem com a chave `photo`.
  - **Campo adicional (opcional)**: `timestamp`.
- **Exemplo de requisição (usando um formulário ou cliente como Postman)**:
  - **Chave**: `photo` (arquivo de imagem)
  - **Campo adicional**: `timestamp`
- **Exemplo de resposta**:

```json
{
  "status": "ok",
  "message": "Photo uploaded successfully",
  "filename": "intruder_2025-03-18-200000.jpg",
  "path": "security_images/intruder_2025-03-18-200000.jpg"
}
```

### 4. `/stop-alarm`:
- **Método**: POST
- **Descrição**: Para o alarme, caso esteja tocando.
- **Exemplo de requisição**:

```json
{}
```

- **Exemplo de resposta**:

```json
{
  "status": "ok",
  "message": "Alarm stopped"
}
```

### 5. `/images`:
- **Método**: GET
- **Descrição**: Retorna uma lista de imagens salvas no diretório `security_images`.
- **Exemplo de resposta**:

```json
{
  "status": "ok",
  "images": [
    {
      "filename": "intruder_2025-03-18-200000.jpg",
      "path": "security_images/intruder_2025-03-18-200000.jpg",
      "timestamp": "2025-03-18T20-00-00"
    },
    {
      "filename": "intruder_2025-03-18-200005.jpg",
      "path": "security_images/intruder_2025-03-18-200005.jpg",
      "timestamp": "2025-03-18T20-00-05"
    }
  ]
}
```

