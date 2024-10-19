import os
import pickle
import hashlib
import time
import datetime
import json
import yaml
import toml
import hcl2
from graphviz import Digraph

class Snapshot:
    def __init__(self, snapshot_name):
        self.snapshot_dir = 'mock'
        self.snapshot_dist = 'dist'
        self.snapshot_name = snapshot_name
        self.snapshot_file = os.path.join(self.snapshot_dir, f'{snapshot_name}.pkl')

        # Cria o diretório "mock" se não existir
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

        # Cria o diretório "dist" se não existir
        if not os.path.exists(self.snapshot_dist):
            os.makedirs(self.snapshot_dist)

    def calculate_hash(self, obj):
        """Calcula o hash do objeto para garantir a integridade."""
        return hashlib.sha256(pickle.dumps(obj)).hexdigest()

    def dict_to_hcl(self, d, indent=0):
        """Converte um dicionário em uma string HCL."""
        hcl_str = ''
        for key, value in d.items():
            hcl_str += '  ' * indent + f'{key} = {self.format_hcl_value(value, indent)}\n'
        return hcl_str

    def format_hcl_value(self, value, indent):
        """Formata o valor para o formato HCL apropriado."""
        if isinstance(value, dict):
            return '{\n' + self.dict_to_hcl(value, indent + 1) + '  ' * indent + '}'
        elif isinstance(value, list):
            return '[{}]'.format(', '.join([self.format_hcl_value(v, indent) for v in value]))
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return 'null'
        else:
            raise TypeError(f'Unsupported type: {type(value)}')

    def create_snapshot(self, obj, version='latest', metadata=None, format='pkl'):
        """
        Cria um novo snapshot com data, hash e metadados opcionais.
        Permite serializar em diferentes formatos: 'pkl', 'json', 'yml', 'toml', 'hcl'.
        """
        current_time = time.time()
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')
        snapshot_data = {
            'snapshot': obj,
            'hash': self.calculate_hash(obj),
            'version': version,
            'created_at': current_time,
            'last_access': current_time,
            'metadata': metadata or {}
        }
        
        # Salva o snapshot no formato escolhido
        if format == 'pkl':
            with open(versioned_file, 'wb') as f:
                pickle.dump(snapshot_data, f)
        elif format == 'json':
            with open(versioned_file, 'w') as f:
                json.dump(snapshot_data, f, indent=4)
        elif format == 'yml':
            with open(versioned_file, 'w') as f:
                yaml.dump(snapshot_data, f)
        elif format == 'toml':
            with open(versioned_file, 'w') as f:
                toml.dump(snapshot_data, f)
        elif format == 'hcl':
            with open(versioned_file, 'w') as f:
                hcl_str = self.dict_to_hcl(snapshot_data)
                f.write(hcl_str)
        
        print(f"Snapshot criado em {versioned_file} com metadados: {metadata}")
        return obj

    def get_or_create_snapshot(self, obj, version='latest', expiration_time=3600, format='pkl'):
        """
        Obtém um snapshot se ele existir e estiver válido, senão cria um novo.
        Suporta recuperação de snapshots em 'pkl', 'json', 'yml', 'toml', 'hcl'.
        """
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')
        current_time = time.time()

        if os.path.exists(versioned_file):
            # Recupera o snapshot baseado no formato
            if format == 'pkl':
                with open(versioned_file, 'rb') as f:
                    snapshot_data = pickle.load(f)
            elif format == 'json':
                with open(versioned_file, 'r') as f:
                    snapshot_data = json.load(f)
            elif format == 'yml':
                with open(versioned_file, 'r') as f:
                    snapshot_data = yaml.safe_load(f)
            elif format == 'toml':
                with open(versioned_file, 'r') as f:
                    snapshot_data = toml.load(f)
            elif format == 'hcl':
                with open(versioned_file, 'r') as f:
                    snapshot_data = hcl2.load(f)
            
            # Verifica expiração do snapshot
            if current_time - snapshot_data['created_at'] > expiration_time:
                print(f"Snapshot {version} expirou. Criando um novo.")
                return self.create_snapshot(obj, version, format=format)

            # Validação do hash
            if self.calculate_hash(snapshot_data['snapshot']) != snapshot_data['hash']:
                raise ValueError(f"Snapshot {version} está corrompido!")

            # Atualiza o tempo de último acesso
            snapshot_data['last_access'] = current_time
            with open(versioned_file, 'wb' if format == 'pkl' else 'w') as f:
                if format == 'pkl':
                    pickle.dump(snapshot_data, f)
                elif format == 'json':
                    json.dump(snapshot_data, f, indent=4)
                elif format == 'yml':
                    yaml.dump(snapshot_data, f)
                elif format == 'toml':
                    toml.dump(snapshot_data, f)
                elif format == 'hcl':
                    hcl_str = self.dict_to_hcl(snapshot_data)
                    f.write(hcl_str)

            print(f"Recuperando snapshot de {versioned_file}")
            return snapshot_data['snapshot']
        else:
            return self.create_snapshot(obj, version, format=format)

    def compare_snapshots(self, version1='latest', version2='latest', format='pkl'):
        """Compara dois snapshots e identifica diferenças."""
        file1 = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version1}.{format}')
        file2 = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version2}.{format}')

        if not os.path.exists(file1) or not os.path.exists(file2):
            raise FileNotFoundError("Um ou ambos os snapshots não foram encontrados")

        if format == 'pkl':
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                snapshot1 = pickle.load(f1)['snapshot']
                snapshot2 = pickle.load(f2)['snapshot']
        elif format == 'json':
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                snapshot1 = json.load(f1)['snapshot']
                snapshot2 = json.load(f2)['snapshot']
        elif format == 'yml':
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                snapshot1 = yaml.safe_load(f1)['snapshot']
                snapshot2 = yaml.safe_load(f2)['snapshot']
        elif format == 'toml':
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                snapshot1 = toml.load(f1)['snapshot']
                snapshot2 = toml.load(f2)['snapshot']
        elif format == 'hcl':
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                snapshot1 = hcl2.load(f1)['snapshot']
                snapshot2 = hcl2.load(f2)['snapshot']

        if snapshot1 == snapshot2:
            print("Os snapshots são idênticos")
        else:
            print("Diferenças encontradas entre os snapshots")

    def generate_snapshot_docs(self, version='latest', format='pkl'):
        """
        Gera documentação automática do snapshot, salvando em formato Markdown (.md).
        """
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')
        if os.path.exists(versioned_file):
            # Carregar o snapshot no formato correto
            if format == 'pkl':
                with open(versioned_file, 'rb') as f:
                    snapshot_data = pickle.load(f)
            elif format == 'json':
                with open(versioned_file, 'r') as f:
                    snapshot_data = json.load(f)
            elif format == 'yml':
                with open(versioned_file, 'r') as f:
                    snapshot_data = yaml.safe_load(f)
            elif format == 'toml':
                with open(versioned_file, 'r') as f:
                    snapshot_data = toml.load(f)
            elif format == 'hcl':
                with open(versioned_file, 'r') as f:
                    snapshot_data = hcl2.load(f)

            # Gerar a documentação
            with open(os.path.join(self.snapshot_dist, f'{self.snapshot_name}_{version}.md'), 'w') as doc:
                doc.write(f"# Snapshot {version}\n")
                doc.write(f"**Criado em**: {datetime.datetime.fromtimestamp(snapshot_data['created_at'])}\n")
                doc.write(f"**Hash**: {snapshot_data['hash']}\n")
                doc.write(f"**Metadados**: {snapshot_data.get('metadata', {})}\n")
                print(f"Documentação gerada para o snapshot {version}!")
        else:
            print(f"Snapshot {version} não encontrado para gerar documentação.")


