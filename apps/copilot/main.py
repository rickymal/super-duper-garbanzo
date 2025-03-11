#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemplo Didático:
Processamento de código Python com Tree-sitter (CST),
U-Net + Seq2Seq simplificado, e reconstrução aproximada.
"""

import numpy as np
from tree_sitter import Language, Parser
import tensorflow as tf
from tensorflow.keras.layers import (
    Input, Conv1D, Dense, Reshape, Add, Activation
)
from tensorflow.keras.models import Model
from sklearn.neighbors import KNeighborsClassifier

# Para reprodutibilidade (opcional)
tf.random.set_seed(42)
np.random.seed(42)

###############################################################################
# 1. Compilar (ou carregar) a linguagem Python para o Tree-sitter
###############################################################################
# Ajuste os caminhos conforme o local do seu tree-sitter-python
# Exemplo (descomentado se necessário):
# Language.build_library(
#     'build/my-languages.so',
#     [
#         'tree-sitter-python'
#     ]
# )

# Carrega a linguagem compilada
PY_LANGUAGE = Language('build/my-languages.so', 'python')

# Cria o parser e define a linguagem
parser = Parser()
parser.set_language(PY_LANGUAGE)

###############################################################################
# 2. Parsing do código Python com Tree-sitter
###############################################################################

def parse_code_with_tree_sitter(code: str):
    """
    Recebe uma string de código Python e retorna a CST
    (Árvore Sintática Concreta) parseada pelo Tree-sitter.
    """
    tree = parser.parse(bytes(code, "utf8"))
    return tree.root_node

###############################################################################
# 3. Conversão da CST em mnemônicos numéricos
###############################################################################

# Dicionário de tipos de nó -> código numérico (exemplo simplificado)
node_type_to_id = {
    'module': 1,
    'function_definition': 2,
    'parameters': 3,
    'parameter': 4,
    'identifier': 5,
    'block': 6,
    'expression_statement': 7,
    'return_statement': 8,
    'binary_operator': 9,
    'integer': 10,
    'string': 11,
    # ... Adicione outros nós conforme necessário
}

# Base para codificar caracteres
base_char_id = 1000

def get_node_type_id(node):
    """Retorna o ID numérico para o tipo de nó, ou 999 se desconhecido."""
    return node_type_to_id.get(node.type, 999)

def cst_to_mnemonics(node, code_bytes):
    """
    Percorre a CST recursivamente e gera uma lista de mnemônicos.
    - Para cada nó, adiciona [ID do tipo de nó].
    - Se for identifier/string, quebra o texto em caracteres (mnemônicos).
    """
    mnemonics = []
    
    node_type_id = get_node_type_id(node)
    mnemonics.append(node_type_id)
    
    # Se o nó for 'identifier' ou 'string', coletamos os caracteres
    if node.type in ['identifier', 'string']:
        start_byte = node.start_byte
        end_byte = node.end_byte
        text = code_bytes[start_byte:end_byte].decode('utf8')
        
        # Remove aspas se for string
        if node.type == 'string':
            text = text.strip('"').strip("'")
        
        for ch in text:
            mnemonics.append(base_char_id + ord(ch))
    
    # Percorre recursivamente os filhos
    for child in node.children:
        mnemonics.extend(cst_to_mnemonics(child, code_bytes))
        
    return mnemonics

###############################################################################
# 4. Funções de Pré-Processamento (Padding, One-Hot etc.)
###############################################################################

def pad_sequence(seq, max_len):
    """
    Preenche (ou trunca) a sequência de mnemônicos para ter max_len.
    Preenchimento com 0 no final.
    """
    padded = np.zeros((max_len,), dtype='int32')
    length = min(len(seq), max_len)
    padded[:length] = seq[:length]
    return padded

def one_hot_encode(seq, vocab_size, max_len):
    """
    Cria um vetor one-hot de shape (max_len, vocab_size) para a sequência seq.
    """
    out = np.zeros((max_len, vocab_size), dtype='float32')
    for i, val in enumerate(seq):
        if val < vocab_size:
            out[i, val] = 1.0
    return out

###############################################################################
# 5. Construção do Modelo (U-Net + Seq2Seq simplificado)
###############################################################################

def build_unet_seq2seq_model(max_len, vocab_size, filters=32, kernel_size=3):
    """
    Cria um modelo inspirados em U-Net + Seq2Seq:
    - Encoder com Conv1D (extração local).
    - Decoder com Conv1D + skip connections.
    - Atenção simplificada (Conv1D com sigmoid).
    - Saída: shape (max_len, vocab_size), com softmax para cada posição.
    """
    inp = Input(shape=(max_len, vocab_size), name="input_one_hot")
    
    # Encoder
    x = Conv1D(filters=filters, kernel_size=kernel_size, padding='same', activation='relu')(inp)
    x = Conv1D(filters=filters, kernel_size=kernel_size, padding='same', activation='relu')(x)
    
    # Armazena saída do encoder para skip connection
    skip_connection = x
    
    # "Compressão" simples do encoder
    x = Conv1D(filters=filters*2, kernel_size=kernel_size, padding='same', activation='relu')(x)
    
    # Decoder
    x = Conv1D(filters=filters, kernel_size=kernel_size, padding='same', activation='relu')(x)
    
    # Skip connection: soma com a saída do encoder
    x = Add()([x, skip_connection])
    
    # Atenção simplificada
    attn = Conv1D(filters=filters, kernel_size=1, padding='same', activation='sigmoid')(x)
    x = tf.multiply(x, attn)  # aplica a atenção multiplicando
    
    # Projeta para vocab_size
    x = Conv1D(filters=vocab_size, kernel_size=1, padding='same', activation='softmax')(x)
    
    model = Model(inputs=inp, outputs=x, name="u_net_seq2seq")
    return model

###############################################################################
# 6. Exemplo de Uso (Overfitting em 1 snippet de código)
###############################################################################

def main():
    # Exemplo de código Python
    example_code = """
