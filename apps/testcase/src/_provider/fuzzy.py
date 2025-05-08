import random
from sqlite3 import IntegrityError
from typing import Dict, List, Optional, Type, Any






class FieldValidator:
    """Classe base para validar campos."""
    def validate(self, value: Any) -> bool:
        """Valida se o valor é aceitável para o campo."""
        raise NotImplementedError("Método validate deve ser implementado.")


# Função fuzzy_dict adaptada
def fuzzy_dict(
    dto_class: Type,
    num_fields_to_change: int = 1,
    num_results: int = 1,
    seed: Optional[int] = None,
    max_attempts: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Gera variações de um DTO, modificando alguns campos e validando as alterações.

    Args:
        dto_class (Type): A classe do DTO.
        num_fields_to_change (int): Número de campos que serão modificados em cada variação.
        num_results (int): Número de variações a serem geradas.
        seed (Optional[int]): Semente para o gerador de números aleatórios.
        max_attempts (int): Número máximo de tentativas para gerar uma variação válida.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários modificados e validados.
    """
    if seed is not None:
        random.seed(seed)

    # Obtém os campos e seus tipos do DTO
    fields = {k: v for k, v in dto_class.__annotations__.items()}
    results = []
    attempts = 0

    while len(results) < num_results and attempts < max_attempts:
        # Cria um novo dicionário com valores gerados
        new_dict = {}
        for field, field_type in fields.items():
            new_dict[field] = field_type.generate()

        # Valida o novo dicionário
        is_valid = True
        for field, field_type in fields.items():
            if not field_type.validate(new_dict[field]):
                is_valid = False
                break

        if is_valid:
            results.append(new_dict)

        attempts += 1

    if attempts >= max_attempts:
        print(f"Aviso: Número máximo de tentativas ({max_attempts}) atingido. Resultados podem estar incompletos.")

    return results


# Exemplo de uso
if __name__ == "__main__":
    # Gerando variações do DTO ClearingMessage
    results = fuzzy_dict(
        ClearingMessage,
        num_fields_to_change=2,
        num_results=5,
        seed=42,
    )

    # Exibindo os resultados
    for i, result in enumerate(results, 1):
        print(f"Variação {i}: {result}")

    # Instanciando um DTO a partir de um JSON
    json_data = {"id": 42, "name": "Alice"}
    clearing_message = ClearingMessage.from_json(json_data)
    print(f"DTO instanciado: {clearing_message}")


if __name__ == "__main__":
    class IntValidator(FieldValidator):
        """Valida se o valor é um inteiro entre 0 e 100."""

        def validate(self, value: Any) -> bool:
            return isinstance(value, int) and 0 <= value <= 100


    class StrValidator(FieldValidator):
        """Valida se o valor é uma string não vazia."""

        def validate(self, value: Any) -> bool:
            return isinstance(value, str) and len(value) > 0


    # Dicionário original
    original_dict = {
        "age": 25,
        "name": "Alice",
        "height": 1.65,
    }

    # Template de validação
    validation_template = {
        "age": IntValidator,
        "name": StrValidator,
    }

    # Gerando variações
    results = fuzzy_dict(
        original_dict,
        fields_to_modify=["age", "name"],
        validation_template=validation_template,
        num_fields_to_change=2,
        num_results=5,
        seed=42,
    )

    # Exibindo os resultados
    for i, result in enumerate(results, 1):
        print(f"Variação {i}: {result}")