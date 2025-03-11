from collections import defaultdict
from collections.abc import Mapping, Iterable


def smart_append(*iterables):
    # Caso não tenha nenhum iterável fornecido
    if not iterables:
        return []

    # Caso tenha apenas um iterável, retornamos ele diretamente
    if len(iterables) == 1:
        return iterables[0]

    # Inicializamos o resultado com uma cópia do primeiro iterável
    result = iterables[0]

    for current in iterables[1:]:
        if isinstance(result, list) and isinstance(current, list):
            # Append para listas
            result.extend(current)
        
        elif isinstance(result, dict) and isinstance(current, dict):
            # Para dicionários com aninhamento e flatten
            for key in set(result.keys()).union(current.keys()):
                val1 = result.get(key, [])
                val2 = current.get(key, [])
                
                # Se ambos os valores forem dicionários, faz a recursão
                if isinstance(val1, Mapping) and isinstance(val2, Mapping):
                    result[key] = smart_append(val1, val2)
                else:
                    # Converte para lista caso não seja iterável, excluindo strings
                    if not isinstance(val1, Iterable) or isinstance(val1, str):
                        val1 = [val1]
                    if not isinstance(val2, Iterable) or isinstance(val2, str):
                        val2 = [val2]
                    
                    # Concatena e achata os valores
                    result[key] = list(val1) + list(val2)
        
        else:
            raise TypeError("Todos os argumentos devem ser do tipo list ou dict, e compatíveis entre si.")
    
    return result



def freeze_structure(item):
    """Converte estruturas mutáveis (listas, dicionários) em tuplas imutáveis para comparação."""
    if isinstance(item, Mapping):
        # Para dicionários, converte para tupla de chave-valor ordenada para consistência
        return tuple((key, freeze_structure(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        # Para listas, converte recursivamente cada item para sua versão imutável
        return tuple(freeze_structure(sub_item) for sub_item in item)
    else:
        # Para tipos primitivos, retorna o próprio valor
        return item

def smart_unique_iterable(lst):
    """Remove elementos duplicados estruturalmente de uma lista, incluindo estruturas aninhadas."""
    seen = set()
    unique_list = []
    
    for item in lst:
        # Converte o item para uma estrutura imutável para comparação
        frozen_item = freeze_structure(item)
        if frozen_item not in seen:
            # Se a estrutura ainda não foi vista, adiciona à lista e marca como vista
            unique_list.append(item)
            seen.add(frozen_item)
    
    return unique_list

class MultiDict:
    def __init__(self):
        # Cada par de chave principal e valor armazena o conjunto completo de chaves relacionadas
        self.relations = defaultdict(set)

    def insert(self, keys, value=None):
        # Converte o conjunto de chaves em uma tupla imutável para usá-las como chave única
        key_tuple = tuple(keys.items())
        
        # Adiciona a tupla de cada chave ao conjunto de cada chave individual
        for single_key, single_value in keys.items():
            # Cada chave individual aponta para o conjunto de todas as outras chaves e valores
            self.relations[(single_key, single_value)].add(key_tuple)

    def get(self, query):
        # Converte a consulta em uma tupla para buscar na estrutura de dados
        query_tuple = tuple(query.items())
        # Pega todos os conjuntos de chaves relacionadas
        results = self.relations.get(query_tuple, set())
        
        # Monta o resultado excluindo a própria chave consultada para evitar repetições
        final_results = []
        for result in results:
            result_dict = dict(result)
            if query_tuple in result:
                final_results.append({k: v for k, v in result if (k, v) != query_tuple})
        
        return final_results




def hook_status_in_context(actual_context, state = {'status': 'not initialized'}):
    actual_context.on_approved = lambda : state.update({'status': 'approved'})
    actual_context.on_rejected = lambda : state.update({'status': 'rejected'})
    actual_context.on_concluded = lambda : state.update({'status': 'concluded'})
    actual_context.on_status_checked = lambda : state['status']

    return actual_context