def soma(a, b):
    return a + b
"""
    
    # 6.1 Parsing e conversão para mnemônicos
    root_node = parse_code_with_tree_sitter(example_code)
    mnemonics_seq = cst_to_mnemonics(root_node, bytes(example_code, "utf8"))
    mnemonics_seq = np.array(mnemonics_seq, dtype='int32')
    
    # Definindo tamanho máximo da sequência
    MAX_LEN = 64
    
    # Padding/truncagem
    padded_mnemonics = pad_sequence(mnemonics_seq, max_len=MAX_LEN)
    
    # Definindo vocab_size com base no mnemônico máximo observado
    VOCAB_SIZE = int(padded_mnemonics.max()) + 1
    
    # One-hot
    X_arr = one_hot_encode(padded_mnemonics, vocab_size=VOCAB_SIZE, max_len=MAX_LEN)
    # Para um autoencoder, a saída também é a mesma (X=Y)
    Y_arr = X_arr.copy()
    
    # Ajuste de shape (precisamos de batch dimension)
    X = X_arr[np.newaxis, ...]  # (1, MAX_LEN, VOCAB_SIZE)
    Y = Y_arr[np.newaxis, ...]  # (1, MAX_LEN, VOCAB_SIZE)
    
    # 6.2 Construir o modelo e compilar
    model = build_unet_seq2seq_model(
        max_len=MAX_LEN,
        vocab_size=VOCAB_SIZE,
        filters=16,     # só para ficar mais leve
        kernel_size=3
    )
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.summary()
    
    # 6.3 Treinamento (overfitting)
    EPOCHS = 30
    history = model.fit(
        X, Y,
        epochs=EPOCHS,
        batch_size=1,   # overfitting em 1 exemplo
        verbose=1
    )
    
    # 6.4 Predição
    pred = model.predict(X)  # (1, MAX_LEN, VOCAB_SIZE)
    pred = pred[0]           # (MAX_LEN, VOCAB_SIZE)
    
    # 7. KNN para “arredondar” resultados
    # (Na prática, é muito parecido com o argmax, mas vamos mostrar.)
    knn = KNeighborsClassifier(n_neighbors=1)
    eye_matrix = np.eye(VOCAB_SIZE, dtype='float32')
    labels = np.arange(VOCAB_SIZE)
    knn.fit(eye_matrix, labels)
    
    knn_indices = []
    for i in range(MAX_LEN):
        vec = pred[i].reshape(1, -1)
        nearest_label = knn.predict(vec)
        knn_indices.append(nearest_label[0])
    
    knn_indices = np.array(knn_indices, dtype='int32')
    
    print("Mnemônicos originais:", padded_mnemonics)
    print("Mnemônicos preditos (KNN):", knn_indices)
    
    # 8. Reconstrução de volta para pseudo-texto
    id_to_node_type = {v: k for k, v in node_type_to_id.items()}

    def mnemonics_to_text(mnemonics):
        """
        Converte mnemônicos para uma pseudo-representação textual:
        - <tipo_de_nó> se for nó conhecido.
        - Caractere se for >= base_char_id.
        - <unk:X> caso não reconhecido ou fora do dicionário.
        """
        lines = []
        for m in mnemonics:
            if m == 0:
                continue  # padding
            if m in id_to_node_type:
                lines.append(f"<{id_to_node_type[m]}>")
            elif m >= base_char_id:
                ch = chr(m - base_char_id)
                lines.append(ch)
            else:
                lines.append(f"<unk:{m}>")
        return " ".join(lines)
    
    reconstructed_text = mnemonics_to_text(knn_indices)
    print("\nReconstrução aproximada:\n", reconstructed_text)
    
    # Exemplo de comparação com argmax
    argmax_indices = np.argmax(pred, axis=-1)
    argmax_text = mnemonics_to_text(argmax_indices)
    print("\nReconstrução com argmax:\n", argmax_text)
    
    ###########################################################################
    # Curiosidade: Modelos baseados em Transformers (como GPT-4, CodeBERT etc.)
    # normalmente não usam a CST explicitamente. Mesmo assim, incluir informações
    # sintáticas pode ajudar em tarefas de análise estática e refatoração.
    ###########################################################################

if __name__ == "__main__":
    main()
