
# default_schema_builder.set_serializer(serializer = yamlSerializer)
import datetime
import hashlib
import pickle
import time
from typing import Mapping, Sequence
from .Iexecutable import Step
from .context import SchemaContext
from .output import NoConsole
from .serial_type import SerialType
from .utils import hook_status_in_context, smart_append, smart_unique_iterable


class DefaultSchemaManager:
    def __init__(self, serializer):
        self.transformers = []
        self.serializer = serializer
        self.types : dict[bool, list[SerialType]] = {
            True: [],
            False: []
        }

    def create_mapping_type(self, serialType: SerialType, propagate: bool = True):
        self.types[propagate].append(serialType)

    from collections.abc import Mapping, Sequence

    def validate_all_values(self, data: any):
        file = self.serializer.data
        ref = file[0]['data']
        
        # Verifica se `data` e `ref` são estruturalmente idênticos
        return data == ref

    def validate_partial_values(self, data: any, reference: str):
        file = self.serializer.data
        ref = file[0]['data']
        
        def recursive_compare(sub_data, sub_ref, mode):
            """Função auxiliar recursiva para comparar estruturas aninhadas."""
            
            if isinstance(sub_data, Mapping) and isinstance(sub_ref, Mapping):
                # Comparação de dicionários
                if mode == 'input':
                    # `sub_data` deve estar contido em `sub_ref`
                    return all(
                        key in sub_ref and recursive_compare(value, sub_ref[key], mode)
                        for key, value in sub_data.items()
                    )
                elif mode == 'snapshot':
                    # `sub_ref` deve estar contido em `sub_data`
                    return all(
                        key in sub_data and recursive_compare(sub_data[key], value, mode)
                        for key, value in sub_ref.items()
                    )
            
            elif isinstance(sub_data, Sequence) and isinstance(sub_ref, Sequence) and not isinstance(sub_data, str):
                # Comparação de listas
                if mode == 'input':
                    # Todos os itens de `sub_data` devem estar em `sub_ref`
                    return all(any(recursive_compare(item, ref_item, mode) for ref_item in sub_ref) for item in sub_data)
                elif mode == 'snapshot':
                    # Todos os itens de `sub_ref` devem estar em `sub_data`
                    return all(any(recursive_compare(data_item, item, mode) for data_item in sub_data) for item in sub_ref)
            
            else:
                # Comparação direta para tipos primitivos ou casos base
                return sub_data == sub_ref

        if reference == 'input':
            return recursive_compare(data, ref, 'input')
        elif reference == 'snapshot':
            return recursive_compare(data, ref, 'snapshot')
        else:
            raise NotImplementedError(f"Referência '{reference}' não implementada.")


    def validate_all_schema(self, obj):

        ref = file[0]['schema']
        for should_propagate, types in self.types.items():
            if should_propagate:
                schema_type_aggregator = []
                for serial_type in types:
                    instance = serial_type()
                    if type(obj) in instance.acceptable_field_type():
                        schema_context = SchemaContext(NoConsole(), field = obj)
                        silent = {'status' : 'pending'}
                        schema_context = hook_status_in_context(schema_context, silent)
                        step = Step("", instance.validate, isolated = False)
                        step.execute(schema_context, event_loop=None, thread_pool_executor=None)
                        if silent['status'] == 'approved':
                            schema_type_aggregator.append(instance.schema_format())

                schema_format = smart_append(*schema_type_aggregator)
                if isinstance(obj, dict):
                    properties = {}
                    required = []
                    schema_format['properties'] = properties
                    schema_format['required'] = required

                    for key, value in obj.items():
                        properties[key] = self.build_schema_sketch(value)
                        required.append(key)
                elif isinstance(obj, list):
                    items = [self.build_schema_sketch(rst) for rst in smart_unique_iterable(obj)]
                    schema_format['items'] = items
            else:
                pass
                # raise NotImplementedError("to com preguiça de fazer esse")


    def build_schema_sketch(self, obj):
        schema_formats = []
        for should_propagate, types in self.types.items():
            if should_propagate:
                schema_type_aggregator = []
                for serial_type in types:
                    instance = serial_type()
                    if type(obj) in instance.acceptable_field_type():
                        schema_context = SchemaContext(NoConsole(), field = obj)
                        silent = {'status' : 'pending'}
                        schema_context = hook_status_in_context(schema_context, silent)
                        step = Step("", instance.validate, isolated = False)
                        step.execute(schema_context, event_loop=None, thread_pool_executor=None)
                        if silent['status'] == 'approved':
                            schema_type_aggregator.append(instance.schema_format())

                schema_format = smart_append(*schema_type_aggregator)
                if isinstance(obj, dict):
                    properties = {}
                    required = []
                    schema_format['properties'] = properties
                    schema_format['required'] = required

                    for key, value in obj.items():
                        properties[key] = self.build_schema_sketch(value)
                        required.append(key)
                elif isinstance(obj, list):
                    items = [self.build_schema_sketch(rst) for rst in smart_unique_iterable(obj)]
                    schema_format['items'] = items

                schema_formats.append(schema_format)
            else:
                pass
                # raise NotImplementedError("to com preguiça de fazer esse")
        return smart_append(*schema_formats)

    def calculate_hash(self, obj):
        """Calcula o hash do objeto para garantir a integridade."""
        return hashlib.sha256(pickle.dumps(obj)).hexdigest()
    

    def generate(self, content):
        current_time = time.time()
        schemas = []

        for obj_tuple in content:
            obj, description, metadata = obj_tuple
            
            schemas.append({
                'schema' : self.build_schema_sketch(obj),
                'description' : description,
                'data' : obj,
                'metadata' : metadata,
                'hash' : self.calculate_hash(obj),
                'created_at': datetime.datetime.fromtimestamp(current_time).isoformat(),
                'last_access': datetime.datetime.fromtimestamp(current_time).isoformat(),
            })

        return schemas


    def save(self, final_data: dict):
        self.serializer.save(final_data)

    def load(self):
        self.serializer.load()