# Exemplo de uso
if __name__ == '__main__':
    snapshot = Snapshot('my_test_snapshot')

    # Exemplo de objeto (pode ser qualquer coisa: lista, dict, etc.)
    my_data = {"key": "value", "another_key": [1, 2, 3]}

    # Cria um snapshot com metadados e em formato TOML
    snapshot.create_snapshot(my_data, version='0.0.1', metadata={"author": "Henrique"}, format='toml')

    # Recupera o snapshot em formato TOML
    snapshot.get_or_create_snapshot(my_data, version='0.0.1', format='toml')

    # Gera a documentação automática do snapshot
    snapshot.generate_snapshot_docs(version='0.0.1', format='toml')


    snapshot = Snapshot('my_test_snapshot 2')

    # Exemplo de objeto (pode ser qualquer coisa: lista, dict, etc.)
    my_data = {"key": "value", "another_key": [1, 2, 3]}

    # Cria um snapshot com metadados e em formato TOML
    snapshot.create_snapshot(my_data, version='0.0.1', metadata={"author": "Henrique"}, format='hcl')

    # Recupera o snapshot em formato TOML
    snapshot.get_or_create_snapshot(my_data, version='0.0.1', format='hcl')

    # Gera a documentação automática do snapshot
    snapshot.generate_snapshot_docs(version='0.0.1', format='hcl')
